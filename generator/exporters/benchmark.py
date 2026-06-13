import json
import os
import random
from pathlib import Path

from generator.core.engine.dataset import generator


def generate_evaluation_benchmark(
    generator: generator, base_dir: str, tenant_id: str = "tenant_default"
):
    root = Path(base_dir) / "test"
    os.makedirs(root, exist_ok=True)

    queries = []

    # Query Type 1: What services depend on X / Who owns X
    if generator.services and generator.teams:
        svc = random.choice(generator.services)
        team = next((t for t in generator.teams if t.id == svc.team_id), None)
        if team:
            queries.append(
                {
                    "query": f"Which team owns {svc.name}?",
                    "expected_answer": team.name,
                    "expected_evidence_nodes": [svc.id, team.id],
                }
            )

    # Query Type 2: Incident Root Cause
    for inc in generator.incidents[:5]:
        pm = next(
            (
                p
                for p in getattr(generator, "postmortems", [])
                if p.incident_id == inc.id
            ),
            None,
        )
        if pm:
            queries.append(
                {
                    "query": f"What was the root cause of {inc.id}?",
                    "expected_answer": pm.root_cause_summary,
                    "expected_evidence_nodes": [inc.id, pm.id],
                }
            )

    # Query Type 3: Missing Tests
    untested_reqs = [
        r
        for r in generator.requirements
        if not any(tc.requirement_id == r.id for tc in generator.test_cases)
    ]
    if untested_reqs:
        queries.append(
            {
                "query": "List 3 requirements that are missing test cases.",
                "expected_answer": ", ".join([r.id for r in untested_reqs[:3]]),
                "expected_evidence_nodes": [r.id for r in untested_reqs[:3]],
            }
        )

    with open(root / f"{tenant_id}.json", "w") as f:
        json.dump(queries, f, indent=2)

    print(f"Exported evaluation benchmark to {root / f'{tenant_id}.json'}")
    return queries
