"""
Telemetry helpers — flattened from infra/telemetry/instrument.py + setup_telemetry.py.
"""

import logging
import time
from functools import wraps

logger = logging.getLogger(__name__)

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter


def setup_telemetry():
    """Initializes OpenTelemetry globally for the codentir engine."""
    provider = TracerProvider()
    # Export traces to the console for visibility.
    # In production, swap ConsoleSpanExporter with OTLPSpanExporter (Prometheus/Grafana).
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)


def instrument(span_name: str):
    """
    A clean decorator to trace execution time and flow of any function
    without polluting business logic.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span(span_name) as span:
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    span.set_status(trace.StatusCode.OK)
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(trace.StatusCode.ERROR, str(e))
                    raise e
                finally:
                    duration = (time.time() - start_time) * 1000
                    span.set_attribute("latency_ms", duration)

        return wrapper

    return decorator
