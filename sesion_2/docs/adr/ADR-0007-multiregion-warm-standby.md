# ADR-0007 · Multi-región activo-pasivo con warm standby para el asistente

- **Estado:** propuesta (para discutir en el taller de la Sesión 2)
- **Fecha:** 2026-10-20
- **Sesión:** 2 · Unidad B
- **Relación:** amplía ADR-0004 (alta disponibilidad multizona)

## Contexto

Nuevo requisito institucional: el asistente debe seguir operando si cae una región de la nube. Objetivo: 99,9 % mensual y RTO de 15 minutos para el asistente; RPO de 5 minutos para las conversaciones (hipótesis de diseño). El lote de PQRS tolera un RTO de 24 h.

Hechos documentados (20-oct-2026):

- El enrutamiento de los despliegues Global y Data Zone de Azure «no reemplaza el failover regional a nivel de aplicación» (guía de alta disponibilidad de Foundry).
- Foundry no replica proyectos, despliegues ni cuota entre regiones.
- Desde el 7-may-2026, la cuota de Global Standard es por suscripción y se comparte entre regiones.
- Un despliegue de pago por token sin tráfico no factura tokens.

## Decisión

- **Asistente (online):** activo-pasivo con *warm standby*: gateway y backend desplegados en la región secundaria desde el mismo artefacto, despliegue del mismo modelo y versión, enrutamiento global con health checks.
- **Conversaciones:** base de datos con réplica entre regiones.
- **Índice vectorial:** reconstruible desde los documentos replicados (RPO de horas aceptado).
- **Lote PQRS:** una sola región; ante una falla regional se reenvía el lote al día siguiente.
- **Configuración** (prompt de sistema, guardrails, versión del modelo): desplegada desde Git a ambas regiones a la vez.
- Ensayo de conmutación trimestral.

## Alternativas consideradas

| Alternativa | Razón |
| --- | --- |
| Solo multizona y capa global del proveedor | No cubre la falla del endpoint regional, del backend ni de los datos |
| Activo-activo | Mayor costo y complejidad de datos; no lo exige el RTO de 15 min |
| Pilot light | RTO mayor por el despliegue en frío del backend; aceptable solo si se relaja el RTO |

## Consecuencias

- Disponibilidad compuesta estimada (cifras hipotéticas): ≈ 99,99 %, limitada por el componente global en serie.
- El segundo despliegue no aumenta la cuota: protege contra la falla regional, no contra el 429 por cuota.
- Costos fijos: gateway y backend en la secundaria; base de datos replicada; tráfico entre regiones.
- Residencia: ambas regiones deben pertenecer a la geografía permitida por la política de datos.

## Fuentes

- https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/business-continuity-disaster-recovery
- https://learn.microsoft.com/en-us/azure/foundry/openai/quotas-limits
- https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/azure-openai-gateway-multi-backend
- https://aws.amazon.com/blogs/architecture/disaster-recovery-dr-architecture-on-aws-part-i-strategies-for-recovery-in-the-cloud
