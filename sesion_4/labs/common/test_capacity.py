import hashlib
import pathlib

import pytest

from capacity import estimate_replicas

ROOT = pathlib.Path(__file__).resolve().parent


def test_caso_base_universidad():
    # 100 usuarios * 15 tok/s = 1500 tok/s; réplica 400 tok/s con 30 % margen -> 280 efectivos -> 6 + 1
    r = estimate_replicas(100, 15, 400)
    assert r["demand_tokens_per_s"] == 1500.0
    assert r["replicas_base"] == 6 and r["replicas_total"] == 7


def test_sin_alta_disponibilidad():
    assert estimate_replicas(10, 10, 1000, headroom=0, high_availability=False)["replicas_total"] == 1


@pytest.mark.parametrize("args", [(0, 10, 100), (1, 0, 100), (1, 10, 0)])
def test_entradas_invalidas(args):
    with pytest.raises(ValueError):
        estimate_replicas(*args)


def test_headroom_invalido():
    with pytest.raises(ValueError):
        estimate_replicas(1, 1, 1, headroom=0.95)


def test_copias_en_laboratorios_son_identicas():
    """Los agentes desplegables llevan una copia local (empaquetado independiente): deben ser idénticas."""
    canon = hashlib.sha256((ROOT / "capacity.py").read_bytes()).hexdigest()
    for p in ROOT.parent.glob("*/**/capacity_tool.py"):
        assert hashlib.sha256(p.read_bytes()).hexdigest() == canon, f"{p} difiere de common/capacity.py"
