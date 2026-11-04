"""Semantic Kernel. ESTADO: modo mantenimiento; Microsoft dirige los proyectos nuevos a Agent Framework.
Se incluye por la gran base instalada y para comparar el modelo de plugins (kernel_function)."""

import asyncio
import sys

from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import kernel_function

from azure_config import INSTRUCTIONS, QUESTION, estimate_inference_replicas, settings, token_provider


class CapacityPlugin:
    @kernel_function(description="Estima réplicas de inferencia LLM a partir de usuarios, tokens/s y capacidad por réplica.")
    def estimate_inference_replicas(
        self, concurrent_users: int, target_tps_per_user: float, replica_tps: float,
        headroom: float = 0.3, high_availability: bool = True,
    ) -> dict:
        return estimate_inference_replicas(concurrent_users, target_tps_per_user, replica_tps, headroom, high_availability)


async def main(question: str) -> None:
    cfg = settings()
    agent = ChatCompletionAgent(
        service=AzureChatCompletion(
            deployment_name=cfg.deployment, endpoint=cfg.openai_endpoint,
            api_version=cfg.api_version, ad_token_provider=token_provider(),
        ),
        name="CapacityAdvisor",
        instructions=INSTRUCTIONS,
        plugins=[CapacityPlugin()],
    )
    response = await agent.get_response(messages=question)
    print(response.content)


if __name__ == "__main__":
    asyncio.run(main(" ".join(sys.argv[1:]) or QUESTION))
