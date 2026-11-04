"""Despliegue serverless en Amazon Bedrock AgentCore Runtime: el mismo agente Strands detrás de un contrato HTTP
(/invocations, /ping) que provee el SDK `bedrock-agentcore`. Cada sesión se aísla en una microVM dedicada."""

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from strands_agent import build_agent

app = BedrockAgentCoreApp()
_agent = build_agent()   # se crea una vez por proceso: reutiliza conexiones y definición de herramientas


@app.entrypoint
def invoke(payload: dict) -> dict:
    prompt = (payload or {}).get("prompt", "").strip()
    if not prompt:
        return {"error": "Falta el campo 'prompt'."}
    return {"result": str(_agent(prompt))}


if __name__ == "__main__":
    app.run()   # local: python agentcore_app.py -> POST http://localhost:8080/invocations
