# Taller · Diseño preliminar de una topología (30 minutos)

**Objetivo:** aplicar los contenidos de la sesión a un caso empresarial y defender las decisiones con un ADR.

**Organización:** equipos de 3 o 4 personas. Cada equipo elige un caso; al menos dos equipos deben trabajar casos distintos.

| Tiempo | Actividad |
| --- | --- |
| 5 min | Explicación del método (diapositiva 48) y elección del caso |
| 18 min | Trabajo en equipo con la [plantilla](plantilla-diseno.md) |
| 7 min | Dos equipos exponen (3 min cada uno + 30 s de preguntas) |

Se entrega completo como tarea, con la [rúbrica](rubrica.md).

## Método en ocho pasos

1. Requisitos y supuestos.
2. Clasificar cargas: online, asíncrona o batch.
3. SLO, RTO y RPO por carga.
4. Datos: clasificación y residencia.
5. Topología: zonas, regiones y estrategia de recuperación.
6. Servicios y modalidades de consumo en una nube principal.
7. Riesgos y controles (al menos uno de OWASP LLM 2025).
8. Costo estimado y ADR.

## Casos

Las cifras son supuestos del ejercicio. Si falta un dato, regístrelo como supuesto y continúe.

### Caso A · Universidad

- Asistente institucional 24/7 para 5.000 estudiantes; en temporada de matrículas, hasta 300 conversaciones concurrentes.
- 20.000 PQRS al mes, clasificadas cada noche y disponibles a las 7:00.
- Reindexación semanal de 2.000 documentos para RAG.
- Requisitos: seguir operando si cae una región; datos personales de estudiantes; presupuesto limitado.

### Caso B · Retail regional

- Chat de soporte en Colombia, México, Perú y Chile; 2.000 conversaciones concurrentes en temporada alta (por ejemplo, días de descuentos).
- Generación nocturna de 50.000 descripciones de productos cuando se actualiza el catálogo.
- Requisitos: p95 del primer token menor que 3 s en el chat; presupuesto ajustado; el catálogo puede publicarse con 24 h de retraso.

### Caso C · Entidad financiera

- Análisis de solicitudes de crédito con documentos de unas 30 páginas; el analista necesita el resumen en menos de 10 minutos.
- 3.000 solicitudes al día en horario laboral.
- Requisitos: la inferencia solo puede ocurrir en el país o, si no hay región, en la zona de datos aprobada por el regulador; auditoría completa; RTO de 1 hora; RPO de 0 para las decisiones registradas.

## Preguntas guía

- ¿Qué carga sobrevive a la caída de una región y cuál no? ¿Es aceptable?
- ¿Quién conmuta: el proveedor, el gateway o el cliente?
- ¿Qué componente global quedó en serie?
- ¿Dónde se procesa cada dato personal?
- ¿Qué pagaría aunque no hubiera tráfico?
