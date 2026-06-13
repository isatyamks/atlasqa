import logging
from datetime import datetime
from typing import Any, Dict, List

from src.core.entities import Dataset
from src.infra.telemetry import instrument

logger = logging.getLogger(__name__)


class TimelineBuilder:
    def __init__(self, dataset: Dataset):
        self.dataset = dataset

    @instrument(span_name="timeline_build")
    def build_timeline(self, artifact_ids: List[str]) -> List[Dict[str, Any]]:
        """Sorts all evidence into a strict chronological trace."""
        timeline = []

        for aid in artifact_ids:
            if aid in self.dataset.incidents:
                inc = self.dataset.incidents[aid]
                content = f"{inc.title}\nSymptoms: {inc.symptoms}"
                timeline.append({"id": aid, "type": "Incident", "time": inc.created_at, "content": content})
            elif aid in self.dataset.tickets:
                tkt = self.dataset.tickets[aid]
                content = f"{tkt.summary}\nDescription: {tkt.description}"
                timeline.append({"id": aid, "type": "Ticket", "time": tkt.created_at, "content": content})
            elif aid in self.dataset.commits:
                commit = self.dataset.commits[aid]
                timeline.append({"id": aid, "type": "Commit", "time": commit.date, "content": commit.message})
            elif aid in self.dataset.requirements:
                req = self.dataset.requirements[aid]
                content = f"{req.title}\nObjective: {req.business_objective}"
                timeline.append({"id": aid, "type": "Requirement", "time": req.created_at, "content": content})

        try:
            timeline.sort(
                key=lambda x: (
                    datetime.fromisoformat(str(x["time"]))
                    if isinstance(x["time"], str)
                    else x["time"]
                )
            )
        except Exception:
            logger.exception("An error occurred sorting timeline")

        return timeline

