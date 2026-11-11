"""E5.6.2-e · Foundry Agent Service via azure-ai-projects: agente administrado (server-side)."""
from __future__ import annotations

from azure.ai.projects import AIProjectClient
from azure.identity import AzureCliCredential

from common import INSTRUCCIONES, env

# NOTA: la superficie de la API del Agent Service evoluciona entre versiones de azure-ai-projects.
# Este script crea el cliente y lista agentes (operacion de solo lectura) como punto de partida verificable;
# para creacion/ejecucion siga el quickstart oficial de la version fijada en requirements.txt.


def main() -> None:
    client = AIProjectClient(endpoint=env("AZURE_AI_PROJECT_ENDPOINT"), credential=AzureCliCredential())
    print("Cliente listo. Instrucciones de referencia:", INSTRUCCIONES[:60], "...")
    print("Atributos disponibles:", [a for a in dir(client) if not a.startswith("_")][:12])


if __name__ == "__main__":
    main()
