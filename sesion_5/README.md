# Sesión 5 · Implementación de Arquitecturas Serverless para LLMs

Curso **Diseño de Infraestructura Escalable para LLMs** (Maestría, BSG Intitute). Repositorio de la sesión: gateway FastAPI con semántica serverless, frontend React, laboratorios local (Ollama) y en AWS, Azure y Google Cloud, y documentación arquitectónica.
Licencias: código MIT; materiales académicos CC BY-SA 4.0 (ver `LICENSE`).

> **Honestidad de verificación:** lo que se ejecutó y lo que sigue pendiente está en [`docs/verificacion.md`](docs/verificacion.md). Ningún laboratorio cloud se ejecutó contra una cuenta real durante la preparación.

## Estructura
```
src/serverless_llm/   Gateway (E5.2): config, providers, cache, security, jobqueue, metrics, service, main
frontend/             React 18 + Vite 6 + TypeScript (E5.3)
tests/                51 pruebas (pytest)           loadtest/, experiments/  Carga y experimentos (E5.4)
labs/local|aws|azure|gcp   Laboratorios E5.1, E5.5.x, E5.6.x, E5.7.x
docs/                 Arquitecturas (Mermaid), seguridad, FinOps, ADR, mapeo ejemplo↔slide, referencias
```
Numeración de ejemplos ↔ diapositivas: [`docs/mapeo-ejemplos-slides.md`](docs/mapeo-ejemplos-slides.md).

## Inicio rápido (Ubuntu 24.04+, Python 3.12, Node 20+)
```bash
make install                 # venv + dependencias + npm ci
make test                    # pytest
make run                     # gateway en :8000 (proveedor mock)
make web                     # frontend en :5173
# Docker:  docker compose up --build      (con Ollama: docker compose --profile ollama up)
```
Prueba: `curl -s -X POST localhost:8000/v1/chat -H 'X-API-Key: dev-key-change-me' -H 'Content-Type: application/json' -d '{"prompt":"hola","temperature":0}'`

## API
`GET /healthz · /readyz · /metrics · /v1/stats` · `POST /v1/chat` · `POST /v1/chat/stream` (SSE) · `POST /v1/jobs` (202, `Idempotency-Key`) · `GET /v1/jobs/{id}`.

## Seguridad
Configuración por variables `SLLM_*` (ver `.env.example`); la API key por defecto se rechaza fuera de `SLLM_ENV=local`. Controles y límites en `docs/seguridad.md`.

## Solución de problemas y limpieza
`docs/troubleshooting.md`; cada laboratorio incluye su sección de limpieza de recursos.
