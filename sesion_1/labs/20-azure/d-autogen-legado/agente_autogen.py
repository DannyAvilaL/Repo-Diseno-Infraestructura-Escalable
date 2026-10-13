"""AZ-D · AutoGen AgentChat (LEGADO, modo mantenimiento) con un modelo de Azure.

Objetivo didáctico: ver el modelo conversacional de AutoGen y su ruta de
migración a Agent Framework. Estado: NO ejecutado en la preparación del curso.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))
import universidad_tools as ut  # noqa: E402


async def main(pregunta: str) -> None:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
    )
    deployment = os.environ["FOUNDRY_MODEL_DEPLOYMENT"]
    model_client = AzureOpenAIChatCompletionClient(
        azure_deployment=deployment,
        model=deployment,
        api_version=os.environ["AZURE_OPENAI_API_VERSION"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        azure_ad_token_provider=token_provider,
    )
    agent = AssistantAgent(
        "asistente_universitario",
        model_client=model_client,
        tools=[ut.consultar_calendario_academico, ut.buscar_reglamento],
        system_message=ut.INSTRUCCIONES_ASISTENTE,
        reflect_on_tool_use=True,
    )
    try:
        result = await agent.run(task=pregunta)
        print(result.messages[-1].content)
    finally:
        await model_client.close()


if __name__ == "__main__":
    asyncio.run(main(" ".join(sys.argv[1:]) or "¿Cuándo son los exámenes finales?"))
