import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class BaseConnector(ABC):
    """
    Abstract base class for all SaaS API connectors.
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the target service."""

    @abstractmethod
    def fetch_data(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Fetch raw data from the service."""

    @abstractmethod
    def export_to_fs(self, output_dir: str, data: List[Dict[str, Any]]) -> None:
        """Export fetched data to the filesystem in the format expected by FileSystemgeneratorReader."""

    def _save_json(
        self, output_dir: str, folder_name: str, file_id: str, payload: dict
    ):
        """Helper to save a JSON payload to the correct directory."""
        target_dir = Path(output_dir) / self.tenant_id / folder_name
        target_dir.mkdir(parents=True, exist_ok=True)

        file_path = target_dir / f"{file_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
