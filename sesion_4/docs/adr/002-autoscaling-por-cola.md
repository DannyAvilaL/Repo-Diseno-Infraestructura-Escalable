# ADR-002 — Autoscaling horizontal por profundidad de cola (KEDA + Prometheus)
**Estado:** Aceptada · **Fecha:** 2026-11-03
**Contexto:** CPU/GPU utilization no representan la demanda insatisfecha de un servidor LLM.
**Decisión:** `ScaledObject` con disparador Prometheus sobre `llm_gateway_queue_depth`, `minReplicaCount: 1`, subida rápida, bajada con ventana de 300 s.
**Alternativas:** HPA por CPU (línea base didáctica `55-hpa-cpu-baseline.yaml`); escalado por TTFT (síntoma tardío); escala a cero (cold start de minutos).
**Consecuencias:** + reacciona antes de que el usuario perciba degradación; − depende de Prometheus y de calibrar el umbral con pruebas de carga reales (el `threshold: 4` es un supuesto inicial).
