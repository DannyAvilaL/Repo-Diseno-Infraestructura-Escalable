from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from serverless_llm.config import Settings
from serverless_llm.main import create_app

API_KEY = "test-key"
HEADERS = {"X-API-Key": API_KEY}


def make_settings(**overrides: object) -> Settings:
    base: dict[str, object] = {
        "environment": "local",
        "api_keys": f"{API_KEY}:tenant-a,other-key:tenant-b",
        "mock_cold_start_s": 0.05,
        "mock_ttft_ms": 5,
        "mock_tpot_ms": 1,
        "queue_retry_backoff_s": 0.01,
        "rate_limit_per_minute": 10_000,
        "log_level": "WARNING",
    }
    base.update(overrides)
    return Settings(**base)  # type: ignore[arg-type]


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app(make_settings())) as c:
        yield c


@pytest.fixture
def headers() -> dict[str, str]:
    return dict(HEADERS)
