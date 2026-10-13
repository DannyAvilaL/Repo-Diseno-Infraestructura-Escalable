"""AWS-B · Asistente universitario con Strands Agents SDK y Amazon Bedrock.

Estado: NO ejecutado contra una cuenta real en la preparación del curso.

Uso:
    aws sso login --profile llm-curso
    python agente_strands.py "¿Qué dice el reglamento sobre asistencia?"
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from strands import Agent, tool
from strands.models import BedrockModel

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))
import universidad_tools as ut  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

# Strands usa la docstring y los type hints para describir la herramienta al modelo.
calendario = tool(ut.consultar_calendario_academico)
reglamento = tool(ut.buscar_reglamento)


def build_agent() -> Agent:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    model_id = os.environ.get("BEDROCK_MODEL_ID")
    region = os.environ.get("AWS_REGION")
    if not model_id or not region:
        raise SystemExit("Defina BEDROCK_MODEL_ID y AWS_REGION en labs/30-aws/.env")
    model = BedrockModel(model_id=model_id, region_name=region, temperature=0.2)
    return Agent(model=model, system_prompt=ut.INSTRUCCIONES_ASISTENTE, tools=[calendario, reglamento])


def main(pregunta: str) -> int:
    agent = build_agent()
    try:
        result = agent(pregunta)
    except Exception:  # credenciales, permisos de IAM o modelo no disponible en la región
        logging.exception("Fallo al invocar el agente. Revise sesión SSO, permisos y BEDROCK_MODEL_ID")
        return 1
    print()
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(" ".join(sys.argv[1:]) or "¿Hasta cuándo se reciben homologaciones?"))
