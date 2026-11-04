"""Invoca el agente creado en la consola de Bedrock (Parte A) mediante boto3 (bedrock-agent-runtime)."""

import sys
import uuid

import boto3
from botocore.exceptions import ClientError

from aws_config import QUESTION, REGION, require


def main(question: str) -> None:
    client = boto3.client("bedrock-agent-runtime", region_name=REGION)
    try:
        response = client.invoke_agent(
            agentId=require("BEDROCK_AGENT_ID"),
            agentAliasId=require("BEDROCK_AGENT_ALIAS_ID"),   # alias creado tras "Prepare" (no use TSTALIASID en producción)
            sessionId=str(uuid.uuid4()),
            inputText=question,
        )
    except ClientError as exc:
        raise SystemExit(f"Error de AWS: {exc.response['Error']['Code']}: {exc.response['Error']['Message']}") from exc

    for event in response["completion"]:        # EventStream: fragmentos de la respuesta
        chunk = event.get("chunk")
        if chunk:
            print(chunk["bytes"].decode("utf-8"), end="", flush=True)
    print()


if __name__ == "__main__":
    main(" ".join(sys.argv[1:]) or QUESTION)
