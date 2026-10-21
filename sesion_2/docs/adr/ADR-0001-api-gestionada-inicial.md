# ADR-0001 · Iniciar con inferencia mediante API gestionada

- **Estado:** propuesta académica (referencia para el taller)
- **Fecha:** 2026-10-13

## Contexto

El asistente universitario requiere 99,9 % de disponibilidad, ≈ 330.000 tokens/min en hora pico (hipótesis) y un equipo de TI sin experiencia operando GPU. El volumen mensual estimado es ≈ 165 M tokens (50.000 solicitudes).

## Decisión

Usar un modelo mediante API gestionada en la nube institucional, detrás de un gateway de modelos propio y del contrato de API del curso.

## Alternativas consideradas

- Self-hosting en Kubernetes con GPU: requiere al menos 2 réplicas en zonas distintas (≈ 1.440 GPU-horas/mes) y un equipo de plataforma.
- Contenedores serverless con GPU: viable para modelos pequeños; arranques en frío con pesos grandes.

## Consecuencias

- Positivas: tiempo a producción corto, costo proporcional al uso, sin operación de GPU.
- Negativas: dependencia del proveedor y de sus cuotas; residencia condicionada al tipo de despliegue.
- Mitigaciones: contrato de API propio, adaptadores intercambiables, revisión de cuotas como requisito no funcional, reevaluar al superar el volumen de equilibrio.
