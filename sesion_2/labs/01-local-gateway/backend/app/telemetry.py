"""Trazas OpenTelemetry del gateway (opcionales).

Igual que en la Sesión 1, cada solicitud online genera un span de inferencia
con atributos ``gen_ai.*``; aquí se añaden la región que atendió, el número de
intentos y si hubo conmutación. Así un tablero puede mostrar el porcentaje de
tráfico servido por la región secundaria durante un incidente.

Las convenciones GenAI de OpenTelemetry están en desarrollo: los nombres de
atributos pueden cambiar. Nunca se registra el contenido de las conversaciones.
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

TRACER_NAME = "gateway-multiregion"


def setup_tracing(app: FastAPI, settings: Settings) -> None:
    if not settings.otel_enabled:
        return
    provider = TracerProvider(resource=Resource.create({"service.name": settings.otel_service_name}))
    if settings.otel_exporter == "otlp":
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        exporter = OTLPSpanExporter()
    else:
        exporter = ConsoleSpanExporter()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    FastAPIInstrumentor.instrument_app(app, excluded_urls="healthz,readyz,v1/regions")


def start_inference_span(operation: str, input_chars: int) -> trace.Span:
    span = trace.get_tracer(TRACER_NAME).start_span(f"{operation} gateway", kind=trace.SpanKind.CLIENT)
    span.set_attribute("gen_ai.operation.name", operation)
    span.set_attribute("app.input_chars", input_chars)
    return span


def record_route(span: trace.Span, *, region: str, model: str, attempts: int) -> None:
    span.set_attribute("gen_ai.request.model", model)
    span.set_attribute("app.region", region)
    span.set_attribute("app.attempts", attempts)
    span.set_attribute("app.failover", attempts > 1)


def record_metrics(span: trace.Span, metrics: InferenceMetrics) -> None:
    if metrics.prompt_tokens is not None:
        span.set_attribute("gen_ai.usage.input_tokens", metrics.prompt_tokens)
    if metrics.completion_tokens is not None:
        span.set_attribute("gen_ai.usage.output_tokens", metrics.completion_tokens)
    if metrics.ttft_ms is not None:
        span.set_attribute("app.ttft_ms", metrics.ttft_ms)
    span.set_attribute("app.e2e_ms", metrics.e2e_ms)
