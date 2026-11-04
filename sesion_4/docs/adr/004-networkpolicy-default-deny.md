# ADR-004 — NetworkPolicy deny-by-default y servidor de inferencia en loopback
**Estado:** Aceptada · **Fecha:** 2026-11-03
**Contexto:** Zero Trust; el servidor de inferencia no autentica por sí mismo.
**Decisión:** denegar ingress/egress por defecto; permitir Ingress controller y Prometheus hacia :8000, DNS y 443 público (solo para la carga inicial, con bloqueo de rangos privados y metadatos); Ollama escucha en 127.0.0.1.
**Consecuencias:** + superficie mínima; − requiere CNI con soporte; el egress 443 abierto es una deuda explícita a eliminar en producción (almacenamiento privado / proxy FQDN).
