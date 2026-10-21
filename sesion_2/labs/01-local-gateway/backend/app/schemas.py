"""Contratos de la API del gateway.

Las rutas /v1/chat y /v1/chat/stream mantienen el contrato común del curso
(Sesión 1) y añaden la región que atendió y los intentos realizados. Las rutas
/v1/batches imitan el ciclo de vida de los servicios batch gestionados.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    messages: list[Message] = Field(min_length=1, max_length=50)


class InferenceMetrics(BaseModel):
    ttft_ms: float | None = Field(description="Time to First Token")
    e2e_ms: float = Field(description="Latencia total")
    tpot_ms: float | None = Field(description="Time per Output Token")
    output_chunks: int
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    tokens_per_second: float | None = None
    region: str | None = Field(default=None, description="Región que atendió")
    attempts: int = Field(default=1, description="Regiones intentadas")
    failover: bool = Field(default=False, description="Hubo conmutación a otra región")


class ChatResponse(BaseModel):
    model: str
    content: str
    metrics: InferenceMetrics


class ReadyResponse(BaseModel):
    status: Literal["ok", "degraded"]
    routing: str
    available_regions: list[str]
    detail: str | None = None


class RegionStatus(BaseModel):
    name: str
    priority: int
    weight: int
    model: str
    healthy: bool
    health_detail: str | None
    circuit: Literal["closed", "open", "half_open"]
    circuit_open_remaining_s: float
    disabled: bool
    inflight: int
    requests: int
    successes: int
    failures: int
    last_error: str | None
    ewma_ttft_ms: float | None
    sim_admin_url: str | None


class RegionsResponse(BaseModel):
    routing: str
    online_inflight: int
    regions: list[RegionStatus]


BatchStatus = Literal[
    "validating", "in_progress", "finalizing", "completed", "failed",
    "expired", "cancelling", "cancelled",
]


class RequestCounts(BaseModel):
    total: int = 0
    completed: int = 0
    failed: int = 0


class BatchJob(BaseModel):
    id: str
    status: BatchStatus
    completion_window: str = "24h"
    description: str | None = None
    created_at: float
    in_progress_at: float | None = None
    finalizing_at: float | None = None
    completed_at: float | None = None
    failed_at: float | None = None
    expired_at: float | None = None
    cancelled_at: float | None = None
    request_counts: RequestCounts = Field(default_factory=RequestCounts)
    errors: list[str] = Field(default_factory=list)
    regions_used: dict[str, int] = Field(default_factory=dict)


class BatchList(BaseModel):
    data: list[BatchJob]
