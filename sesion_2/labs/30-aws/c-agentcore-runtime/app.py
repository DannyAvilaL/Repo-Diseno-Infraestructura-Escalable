"""AWS-C · Agente Strands empaquetado para Amazon Bedrock AgentCore Runtime.

AgentCore Runtime ejecuta cada sesión en un entorno aislado y gestiona el
escalado; el código del agente (Strands) no cambia. Estado: NO ejecutado en
la preparación del curso; verifique la API del SDK `bedrock-agentcore` y el
procedimiento de despliegue vigente en la documentación oficial.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent, tool
from strands.models import BedrockModel

sys.path.insert(0, str(Path(__file__).resolve().parent / "common"))  # copiado al empaquetar
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))  # ejecución local
import universidad_tools as ut  # noqa: E402

MAX_PROMPT_CHARS = 2000

app = BedrockAgentCoreApp()
agent = Agent(
    model=BedrockModel(model_id=os.environ["BEDROCK_MODEL_ID"], region_name=os.environ["AWS_REGION"]),
    system_prompt=ut.INSTRUCCIONES_ASISTENTE,
    tools=[tool(ut.consultar_calendario_academico), tool(ut.buscar_reglamento)],
)


@app.entrypoint
def invoke(payload: dict) -> dict:
    prompt = str(payload.get("prompt", "")).strip()
    if not prompt or len(prompt) > MAX_PROMPT_CHARS:
        return {"error": f"'prompt' es obligatorio y de máximo {MAX_PROMPT_CHARS} caracteres"}
    result = agent(prompt)
    return {"result": str(result)}


if __name__ == "__main__":
    app.run()  # servidor local para pruebas antes del despliegue
