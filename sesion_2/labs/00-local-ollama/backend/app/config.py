"""Configuración del backend mediante variables de entorno (12-factor).

Ningún secreto se define en el código: los valores sensibles llegan por
variables de entorno o por el archivo .env local (excluido de git).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Parámetros del servicio. Prefijo de entorno: ``APP_``."""

    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")

    # Proveedor de inferencia: "ollama" (local) u "openai_compat" (cualquier
    # endpoint compatible con la API de OpenAI: Ollama /v1, Foundry, etc.).
    provider: Literal["ollama", "openai_compat"] = "ollama"

    ollama_base_url: HttpUrl = HttpUrl("http://127.0.0.1:11434")
    model: str = "qwen2.5:1.5b"

    openai_base_url: HttpUrl | None = None
    openai_api_key: str | None = Field(default=None, repr=False)

    system_prompt: str = (
        "Eres el asistente institucional de una universidad. Responde en español, "
        "de forma breve y precisa. Si no conoces la respuesta, dilo."
    )

    # Límites de protección (mitigan OWASP LLM10: Unbounded Consumption).
    max_input_chars: int = Field(default=4000, ge=1, le=100_000)
    max_output_tokens: int = Field(default=512, ge=1, le=8192)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)

    # Timeouts y reintentos controlados hacia el proveedor.
    connect_timeout_s: float = 5.0
    read_timeout_s: float = 120.0
    max_retries: int = Field(default=2, ge=0, le=5)

    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    log_level: str = "INFO"

    # OpenTelemetry (desactivado por defecto). Con "otlp", el destino se define
    # con la variable estándar OTEL_EXPORTER_OTLP_ENDPOINT.
    otel_enabled: bool = False
    otel_exporter: Literal["console", "otlp"] = "console"
    otel_service_name: str = "asistente-universitario"


@lru_cache
def get_settings() -> Settings:
    return Settings()
