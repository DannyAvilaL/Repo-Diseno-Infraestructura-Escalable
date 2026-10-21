"""Genera el lote PQRS en el formato de entrada de cada proveedor.

Ejemplos:
    python scripts/generar_lote.py --n 200 --formato openai --modelo simulado --salida data/lote.jsonl
    python scripts/generar_lote.py --n 200 --formato gemini --salida data/lote-gemini.jsonl
    python scripts/generar_lote.py --n 200 --formato bedrock --salida data/lote-bedrock.jsonl
    python scripts/generar_lote.py --n 200 --formato etiquetas --salida data/etiquetas.jsonl

El formato "etiquetas" guarda las respuestas esperadas para evaluar la
calidad del resultado con scripts/evaluar_lote.py.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))

import lote_pqrs as lp  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--n", type=int, default=200)
    parser.add_argument("--semilla", type=int, default=42)
    parser.add_argument("--formato", choices=["openai", "gemini", "bedrock", "etiquetas"], default="openai")
    parser.add_argument("--modelo", default="simulado", help="Formato openai: nombre del modelo o despliegue")
    parser.add_argument("--salida", type=Path, required=True)
    args = parser.parse_args()

    lote = lp.generar_pqrs(args.n, semilla=args.semilla)
    if args.formato == "openai":
        lineas = lp.a_openai_batch(lote, args.modelo)
    elif args.formato == "gemini":
        lineas = lp.a_gemini_batch(lote)
    elif args.formato == "bedrock":
        lineas = lp.a_bedrock_batch(lote)
    else:
        lineas = [asdict(p) for p in lote]
    n = lp.escribir_jsonl(lineas, args.salida)
    print(f"{n} líneas escritas en {args.salida} (formato {args.formato})")


if __name__ == "__main__":
    main()
