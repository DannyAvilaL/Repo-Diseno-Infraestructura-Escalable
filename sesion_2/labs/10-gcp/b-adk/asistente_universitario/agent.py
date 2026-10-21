"""GCP-B · Asistente universitario con Google Agent Development Kit (ADK).

Estructura de paquete que ADK espera: carpeta con __init__.py y agent.py
que define `root_agent`. Estado: NO ejecutado contra un proyecto real en la
preparación del curso; validar antes de asignarlo.

Ejecución local (desde labs/10-gcp/b-adk):
    adk web          # interfaz de desarrollo en el navegador
    adk run asistente_universitario
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import Agent

load_dotenv(Path(__file__).resolve().parent / ".env")
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "common"))
from universidad_tools import (  # noqa: E402
    INSTRUCCIONES_ASISTENTE,
    buscar_reglamento,
    consultar_calendario_academico,
)

MODEL = os.environ.get("GEMINI_MODEL")
if not MODEL:
    raise RuntimeError("Defina GEMINI_MODEL en asistente_universitario/.env")

# ADK construye el esquema de cada herramienta a partir de los type hints y la docstring.
root_agent = Agent(
    name="asistente_universitario",
    model=MODEL,
    description="Responde preguntas sobre calendario académico y reglamento estudiantil.",
    instruction=INSTRUCCIONES_ASISTENTE,
    tools=[consultar_calendario_academico, buscar_reglamento],
)
