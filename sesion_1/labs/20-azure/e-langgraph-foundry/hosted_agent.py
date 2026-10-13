"""AZ-E (extensión) · El mismo grafo LangGraph como hosted agent de Foundry.

Sigue la guía oficial «LangChain/LangGraph hosted agents» de Microsoft Foundry:
el grafo se envuelve con ResponsesHostServer (endpoint compatible /responses)
y el modelo se obtiene del proyecto de Foundry con identidad, sin claves.

Validado (13-oct-2026): importación y construcción del servidor con
langchain-azure-ai 1.x. No se desplegó en Foundry.

Local:   python hosted_agent.py   ->   curl -X POST http://127.0.0.1:8088/responses \\
             -H "Content-Type: application/json" -d '{"input": "¿Cuándo inician las clases?"}'
"""

from __future__ import annotations

import os

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from langchain_azure_ai.agents.hosting import ResponsesHostServer
from langchain_openai import ChatOpenAI

from grafo_langgraph import build_graph

_AZURE_AI_SCOPE = "https://ai.azure.com/.default"


def build_chat_model() -> ChatOpenAI:
    """Cliente de modelo a través del proyecto de Foundry (variables inyectadas en el hosting)."""
    project_endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"].rstrip("/")
    deployment = os.environ.get("FOUNDRY_MODEL_NAME") or os.environ["FOUNDRY_MODEL_DEPLOYMENT"]
    credential = DefaultAzureCredential()
    project = AIProjectClient(endpoint=project_endpoint, credential=credential)
    openai_client = project.get_openai_client()
    token_provider = get_bearer_token_provider(credential, _AZURE_AI_SCOPE)
    return ChatOpenAI(model=deployment, base_url=str(openai_client.base_url), api_key=token_provider)


def main() -> None:
    graph = build_graph(build_chat_model())
    # En Foundry el contenedor debe escuchar en todas las interfaces (valor por defecto
    # de la guía oficial). En local use HOST=127.0.0.1 para no exponer el puerto.
    ResponsesHostServer(graph).run(host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", "8088")))


if __name__ == "__main__":
    main()
