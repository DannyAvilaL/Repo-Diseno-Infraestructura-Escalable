"""GCP-D (parte batch) · Clasificación de PQRS con batch inference de Gemini.

Flujo:
    preparar  -> genera el lote en formato Gemini y lo sube a gs://<bucket>/pqrs/entrada.jsonl
    enviar    -> crea el trabajo (client.batches.create) con destino gs://<bucket>/pqrs/salida/
    estado    -> consulta el estado (JOB_STATE_*)
    descargar -> descarga los JSONL de salida a data/salida_gemini.jsonl
    cancelar  -> cancela el trabajo

La documentación de precios indica que los modelos Gemini están disponibles
en modo batch con 50 % de descuento (consultada el 20-oct-2026).

Uso:
    python batch_gemini.py preparar --n 200
    python batch_gemini.py enviar
    python batch_gemini.py estado --esperar
    python batch_gemini.py descargar
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))

import lote_pqrs as lp  # noqa: E402

DATA = Path(__file__).resolve().parent / "data"
ESTADO = DATA / "estado_batch.json"
PREFIJO = "pqrs"
TERMINALES = {
    "JOB_STATE_SUCCEEDED", "JOB_STATE_FAILED", "JOB_STATE_CANCELLED",
    "JOB_STATE_EXPIRED", "JOB_STATE_PARTIALLY_SUCCEEDED",
}


def _env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Defina {name} en .env (ver .env.example)")
    return value


def _state_name(job: Any) -> str:
    state = getattr(job, "state", None)
    return getattr(state, "name", None) or str(state)


def preparar(storage_client: Any, bucket: str, n: int) -> str:
    lote = lp.generar_pqrs(n)
    local = DATA / "lote_gemini.jsonl"
    lp.escribir_jsonl(lp.a_gemini_batch(lote), local)
    lp.escribir_jsonl(({**p.__dict__} for p in lote), DATA / "etiquetas.jsonl")
    blob = storage_client.bucket(bucket).blob(f"{PREFIJO}/entrada.jsonl")
    blob.upload_from_filename(str(local), content_type="application/jsonl")
    uri = f"gs://{bucket}/{PREFIJO}/entrada.jsonl"
    print(f"{n} solicitudes subidas a {uri}")
    return uri


def enviar(client: Any, bucket: str, model: str) -> Any:
    from google.genai import types

    job = client.batches.create(
        model=model,
        src=f"gs://{bucket}/{PREFIJO}/entrada.jsonl",
        config=types.CreateBatchJobConfig(dest=f"gs://{bucket}/{PREFIJO}/salida/", display_name="pqrs-nocturnas"),
    )
    ESTADO.write_text(json.dumps({"name": job.name, "enviado": time.time()}, indent=2), encoding="utf-8")
    print(f"Trabajo {job.name} · estado {_state_name(job)}")
    return job


def _leer_nombre() -> str:
    if not ESTADO.exists():
        raise SystemExit("No hay un trabajo enviado. Ejecute: python batch_gemini.py enviar")
    return json.loads(ESTADO.read_text(encoding="utf-8"))["name"]


def estado(client: Any, esperar: bool, intervalo_s: int) -> Any:
    name = _leer_nombre()
    while True:
        job = client.batches.get(name=name)
        stats = getattr(job, "completion_stats", None)
        extra = ""
        if stats is not None:
            extra = f" ok={getattr(stats, 'successful_count', '?')} fallidas={getattr(stats, 'failed_count', '?')}"
        print(f"{time.strftime('%H:%M:%S')} estado={_state_name(job)}{extra}")
        if not esperar or _state_name(job) in TERMINALES:
            return job
        time.sleep(intervalo_s)


def descargar(client: Any, storage_client: Any) -> Path:
    job = client.batches.get(name=_leer_nombre())
    dest = getattr(getattr(job, "dest", None), "gcs_uri", None)
    if not dest:
        raise SystemExit(f"El trabajo no informa destino en Cloud Storage (estado {_state_name(job)})")
    bucket_name, _, prefix = dest.removeprefix("gs://").partition("/")
    # No se asume el nombre exacto del archivo: se descargan todos los JSONL del destino.
    blobs = [b for b in storage_client.list_blobs(bucket_name, prefix=prefix) if b.name.endswith(".jsonl")]
    if not blobs:
        raise SystemExit(f"No hay archivos JSONL en {dest}")
    salida = DATA / "salida_gemini.jsonl"
    with salida.open("wb") as f:
        for blob in blobs:
            f.write(blob.download_as_bytes())
    print(f"{len(blobs)} archivo(s) combinados en {salida}")
    print("Evalúe con: python ../01-local-gateway/scripts/evaluar_lote.py "
          "--resultados data/salida_gemini.jsonl --etiquetas data/etiquetas.jsonl")
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
    from google import genai
    from google.cloud import storage

    project = _env("GOOGLE_CLOUD_PROJECT")
    bucket = _env("GCP_BATCH_BUCKET")
    storage_client = storage.Client(project=project)
    client = genai.Client(enterprise=True, project=project, location=_env("GCP_BATCH_LOCATION"))
    if args.cmd == "preparar":
        preparar(storage_client, bucket, args.n)
    elif args.cmd == "enviar":
        enviar(client, bucket, _env("GEMINI_MODEL"))
    elif args.cmd == "estado":
        estado(client, args.esperar, max(30, args.intervalo))
    elif args.cmd == "descargar":
        descargar(client, storage_client)
    else:
        client.batches.cancel(name=_leer_nombre())
        print("Cancelación solicitada")


if __name__ == "__main__":
    main()
