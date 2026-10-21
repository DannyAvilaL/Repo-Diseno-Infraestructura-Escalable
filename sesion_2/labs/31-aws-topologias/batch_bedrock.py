"""AWS-E (parte batch) · Clasificación de PQRS con Amazon Bedrock batch inference.

Requisitos documentados (consultados el 20-oct-2026):
- Mínimo de registros por trabajo: 100 para los modelos listados en las
  cuotas de Bedrock; por eso el lote predeterminado tiene 200.
- Amazon Nova Lite (``amazon.nova-lite-v1:0``) admite batch en una sola región
  en us-east-1; Nova 2 Lite solo mediante perfiles de inferencia entre regiones.
- Rol de servicio que Bedrock asume para leer la entrada y escribir la salida
  en S3 (plantillas en ``iam/``).
- Descuento de 50 % frente a on-demand y ventana de 24 h según la guía de
  capacidad y costos de Bedrock.

Flujo:
    preparar  -> genera el lote (invocación Converse) y lo sube a s3://<bucket>/pqrs/entrada/
    enviar    -> create_model_invocation_job (modelInvocationType="Converse")
    estado    -> Submitted, Validating, Scheduled, InProgress, Completed, PartiallyCompleted, ...
    descargar -> combina los *.jsonl.out en data/salida_bedrock.jsonl y muestra el manifiesto
    cancelar  -> stop_model_invocation_job
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))

import lote_pqrs as lp  # noqa: E402

DATA = Path(__file__).resolve().parent / "data"
ESTADO = DATA / "estado_batch.json"
PREFIJO = "pqrs"
MIN_REGISTROS = 100
TERMINALES = {"Completed", "PartiallyCompleted", "Failed", "Stopped", "Expired"}


def _env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Defina {name} en .env (ver .env.example)")
    return value


def preparar(s3: Any, bucket: str, n: int) -> str:
    if n < MIN_REGISTROS:
        raise SystemExit(f"Bedrock exige al menos {MIN_REGISTROS} registros por trabajo; use --n {MIN_REGISTROS} o más")
    lote = lp.generar_pqrs(n)
    local = DATA / "lote_bedrock.jsonl"
    lp.escribir_jsonl(lp.a_bedrock_batch(lote), local)
    lp.escribir_jsonl(({**p.__dict__} for p in lote), DATA / "etiquetas.jsonl")
    key = f"{PREFIJO}/entrada/lote.jsonl"
    s3.upload_file(str(local), bucket, key)
    print(f"{n} registros subidos a s3://{bucket}/{key}")
    return f"s3://{bucket}/{PREFIJO}/entrada/"


def enviar(bedrock: Any, bucket: str, model_id: str, role_arn: str) -> str:
    resp = bedrock.create_model_invocation_job(
        jobName=f"pqrs-{time.strftime('%Y%m%d-%H%M%S')}",
        clientRequestToken=str(uuid.uuid4()),  # idempotencia si se reintenta la llamada
        roleArn=role_arn,
        modelId=model_id,
        modelInvocationType="Converse",
        inputDataConfig={"s3InputDataConfig": {"s3Uri": f"s3://{bucket}/{PREFIJO}/entrada/"}},
        outputDataConfig={"s3OutputDataConfig": {"s3Uri": f"s3://{bucket}/{PREFIJO}/salida/"}},
        timeoutDurationInHours=24,
        tags=[{"key": "curso", "value": "llm-infra"}],
    )
    ESTADO.write_text(json.dumps({"jobArn": resp["jobArn"], "enviado": time.time()}, indent=2), encoding="utf-8")
    print(f"Trabajo enviado: {resp['jobArn']}")
    return resp["jobArn"]


def _job_arn() -> str:
    if not ESTADO.exists():
        raise SystemExit("No hay un trabajo enviado. Ejecute: python batch_bedrock.py enviar")
    return json.loads(ESTADO.read_text(encoding="utf-8"))["jobArn"]


def estado(bedrock: Any, esperar: bool, intervalo_s: int) -> dict[str, Any]:
    arn = _job_arn()
    while True:
        job = bedrock.get_model_invocation_job(jobIdentifier=arn)
        conteos = ""
        if job.get("totalRecordCount") is not None:
            conteos = (f" procesados={job.get('processedRecordCount')}/{job.get('totalRecordCount')}"
                       f" ok={job.get('successRecordCount')} errores={job.get('errorRecordCount')}")
        print(f"{time.strftime('%H:%M:%S')} estado={job['status']}{conteos}" + (f" · {job['message']}" if job.get("message") else ""))
        if not esperar or job["status"] in TERMINALES:
            return job
        time.sleep(intervalo_s)


def descargar(s3: Any, bucket: str) -> Path:
    # No se asume la estructura exacta de carpetas: se recorren los objetos del prefijo de salida.
    paginator = s3.get_paginator("list_objects_v2")
    keys = [o["Key"] for page in paginator.paginate(Bucket=bucket, Prefix=f"{PREFIJO}/salida/") for o in page.get("Contents", [])]
    resultados = [k for k in keys if k.endswith(".jsonl.out")]
    manifiestos = [k for k in keys if k.endswith("manifest.json.out")]
    if not resultados:
        raise SystemExit("Aún no hay resultados (*.jsonl.out) en el prefijo de salida")
    salida = DATA / "salida_bedrock.jsonl"
    with salida.open("wb") as f:
        for key in resultados:
            f.write(s3.get_object(Bucket=bucket, Key=key)["Body"].read())
    for key in manifiestos:
        print("Manifiesto:", s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8"))
    print(f"{len(resultados)} archivo(s) combinados en {salida}")
    print("Evalúe con: python ../01-local-gateway/scripts/evaluar_lote.py "
          "--resultados data/salida_bedrock.jsonl --etiquetas data/etiquetas.jsonl")
    return salida


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("preparar")
    p.add_argument("--n", type=int, default=200)
    sub.add_parser("enviar")
    e = sub.add_parser("estado")
    e.add_argument("--esperar", action="store_true")
    e.add_argument("--intervalo", type=int, default=60)
    sub.add_parser("descargar")
    sub.add_parser("cancelar")
    args = parser.parse_args()

    load_dotenv()
    DATA.mkdir(exist_ok=True)
    import boto3

    region = _env("AWS_BATCH_REGION")
    bucket = _env("AWS_BATCH_BUCKET")
    s3 = boto3.client("s3", region_name=region)
    bedrock = boto3.client("bedrock", region_name=region)
    if args.cmd == "preparar":
        preparar(s3, bucket, args.n)
    elif args.cmd == "enviar":
        enviar(bedrock, bucket, _env("AWS_BATCH_MODEL_ID"), _env("AWS_BATCH_ROLE_ARN"))
    elif args.cmd == "estado":
        estado(bedrock, args.esperar, max(30, args.intervalo))
    elif args.cmd == "descargar":
        descargar(s3, bucket)
    else:
        bedrock.stop_model_invocation_job(jobIdentifier=_job_arn())
        print("Detención solicitada")


if __name__ == "__main__":
    main()
