"""Microsoft Agent Framework (GA 1.0, abr-2026): sucesor de Semantic Kernel y AutoGen. Recomendado para nuevos proyectos."""

import asyncio
import sys

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential

from azure_config import INSTRUCTIONS, QUESTION, estimate_inference_replicas, require


async def main(question: str) -> None:
    agent = Agent(
        client=FoundryChatClient(
            project_endpoint=require("AZURE_AI_PROJECT_ENDPOINT"),
            model=require("AZURE_AI_MODEL_DEPLOYMENT"),
            credential=AzureCliCredential(),  # en Azure: ManagedIdentityCredential
        ),
        instructions=INSTRUCTIONS,
        tools=[estimate_inference_replicas],
    )
    print(await agent.run(question))


if __name__ == "__main__":
    asyncio.run(main(" ".join(sys.argv[1:]) or QUESTION))
