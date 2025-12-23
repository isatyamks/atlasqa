from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ParsedDocument:
    file_path: Path
    content: str
    file_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    parse_timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def filename(self) -> str:
        return self.file_path.name
    
    @property
    def file_size(self) -> int:
        return len(self.content.encode('utf-8'))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": str(self.file_path),
            "filename": self.filename,
            "content": self.content,
            "content_length": len(self.content),
            "file_type": self.file_type,
            "metadata": self.metadata,
            "parse_timestamp": self.parse_timestamp.isoformat(),
            "file_size_bytes": self.file_size
        }


class BaseParser(ABC):
    
    def __init__(self):
        self.supported_extensions: List[str] = []
    
    @abstractmethod
    def parse(self, file_path: Path) -> ParsedDocument:
        pass
    
    def can_parse(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.supported_extensions
    
    def validate_file(self, file_path: Path) -> None:
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        if not self.can_parse(file_path):
            raise ValueError(
                f"Unsupported file type: {file_path.suffix}. "
                f"Supported: {', '.join(self.supported_extensions)}"
            )
    
    def extract_basic_metadata(self, file_path: Path) -> Dict[str, Any]:
        stat = file_path.stat()
        
        return {
            "file_name": file_path.name,
            "file_extension": file_path.suffix.lower(),
            "file_size_bytes": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }
