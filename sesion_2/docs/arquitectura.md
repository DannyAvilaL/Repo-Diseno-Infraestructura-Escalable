# Documento de arquitectura · Asistente institucional de conocimiento

Arquitectura de referencia del caso transversal del curso. Los parámetros son **supuestos académicos**, no mediciones de carga.

## 1. Requerimientos

### Funcionales

| ID | Requerimiento |
| --- | --- |
| RF-01 | Responder preguntas sobre procesos, reglamentos y servicios académicos en español |
| RF-02 | Citar el documento institucional que respalda cada respuesta |
| RF-03 | Restringir la información según el perfil del usuario (estudiante, docente, administrativo) |
| RF-04 | Mantener el contexto de la conversación durante la sesión |
| RF-05 | Reindexar automáticamente cuando se publica o actualiza un documento |
| RF-06 | Permitir a administradores consultar trazas y métricas de uso |

### No funcionales

| ID | Atributo | Requerimiento (hipótesis de diseño) |
| --- | --- | --- |
| RNF-01 | Escala | 5.000 usuarios potenciales; 100 concurrentes en hora pico |
| RNF-02 | Disponibilidad | 99,9 % mensual (≈ 43 min de indisponibilidad) |
| RNF-03 | Latencia | TTFT p95 ≤ 2 s; streaming de la respuesta (propuesta a validar) |
| RNF-04 | Capacidad | ≈ 330.000 tokens/min en hora pico (300 K entrada, 30 K salida) |
| RNF-05 | Seguridad | SSO institucional; identidades de carga sin secretos estáticos; red privada |
| RNF-06 | Privacidad | Cumplimiento de la Ley 1581 de 2012; minimización; logging sin contenido en claro |
| RNF-07 | Auditoría | Traza por solicitud: usuario seudónimo, tokens, latencias, documentos citados |
| RNF-08 | Costo | Presupuesto mensual con alertas; costo por conversación medido |
| RNF-09 | Portabilidad | Contrato de API propio; proveedor de modelo intercambiable |

## 2. Vista de componentes

Ver [`diagrams/D-06-arquitectura-referencia.mmd`](diagrams/D-06-arquitectura-referencia.mmd).

| Componente | Responsabilidad | Dependencias | Falla típica | Mitigación |
| --- | --- | --- | --- | --- |
| Cliente web | Interfaz y streaming | Gateway, IdP | Conexiones cortadas | Reintento de cliente, timeouts del balanceador ajustados |
| Proveedor de identidad | Autenticación OIDC | Directorio institucional | Caída del IdP | Sesiones con expiración razonable; IdP con SLA |
| API Gateway | Autenticación, cuotas por usuario, WAF | Backend | Rate limit mal dimensionado | Cuotas por perfil derivadas de RNF-04 |
| Backend / orquestador | Prompt, recuperación, herramientas | Gateway de modelos, vector store | Timeouts encadenados | Timeouts por dependencia, circuit breaker |
| Guardrails | Filtrar entrada y salida | Backend | Falsos positivos | Medición y ajuste continuo |
| Gateway de modelos | Enrutar, reintentar, aplicar cuotas | Serving | Punto único de fallo | Réplicas multizona; modelo de respaldo |
| Serving | Inferencia | GPU o API gestionada | Saturación de memoria | Autoscaling por cola; límites de tokens |
| Vector store | Recuperación semántica con permisos | Almacenamiento | Índice desactualizado | Reindexación por eventos (RF-05) |
| Observabilidad | Logs, métricas, trazas | Todos | Registrar datos personales | Enmascaramiento y retención limitada |

## 3. Flujos de datos

1. **Consulta:** usuario → IdP (token) → gateway → backend → vector store (filtrado por perfil) → gateway de modelos → serving → streaming al usuario → traza a observabilidad. Ver D-02.
2. **Ingesta:** publicación de documento → evento → extracción y división → embeddings → índice con metadatos de permisos. Ver D-10.

## 4. Alternativas arquitectónicas

| Alternativa | Ventajas | Limitaciones | Escenario de uso |
| --- | --- | --- | --- |
| A · API de modelos gestionada + contenedores serverless | Tiempo a producción corto; sin operación de GPU; costo proporcional al uso | Dependencia del proveedor; cuotas TPM; residencia sujeta a la región y tipo de despliegue | Volumen bajo o variable; equipo pequeño (recomendada para iniciar el caso) |
| B · Self-hosting en Kubernetes con GPU | Control de datos y modelo; costo marginal bajo con volumen alto | Costo fijo de 2+ réplicas GPU; equipo de plataforma; parches | Volumen alto y sostenido; requisitos estrictos de residencia |
| C · Runtime gestionado de agentes | Sesiones, memoria e identidad gestionadas | Mayor dependencia; capacidades en evolución | Cuando el asistente evolucione a ejecutar acciones (agente) |

## 5. Análisis de seguridad (resumen STRIDE + OWASP LLM 2025)

| Amenaza | Componente | Riesgo OWASP | Control |
| --- | --- | --- | --- |
| Suplantación de usuario | Gateway | — | OIDC, validación de tokens en el gateway |
| Exposición de documentos restringidos | Vector store | LLM02, LLM08 | Filtrado por permisos del usuario final en la recuperación |
| Inyección indirecta en documentos | Ingesta, backend | LLM01, LLM04 | Procedencia de documentos, delimitación de contexto, guardrails de salida |
| Abuso de consumo | Gateway, serving | LLM10 | Cuotas por usuario, límites de tokens, alertas de costo |
| Filtración de secretos | Backend | — | Identidades gestionadas, Key Vault / Secrets Manager / Secret Manager |
| Exceso de agencia (fase agéntica) | Herramientas | LLM06 | Herramientas de solo lectura, aprobación humana para acciones |
| Repudio | Observabilidad | — | Trazas firmadas por solicitud con usuario seudónimo |

## 6. Decisiones

Ver [`adr/`](adr). Las decisiones del curso se registran con el formato ADR (contexto, decisión, alternativas, consecuencias).
