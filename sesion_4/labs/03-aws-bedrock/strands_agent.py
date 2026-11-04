"""Agente con Strands Agents SDK (open source, model-driven) sobre un modelo de Amazon Bedrock."""

import sys

from strands import Agent, tool
from strands.models import BedrockModel

from aws_config import QUESTION, REGION, SYSTEM_PROMPT, require
from capacity_tool import estimate_replicas


@tool
def estimate_inference_replicas(
    concurrent_users: int, target_tps_per_user: float, replica_tps: float,
    headroom: float = 0.3, high_availability: bool = True,
) -> dict:
    """Estima réplicas de inferencia LLM a partir de usuarios concurrentes, tokens/s por usuario y tokens/s por réplica.

    Args:
        concurrent_users: usuarios concurrentes.
        target_tps_per_user: tokens por segundo deseados por usuario.
        replica_tps: tokens por segundo agregados medidos para una réplica.
        headroom: margen de seguridad entre 0 y 0.9.
        high_availability: True para agregar una réplica N+1.
    """
    try:
        return {"status": "success", **estimate_replicas(
            concurrent_users, target_tps_per_user, replica_tps, headroom, high_availability)}
    except ValueError as exc:
        return {"status": "error", "error_message": str(exc)}


def build_agent() -> Agent:
    # BEDROCK_MODEL_ID: ID o perfil de inferencia habilitado en su cuenta/región (ver README, paso 1).
    model = BedrockModel(model_id=require("BEDROCK_MODEL_ID"), region_name=REGION)
    return Agent(model=model, system_prompt=SYSTEM_PROMPT, tools=[estimate_inference_replicas])


if __name__ == "__main__":
    print(build_agent()(" ".join(sys.argv[1:]) or QUESTION))
