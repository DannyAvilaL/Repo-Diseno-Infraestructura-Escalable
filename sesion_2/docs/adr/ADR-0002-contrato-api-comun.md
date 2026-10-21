# ADR-0002 · Contrato de API común para todos los laboratorios

- **Estado:** aceptada
- **Fecha:** 2026-10-13

## Contexto

El curso compara tres nubes y un entorno local. Sin una interfaz común, la comparación mezcla diferencias de proveedor con diferencias de implementación.

## Decisión

Todos los backends del curso exponen `GET /healthz`, `GET /readyz`, `POST /v1/chat` y `POST /v1/chat/stream` (SSE con eventos `token`, `metrics`, `error`, `done`), con los esquemas de `labs/00-local-ollama/backend/app/schemas.py`. El proveedor se encapsula en adaptadores.

## Consecuencias

El mismo frontend y la misma prueba de carga sirven para todos los proveedores. Las métricas TTFT y TPOT se miden de forma homogénea desde el backend.
