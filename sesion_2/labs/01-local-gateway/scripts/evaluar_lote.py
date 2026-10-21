"""Evalúa los resultados de un lote PQRS contra las etiquetas esperadas.

Acepta la salida de los cuatro entornos del curso:
- local / Azure OpenAI Batch: líneas con ``custom_id`` y ``response.body.choices``
- Gemini batch inference: líneas con ``request`` y ``response.candidates``; como
  la salida no trae un identificador propio, se empareja por el texto de la PQRS
- Amazon Bedrock batch (Converse): líneas con ``recordId`` y ``modelOutput.output.message``

Uso:
    python scripts/evaluar_lote.py --resultados salida.jsonl --etiquetas data/etiquetas.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))

import lote_pqrs as lp  # noqa: E402


TEXTO = "texto:"


def extraer(linea: dict[str, Any]) -> tuple[str, str] | None:
    """Devuelve (id, texto del modelo) para cualquiera de los tres formatos."""
    if "custom_id" in linea:  # OpenAI / Azure / gateway local
        body = (linea.get("response") or {}).get("body") or {}
        choices = body.get("choices") or []
        if not choices:
            return None
        return linea["custom_id"], choices[0].get("message", {}).get("content") or ""
    if "recordId" in linea:  # Amazon Bedrock, invocación Converse
        content = (((linea.get("modelOutput") or {}).get("output") or {}).get("message") or {}).get("content") or []
        return linea["recordId"], "".join(c.get("text", "") for c in content if isinstance(c, dict))
    if "request" in linea:  # Gemini: se identifica por el texto de la solicitud
        candidates = (linea.get("response") or {}).get("candidates") or []
        if not candidates:
            return None
        parts = (candidates[0].get("content") or {}).get("parts") or []
        user_parts = ((linea["request"].get("contents") or [{}])[0].get("parts")) or []
        texto = "".join(p.get("text", "") for p in user_parts if isinstance(p, dict))
        return TEXTO + texto, "".join(p.get("text", "") for p in parts if isinstance(p, dict))
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--resultados", type=Path, nargs="+", required=True, help="Uno o más archivos JSONL de salida")
    parser.add_argument("--etiquetas", type=Path, required=True)
    args = parser.parse_args()

    lote = [lp.PQRS(**json.loads(l)) for l in args.etiquetas.read_text(encoding="utf-8").splitlines() if l.strip()]
    # Para Gemini: texto de la PQRS -> ids pendientes (textos repetidos tienen las mismas etiquetas).
    por_texto: dict[str, list[str]] = {}
    for p in lote:
        por_texto.setdefault(p.texto, []).append(p.id)
    resultados: dict[str, str] = {}
    ilegibles = 0
    for ruta in args.resultados:
        for raw in ruta.read_text(encoding="utf-8").splitlines():
            if not raw.strip():
                continue
            par = extraer(json.loads(raw))
            if par is None:
                ilegibles += 1
            elif par[0].startswith(TEXTO):
                ids = por_texto.get(par[0][len(TEXTO):]) or []
                if ids:
                    resultados[ids.pop(0)] = par[1]
                else:
                    ilegibles += 1
            else:
                resultados[par[0]] = par[1]
    resumen = lp.resumir(resultados, lote)
    resumen["lineas_sin_respuesta"] = ilegibles
    print(json.dumps(resumen, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
