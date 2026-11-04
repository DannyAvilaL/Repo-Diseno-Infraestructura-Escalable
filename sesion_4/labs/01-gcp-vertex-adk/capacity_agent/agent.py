"""Agente ADK 'capacity_advisor': asesor de dimensionamiento de réplicas de inferencia."""

import os

from google.adk.agents import Agent

from .capacity_tool import estimate_replicas

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")  # VERIFICAR vigencia en el catálogo (ver README)


def estimate_inference_replicas(
    concurrent_users: int,
    target_tps_per_user: float,
    replica_tps: float,
    headroom: float = 0.3,
    high_availability: bool = True,
) -> dict:
    """Estima cuántas réplicas de un servidor de inferencia LLM se necesitan.

    Args:
        concurrent_users: número de usuarios concurrentes.
        target_tps_per_user: tokens por segundo deseados por usuario (típico 10-20).
        replica_tps: tokens por segundo agregados medidos para UNA réplica.
        headroom: margen de seguridad entre 0 y 0.9 (0.3 = 30 %).
        high_availability: True para agregar una réplica N+1.

    Returns:
        Un diccionario con 'status' y el resultado del cálculo o 'error_message'.
    """
    try:
        return {"status": "success", **estimate_replicas(
            concurrent_users, target_tps_per_user, replica_tps, headroom, high_availability)}
    except ValueError as exc:
        return {"status": "error", "error_message": str(exc)}


root_agent = Agent(
    name="capacity_advisor",
    model=MODEL,
    description="Asesor de dimensionamiento de infraestructura de inferencia LLM.",
    instruction=(
        "Eres un arquitecto de infraestructura de LLM. Responde en español. "
        "Cuando te pidan dimensionar capacidad, usa SIEMPRE la herramienta estimate_inference_replicas; "
        "si falta algún parámetro (por ejemplo replica_tps), pregúntalo en lugar de inventarlo. "
        "Aclara que los resultados son estimaciones que deben validarse con pruebas de carga."
    ),
    tools=[estimate_inference_replicas],
)
