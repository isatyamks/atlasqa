from typing import Dict, List

from src.data.graph import GraphService
from src.engine.causal.models import ImpactExplanation
from src.infra.telemetry import instrument


class ImpactService:
    def __init__(self, graph_svc: GraphService):
        self.graph_svc = graph_svc

    @instrument(span_name="impact_calculate_blast_radius")
    def calculate_blast_radius(
        self, root_cause_ids: List[str], tenant_id: str
    ) -> Dict[str, List[ImpactExplanation]]:
        """
        Calculates 7-dimensional blast radius based on the proven root cause(s).
        Returns evidence-backed explanations for every affected entity.
        """
        blast_radius = {
            "Affected Services": {},
            "Affected APIs": {},
            "Affected Requirements": {},
            "Affected Tests": {},
            "Affected Owners": {},
            "Affected Deployments": {},
            "Affected Downstream Services": {},
        }

        g = self.graph_svc.graph

        for root_id in root_cause_ids:
            if "::" not in root_id:
                root_id = f"{tenant_id}::{root_id}"

            if root_id in g:
                # Constrained BFS for dependency-aware propagation
                reachable = {root_id}
                queue = [root_id]

                VALID_EDGE_TYPES = {
                    "exposes_api",
                    "has_dependency",
                    "deployed_service",
                    "belongs_to_team",
                    "has_repository",
                    "shipped_in",
                    "has_member",
                }

                paths = {root_id: [root_id]}

                while queue:
                    current = queue.pop(0)
                    for neighbor in g.neighbors(current):
                        edge_data = g.get_edge_data(current, neighbor)
                        if edge_data and edge_data.get("type") in VALID_EDGE_TYPES:
                            if neighbor not in reachable:
                                reachable.add(neighbor)
                                queue.append(neighbor)
                                paths[neighbor] = paths[current] + [neighbor]

                for node_id in reachable:
                    node_data = g.nodes[node_id]
                    ntype = node_data.get("type")
                    clean_id = node_id.split("::")[-1]

                    path = paths[node_id]

                    # Calculate score
                    impact_score = max(0.95 - (len(path) * 0.05), 0.1)

                    # Determine reason
                    reason = (
                        f"Depends on {path[-2].split('::')[-1]}"
                        if len(path) > 1
                        else "Direct root cause node."
                    )

                    explanation = ImpactExplanation(
                        entity_id=clean_id,
                        reason=reason,
                        graph_path=path,
                        impact_score=round(impact_score, 2),
                    )

                    category = None
                    if ntype == "service":
                        category = "Affected Services"
                    elif ntype == "api":
                        category = "Affected APIs"
                    elif ntype == "requirement":
                        category = "Affected Requirements"
                    elif ntype == "test_case":
                        category = "Affected Tests"
                    elif ntype == "team":
                        category = "Affected Owners"
                    elif ntype == "deployment":
                        category = "Affected Deployments"

                    if category:
                        if clean_id not in blast_radius[category]:
                            blast_radius[category][clean_id] = explanation
                        elif (
                            blast_radius[category][clean_id].impact_score < impact_score
                        ):
                            blast_radius[category][clean_id] = explanation

        # Convert dicts to sorted lists
        return {
            k: sorted(list(v.values()), key=lambda x: x.impact_score, reverse=True)
            for k, v in blast_radius.items()
        }
