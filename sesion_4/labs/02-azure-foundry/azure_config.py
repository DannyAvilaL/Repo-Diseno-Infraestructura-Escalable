"""Configuración y autenticación comunes (Entra ID; sin claves de API)."""

import os
from dataclasses import dataclass

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv

load_dotenv()
SCOPE = "https://cognitiveservices.azure.com/.default"
QUESTION = "Tengo 100 usuarios concurrentes, 15 tok/s por usuario y una réplica sostiene 400 tok/s. ¿Cuántas réplicas necesito?"
INSTRUCTIONS = (
    "Eres un arquitecto de infraestructura de LLM. Responde en español. Para dimensionar capacidad usa SIEMPRE la "
    "herramienta de estimación; si falta algún parámetro, pregúntalo en lugar de inventarlo. "
    "Aclara que son estimaciones que deben validarse con pruebas de carga."
)


@dataclass(frozen=True)
class AzureSettings:
    project_endpoint: str      # https://<cuenta>.services.ai.azure.com/api/projects/<proyecto>
    openai_endpoint: str       # https://<cuenta>.openai.azure.com/  (endpoint compatible con Azure OpenAI)
    deployment: str            # NOMBRE del despliegue del modelo en Foundry
    api_version: str


def require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"Falta la variable de entorno {name}. Copie .env.example a .env y complétela.")
    return value


def settings() -> AzureSettings:
    return AzureSettings(
        project_endpoint=os.getenv("AZURE_AI_PROJECT_ENDPOINT", ""),
        openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
        deployment=require("AZURE_AI_MODEL_DEPLOYMENT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
    )


def token_provider():
    """Proveedor de tokens Entra ID: `az login` en local, identidad administrada en Azure."""
    return get_bearer_token_provider(DefaultAzureCredential(), SCOPE)


def estimate_inference_replicas(
    concurrent_users: int, target_tps_per_user: float, replica_tps: float,
    headroom: float = 0.3, high_availability: bool = True,
) -> dict:
    """Estima cuántas réplicas de un servidor de inferencia LLM se necesitan (tokens/s por usuario y por réplica)."""
    from capacity_tool import estimate_replicas

    try:
        return {"status": "success", **estimate_replicas(
            concurrent_users, target_tps_per_user, replica_tps, headroom, high_availability)}
    except ValueError as exc:
        return {"status": "error", "error_message": str(exc)}
