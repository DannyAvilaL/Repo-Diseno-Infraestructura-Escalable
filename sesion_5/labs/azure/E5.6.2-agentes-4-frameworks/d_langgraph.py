"""E5.6.2-d · LangGraph (agente ReAct) con modelo alojado en Azure OpenAI/Foundry."""
from __future__ import annotations

from azure.identity import AzureCliCredential, get_bearer_token_provider
from langchain_core.tools import tool
from langchain_openai import AzureChatOpenAI
from langgraph.prebuilt import create_react_agent

from common import INSTRUCCIONES, PREGUNTA, consultar_estado_pedido, env


@tool
def estado_pedido(pedido_id: str) -> str:
    """Devuelve el estado de un pedido por su ID (ficticio)."""
    return consultar_estado_pedido(pedido_id)


def build_agent():  # noqa: ANN201 - tipo CompiledStateGraph
    token_provider = get_bearer_token_provider(AzureCliCredential(), "https://cognitiveservices.azure.com/.default")
    llm = AzureChatOpenAI(
        azure_deployment=env("AZURE_OPENAI_DEPLOYMENT"),
        azure_endpoint=env("AZURE_OPENAI_ENDPOINT"),
        api_version=env("AZURE_OPENAI_API_VERSION"),
        azure_ad_token_provider=token_provider,
        temperature=0,
    )
    return create_react_agent(llm, tools=[estado_pedido], prompt=INSTRUCCIONES)


def main() -> None:
    result = build_agent().invoke({"messages": [("user", PREGUNTA)]})
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
