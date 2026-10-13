"""AZ-C · Semantic Kernel (LEGADO, modo mantenimiento) con un modelo de Azure.

Objetivo didáctico: reconocer el modelo de plugins de SK y compararlo con
Agent Framework, su sucesor. Estado: NO ejecutado en la preparación del
curso; la API de SK Python debe verificarse contra la versión instalada.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Annotated

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import kernel_function

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))
import universidad_tools as ut  # noqa: E402


class UniversidadPlugin:
    """En SK las herramientas se agrupan en plugins con funciones decoradas."""

    @kernel_function(description="Consulta la fecha de un evento del calendario académico")
    def calendario(self, evento: Annotated[str, "Evento, p. ej. 'inicio de clases'"]) -> str:
        return ut.consultar_calendario_academico(evento)

    @kernel_function(description="Busca el artículo del reglamento estudiantil sobre un tema")
    def reglamento(self, tema: Annotated[str, "Tema, p. ej. 'homologacion'"]) -> str:
        return ut.buscar_reglamento(tema)


async def main(pregunta: str) -> None:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
    )
    service = AzureChatCompletion(
        deployment_name=os.environ["FOUNDRY_MODEL_DEPLOYMENT"],
        endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_version=os.environ["AZURE_OPENAI_API_VERSION"],
        ad_token_provider=token_provider,
    )
    agent = ChatCompletionAgent(
        service=service,
        name="AsistenteSK",
        instructions=ut.INSTRUCCIONES_ASISTENTE,
        plugins=[UniversidadPlugin()],
    )
    response = await agent.get_response(messages=pregunta)
    print(response)


if __name__ == "__main__":
    asyncio.run(main(" ".join(sys.argv[1:]) or "¿Qué dice el reglamento sobre cancelación de asignaturas?"))
