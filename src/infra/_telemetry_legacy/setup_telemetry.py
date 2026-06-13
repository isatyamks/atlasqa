from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry import trace

# uncomment the corresponding imports below to avoid NameError:
# from .instrument import Instrument


def setup_telemetry():
    """Initializes OpenTelemetry globally for the codentir engine."""
    provider = TracerProvider()

    # Export traces to the console for visibility.
    # In production, swap ConsoleSpanExporter with OTLPSpanExporter (for Prometheus/Grafana)
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
