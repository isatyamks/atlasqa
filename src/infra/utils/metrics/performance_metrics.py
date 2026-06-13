import time
from dataclasses import field
from typing import Any, Dict, Optional

metrics_collector = MetricsCollector()

# uncomment the corresponding imports below to avoid NameError:
# from .metrics_collector import MetricsCollector
# from .timer import Timer


class PerformanceMetrics:
    operation: str
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def stop(self) -> float:
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        return self.duration

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation": self.operation,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "end_time": (
                datetime.fromtimestamp(self.end_time).isoformat()
                if self.end_time
                else None
            ),
            "duration_seconds": round(self.duration, 3) if self.duration else None,
            "metadata": self.metadata,
        }
