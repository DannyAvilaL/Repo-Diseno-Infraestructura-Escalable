"""Pruebas del generador del lote PQRS (Sesión 2)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import lote_pqrs as lp  # noqa: E402


def test_generacion_reproducible_y_ids_unicos() -> None:
    a = lp.generar_pqrs(200, semilla=7)
    b = lp.generar_pqrs(200, semilla=7)
    assert a == b
    assert len({p.id for p in a}) == 200
    assert all(len(p.id) == 11 and p.id.isalnum() for p in a)


def test_generacion_valida_parametros() -> None:
    with pytest.raises(ValueError):
        lp.generar_pqrs(0)
    with pytest.raises(ValueError):
        lp.generar_pqrs(5, proporcion_inyeccion=1.5)


def test_formatos_por_proveedor() -> None:
    lote = lp.generar_pqrs(3)
    oa = lp.a_openai_batch(lote, "mi-despliegue")
    assert {l["method"] for l in oa} == {"POST"}
    assert {l["body"]["model"] for l in oa} == {"mi-despliegue"}
    assert oa[0]["body"]["messages"][0]["role"] == "system"

    ge = lp.a_gemini_batch(lote)
    assert set(ge[0]) == {"request"}
    assert ge[0]["request"]["contents"][0]["parts"][0]["text"] == lote[0].texto

    br = lp.a_bedrock_batch(lote)
    assert br[0]["recordId"] == lote[0].id
    assert br[0]["modelInput"]["messages"][0]["content"][0]["text"] == lote[0].texto


def test_escribir_jsonl_sin_bom(tmp_path: Path) -> None:
    ruta = tmp_path / "lote.jsonl"
    n = lp.escribir_jsonl(lp.a_openai_batch(lp.generar_pqrs(5), "m"), ruta)
    datos = ruta.read_bytes()
    assert n == 5
    assert not datos.startswith(b"\xef\xbb\xbf")
    assert len([json.loads(l) for l in datos.decode("utf-8").splitlines()]) == 5


@pytest.mark.parametrize(
    ("texto", "valido"),
    [
        ('{"tipo":"queja","area":"biblioteca","prioridad":"media","resumen":"x"}', True),
        ('```json\n{"tipo":"queja","area":"biblioteca","prioridad":"alta","resumen":"x"}\n```', True),
        ('{"tipo":"otro","area":"biblioteca","prioridad":"media"}', False),
        ("no es json", False),
        ("[1, 2]", False),
    ],
)
def test_parsear_clasificacion(texto: str, valido: bool) -> None:
    assert (lp.parsear_clasificacion(texto) is not None) is valido


def test_resumir_calcula_exactitud() -> None:
    lote = lp.generar_pqrs(2, proporcion_inyeccion=0.0)
    p0, p1 = lote
    resultados = {
        p0.id: json.dumps({"tipo": p0.tipo_esperado, "area": p0.area_esperada, "prioridad": "baja", "resumen": "r"}),
        p1.id: "respuesta inválida",
    }
    r = lp.resumir(resultados, lote)
    assert r["json_validos"] == 1
    assert r["exactitud_tipo"] == 1.0
    assert r["faltantes"] == 0
