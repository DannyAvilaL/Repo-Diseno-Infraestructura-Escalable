# Caso transversal · Asistente institucional de conocimiento

Una universidad necesita un asistente que responda preguntas de estudiantes, docentes y personal administrativo sobre procesos, reglamentos y servicios académicos.

## Supuestos de diseño

Estos parámetros son **hipótesis académicas**, no mediciones reales de carga.

| Parámetro | Valor |
| --- | --- |
| Usuarios potenciales | 5.000 |
| Usuarios concurrentes en hora pico | 100 |
| Frecuencia por usuario activo | 1 pregunta por minuto |
| Tokens por solicitud | ~3.000 de entrada (instrucciones + historial + RAG) y ~300 de salida |
| Disponibilidad objetivo | 99,9 % mensual |
| Fuentes | Reglamentos, calendario académico, procedimientos, preguntas frecuentes; algunos documentos son de acceso restringido |
| Acceso | Autenticado con la identidad institucional |
| Requisitos adicionales | Protección de datos personales (Ley 1581 de 2012), registro y auditoría, observabilidad, presupuesto limitado |

## Lo que debe entregar cada equipo

1. Requerimientos funcionales y no funcionales.
2. Arquitectura conceptual (diagrama) con al menos 8 componentes, límites de red y de confianza.
3. Servicios cloud seleccionados en una nube.
4. Componentes críticos y puntos únicos de fallo.
5. Controles de seguridad: al menos 5 riesgos OWASP LLM 2025 con su control.
6. Decisiones de cómputo y almacenamiento (incluida una estimación de memoria o de tokens por minuto).
7. Riesgos y costos (orden de magnitud, sin inventar precios).
8. Decisión gestionado vs. autogestionado en formato ADR (ver `docs/adr/`).
9. Indicadores de evaluación: al menos un SLI y un SLO.

## Plantilla del taller (D-28)

```text
[ Usuario ] -> [ Identidad: ________ ] -> [ Gateway: ________ ]
                                              |
                                      [ Backend: ________ ] -> [ Guardrails: ________ ]
                                         |            |
                         [ Vector store: ________ ]  [ Modelo / serving: ________ ]
Red pública: ______________     Red privada: ______________
Observabilidad: ___________     Secretos/identidades de carga: ___________
SLO: ______________   Memoria o tokens/min estimados: ______________
Decisión (ADR): gestionado / autogestionado porque 1) ____ 2) ____ 3) ____
```
