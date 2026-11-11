"""Azure Functions (Python v2, Flex Consumption) - Service Bus trigger -> Foundry/Azure OpenAI (Entra ID)."""
from __future__ import annotations

import json
import logging
import os

import azure.functions as func
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI

app = func.FunctionApp()
_client: AzureOpenAI | None = None


def _get_client() -> AzureOpenAI:
    """Cliente global reutilizado entre invocaciones (se crea una vez por instancia)."""
    global _client
    if _client is None:
        provider = get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")
        _client = AzureOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            azure_ad_token_provider=provider,
            api_version=os.environ["AZURE_OPENAI_API_VERSION"],
            max_retries=2,
        )
    return _client


@app.service_bus_queue_trigger(arg_name="msg", queue_name="jobs", connection="ServiceBusConnection")
def worker(msg: func.ServiceBusMessage) -> None:
    """Excepcion => Service Bus reintenta (MaxDeliveryCount) y luego mueve a la dead-letter queue."""
    body = json.loads(msg.get_body().decode("utf-8"))
    prompt = str(body["prompt"])[:4000]
    resp = _get_client().chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=512,
    )
    usage = resp.usage.total_tokens if resp.usage else None
    logging.info("job=%s tokens=%s", body.get("job_id"), usage)
    # Produccion: persistir resultado con clave idempotente job_id (Cosmos DB / Table Storage).
