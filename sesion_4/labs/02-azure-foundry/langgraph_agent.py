"""LangGraph (LangChain) con un modelo desplegado en Azure. El grafo se construye explícitamente
(nodo LLM -> condicional -> nodo de herramientas) para mostrar el control de flujo y evitar depender de helpers de alto nivel."""

import asyncio
import sys

from langchain_core.tools import tool
from langchain_openai import AzureChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from azure_config import INSTRUCTIONS, QUESTION, estimate_inference_replicas as _estimate, settings, token_provider


@tool
def estimate_inference_replicas(
    concurrent_users: int, target_tps_per_user: float, replica_tps: float,
    headroom: float = 0.3, high_availability: bool = True,
) -> dict:
    """Estima réplicas de inferencia LLM a partir de usuarios concurrentes, tokens/s por usuario y tokens/s por réplica."""
    return _estimate(concurrent_users, target_tps_per_user, replica_tps, headroom, high_availability)


def build_graph():
    cfg = settings()
    llm = AzureChatOpenAI(
        azure_deployment=cfg.deployment, azure_endpoint=cfg.openai_endpoint,
        api_version=cfg.api_version, azure_ad_token_provider=token_provider(),
    ).bind_tools([estimate_inference_replicas])

    def call_model(state: MessagesState) -> dict:
        return {"messages": [llm.invoke([("system", INSTRUCTIONS), *state["messages"]])]}

    graph = StateGraph(MessagesState)
    graph.add_node("llm", call_model)
    graph.add_node("tools", ToolNode([estimate_inference_replicas]))
    graph.add_edge(START, "llm")
    graph.add_conditional_edges("llm", tools_condition)   # sin tool_calls -> END; con tool_calls -> "tools"
    graph.add_edge("tools", "llm")
    return graph.compile()


async def main(question: str) -> None:
    out = await asyncio.to_thread(build_graph().invoke, {"messages": [("user", question)]})
    print(out["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main(" ".join(sys.argv[1:]) or QUESTION))
