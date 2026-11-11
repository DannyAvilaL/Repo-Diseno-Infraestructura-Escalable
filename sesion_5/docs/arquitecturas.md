# Arquitecturas de referencia

## A1. Síncrona con caché y backpressure
```mermaid
flowchart LR
  C[Cliente] --> GW[API Gateway / Function URL]
  GW --> F[Función serverless\nauth + guards + rate limit]
  F -->|hit| K[(Caché TTL)]
  F -->|miss, con slot| M[Modelo administrado / autogestionado]
  F -.->|sin slot| R[429 + Retry-After]
```
## A2. Asíncrona con cola (orquestación de inferencia)
```mermaid
flowchart LR
  C[Cliente] -->|POST /jobs + Idempotency-Key| S[Submit function]
  S --> Q[(Cola)] --> W[Worker function\nconcurrencia máx.] --> M[Modelo]
  Q -. N intentos .-> D[(DLQ)]
  W --> DB[(Estado/resultado)]
  C -->|GET /jobs/id| DB
```
## A3. Agente serverless
```mermaid
flowchart TB
  U[Usuario] --> RT[Runtime de agente serverless\nAgentCore / Foundry Agent Service / Agent Runtime]
  RT --> LLM[Modelo]
  RT --> T1[Herramienta A\nmínimo privilegio]
  RT --> T2[Herramienta B]
  RT --> OBS[Trazas OTel]
```
Patrones aplicados: Queue-Based Load Leveling, Competing Consumers, Retry+DLQ, Idempotent Receiver, Cache-Aside, Bulkhead (semáforo), Circuit Breaker (extensión sugerida), Claim Check para payloads grandes.
