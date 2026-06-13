import logging

logger = logging.getLogger(__name__)

import time
from functools import wraps
from opentelemetry import trace

# uncomment the corresponding imports below to avoid NameError:
# from .setup_telemetry import SetupTelemetry


def instrument(span_name: str):
    """
    A clean, SOLID-compliant decorator to trace the execution time and flow
    of any Python microservice function without polluting the business logic.
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
