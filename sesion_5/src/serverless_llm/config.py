"""Configuración por variables de entorno (prefijo ``SLLM_``).

Principio de la sesión: la configuración se inyecta desde el entorno (12-factor)
y los secretos nunca se versionan. Ver ``.env.example``.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_DEFAULT_KEY = "dev-key-change-me"


class Settings(BaseSettings):
    """Parámetros de la aplicación. Todos sobreescribibles con ``SLLM_<NOMBRE>``."""

    model_config = SettingsConfigDict(env_prefix="SLLM_", env_file=".env", extra="ignore")

    # --- General -----------------------------------------------------------
    app_name: str = "serverless-llm-gateway"
    environment: Literal["local", "dev", "staging", "prod"] = "local"
    log_level: str = "INFO"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    # --- Proveedor de inferencia ------------------------------------------
    provider: Literal["mock", "ollama"] = "mock"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:1b"
    # keep_alive: cuánto tiempo Ollama mantiene el modelo en memoria tras la
    # última petición. Es el análogo local de "provisioned concurrency".
    ollama_keep_alive: str = "5m"
    request_timeout_s: float = 120.0

    # --- Simulación (solo proveedor mock) ---------------------------------
    mock_cold_start_s: float = 1.5  # "carga del modelo" en el primer uso
    mock_ttft_ms: float = 120.0  # time to first token
    mock_tpot_ms: float = 15.0  # time per output token

    # --- Mitigación de cold start -----------------------------------------
    eager_init: bool = True  # cargar el modelo en el arranque (lifespan)

    # --- Seguridad ---------------------------------------------------------
    # Formato: "clave1:tenantA,clave2:tenantB". Las claves reales van en un
    # gestor de secretos (Secrets Manager / Key Vault / Secret Manager).
    api_keys: str = f"{DEV_DEFAULT_KEY}:dev-tenant"
    max_prompt_chars: int = 4000
    max_output_tokens: int = 512
    injection_policy: Literal["off", "flag", "block"] = "flag"
    rate_limit_per_minute: int = 60
    redact_pii_in_logs: bool = True

    # --- Concurrencia y backpressure --------------------------------------
    max_concurrency: int = 4  # inferencias simultáneas por instancia
    queue_wait_timeout_s: float = 2.0  # espera máxima antes de responder 429

    # --- Caché de respuestas ----------------------------------------------
    cache_enabled: bool = True
    cache_ttl_s: float = 300.0
    cache_max_entries: int = 1024

    # --- Cola de trabajos asíncronos --------------------------------------
    worker_count: int = 2
    queue_visibility_timeout_s: float = 30.0
    queue_max_receive_count: int = 3
    queue_retry_backoff_s: float = 0.5

    @field_validator("api_keys")
    @classmethod
    def _validate_api_keys(cls, value: str) -> str:
        for pair in filter(None, (p.strip() for p in value.split(","))):
            if ":" not in pair:
                raise ValueError("SLLM_API_KEYS debe tener el formato 'clave:tenant,clave:tenant'")
        return value

    @model_validator(mode="after")
    def _forbid_default_key_outside_local(self) -> Settings:
        if self.environment != "local" and DEV_DEFAULT_KEY in self.api_keys:
            raise ValueError("No se permite la clave de desarrollo fuera del entorno 'local'")
        return self

    def parsed_api_keys(self) -> dict[str, str]:
        """Devuelve ``{clave: tenant}``."""
        result: dict[str, str] = {}
        for pair in filter(None, (p.strip() for p in self.api_keys.split(","))):
            key, tenant = pair.split(":", 1)
            result[key.strip()] = tenant.strip()
        return result


@lru_cache
def get_settings() -> Settings:
    return Settings()
