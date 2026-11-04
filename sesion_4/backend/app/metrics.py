"""Métricas Prometheus. Se usa un registro propio por aplicación para facilitar las pruebas."""

from dataclasses import dataclass

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

# Buckets orientados a LLM: TTFT en cientos de ms, latencia e2e en segundos.
_TTFT_BUCKETS = (0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 30)
_E2E_BUCKETS = (0.25, 0.5, 1, 2, 5, 10, 20, 30, 60, 120)
_TPOT_BUCKETS = (0.005, 0.01, 0.02, 0.05, 0.1, 0.25, 0.5, 1)


@dataclass
class Metrics:
    registry: CollectorRegistry
    requests: Counter
    rejected: Counter
    in_flight: Gauge
    queue_depth: Gauge
    ttft: Histogram
    tpot: Histogram
    e2e: Histogram
    queue_wait: Histogram
    output_tokens: Counter
    input_tokens: Counter


def build_metrics() -> Metrics:
    r = CollectorRegistry()
    return Metrics(
        registry=r,
        requests=Counter("llm_gateway_requests_total", "Solicitudes por resultado", ["outcome"], registry=r),
        rejected=Counter("llm_gateway_rejected_total", "Solicitudes rechazadas por admisión", ["reason"], registry=r),
        in_flight=Gauge("llm_gateway_in_flight", "Solicitudes en ejecución en el modelo", registry=r),
        # Señal principal de autoscaling (ver k8s/keda-scaledobject.yaml).
        queue_depth=Gauge("llm_gateway_queue_depth", "Solicitudes esperando un slot de inferencia", registry=r),
        ttft=Histogram("llm_gateway_ttft_seconds", "Time To First Token", buckets=_TTFT_BUCKETS, registry=r),
        tpot=Histogram("llm_gateway_tpot_seconds", "Time Per Output Token", buckets=_TPOT_BUCKETS, registry=r),
        e2e=Histogram("llm_gateway_e2e_seconds", "Latencia end-to-end", buckets=_E2E_BUCKETS, registry=r),
        queue_wait=Histogram("llm_gateway_queue_wait_seconds", "Tiempo en cola", buckets=_TTFT_BUCKETS, registry=r),
        output_tokens=Counter("llm_gateway_output_tokens_total", "Tokens generados", registry=r),
        input_tokens=Counter("llm_gateway_input_tokens_total", "Tokens de prompt", registry=r),
    )
