"""Trazas OpenTelemetry del backend (opcionales, activadas por configuración).

Cada solicitud genera un span HTTP (instrumentación de FastAPI) y un span hijo
de inferencia con atributos de las convenciones semánticas GenAI de
OpenTelemetry (gen_ai.*) más las métricas de la Unidad F (TTFT, TPOT).

Las convenciones GenAI están en estado de desarrollo en la especificación de
OpenTelemetry: los nombres de atributos pueden cambiar entre versiones.

Exportadores:
- "console": imprime los spans en la salida estándar (clase y laboratorio).
- "otlp": envía por OTLP/HTTP al colector indicado en la variable estándar
  OTEL_EXPORTER_OTLP_ENDPOINT (por ejemplo, un OpenTelemetry Collector o el
  endpoint OTLP del servicio de observabilidad de cada nube).

Por privacidad, NUNCA se registra el contenido de prompts ni respuestas.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

if TYPE_CHECKING:
    from fastapi import FastAPI

    from .config import Settings
    from .schemas import InferenceMetrics

TRACER_NAME = "asistente-universitario"


def setup_tracing(app: FastAPI, settings: Settings) -> None:
    """Configura el proveedor de trazas global e instrumenta FastAPI."""
    if not settings.otel_enabled:
        return
    provider = TracerProvider(
        resource=Resource.create({"service.name": settings.otel_service_name, "service.version": "1.0.0"})
    )
    if settings.otel_exporter == "otlp":
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        exporter = OTLPSpanExporter()  # lee OTEL_EXPORTER_OTLP_ENDPOINT y cabeceras estándar
    else:
        exporter = ConsoleSpanExporter()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    FastAPIInstrumentor.instrument_app(app, excluded_urls="healthz,readyz")


def get_tracer() -> trace.Tracer:
    return trace.get_tracer(TRACER_NAME)


def start_inference_span(provider_name: str, model: str, input_chars: int) -> trace.Span:
    """Abre el span de inferencia con los atributos de la solicitud."""
    span = get_tracer().start_span(f"chat {model}", kind=trace.SpanKind.CLIENT)
    span.set_attribute("gen_ai.operation.name", "chat")
    span.set_attribute("gen_ai.provider.name", provider_name)
    span.set_attribute("gen_ai.request.model", model)
    span.set_attribute("app.input_chars", input_chars)
    return span


def record_metrics(span: trace.Span, metrics: InferenceMetrics) -> None:
    """Agrega uso de tokens y latencias al span antes de cerrarlo."""
    if metrics.prompt_tokens is not None:
        span.set_attribute("gen_ai.usage.input_tokens", metrics.prompt_tokens)
    if metrics.completion_tokens is not None:
        span.set_attribute("gen_ai.usage.output_tokens", metrics.completion_tokens)
    if metrics.ttft_ms is not None:
        span.set_attribute("app.ttft_ms", metrics.ttft_ms)
    if metrics.tpot_ms is not None:
        span.set_attribute("app.tpot_ms", metrics.tpot_ms)
    span.set_attribute("app.e2e_ms", metrics.e2e_ms)
