# Sesión 2 · Diseño de Topologías y Casos de Uso Empresariales

Capítulo 1 · Fundamentos de Infraestructura para LLMs · 180 minutos.

**Objetivo de desempeño:** diseñar una topología base en la nube para inferencia LLM considerando cómputo, red y almacenamiento.

Temas:

- Inferencia en línea vs. por lotes.
- Diseño de arquitecturas multi-región y redundantes.
- Selección de servicios gestionados según el caso de uso.
- Ejercicio práctico de diseño preliminar.

## Materiales

| Material | Ubicación |
| --- | --- |
| Presentación (56 diapositivas con notas del expositor) | [`slides/S02-Topologias-Casos-Empresariales.pptx`](slides/S02-Topologias-Casos-Empresariales.pptx) · generador [`slides/build_deck.js`](slides/build_deck.js) |
| Guía del estudiante | [`guia-estudiante.md`](guia-estudiante.md) |
| Taller de diseño preliminar | [`taller/`](taller) (casos, plantilla, rúbrica) |
| Evaluación formativa | [`evaluacion/preguntas.md`](evaluacion/preguntas.md) |
| Diagramas D-29 a D-44 | [`docs/diagrams`](../../docs/diagrams) |
| Decisiones de arquitectura | [ADR-0006](../../docs/adr/ADR-0006-separar-online-batch.md) · [ADR-0007](../../docs/adr/ADR-0007-multiregion-warm-standby.md) · [ADR-0008](../../docs/adr/ADR-0008-gateway-ia.md) |

## Laboratorios

| ID | Laboratorio | Nube |
| --- | --- | --- |
| LOC-02 | [`labs/01-local-gateway`](../../labs/01-local-gateway): gateway multi-región, failover, circuit breaker, API batch, React | Local |
| AZ-G | [`labs/21-azure-topologias`](../../labs/21-azure-topologias): dos regiones de Foundry, conmutación, Azure OpenAI Batch, API Management | Azure |
| GCP-D | [`labs/11-gcp-topologias`](../../labs/11-gcp-topologias): ubicaciones de Gemini, conmutación, batch inference | Google Cloud |
| AWS-E | [`labs/31-aws-topologias`](../../labs/31-aws-topologias): Cross-Region inference, niveles de servicio, batch con rol de servicio | AWS |

Los agentes de consola y de frameworks (ADK, Agent Framework, Semantic Kernel, AutoGen, LangGraph, Strands, AgentCore) se construyeron en la Sesión 1 y no se repiten. En esta sesión se analizan desde la topología: en qué región corren, cómo se replican y qué modalidad de consumo usan.

## Agenda

| Tiempo | Bloque | Diapositivas | Tipo |
| --- | --- | --- | --- |
| 0:00–0:08 | Apertura: caso ampliado, resultados, puente con la Sesión 1 | 1–4 | Teoría |
| 0:08–0:35 | Unidad A · Online vs. por lotes (incluye Demo 1, 7 min) | 5–15 | Teoría + demo |
| 0:35–1:15 | Unidad B · Topologías redundantes y multi-región (incluye Demo 2, 10 min) | 16–31 | Teoría + demo |
| 1:15–1:25 | Pausa | — | — |
| 1:25–2:05 | Unidad C · Selección de servicios gestionados (incluye Demo 3 en Azure, 10 min) | 32–41 | Teoría + demo |
| 2:05–2:20 | Unidad D · Seguridad, residencia y costo de la redundancia | 42–46 | Teoría |
| 2:20–2:50 | Taller de diseño preliminar | 47–51 | Práctica |
| 2:50–3:00 | Síntesis, autoevaluación y próxima sesión | 52–56 | Discusión |

Distribución sobre 170 minutos efectivos: 60 % teoría, 16 % demostraciones y 24 % taller y discusión. La distribución predeterminada del curso (65/25/10) se ajustó porque el tema incluye un ejercicio práctico de diseño.

## Resultados de aprendizaje

| RA | Al finalizar, el estudiante podrá… |
| --- | --- |
| RA1 | Distinguir inferencia online, asíncrona y por lotes por su SLO, su costo y su patrón de arquitectura |
| RA2 | Calcular la disponibilidad compuesta de una topología y relacionarla con RTO y RPO |
| RA3 | Diseñar topologías redundantes (multizona, activo-pasivo, activo-activo) con patrones de resiliencia |
| RA4 | Seleccionar servicios gestionados de Azure, Google Cloud y AWS según el caso de uso |
| RA5 | Evaluar residencia de datos, seguridad y costo de una topología multi-región |
| RA6 | Elaborar y justificar un diseño preliminar con un ADR |

## Vigencia

Servicios, modalidades, cuotas y precios verificados en documentación oficial el **20 de octubre de 2026**; detalle en [`docs/referencias.md`](../../docs/referencias.md). Hechos con impacto directo en la clase:

- Azure OpenAI Batch no está disponible en suscripciones *free trial* (cuota «N/A»): la parte batch de AZ-G es demostración del docente.
- El plan Free de AWS no admite funciones entre regiones: Cross-Region inference requiere el plan Paid.
- Google anunció el retiro de Gemini 2.5 en la plataforma: los laboratorios usan el modelo Flash vigente, configurable en `.env`.
