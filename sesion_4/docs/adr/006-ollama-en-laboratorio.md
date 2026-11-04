# ADR-006 — Ollama como servidor de inferencia del laboratorio
**Estado:** Aceptada (alcance: laboratorio) · **Fecha:** 2026-11-03
**Contexto:** el curso necesita que cualquier estudiante ejecute un LLM local con un comando.
**Decisión:** Ollama por su instalación simple y su API HTTP; el gateway aísla al resto del sistema de ese detalle.
**Alternativas para producción de alto rendimiento:** servidores con *continuous batching* y gestión paginada de KV cache (p. ej. vLLM), evaluar con sus propias pruebas.
**Consecuencias:** + reproducibilidad; − no representa necesariamente el rendimiento de un servidor optimizado para alto *throughput*: no extrapole mediciones.
