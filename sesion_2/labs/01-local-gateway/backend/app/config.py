"""Configuración del gateway multi-región (LOC-02) por variables de entorno.

Las regiones se declaran en ``APP_REGIONS`` como una lista JSON. Las claves de
API NUNCA van en esa lista: cada región indica el NOMBRE de la variable de
entorno que contiene su clave (``api_key_env``), que se lee al iniciar.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class RegionConfig(BaseModel):
    """Un endpoint de inferencia compatible con la API Chat Completions."""

    name: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,39}$")
    base_url: HttpUrl
    model: str = Field(min_length=1)
    # Menor número = mayor prioridad (como los grupos de prioridad de un pool
    # de backends de un API gateway). Regiones con igual prioridad se reparten.
    priority: int = Field(default=1, ge=1, le=10)
    weight: int = Field(default=1, ge=1, le=100)
    api_key_env: str | None = Field(default=None, pattern=r"^[A-Z_][A-Z0-9_]*$")
    auth_header: Literal["authorization", "api-key"] = "authorization"
    # Health check activo. Algunos proveedores listan modelos base y no
    # nombres de despliegue: en ese caso, desactive la verificación del modelo.
    health_path: str = Field(default="/models", pattern=r"^/[A-Za-z0-9/_\-.]*$")
    check_model: bool = True
    # URL del panel de administración del simulador (solo para la demo de fallas).
    sim_admin_url: HttpUrl | None = None

    def api_key(self) -> str | None:
        return os.environ.get(self.api_key_env) if self.api_key_env else None


_REGIONES_POR_DEFECTO = (
    '[{"name":"region-a","base_url":"http://127.0.0.1:9001/v1","model":"simulado","priority":1},'
    '{"name":"region-b","base_url":"http://127.0.0.1:9002/v1","model":"simulado","priority":2}]'
)


class Settings(BaseSettings):
    """Parámetros del gateway. Prefijo de entorno: ``APP_``."""

    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")

    regions: list[RegionConfig] = Field(default_factory=lambda: _parse_default())
    # "priority": activo-pasivo (failover por prioridad).
    # "round_robin": activo-activo (reparto ponderado entre regiones sanas).
    routing: Literal["priority", "round_robin"] = "priority"

    system_prompt: str = (
        "Eres el asistente institucional de una universidad. Responde en español, "
        "de forma breve y precisa. Si no conoces la respuesta, dilo."
    )
    max_input_chars: int = Field(default=4000, ge=1, le=100_000)
    max_output_tokens: int = Field(default=512, ge=1, le=8192)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)

    # Tiempos de espera: el de primer byte decide cuándo una región "lenta"
    # se trata como fallida y se intenta la siguiente.
    connect_timeout_s: float = Field(default=2.0, gt=0)
    first_byte_timeout_s: float = Field(default=15.0, gt=0)
    read_timeout_s: float = Field(default=120.0, gt=0)
    max_attempts: int = Field(default=3, ge=1, le=10)

    # Circuit breaker por región.
    cb_failure_threshold: int = Field(default=3, ge=1, le=100)
    cb_failure_window_s: float = Field(default=30.0, gt=0)
    cb_open_s: float = Field(default=15.0, gt=0)
    cb_max_open_s: float = Field(default=300.0, gt=0)

    # Health checks activos (GET /models: no consume capacidad del modelo).
    health_interval_s: float = Field(default=5.0, gt=0)
    health_timeout_s: float = Field(default=2.0, gt=0)

    # Inferencia por lotes.
    batch_dir: Path = Path("data/batches")
    batch_concurrency: int = Field(default=2, ge=1, le=64)
    batch_max_requests: int = Field(default=5000, ge=1, le=100_000)
    batch_max_bytes: int = Field(default=10 * 1024 * 1024, ge=1024)
    batch_max_retries: int = Field(default=3, ge=0, le=10)
    batch_retry_base_s: float = Field(default=2.0, ge=0)
    # Prioridad de lo online: el lote se detiene mientras haya al menos este
    # número de solicitudes online en curso.
    batch_yield_online_inflight: int = Field(default=2, ge=1)
    # Ventana de finalización (24 h en los servicios gestionados). Configurable
    # para poder demostrar el estado "expired" en clase.
    batch_completion_window_s: float = Field(default=86_400.0, gt=0)

    # Si se define, las rutas /admin exigen la cabecera X-Admin-Token.
    admin_token: str | None = Field(default=None, repr=False)

    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    log_level: str = "INFO"

    otel_enabled: bool = False
    otel_exporter: Literal["console", "otlp"] = "console"
    otel_service_name: str = "gateway-multiregion"

    @field_validator("regions")
    @classmethod
    def _regiones_unicas(cls, regions: list[RegionConfig]) -> list[RegionConfig]:
        if not regions:
            raise ValueError("Debe configurar al menos una región en APP_REGIONS")
        names = [r.name for r in regions]
        if len(names) != len(set(names)):
            raise ValueError("Los nombres de región deben ser únicos")
        return regions

    @model_validator(mode="after")
    def _coherencia(self) -> Settings:
        if self.cb_open_s > self.cb_max_open_s:
            raise ValueError("APP_CB_OPEN_S no puede superar APP_CB_MAX_OPEN_S")
        return self


def _parse_default() -> list[RegionConfig]:
    import json

    return [RegionConfig.model_validate(r) for r in json.loads(_REGIONES_POR_DEFECTO)]


@lru_cache
def get_settings() -> Settings:
    return Settings()
