"""Contrato de la API del asistente (común a todos los laboratorios)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    messages: list[Message] = Field(min_length=1, max_length=50)


class InferenceMetrics(BaseModel):
    """Métricas de la Unidad F medidas desde el backend."""

    ttft_ms: float | None = Field(description="Time to First Token")
    e2e_ms: float = Field(description="Latencia total de la generación")
    tpot_ms: float | None = Field(description="Time per Output Token")
    output_chunks: int
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    tokens_per_second: float | None = None


class ChatResponse(BaseModel):
    model: str
    content: str
    metrics: InferenceMetrics


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    provider: str
    model: str
    detail: str | None = None
