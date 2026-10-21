# ADR-0004 · Despliegue multizona para el objetivo de 99,9 %

- **Estado:** propuesta académica
- **Fecha:** 2026-10-13

## Contexto

99,9 % mensual admite ≈ 43 minutos de indisponibilidad, menos que la duración típica de una falla de zona.

## Decisión

Backend, gateway de modelos y almacenamiento de estado en al menos dos zonas. Con self-hosting, al menos dos réplicas de serving en zonas distintas. Con API gestionada, evaluar un modelo o región de respaldo si el SLA del proveedor es inferior al SLO.

## Consecuencias

Duplica el costo de serving en self-hosting. Exige pruebas de conmutación y alertas sobre el presupuesto de error.
