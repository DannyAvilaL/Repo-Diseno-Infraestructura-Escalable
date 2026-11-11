"""Cola de trabajos con semántica tipo Amazon SQS / Service Bus / Pub/Sub.

Se implementa en memoria para poder estudiar, sin cuenta cloud, los conceptos
que SÍ son idénticos en los tres proveedores:

* **At-least-once delivery**: un mensaje puede entregarse más de una vez
  → los consumidores deben ser **idempotentes**.
* **Visibility timeout** (SQS) ≈ *lock duration* (Service Bus) ≈ *ack deadline*
  (Pub/Sub): un mensaje recibido deja de ser visible; si no se confirma
  (``delete``), reaparece.
* **Max receive count → DLQ** (dead-letter queue): evita mensajes "veneno".
* **Backoff** exponencial entre reintentos.

La interfaz ``JobQueue`` es el punto de extensión: ``SqsQueue``, ``PubSubQueue``
o ``ServiceBusQueue`` implementarían los mismos 4 métodos.
"""

from __future__ import annotations

import asyncio
import contextlib
import time
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Protocol

from .schemas import ChatRequest, ChatResponse, JobStatus


@dataclass(slots=True)
class Message:
    message_id: str
    job_id: str
    body: ChatRequest
    tenant: str
    receive_count: int = 0
    visible_at: float = 0.0
    receipt: str | None = None


@dataclass(slots=True)
class JobRecord:
    job_id: str
    tenant: str
    status: JobStatus = JobStatus.PENDING
    attempts: int = 0
    result: ChatResponse | None = None
    error: str | None = None
    idempotency_key: str | None = None
    created_at: float = field(default_factory=time.time)


class JobQueue(Protocol):
    async def send(self, msg: Message) -> None: ...
    async def receive(self, max_messages: int = 1) -> list[Message]: ...
    async def delete(self, receipt: str) -> None: ...
    async def change_visibility(self, receipt: str, timeout_s: float) -> None: ...
    def depth(self) -> int: ...


class InMemoryQueue:
    def __init__(
        self,
        *,
        visibility_timeout_s: float,
        max_receive_count: int,
        clock: Callable[[], float] = time.monotonic,
        on_dead_letter: Callable[[Message], None] | None = None,
    ) -> None:
        self._visibility_s = visibility_timeout_s
        self._max_receive = max_receive_count
        self._clock = clock
        self._messages: dict[str, Message] = {}
        self._by_receipt: dict[str, str] = {}
        self._lock = asyncio.Lock()
        self.dead_letters: list[Message] = []
        self._on_dead_letter = on_dead_letter

    @property
    def max_receive_count(self) -> int:
        return self._max_receive

    def depth(self) -> int:
        """Mensajes en cola (visibles o en vuelo), equivalente a ApproximateNumberOfMessages*."""
        return len(self._messages)

    async def send(self, msg: Message) -> None:
        async with self._lock:
            msg.visible_at = self._clock()
            self._messages[msg.message_id] = msg

    async def receive(self, max_messages: int = 1) -> list[Message]:
        now = self._clock()
        out: list[Message] = []
        async with self._lock:
            for msg in list(self._messages.values()):
                if len(out) >= max_messages:
                    break
                if msg.visible_at > now:
                    continue
                if msg.receive_count >= self._max_receive:
                    # Redrive policy: supera maxReceiveCount -> DLQ
                    del self._messages[msg.message_id]
                    self.dead_letters.append(msg)
                    if self._on_dead_letter:
                        self._on_dead_letter(msg)
                    continue
                msg.receive_count += 1
                msg.visible_at = now + self._visibility_s
                msg.receipt = uuid.uuid4().hex
                self._by_receipt[msg.receipt] = msg.message_id
                out.append(msg)
        return out

    async def delete(self, receipt: str) -> None:
        async with self._lock:
            message_id = self._by_receipt.pop(receipt, None)
            if message_id:
                self._messages.pop(message_id, None)

    async def change_visibility(self, receipt: str, timeout_s: float) -> None:
        async with self._lock:
            message_id = self._by_receipt.get(receipt)
            if message_id and message_id in self._messages:
                self._messages[message_id].visible_at = self._clock() + timeout_s


