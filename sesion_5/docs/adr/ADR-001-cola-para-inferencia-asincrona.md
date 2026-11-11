# ADR-001: Cola entre cliente y modelo para cargas no interactivas
**Estado:** aceptada. **Contexto:** picos que superan cuotas del modelo. **Decisión:** SQS/Service Bus/Pub/Sub con DLQ, idempotencia y concurrencia máxima. **Consecuencias:** + resiliencia y control de costo; − latencia y complejidad de consulta de estado. **Alternativas:** HTTP síncrono con reintentos (rechazada para batch).
