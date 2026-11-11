"""E5.6.2-a · Microsoft Agent Framework (sucesor recomendado de SK y AutoGen) sobre Foundry."""
from __future__ import annotations

import asyncio

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential

from common import INSTRUCCIONES, PREGUNTA, consultar_estado_pedido, env


def build_agent() -> Agent:
    client = FoundryChatClient(
        project_endpoint=env("AZURE_AI_PROJECT_ENDPOINT"),
        model=env("AZURE_AI_MODEL_DEPLOYMENT"),
        credential=AzureCliCredential(),
    )
    return Agent(client=client, instructions=INSTRUCCIONES, name="soporte", tools=[consultar_estado_pedido])


async def main() -> None:
    result = await build_agent().run(PREGUNTA)
    print(result.text)


if __name__ == "__main__":
    asyncio.run(main())
