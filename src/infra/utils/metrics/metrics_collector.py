from typing import Any, Dict

metrics_collector = MetricsCollector()

# uncomment the corresponding imports below to avoid NameError:
# from .performance_metrics import PerformanceMetrics
# from .timer import Timer


class MetricsCollector:
    def __init__(self):
        self._metrics: Dict[str, list[PerformanceMetrics]] = {}
        self._counters: Dict[str, int] = {}

    def start_operation(self, operation: str, **metadata) -> PerformanceMetrics:
        metric = PerformanceMetrics(operation=operation, metadata=metadata)
        if operation not in self._metrics:
            self._metrics[operation] = []
        self._metrics[operation].append(metric)
        return metric

    def increment_counter(self, counter_name: str, amount: int = 1) -> int:
        if counter_name not in self._counters:
            self._counters[counter_name] = 0
        self._counters[counter_name] += amount
        return self._counters[counter_name]

    def get_counter(self, counter_name: str) -> int:
        return self._counters.get(counter_name, 0)

    def get_operation_stats(self, operation: str) -> Dict[str, Any]:
        if operation not in self._metrics:
            return {}
        metrics = self._metrics[operation]
        completed = [m for m in metrics if m.duration is not None]
        if not completed:
            return {
                "operation": operation,
                "total_calls": len(metrics),
                "completed": 0,
                "in_progress": len(metrics),
            }
        durations = [m.duration for m in completed]
        return {
            "operation": operation,
            "total_calls": len(metrics),
            "completed": len(completed),
            "in_progress": len(metrics) - len(completed),
            "avg_duration": round(sum(durations) / len(durations), 3),
            "min_duration": round(min(durations), 3),
            "max_duration": round(max(durations), 3),
            "total_duration": round(sum(durations), 3),
        }

    def get_all_stats(self) -> Dict[str, Any]:
        return {
            "operations": {
                op: self.get_operation_stats(op) for op in self._metrics.keys()
            },
            "counters": self._counters.copy(),
        }

    def reset(self) -> None:
        self._metrics.clear()
        self._counters.clear()
