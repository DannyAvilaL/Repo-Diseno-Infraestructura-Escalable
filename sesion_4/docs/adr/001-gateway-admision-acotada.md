# ADR-001 — Gateway con control de admisión y cola acotada
**Estado:** Aceptada · **Fecha:** 2026-11-03
**Contexto:** el servidor de inferencia tiene capacidad finita; sin límites, la latencia crece sin cota y OWASP LLM10 (consumo sin límites) queda expuesto.
**Decisión:** un gateway FastAPI delante de cada servidor de inferencia con semáforo de concurrencia (= paralelismo del servidor), cola máxima y timeout; responde 429/503 con `Retry-After`.
**Alternativas:** (a) sin gateway: más simple, sin backpressure ni métricas; (b) rate limiting solo en el Ingress: limita tasa, no capacidad real del modelo.
**Consecuencias:** + degradación controlada y señal de cola para autoscaling; − un salto de red/proceso adicional y un componente más que operar; el límite es por réplica.
