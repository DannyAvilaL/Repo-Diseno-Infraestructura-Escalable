"""Pruebas de la cola: visibilidad, reintentos con backoff, DLQ e idempotencia."""

from __future__ import annotations

import asyncio

from serverless_llm.jobqueue import InMemoryQueue, JobStore, Message, WorkerPool
from serverless_llm.schemas import ChatRequest, ChatResponse, JobStatus, Timings, Usage


def _msg(job_id: str = "j1") -> Message:
    return Message(message_id=job_id, job_id=job_id, body=ChatRequest(prompt="hola"), tenant="t")


def _ok_response() -> ChatResponse:
    return ChatResponse(
        text="ok", model="m", usage=Usage(), timings=Timings(total_ms=1.0), instance_id="i"
    )


async def test_visibility_timeout_hides_then_redelivers() -> None:
    now = [0.0]
    q = InMemoryQueue(visibility_timeout_s=10, max_receive_count=5, clock=lambda: now[0])
    await q.send(_msg())
    first = await q.receive()
    assert len(first) == 1 and first[0].receive_count == 1
    assert await q.receive() == []  # en vuelo: invisible
    now[0] = 11  # venció el visibility timeout sin delete -> reaparece
    again = await q.receive()
    assert len(again) == 1 and again[0].receive_count == 2


async def test_delete_removes_message() -> None:
    q = InMemoryQueue(visibility_timeout_s=1, max_receive_count=5)
    await q.send(_msg())
    (m,) = await q.receive()
    assert m.receipt
    await q.delete(m.receipt)
    assert q.depth() == 0


async def test_redrive_to_dlq_after_max_receive_count() -> None:
    now = [0.0]
    dead: list[Message] = []
    q = InMemoryQueue(
        visibility_timeout_s=1,
        max_receive_count=2,
        clock=lambda: now[0],
        on_dead_letter=dead.append,
    )
    await q.send(_msg())
    for _ in range(2):  # dos recepciones sin confirmar
        assert len(await q.receive()) == 1
        now[0] += 2
    assert await q.receive() == []  # tercera: va a la DLQ
    assert len(q.dead_letters) == 1 and len(dead) == 1
    assert q.depth() == 0


async def test_worker_success() -> None:
    q = InMemoryQueue(visibility_timeout_s=5, max_receive_count=3)
    store = JobStore()
    job, _ = store.create("t", None)
    await q.send(Message(message_id=job.job_id, job_id=job.job_id, body=ChatRequest(prompt="x"), tenant="t"))

    async def handler(_m: Message) -> ChatResponse:
        return _ok_response()

    pool = WorkerPool(queue=q, store=store, handler=handler, workers=1, backoff_s=0.01)
    pool.start()
    try:
        await _wait_for(lambda: job.status == JobStatus.SUCCEEDED)
    finally:
        await pool.stop()
    assert job.attempts == 1 and q.depth() == 0


async def test_worker_retries_transient_failure_then_succeeds() -> None:
    q = InMemoryQueue(visibility_timeout_s=5, max_receive_count=4)
    store = JobStore()
    job, _ = store.create("t", None)
    await q.send(Message(message_id=job.job_id, job_id=job.job_id, body=ChatRequest(prompt="x"), tenant="t"))
    attempts = 0

    async def flaky(_m: Message) -> ChatResponse:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise RuntimeError("fallo transitorio")
        return _ok_response()

    pool = WorkerPool(queue=q, store=store, handler=flaky, workers=1, backoff_s=0.01)
    pool.start()
    try:
        await _wait_for(lambda: job.status == JobStatus.SUCCEEDED, within=3)
    finally:
        await pool.stop()
    assert attempts == 3 and job.attempts == 3


async def test_poison_message_ends_in_dlq() -> None:
    q = InMemoryQueue(visibility_timeout_s=5, max_receive_count=2)
    store = JobStore()
    job, _ = store.create("t", None)
    await q.send(Message(message_id=job.job_id, job_id=job.job_id, body=ChatRequest(prompt="x"), tenant="t"))

    async def always_fails(_m: Message) -> ChatResponse:
        raise ValueError("veneno")

    pool = WorkerPool(queue=q, store=store, handler=always_fails, workers=1, backoff_s=0.01)
    pool.start()
    try:
        await _wait_for(lambda: job.status == JobStatus.DEAD, within=3)
    finally:
        await pool.stop()
    assert len(q.dead_letters) == 1
    assert job.error and "ValueError" in job.error


def test_idempotency_key_returns_same_job() -> None:
    store = JobStore()
    a, replay_a = store.create("t", "key-1")
    b, replay_b = store.create("t", "key-1")
    c, _ = store.create("other", "key-1")
    assert a.job_id == b.job_id and (replay_a, replay_b) == (False, True)
    assert c.job_id != a.job_id  # la clave es por tenant


async def _wait_for(predicate, within: float = 2.0) -> None:  # type: ignore[no-untyped-def]
    deadline = asyncio.get_running_loop().time() + within
    while not predicate():
        if asyncio.get_running_loop().time() > deadline:
            raise AssertionError("condición no alcanzada a tiempo")
        await asyncio.sleep(0.01)
