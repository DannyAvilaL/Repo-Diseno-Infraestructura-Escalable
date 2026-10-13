"""AZ-E · LangGraph con un modelo alojado en Azure (orquestación explícita).

El grafo se declara nodo por nodo: el desarrollador controla el flujo
(modelo -> herramientas -> modelo) en lugar de delegarlo por completo al
agente. Estado: NO ejecutado en la preparación del curso.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import AzureChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))
import universidad_tools as ut  # noqa: E402

MAX_PASOS = 6  # límite explícito de iteraciones: control de costo y de bucles


@tool
def calendario(evento: str) -> str:
    """Consulta la fecha de un evento del calendario académico."""
    return ut.consultar_calendario_academico(evento)


@tool
def reglamento(tema: str) -> str:
    """Busca el artículo del reglamento estudiantil sobre un tema."""
    return ut.buscar_reglamento(tema)


def build_azure_llm() -> AzureChatOpenAI:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
    )
    return AzureChatOpenAI(
        azure_deployment=os.environ["FOUNDRY_MODEL_DEPLOYMENT"],
        api_version=os.environ["AZURE_OPENAI_API_VERSION"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        azure_ad_token_provider=token_provider,
        timeout=60,
        max_retries=2,
    )


def build_graph(llm=None):
    """Compila el grafo. `llm` permite reutilizarlo con otro cliente (hosted agent)."""
    llm = llm or build_azure_llm()
    tools = [calendario, reglamento]
    llm_with_tools = llm.bind_tools(tools)

    def modelo(state: MessagesState) -> dict:
        return {"messages": [llm_with_tools.invoke(state["messages"])]}

    graph = StateGraph(MessagesState)
    graph.add_node("modelo", modelo)
    graph.add_node("herramientas", ToolNode(tools))
    graph.add_edge(START, "modelo")
    graph.add_conditional_edges("modelo", tools_condition, {"tools": "herramientas", END: END})
    graph.add_edge("herramientas", "modelo")
    return graph.compile()


if __name__ == "__main__":
    pregunta = " ".join(sys.argv[1:]) or "¿Qué requisitos tiene la homologación y hasta cuándo se recibe?"
    app = build_graph()
    final = app.invoke(
        {"messages": [SystemMessage(ut.INSTRUCCIONES_ASISTENTE), HumanMessage(pregunta)]},
        config={"recursion_limit": MAX_PASOS},
    )
    print(final["messages"][-1].content)
