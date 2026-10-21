"""AZ-B · Asistente universitario con Microsoft Agent Framework 1.x.

API tomada del anuncio oficial de la versión 1.0 y de la documentación de
function tools (Microsoft Learn). Estado: NO ejecutado contra una suscripción
real en la preparación del curso; validar antes de asignarlo.

Uso:
    az login
    python agente_maf.py "¿Hasta cuándo puedo solicitar una homologación?"
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))
from universidad_tools import (  # noqa: E402
    INSTRUCCIONES_ASISTENTE,
    buscar_reglamento,
    consultar_calendario_academico,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("az-b")


def build_agent() -> Agent:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    endpoint = os.environ.get("FOUNDRY_PROJECT_ENDPOINT")
    model = os.environ.get("FOUNDRY_MODEL_DEPLOYMENT")
    if not endpoint or not model:
        raise SystemExit("Defina FOUNDRY_PROJECT_ENDPOINT y FOUNDRY_MODEL_DEPLOYMENT en labs/20-azure/.env")
    return Agent(
        client=FoundryChatClient(project_endpoint=endpoint, model=model, credential=AzureCliCredential()),
        name="AsistenteUniversitario",
        instructions=INSTRUCCIONES_ASISTENTE,
        tools=[consultar_calendario_academico, buscar_reglamento],
    )


async def main(pregunta: str) -> int:
    agent = build_agent()
    try:
        result = await asyncio.wait_for(agent.run(pregunta), timeout=120)
    except TimeoutError:
        logger.error("La ejecución superó 120 s")
        return 1
    except Exception:  # errores de autenticación, cuota o red del SDK
        logger.exception("Fallo al ejecutar el agente. Revise `az login`, rol en el proyecto y cuota del modelo")
        return 1
    print(result.text)
    return 0


if __name__ == "__main__":
    pregunta = " ".join(sys.argv[1:]) or "¿Cuándo inician las clases y qué dice el reglamento sobre asistencia?"
    raise SystemExit(asyncio.run(main(pregunta)))
