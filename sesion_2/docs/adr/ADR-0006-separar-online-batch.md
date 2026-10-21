# ADR-0006 · Separar los caminos online y por lotes, con prioridad para lo interactivo

- **Estado:** aceptada
- **Fecha:** 2026-10-20
- **Sesión:** 2 · Unidad A

## Contexto

El asistente universitario atiende conversaciones de estudiantes (alguien espera cada respuesta) y, además, clasifica unas 20.000 PQRS al mes cada noche (hipótesis de diseño). Ambas cargas usan el mismo modelo. Si comparten capacidad sin control, un lote grande puede agotar la cuota o saturar el servidor y degradar la latencia de los estudiantes.

Hechos documentados (20-oct-2026):

- Azure OpenAI Batch usa una cuota de tokens encolados separada de la online y cuesta 50 % menos que Global Standard, con objetivo de 24 h.
- Google indica que Gemini está disponible en modo batch con 50 % de descuento.
- La guía de costos de Bedrock indica 50 % de ahorro en batch y ventana de 24 h; las solicitudes priority, default y flex comparten la cuota on-demand.

## Decisión

1. Las cargas sin usuario esperando se ejecutan por un **camino batch** separado: servicio batch gestionado cuando el plazo de 24 h es aceptable; cola propia con workers cuando se requiere un plazo menor o control del ritmo.
2. Cuando la capacidad es compartida (cuota on-demand o GPU propia), un **control de admisión** da prioridad a lo online y limita la concurrencia del lote.
3. Los SLI se miden por separado: TTFT y p95 para lo online; tiempo hasta completar, proporción de ítems exitosos y costo por 1.000 ítems para el lote.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
| --- | --- |
| Procesar el lote con llamadas online en horas valle | Sin descuento y con riesgo de 429 si el lote se alarga hasta horas de uso |
| Un solo endpoint sin prioridad | El lote degrada la latencia de los estudiantes |
| GPU propia dedicada al lote | A este volumen cuesta más que el batch gestionado (Sesión 2, Unidad D) |

## Consecuencias

- Positivas: menor costo por token del lote; la latencia online no depende del lote.
- Negativas: dos caminos que operar; los resultados del lote no conservan el orden y pueden ser parciales (se empareja por identificador y se reprocesan faltantes).
- Implementación de referencia: `labs/01-local-gateway` (`batch.py`, parámetro `APP_BATCH_YIELD_ONLINE_INFLIGHT`).

## Fuentes

- https://learn.microsoft.com/azure/foundry/openai/how-to/batch
- https://cloud.google.com/vertex-ai/generative-ai/pricing
- https://docs.aws.amazon.com/bedrock/latest/userguide/capacity-limits-cost-optimization.html
- https://docs.aws.amazon.com/bedrock/latest/userguide/service-tiers-inference.html
