"""E5.6.2-b · Semantic Kernel (en mantenimiento: se mantiene para codigo existente)."""
from __future__ import annotations

import asyncio
from typing import Annotated

from azure.identity import AzureCliCredential, get_bearer_token_provider
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import kernel_function

from common import INSTRUCCIONES, PREGUNTA, consultar_estado_pedido, env


class PedidosPlugin:
    @kernel_function(description="Devuelve el estado de un pedido")
    def consultar_estado_pedido(self, pedido_id: Annotated[str, "ID del pedido"]) -> str:
        return consultar_estado_pedido(pedido_id)


def build_agent() -> ChatCompletionAgent:
    service = AzureChatCompletion(
        deployment_name=env("AZURE_OPENAI_DEPLOYMENT"),
        endpoint=env("AZURE_OPENAI_ENDPOINT"),
        ad_token_provider=get_bearer_token_provider(AzureCliCredential(), "https://cognitiveservices.azure.com/.default"),
    )
    return ChatCompletionAgent(service=service, name="soporte", instructions=INSTRUCCIONES, plugins=[PedidosPlugin()])


async def main() -> None:
    response = await build_agent().get_response(messages=PREGUNTA)
    print(response.content)


if __name__ == "__main__":
    asyncio.run(main())
