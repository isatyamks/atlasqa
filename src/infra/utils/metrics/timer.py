from typing import Optional

metrics_collector = MetricsCollector()

# uncomment the corresponding imports below to avoid NameError:
# from .performance_metrics import PerformanceMetrics
# from .metrics_collector import MetricsCollector


class timer:
    def __init__(self, operation: str, **metadata):
        self.operation = operation
        self.metadata = metadata
        self.metric: Optional[PerformanceMetrics] = None

    def __enter__(self) -> PerformanceMetrics:
        self.metric = metrics_collector.start_operation(self.operation, **self.metadata)
        return self.metric

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.metric:
            self.metric.stop()
