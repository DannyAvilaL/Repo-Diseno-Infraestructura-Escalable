"""Pruebas unitarias del backend. No requieren Ollama ni red."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app, get_provider
from app.metrics import compute_metrics
from app.providers import InferenceProvider, ProviderError, TextChunk, Usage
from app.providers.ollama import OllamaProvider
from app.providers.openai_compat import OpenAICompatProvider


class FakeProvider(InferenceProvider):
    name = "fake"
    model = "fake-model"

    def __init__(self, chunks: list[str], fail: bool = False) -> None:
        self.chunks = chunks
        self.fail = fail

    async def stream_chat(self, messages: list[dict[str, str]]) -> AsyncIterator[object]:
        if self.fail:
            raise ProviderError("proveedor caído")
        for c in self.chunks:
            yield TextChunk(c)
        yield Usage(prompt_tokens=12, completion_tokens=len(self.chunks))

    async def health(self) -> None:
        if self.fail:
            raise ProviderError("proveedor caído")


@pytest.fixture
def client_factory():
    def make(provider: InferenceProvider) -> TestClient:
        app.dependency_overrides[get_provider] = lambda: provider
        return TestClient(app)

    yield make
    app.dependency_overrides.clear()


# --- Métricas -------------------------------------------------------------


def test_tpot_formula() -> None:
    m = compute_metrics(ttft_ms=200.0, e2e_ms=1100.0, output_chunks=10, completion_tokens=10)
    assert m.tpot_ms == pytest.approx(100.0)
    assert m.tokens_per_second == pytest.approx(10.0)


def test_metrics_without_tokens() -> None:
    m = compute_metrics(ttft_ms=None, e2e_ms=50.0, output_chunks=0)
    assert m.tpot_ms is None and m.ttft_ms is None


# --- API ------------------------------------------------------------------


def test_healthz(client_factory) -> None:
    with client_factory(FakeProvider(["a"])) as client:
        assert client.get("/healthz").json() == {"status": "ok"}


def test_readyz_degraded(client_factory) -> None:
    with client_factory(FakeProvider([], fail=True)) as client:
        r = client.get("/readyz")
        assert r.status_code == 503
        assert r.json()["status"] == "degraded"


def test_chat_returns_content_and_metrics(client_factory) -> None:
    with client_factory(FakeProvider(["Hola", " mundo"])) as client:
        r = client.post("/v1/chat", json={"messages": [{"role": "user", "content": "hola"}]})
        assert r.status_code == 200
        body = r.json()
        assert body["content"] == "Hola mundo"
        assert body["metrics"]["completion_tokens"] == 2
        assert body["metrics"]["ttft_ms"] is not None


def test_chat_rejects_oversized_input(client_factory) -> None:
    with client_factory(FakeProvider(["x"])) as client:
        big = "a" * 10_000
        r = client.post("/v1/chat", json={"messages": [{"role": "user", "content": big}]})
        assert r.status_code == 413


def test_chat_validation_error(client_factory) -> None:
    with client_factory(FakeProvider(["x"])) as client:
        r = client.post("/v1/chat", json={"messages": []})
        assert r.status_code == 422


def test_chat_provider_error_maps_to_502(client_factory) -> None:
    with client_factory(FakeProvider([], fail=True)) as client:
        r = client.post("/v1/chat", json={"messages": [{"role": "user", "content": "hola"}]})
        assert r.status_code == 502


def test_stream_emits_tokens_metrics_done(client_factory) -> None:
    with client_factory(FakeProvider(["A", "B", "C"])) as client:
        r = client.post("/v1/chat/stream", json={"messages": [{"role": "user", "content": "hola"}]})
        assert r.status_code == 200
        events = [line.split(": ", 1)[1] for line in r.text.splitlines() if line.startswith("event:")]
        assert events == ["token", "token", "token", "metrics", "done"]


def test_stream_reports_error_event(client_factory) -> None:
    with client_factory(FakeProvider([], fail=True)) as client:
        r = client.post("/v1/chat/stream", json={"messages": [{"role": "user", "content": "hola"}]})
        assert "event: error" in r.text


# --- Adaptadores con transporte simulado -----------------------------------


@pytest.mark.asyncio
async def test_ollama_parses_ndjson() -> None:
    lines = [
        {"message": {"role": "assistant", "content": "Hola"}, "done": False},
        {"message": {"role": "assistant", "content": "!"}, "done": False},
        {"message": {"role": "assistant", "content": ""}, "done": True,
         "prompt_eval_count": 20, "eval_count": 2},
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/chat"
        assert json.loads(request.content)["stream"] is True
        return httpx.Response(200, text="\n".join(json.dumps(x) for x in lines))

    client = httpx.AsyncClient(base_url="http://ollama", transport=httpx.MockTransport(handler))
    p = OllamaProvider("http://ollama", "m", temperature=0, max_output_tokens=10,
                       timeout=httpx.Timeout(5), max_retries=0, client=client)
    events = [e async for e in p.stream_chat([{"role": "user", "content": "hi"}])]
    assert [e.text for e in events if isinstance(e, TextChunk)] == ["Hola", "!"]
    assert events[-1] == Usage(prompt_tokens=20, completion_tokens=2)


@pytest.mark.asyncio
async def test_ollama_health_missing_model() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"models": [{"name": "otro:latest"}]})

    client = httpx.AsyncClient(base_url="http://ollama", transport=httpx.MockTransport(handler))
    p = OllamaProvider("http://ollama", "m", temperature=0, max_output_tokens=10,
                       timeout=httpx.Timeout(5), max_retries=0, client=client)
    with pytest.raises(ProviderError, match="ollama pull m"):
        await p.health()


@pytest.mark.asyncio
async def test_retry_on_503_then_success() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(503, text="ocupado")
        return httpx.Response(200, text=json.dumps({"message": {"content": "ok"}, "done": True}))

    client = httpx.AsyncClient(base_url="http://ollama", transport=httpx.MockTransport(handler))
    p = OllamaProvider("http://ollama", "m", temperature=0, max_output_tokens=10,
                       timeout=httpx.Timeout(5), max_retries=1, client=client)
    events = [e async for e in p.stream_chat([{"role": "user", "content": "hi"}])]
    assert calls["n"] == 2
    assert isinstance(events[0], TextChunk)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("models", "ok"),
    [([{"id": "m"}, {"id": "otro"}], True), ([{"id": "otro"}], False), ([], False), (None, False)],
)
async def test_openai_compat_health_checks_model(models: list[dict[str, str]] | None, ok: bool) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/models")
        return httpx.Response(200, json={"object": "list", "data": models})

    client = httpx.AsyncClient(base_url="http://api/v1", transport=httpx.MockTransport(handler))
    p = OpenAICompatProvider("http://api/v1", "m", None, temperature=0, max_output_tokens=10,
                             timeout=httpx.Timeout(5), max_retries=0, client=client)
    if ok:
        await p.health()
    else:
        with pytest.raises(ProviderError):
            await p.health()


@pytest.mark.asyncio
async def test_openai_compat_parses_sse() -> None:
    sse = (
        'data: {"choices":[{"delta":{"content":"Ho"}}]}\n\n'
        'data: {"choices":[{"delta":{"content":"la"}}]}\n\n'
        'data: {"choices":[],"usage":{"prompt_tokens":5,"completion_tokens":2}}\n\n'
        "data: [DONE]\n\n"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer k"
        return httpx.Response(200, text=sse)

    client = httpx.AsyncClient(base_url="http://api/v1", transport=httpx.MockTransport(handler),
                               headers={"Authorization": "Bearer k"})
    p = OpenAICompatProvider("http://api/v1", "m", "k", temperature=0, max_output_tokens=10,
                             timeout=httpx.Timeout(5), max_retries=0, client=client)
    events = [e async for e in p.stream_chat([{"role": "user", "content": "hi"}])]
    assert "".join(e.text for e in events if isinstance(e, TextChunk)) == "Hola"
    assert events[-1] == Usage(prompt_tokens=5, completion_tokens=2)


# --- OpenTelemetry -----------------------------------------------------------


def test_inference_span_attributes(client_factory) -> None:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    with client_factory(FakeProvider(["Hola", " mundo"])) as client:
        r = client.post("/v1/chat/stream", json={"messages": [{"role": "user", "content": "hola"}]})
        assert r.status_code == 200

    spans = [s for s in exporter.get_finished_spans() if s.name.startswith("chat ")]
    assert len(spans) == 1
    attrs = spans[0].attributes
    assert attrs["gen_ai.operation.name"] == "chat"
    assert attrs["gen_ai.request.model"] == "fake-model"
    assert attrs["gen_ai.usage.output_tokens"] == 2
    assert "app.ttft_ms" in attrs
    # Privacidad: ningún atributo contiene el texto de la conversación
    assert all("Hola" not in str(v) and "hola" != v for v in attrs.values())