class JobStore:
    """Estado de los trabajos (en AWS sería DynamoDB; en Azure Cosmos/Table; en GCP Firestore)."""

    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._idem: dict[tuple[str, str], str] = {}

    def create(self, tenant: str, idempotency_key: str | None) -> tuple[JobRecord, bool]:
        """Devuelve ``(job, replay)``. ``replay=True`` si la clave ya existía."""
        if idempotency_key:
            existing_id = self._idem.get((tenant, idempotency_key))
            if existing_id:
                return self._jobs[existing_id], True
        job = JobRecord(job_id=uuid.uuid4().hex, tenant=tenant, idempotency_key=idempotency_key)
        self._jobs[job.job_id] = job
        if idempotency_key:
            self._idem[(tenant, idempotency_key)] = job.job_id
        return job, False

    def get(self, job_id: str) -> JobRecord | None:
        return self._jobs.get(job_id)


Handler = Callable[[Message], Awaitable[ChatResponse]]


class WorkerPool:
    """Consumidores concurrentes (equivalente a un *event source mapping* / trigger)."""

    def __init__(
        self,
        *,
        queue: InMemoryQueue,
        store: JobStore,
        handler: Handler,
        workers: int,
        backoff_s: float,
        poll_interval_s: float = 0.05,
        on_terminal: Callable[[JobRecord], None] | None = None,
    ) -> None:
        self._queue = queue
        self._store = store
        self._handler = handler
        self._workers = workers
        self._backoff_s = backoff_s
        self._poll_s = poll_interval_s
        self._on_terminal = on_terminal
        self._tasks: list[asyncio.Task[None]] = []
        self._stopping = asyncio.Event()

    def start(self) -> None:
        self._stopping.clear()
        self._tasks = [
            asyncio.create_task(self._run(i), name=f"worker-{i}") for i in range(self._workers)
        ]

    async def stop(self) -> None:
        self._stopping.set()
        for task in self._tasks:
            task.cancel()
        for task in self._tasks:
            with contextlib.suppress(asyncio.CancelledError):
                await task
        self._tasks.clear()

    async def _run(self, _index: int) -> None:
        while not self._stopping.is_set():
            batch = await self._queue.receive(1)
            if not batch:
                await asyncio.sleep(self._poll_s)
                continue
            for msg in batch:
                await self._process(msg)

    async def _process(self, msg: Message) -> None:
        job = self._store.get(msg.job_id)
        if job is None or job.status in (JobStatus.SUCCEEDED, JobStatus.DEAD):
            # Idempotencia: entrega duplicada de un trabajo ya resuelto.
            if msg.receipt:
                await self._queue.delete(msg.receipt)
            return
        job.status = JobStatus.RUNNING
        job.attempts = msg.receive_count
        try:
            job.result = await self._handler(msg)
            job.status = JobStatus.SUCCEEDED
            job.error = None
            if msg.receipt:
                await self._queue.delete(msg.receipt)
            if self._on_terminal:
                self._on_terminal(job)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001 - frontera de reintentos
            job.error = f"{type(exc).__name__}: {exc}"
            if msg.receive_count >= self._queue.max_receive_count:
                job.status = JobStatus.DEAD
                if msg.receipt:
                    await self._queue.delete(msg.receipt)
                self._queue.dead_letters.append(msg)
                if self._on_terminal:
                    self._on_terminal(job)
            else:
                job.status = JobStatus.FAILED  # transitorio: se reintentará
                delay = self._backoff_s * (2 ** (msg.receive_count - 1))
                if msg.receipt:
                    await self._queue.change_visibility(msg.receipt, delay)
