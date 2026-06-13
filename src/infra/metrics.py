# Re-export metrics_collector from its original nested location.
from src.infra.utils.metrics.metrics_collector import metrics_collector

__all__ = ["metrics_collector"]
