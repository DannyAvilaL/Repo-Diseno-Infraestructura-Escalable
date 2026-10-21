import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from universidad_tools import buscar_reglamento, consultar_calendario_academico  # noqa: E402


def test_calendario_con_tildes() -> None:
    assert "1 de febrero" in consultar_calendario_academico("Inicio de clases")


def test_calendario_no_encontrado() -> None:
    assert consultar_calendario_academico("vacaciones").startswith("No se encontró")


def test_reglamento_homologacion() -> None:
    assert "art. 45" in buscar_reglamento("homologación")


def test_validacion_vacia() -> None:
    with pytest.raises(ValueError):
        buscar_reglamento("   ")


def test_validacion_longitud() -> None:
    with pytest.raises(ValueError):
        buscar_reglamento("x" * 500)
