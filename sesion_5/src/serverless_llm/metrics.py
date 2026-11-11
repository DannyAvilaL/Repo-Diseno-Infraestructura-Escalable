"""Métricas Prometheus (registro por aplicación para no colisionar en tests).

Las mismas señales existen en los servicios gestionados:
CloudWatch (Lambda: Duration, Init Duration, ConcurrentExecutions, Throttles),
Azure Monitor (Functions/Container Apps) y Cloud Monitoring (Cloud Run:
request_latencies, container/instance_count, billable_instance_time).
"""

from __future__ import annotations

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest

LATENCY_BUCKETS = (0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 30)


class Metrics:
    def __init__(self) -> None:
        self.registry = CollectorRegistry()
        self.requests = Counter(
            "sllm_requests_total", "Peticiones HTTP", ["route", "status"], registry=self.registry
        )
        self.latency = Histogram(
            "sllm_request_seconds",
            "Latencia end-to-end por ruta",
            ["route"],
            buckets=LATENCY_BUCKETS,
            registry=self.registry,
        )
        self.ttft = Histogram(
            "sllm_ttft_seconds",
            "Time to first token",
            buckets=LATENCY_BUCKETS,
            registry=self.registry,
        )
        self.cache = Counter(
            "sllm_cache_total", "Resultados de caché", ["result"], registry=self.registry
        )
        self.cold_starts = Counter(
            "sllm_cold_starts_total", "Primeras invocaciones de la instancia", registry=self.registry
        )
        self.init_seconds = Gauge(
            "sllm_init_seconds", "Duración de la inicialización de la instancia", registry=self.registry
        )
        self.tokens = Counter(
            "sllm_tokens_total", "Tokens procesados", ["kind"], registry=self.registry
        )
        self.jobs = Counter(
            "sllm_jobs_total", "Trabajos asíncronos por estado final", ["status"], registry=self.registry
        )
        self.queue_depth = Gauge(
            "sllm_queue_depth", "Mensajes pendientes en la cola", registry=self.registry
        )
        self.inflight = Gauge(
            "sllm_inflight_inferences", "Inferencias en curso", registry=self.registry
        )
        self.rejected = Counter(
            "sllm_rejected_total", "Rechazos por motivo", ["reason"], registry=self.registry
        )

    def render(self) -> bytes:
        return generate_latest(self.registry)
