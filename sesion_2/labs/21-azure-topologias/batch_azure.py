"""AZ-G (parte batch) · Clasificación nocturna de PQRS con Azure OpenAI Batch.

IMPORTANTE: según la tabla oficial de cuotas (consultada el 20-oct-2026), las
suscripciones de prueba gratuita y Azure for Students tienen cuota Global Batch
"N/A". Este script requiere una suscripción de pago (por ejemplo, la del
docente). Los estudiantes con trial ejecutan el mismo lote en LOC-02, GCP-D o
AWS-E y comparan.

Flujo (documentación "Getting started with Azure OpenAI batch deployments"):
    preparar  -> genera data/lote_azure.jsonl con el nombre del despliegue Global Batch
    enviar    -> sube el archivo (purpose="batch") y crea el trabajo (ventana 24h)
    estado    -> consulta el estado (la documentación sugiere esperar >= 60 s entre consultas)
    descargar -> guarda resultados y errores en data/
    cancelar  -> cancela; lo completado se conserva y se factura

Uso:
    python batch_azure.py preparar --n 200
    python batch_azure.py enviar
    python batch_azure.py estado --esperar
    python batch_azure.py descargar
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
from multiregion import build_client  # noqa: E402

DATA = Path(__file__).resolve().parent / "data"
LOTE = DATA / "lote_azure.jsonl"
ETIQUETAS = DATA / "etiquetas.jsonl"
ESTADO = DATA / "estado_batch.json"
TERMINALES = {"completed", "failed", "expired", "cancelled"}


def _env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Defina {name} en .env (ver .env.example)")
    return value


def _guardar_estado(data: dict[str, Any]) -> None:
    ESTADO.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _leer_estado() -> dict[str, Any]:
    if not ESTADO.exists():
        raise SystemExit("No hay un trabajo enviado. Ejecute primero: python batch_azure.py enviar")
    return json.loads(ESTADO.read_text(encoding="utf-8"))


def preparar(n: int, deployment: str) -> None:
    lote = lp.generar_pqrs(n)
    lp.escribir_jsonl(lp.a_openai_batch(lote, deployment), LOTE)
    lp.escribir_jsonl(({**p.__dict__} for p in lote), ETIQUETAS)
    print(f"{n} solicitudes en {LOTE} (despliegue '{deployment}', UTF-8 sin BOM)")


def enviar(client: Any) -> None:
    if not LOTE.exists():
        raise SystemExit("Falta el lote. Ejecute: python batch_azure.py preparar")
    with LOTE.open("rb") as f:
        archivo = client.files.create(
            file=f,
            purpose="batch",
            # Caducidad del archivo de entrada: 14 días (rango documentado: 14 a 30 días).
            extra_body={"expires_after": {"seconds": 1_209_600, "anchor": "created_at"}},
        )
    trabajo = client.batches.create(
        input_file_id=archivo.id,
        # La documentación de Azure usa "/chat/completions"; el servicio lee el tipo de
        # solicitud del propio archivo. Los tipos del SDK de OpenAI listan "/v1/...".
        endpoint="/chat/completions",  # type: ignore[arg-type]
        completion_window="24h",  # único valor válido
        extra_body={"output_expires_after": {"seconds": 1_209_600, "anchor": "created_at"}},
    )
    _guardar_estado({"file_id": archivo.id, "batch_id": trabajo.id, "enviado": time.time()})
    print(f"Archivo {archivo.id} · trabajo {trabajo.id} · estado {trabajo.status}")


def estado(client: Any, esperar: bool, intervalo_s: int) -> Any:
    batch_id = _leer_estado()["batch_id"]
    while True:
        trabajo = client.batches.retrieve(batch_id)
        counts = trabajo.request_counts
        print(f"{time.strftime('%H:%M:%S')} estado={trabajo.status} "
              f"completadas={getattr(counts, 'completed', '?')} fallidas={getattr(counts, 'failed', '?')} "
              f"total={getattr(counts, 'total', '?')}")
        if not esperar or trabajo.status in TERMINALES:
            return trabajo
        time.sleep(intervalo_s)


def descargar(client: Any) -> None:
    trabajo = client.batches.retrieve(_leer_estado()["batch_id"])
    for nombre, file_id in (("salida", trabajo.output_file_id), ("errores", trabajo.error_file_id)):
        if not file_id:
            print(f"Sin archivo de {nombre}")
            continue
        destino = DATA / f"{nombre}_azure.jsonl"
        destino.write_bytes(client.files.content(file_id).read())
        print(f"{nombre}: {destino} ({destino.stat().st_size} bytes)")
    print("Evalúe con: python ../01-local-gateway/scripts/evaluar_lote.py "
          "--resultados data/salida_azure.jsonl --etiquetas data/etiquetas.jsonl")


def cancelar(client: Any) -> None:
    trabajo = client.batches.cancel(_leer_estado()["batch_id"])
    print(f"Trabajo {trabajo.id}: {trabajo.status} (puede tardar hasta 10 minutos)")


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
    if args.cmd == "preparar":
        preparar(args.n, _env("AZ_BATCH_DEPLOYMENT"))
        return
    client = build_client(_env("AZ_BATCH_ENDPOINT").rstrip("/"), timeout_s=120)
    {"enviar": lambda: enviar(client),
     "estado": lambda: estado(client, args.esperar, max(60, args.intervalo)),
     "descargar": lambda: descargar(client),
     "cancelar": lambda: cancelar(client)}[args.cmd]()


if __name__ == "__main__":
    main()
