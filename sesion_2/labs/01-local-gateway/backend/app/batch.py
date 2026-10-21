"""Inferencia por lotes (batch) sobre el mismo router multi-región.

Reproduce, a escala de laboratorio, el ciclo de vida de los servicios batch
gestionados (Azure OpenAI Batch, batch inference de Gemini y de Amazon
Bedrock):

    validating -> in_progress -> finalizing -> completed
                \\-> failed (entrada inválida)
    in_progress -> expired (venció la ventana de finalización; resultados parciales)
    in_progress -> cancelling -> cancelled (resultados parciales)

Decisiones de diseño (ADR-0006):

- **Formato de entrada:** JSONL con ``custom_id``, ``method``, ``url`` y
  ``body``, el mismo de OpenAI y Azure OpenAI Batch. Los resultados NO
  conservan el orden de entrada: se emparejan por ``custom_id``.
- **Prioridad de lo online:** el procesador cede la capacidad mientras haya
  solicitudes online en curso (``batch_yield_online_inflight``). Así un lote
  grande no degrada la latencia de los usuarios interactivos.
- **Reintentos con espera exponencial:** el lote tolera demoras, por lo que
  reintenta más y espera más que el camino online.
- **Durabilidad:** el estado y los resultados se escriben en disco; al
  reiniciar, los trabajos no terminados se reanudan sin repetir solicitudes
  ya resueltas.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import tempfile
import time
import uuid
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from .config import Settings
from .region_client import RegionError
from .router import NoRegionAvailable, Router
from .schemas import BatchJob

logger = logging.getLogger("gateway.batch")

TERMINAL = {"completed", "failed", "expired", "cancelled"}
URLS_VALIDAS = {"/v1/chat/completions", "/chat/completions"}
ROLES_VALIDOS = {"system", "user", "assistant"}
MAX_ERRORES_REPORTADOS = 20


class BatchValidationError(ValueError):
    def __init__(self, errors: list[str]) -> None:
        super().__init__("; ".join(errors))
        self.errors = errors


class JobNotFound(KeyError):
    pass


class InvalidJobState(RuntimeError):
    pass


def parse_batch_input(raw: bytes, *, max_requests: int, max_bytes: int) -> list[dict[str, Any]]:
    """Valida el archivo JSONL completo antes de aceptar el trabajo."""
    if len(raw) > max_bytes:
        raise BatchValidationError([f"El archivo supera {max_bytes} bytes"])
    if raw.startswith(b"\xef\xbb\xbf"):
        raise BatchValidationError(["El archivo tiene BOM UTF-8; guárdelo como UTF-8 sin BOM"])
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BatchValidationError(["El archivo no está codificado en UTF-8"]) from exc

    errors: list[str] = []
    lines: list[dict[str, Any]] = []
    seen: set[str] = set()

    def err(n: int, msg: str) -> None:
        if len(errors) < MAX_ERRORES_REPORTADOS:
            errors.append(f"línea {n}: {msg}")

    for n, raw_line in enumerate(text.splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            obj = json.loads(raw_line)
        except json.JSONDecodeError:
            err(n, "JSON inválido")
            continue
        if not isinstance(obj, dict):
            err(n, "se esperaba un objeto JSON")
            continue
        cid = obj.get("custom_id")
        if not isinstance(cid, str) or not 1 <= len(cid) <= 64:
            err(n, "custom_id debe ser texto de 1 a 64 caracteres")
            continue
        if cid in seen:
            err(n, f"custom_id duplicado: {cid}")
            continue
        if obj.get("method") != "POST":
            err(n, "method debe ser POST")
            continue
        if obj.get("url") not in URLS_VALIDAS:
            err(n, "url debe ser /v1/chat/completions")
            continue
        body = obj.get("body")
        messages = body.get("messages") if isinstance(body, dict) else None
        if not isinstance(messages, list) or not messages:
            err(n, "body.messages debe ser una lista no vacía")
            continue
        if not all(
            isinstance(m, dict) and m.get("role") in ROLES_VALIDOS and isinstance(m.get("content"), str)
            for m in messages
        ):
            err(n, "cada mensaje necesita role (system|user|assistant) y content (texto)")
            continue
        seen.add(cid)
        lines.append(obj)

    if not errors and not lines:
        errors.append("El archivo no contiene solicitudes")
    if len(lines) > max_requests:
        errors.append(f"El archivo tiene {len(lines)} solicitudes; el máximo es {max_requests}")
    if errors:
        raise BatchValidationError(errors)
    return lines


class BatchStore:
    """Persistencia en disco: estado (JSON) y resultados (JSONL) por trabajo."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, job_id: str, suffix: str) -> Path:
        if not job_id.startswith("batch_") or not job_id[6:].isalnum():
            raise JobNotFound(job_id)  # evita recorrer rutas con ids manipulados
        return self.root / f"{job_id}.{suffix}"

    def save(self, job: BatchJob) -> None:
        path = self._path(job.id, "json")
        fd, tmp = tempfile.mkstemp(dir=self.root, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(job.model_dump_json(indent=2))
        os.replace(tmp, path)  # escritura atómica

    def load(self, job_id: str) -> BatchJob:
        path = self._path(job_id, "json")
        if not path.exists():
            raise JobNotFound(job_id)
        return BatchJob.model_validate_json(path.read_text(encoding="utf-8"))

    def list(self) -> list[BatchJob]:
        jobs = [BatchJob.model_validate_json(p.read_text(encoding="utf-8")) for p in self.root.glob("batch_*.json")]
        return sorted(jobs, key=lambda j: j.created_at, reverse=True)

    def write_input(self, job_id: str, lines: list[dict[str, Any]]) -> None:
        with self._path(job_id, "input.jsonl").open("w", encoding="utf-8") as f:
            for line in lines:
                f.write(json.dumps(line, ensure_ascii=False) + "\n")

    def read_input(self, job_id: str) -> list[dict[str, Any]]:
        with self._path(job_id, "input.jsonl").open(encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    def output_path(self, job_id: str) -> Path:
        return self._path(job_id, "output.jsonl")

    def error_path(self, job_id: str) -> Path:
        return self._path(job_id, "errors.jsonl")

    def append(self, path: Path, record: dict[str, Any]) -> None:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def resolved_ids(self, job_id: str) -> tuple[set[str], set[str]]:
        def ids(path: Path) -> set[str]:
            if not path.exists():
                return set()
            with path.open(encoding="utf-8") as f:
                return {json.loads(line)["custom_id"] for line in f if line.strip()}

        return ids(self.output_path(job_id)), ids(self.error_path(job_id))


class BatchProcessor:
    def __init__(
        self,
        settings: Settings,
        router: Router,
        store: BatchStore,
        *,
        clock: Callable[[], float] = time.time,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self.settings = settings
        self.router = router
        self.store = store
        self._clock = clock
        self._sleep = sleep
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._cancel: set[str] = set()
        self._lock = asyncio.Lock()
        self._task: asyncio.Task[None] | None = None

    # -------------------------------------------------------------- API
    def submit(self, raw: bytes, description: str | None = None) -> BatchJob:
        now = self._clock()
        job = BatchJob(id=f"batch_{uuid.uuid4().hex}", status="validating", created_at=now, description=description)
        try:
            lines = parse_batch_input(
                raw, max_requests=self.settings.batch_max_requests, max_bytes=self.settings.batch_max_bytes
            )
        except BatchValidationError as exc:
            job.status, job.failed_at, job.errors = "failed", now, exc.errors
            self.store.save(job)
            raise
        job.request_counts.total = len(lines)
        self.store.write_input(job.id, lines)
        self.store.save(job)
        self._queue.put_nowait(job.id)
        logger.info("lote_recibido", extra={"job_id": job.id, "requests": len(lines)})
        return job

    def cancel(self, job_id: str) -> BatchJob:
        job = self.store.load(job_id)
        if job.status in TERMINAL:
            raise InvalidJobState(f"El trabajo ya terminó con estado {job.status}")
        job.status = "cancelling"
        self.store.save(job)
        self._cancel.add(job_id)
        return job

    # ------------------------------------------------------------ worker
    def start(self) -> None:
        for job in sorted(self.store.list(), key=lambda j: j.created_at):
            if job.status not in TERMINAL:
                logger.info("lote_reanudado", extra={"job_id": job.id, "status": job.status})
                if job.status == "cancelling":
                    self._cancel.add(job.id)
                self._queue.put_nowait(job.id)
        if self._task is None:
            self._task = asyncio.create_task(self._worker())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _worker(self) -> None:
        while True:
            job_id = await self._queue.get()
            try:
                await self.process(job_id)
            except Exception:  # pragma: no cover - un lote defectuoso no detiene el worker
                logger.exception("error_lote", extra={"job_id": job_id})
            finally:
                self._queue.task_done()

    async def wait_idle(self) -> None:
        await self._queue.join()

    async def process(self, job_id: str) -> BatchJob:
        job = self.store.load(job_id)
        if job.status in TERMINAL:
            return job
        if job_id in self._cancel and job.in_progress_at is None:
            return self._finish(job, "cancelled")
        if job.status == "validating":
            job.status, job.in_progress_at = "in_progress", self._clock()
            self.store.save(job)

        lines = self.store.read_input(job_id)
        ok_ids, err_ids = self.store.resolved_ids(job_id)
        job.request_counts.completed, job.request_counts.failed = len(ok_ids), len(err_ids)
        pending = [line for line in lines if line["custom_id"] not in ok_ids | err_ids]
        deadline = job.created_at + self.settings.batch_completion_window_s
        semaphore = asyncio.Semaphore(self.settings.batch_concurrency)
        expired = False

        async def run(line: dict[str, Any]) -> None:
            nonlocal expired
            async with semaphore:
                if job_id in self._cancel or expired:
                    return
                if self._clock() > deadline:
                    expired = True
                    return
                await self._yield_to_online(job_id)
                if job_id in self._cancel:
                    return
                record, region = await self._execute(line)
                async with self._lock:
                    if record["error"] is None:
                        self.store.append(self.store.output_path(job_id), record)
                        job.request_counts.completed += 1
                        job.regions_used[region] = job.regions_used.get(region, 0) + 1
                    else:
                        self.store.append(self.store.error_path(job_id), record)
                        job.request_counts.failed += 1
                    current = self.store.load(job_id)
                    job.status = current.status if current.status == "cancelling" else job.status
                    self.store.save(job)

        await asyncio.gather(*(run(line) for line in pending))

        if job_id in self._cancel:
            self._cancel.discard(job_id)
            return self._finish(job, "cancelled")
        if expired:
            return self._finish(job, "expired")
        job.status, job.finalizing_at = "finalizing", self._clock()
        self.store.save(job)
        return self._finish(job, "completed")

    def _finish(self, job: BatchJob, status: str) -> BatchJob:
        now = self._clock()
        job.status = status  # type: ignore[assignment]
        setattr(job, f"{status}_at", now)
        self.store.save(job)
        logger.info(
            "lote_terminado",
            extra={"job_id": job.id, "status": status, **job.request_counts.model_dump(), "regions": job.regions_used},
        )
        return job

    async def _yield_to_online(self, job_id: str) -> None:
        """Cede la capacidad a las solicitudes interactivas."""
        while self.router.online_inflight >= self.settings.batch_yield_online_inflight and job_id not in self._cancel:
            await self._sleep(0.2)

    async def _execute(self, line: dict[str, Any]) -> tuple[dict[str, Any], str]:
        body = line["body"]
        max_tokens = min(int(body.get("max_tokens") or self.settings.max_output_tokens), self.settings.max_output_tokens)
        temperature = float(body.get("temperature", 0.0))
        last_error = "sin intentos"
        for attempt in range(self.settings.batch_max_retries + 1):
            try:
                state, response, attempts = await self.router.complete(
                    body["messages"], max_tokens=max_tokens, temperature=temperature
                )
            except RegionError as exc:
                if not exc.retryable:
                    return self._error(line, "invalid_request", str(exc)), ""
                last_error = str(exc)
            except NoRegionAvailable as exc:
                last_error = f"{exc} {exc.errors}" if exc.errors else str(exc)
            else:
                response["x_region"] = state.name
                response["x_attempts"] = attempts
                return (
                    {
                        "id": f"batch_req_{uuid.uuid4().hex}",
                        "custom_id": line["custom_id"],
                        "response": {"status_code": 200, "body": response},
                        "error": None,
                    },
                    state.name,
                )
            if attempt < self.settings.batch_max_retries:
                delay = self.settings.batch_retry_base_s * (2**attempt)
                await self._sleep(delay + random.uniform(0, delay / 2))  # backoff con jitter
        return self._error(line, "regions_unavailable", last_error), ""

    @staticmethod
    def _error(line: dict[str, Any], code: str, message: str) -> dict[str, Any]:
        return {
            "id": f"batch_req_{uuid.uuid4().hex}",
            "custom_id": line["custom_id"],
            "response": None,
            "error": {"code": code, "message": message[:500]},
        }
