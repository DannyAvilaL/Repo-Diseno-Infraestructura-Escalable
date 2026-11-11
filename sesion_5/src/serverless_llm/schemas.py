"""Contratos de la API (Pydantic v2)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(min_length=1, description="Mensaje del usuario")
    system: str | None = Field(default=None, description="Instrucción de sistema opcional")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: int = Field(default=256, ge=1, le=4096)


class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0


class Timings(BaseModel):
    """Métricas de latencia expuestas al cliente (útiles en clase)."""

    total_ms: float
    queue_wait_ms: float = 0.0
    ttft_ms: float | None = None
    load_ms: float | None = None


class ChatResponse(BaseModel):
    text: str
    model: str
    usage: Usage
    timings: Timings
    cache_hit: bool = False
    coalesced: bool = False
    cold_start: bool = False
    instance_id: str
    flags: list[str] = Field(default_factory=list)


class JobStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    DEAD = "DEAD"  # agotó reintentos y fue a la DLQ


class JobAccepted(BaseModel):
    job_id: str
    status: JobStatus
    status_url: str
    idempotent_replay: bool = False


class JobView(BaseModel):
    job_id: str
    status: JobStatus
    attempts: int
    result: ChatResponse | None = None
    error: str | None = None


class ErrorBody(BaseModel):
    error: str
    detail: str | None = None
    extra: dict[str, Any] | None = None
