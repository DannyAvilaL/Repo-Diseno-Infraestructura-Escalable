# ADR-0008 · Un gateway de IA por región frente a los endpoints de modelos

- **Estado:** aceptada
- **Fecha:** 2026-10-20
- **Sesión:** 2 · Unidades B y C

## Contexto

La lógica de conmutación, los límites de tokens por cliente y la observabilidad de tokens pueden vivir en cada aplicación cliente, en un gateway propio o en un gateway gestionado (API Management, Apigee, API Gateway). El gateway agrega un componente en serie y puede volverse un punto único de falla.

Recomendaciones documentadas (Azure Architecture Center, 2026): desplegar el gateway en la misma región que los modelos; no usar un gateway de una sola región frente a backends de varias regiones para cargas críticas; no unificar el gateway entre regiones geopolíticas cuando aplica residencia; tratar 429, 500 y 503 como señales de circuit breaker y respetar `Retry-After`.

## Decisión

- Un gateway **por región**, detrás del enrutamiento global.
- En el curso se usa un gateway propio didáctico (LOC-02) para entender el mecanismo. En producción se prefiere un gateway gestionado cuando la institución ya lo opera. En Azure, API Management con pool por prioridad y circuit breaker: no disponible en el nivel Consumption.
- Los SDK de los clientes se configuran **sin reintentos automáticos** cuando el gateway conmuta, para evitar tormentas de reintentos.

## Consecuencias

- Lógica de resiliencia y límites en un solo lugar; contrato de API propio que facilita cambiar de proveedor.
- Costo por hora del gateway gestionado y latencia adicional por salto.
- El gateway debe tener al menos la disponibilidad objetivo del sistema, porque está en serie.

## Fuentes

- https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/azure-openai-gateway-multi-backend
- https://learn.microsoft.com/en-us/azure/api-management/backends
