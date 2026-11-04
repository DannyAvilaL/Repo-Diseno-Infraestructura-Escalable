"""Configuración común AWS. Credenciales: cadena estándar de boto3 (SSO / rol IAM); sin claves en código."""

import os

from dotenv import load_dotenv

load_dotenv()
QUESTION = "Tengo 100 usuarios concurrentes, 15 tok/s por usuario y una réplica sostiene 400 tok/s. ¿Cuántas réplicas necesito?"
SYSTEM_PROMPT = (
    "Eres un arquitecto de infraestructura de LLM. Responde en español. Para dimensionar capacidad usa SIEMPRE la "
    "herramienta de estimación; si falta algún parámetro, pregúntalo en lugar de inventarlo. "
    "Aclara que son estimaciones que deben validarse con pruebas de carga."
)


def require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"Falta la variable de entorno {name}. Copie .env.example a .env y complétela.")
    return value


REGION = os.getenv("AWS_REGION", "us-east-1")
