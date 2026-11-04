"""AutoGen (v0.4+ AgentChat). ESTADO: modo mantenimiento; sucesor: Microsoft Agent Framework."""

import asyncio
import sys

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

from azure_config import INSTRUCTIONS, QUESTION, estimate_inference_replicas, settings, token_provider


async def main(question: str) -> None:
    cfg = settings()
    model_client = AzureOpenAIChatCompletionClient(
        azure_deployment=cfg.deployment,
        model=cfg.deployment,            # AutoGen exige el nombre base del modelo para validar capacidades; ajústelo si difiere
        api_version=cfg.api_version,
        azure_endpoint=cfg.openai_endpoint,
        azure_ad_token_provider=token_provider(),
    )
    agent = AssistantAgent(
        name="capacity_advisor",
        model_client=model_client,
        tools=[estimate_inference_replicas],
        system_message=INSTRUCTIONS,
        reflect_on_tool_use=True,        # una segunda llamada al LLM para redactar con el resultado de la herramienta
    )
    try:
        result = await agent.run(task=question)
        print(result.messages[-1].content)
    finally:
        await model_client.close()


if __name__ == "__main__":
    asyncio.run(main(" ".join(sys.argv[1:]) or QUESTION))
