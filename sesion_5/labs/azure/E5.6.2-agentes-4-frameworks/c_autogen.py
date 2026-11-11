"""E5.6.2-c · AutoGen (LEGADO: proyecto en mantenimiento/archivado; solo para comparacion y migracion)."""
from __future__ import annotations

import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from azure.identity import AzureCliCredential, get_bearer_token_provider

from common import INSTRUCCIONES, PREGUNTA, consultar_estado_pedido, env


def build_agent() -> AssistantAgent:
    token_provider = get_bearer_token_provider(AzureCliCredential(), "https://cognitiveservices.azure.com/.default")
    client = AzureOpenAIChatCompletionClient(
        azure_deployment=env("AZURE_OPENAI_DEPLOYMENT"),
        model=env("AZURE_OPENAI_MODEL"),
        api_version=env("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=env("AZURE_OPENAI_ENDPOINT"),
        azure_ad_token_provider=token_provider,
    )
    return AssistantAgent(
        name="soporte", model_client=client, tools=[consultar_estado_pedido],
        system_message=INSTRUCCIONES, reflect_on_tool_use=True,
    )


async def main() -> None:
    agent = build_agent()
    result = await agent.run(task=PREGUNTA)
    print(result.messages[-1].content)


if __name__ == "__main__":
    asyncio.run(main())
