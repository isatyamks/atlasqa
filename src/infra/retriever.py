"""
Retriever implementations — BM25, Dense (embedding-based), and Hybrid.
These are concrete implementations of src.core.contracts.IRetriever.
"""

from typing import List

from src.core.contracts import IRetriever, ICrossEncoderReranker, SearchResult
from src.core.entities import Dataset


class BM25Retriever(IRetriever):
    """Sparse BM25 keyword retriever."""

    def __init__(self):
        self._corpus: List[str] = []
        self._meta: List[dict] = []

    def index(self, dataset: Dataset) -> None:
        self._corpus = []
        self._meta = []
        self._index_collection(dataset.tickets, "ticket")
        self._index_collection(dataset.commits, "commit")
        self._index_collection(dataset.incidents, "incident")
        self._index_collection(dataset.slack_messages, "slack_message")
        self._index_collection(dataset.pull_requests, "pull_request")
        self._index_collection(dataset.requirements, "requirement")
        self._index_collection(dataset.alerts, "alert")
        self._index_collection(dataset.postmortems, "postmortem")

    def _index_collection(self, collection: dict, artifact_type: str):
        for artifact_id, obj in collection.items():
            text = self._to_text(obj)
            self._corpus.append(text)
            self._meta.append(
                {
                    "artifact_id": artifact_id,
                    "artifact_type": artifact_type,
                    "content": text,
                    "tenant_id": getattr(obj, "tenant_id", "tenant_default"),
                }
            )

    def _to_text(self, obj) -> str:
        parts = []
        for field in ["summary", "message", "title", "text", "symptoms", "observations", "content", "description", "body"]:
            v = getattr(obj, field, None)
            if v:
                parts.append(str(v))
        return " ".join(parts)

    def search(self, query: str, tenant_id: str, top_k: int = 10) -> List[SearchResult]:
        """Simple keyword overlap BM25 approximation."""
        query_tokens = set(query.lower().split())
        scored = []
        for meta, text in zip(self._meta, self._corpus):
            if meta["tenant_id"] != tenant_id:
                continue
            doc_tokens = set(text.lower().split())
            overlap = len(query_tokens & doc_tokens)
            if overlap > 0:
                score = overlap / (len(doc_tokens) + 1)
                scored.append((score, meta))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            SearchResult(
                artifact_id=m["artifact_id"],
                artifact_type=m["artifact_type"],
                score=s,
                content=m["content"][:500],
                tenant_id=m["tenant_id"],
            )
            for s, m in scored[:top_k]
        ]


class DenseRetriever(IRetriever):
    """Dense embedding-based retriever using sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model_name = model_name
        self._embeddings = []
        self._meta = []
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self._model_name)
            except ImportError:
                self._model = None
        return self._model

    def index(self, dataset: Dataset) -> None:
        self._embeddings = []
        self._meta = []
        model = self._get_model()

        for collection, atype in [
            (dataset.tickets, "ticket"),
            (dataset.commits, "commit"),
            (dataset.incidents, "incident"),
            (dataset.slack_messages, "slack_message"),
            (dataset.pull_requests, "pull_request"),
        ]:
            for artifact_id, obj in collection.items():
                text = self._to_text(obj)
                self._meta.append({
                    "artifact_id": artifact_id,
                    "artifact_type": atype,
                    "content": text,
                    "tenant_id": getattr(obj, "tenant_id", "tenant_default"),
                })
                if model:
                    self._embeddings.append(model.encode(text))

    def _to_text(self, obj) -> str:
        parts = []
        for field in ["summary", "message", "title", "text", "symptoms", "observations"]:
            v = getattr(obj, field, None)
            if v:
                parts.append(str(v))
        return " ".join(parts)

    def search(self, query: str, tenant_id: str, top_k: int = 10) -> List[SearchResult]:
        model = self._get_model()
        if not model or not self._embeddings:
            return []

        import numpy as np
        q_emb = model.encode(query)
        scores = []
        for i, (emb, meta) in enumerate(zip(self._embeddings, self._meta)):
            if meta["tenant_id"] != tenant_id:
                continue
            sim = float(np.dot(q_emb, emb) / (np.linalg.norm(q_emb) * np.linalg.norm(emb) + 1e-8))
            scores.append((sim, meta))

        scores.sort(key=lambda x: x[0], reverse=True)
        return [
            SearchResult(
                artifact_id=m["artifact_id"],
                artifact_type=m["artifact_type"],
                score=s,
                content=m["content"][:500],
                tenant_id=m["tenant_id"],
            )
            for s, m in scores[:top_k]
        ]


class HybridRetriever(IRetriever):
    """Combines BM25 + Dense retrieval with optional reranking."""

    def __init__(
        self,
        bm25: BM25Retriever,
        dense: DenseRetriever,
        reranker: ICrossEncoderReranker = None,
        alpha: float = 0.5,
    ):
        self.bm25 = bm25
        self.dense = dense
        self.reranker = reranker
        self.alpha = alpha

    def index(self, dataset: Dataset) -> None:
        self.bm25.index(dataset)
        self.dense.index(dataset)

    def search(self, query: str, tenant_id: str, top_k: int = 10) -> List[SearchResult]:
        bm25_results = self.bm25.search(query, tenant_id, top_k=top_k * 2)
        dense_results = self.dense.search(query, tenant_id, top_k=top_k * 2)

        # Reciprocal rank fusion
        scores: dict = {}
        for rank, r in enumerate(bm25_results):
            scores[r.artifact_id] = scores.get(r.artifact_id, 0) + (1 - self.alpha) / (rank + 1)
        for rank, r in enumerate(dense_results):
            scores[r.artifact_id] = scores.get(r.artifact_id, 0) + self.alpha / (rank + 1)

        # Rebuild merged results
        seen = {}
        for r in bm25_results + dense_results:
            if r.artifact_id not in seen:
                seen[r.artifact_id] = r

        merged = sorted(seen.values(), key=lambda r: scores.get(r.artifact_id, 0), reverse=True)
        merged = merged[:top_k]

        for r in merged:
            r.score = scores.get(r.artifact_id, 0)

        if self.reranker and merged:
            merged = self.reranker.rerank(query, merged)

        return merged
