# MC-01 · Comparativo multicloud del caso universitario

> El análisis de referencia completo (precios oficiales consultados el 13-oct-2026, punto de equilibrio y matriz) está en el repositorio privado del docente. Fuentes oficiales para sus cálculos: [Azure Retail Prices API](https://prices.azure.com/api/retail/prices), [precios de IA generativa en Google Cloud](https://cloud.google.com/vertex-ai/generative-ai/pricing), [precios de Amazon Bedrock](https://aws.amazon.com/bedrock/pricing/) y [precios de Cloud Run](https://cloud.google.com/run/pricing).

Análisis arquitectónico del mismo caso en AWS, Azure y Google Cloud. **No se declara una nube ganadora**: el resultado depende del contexto de la organización.

## Objetivo

Comparar modalidades, servicios y responsabilidades con un caso homogéneo, distinguiendo **hechos documentados** (con fuente y fecha) de **recomendaciones** (con criterio explícito).

## Matriz de comparación (completar con fuentes fechadas)

| Dimensión | AWS | Azure | Google Cloud | Tipo (hecho / recomendación) | Fuente y fecha |
| --- | --- | --- | --- | --- | --- |
| Servicio de modelos | Amazon Bedrock | Microsoft Foundry | Gemini Enterprise Agent Platform | Hecho | `docs/referencias.md` |
| Modalidades de inferencia | | | | | |
| Plataforma agéntica | AgentCore | Foundry Agent Service | Agent Engine / Agent Runtime | Hecho | |
| Contenedores y Kubernetes | ECS, EKS | Container Apps, AKS | Cloud Run, GKE | Hecho | |
| Serverless con GPU | | Container Apps (GPU) | Cloud Run (L4 24 GB) | Hecho | |
| GPU dedicada | | | | | |
| Autenticación y autorización | | | | | |
| Seguridad de red (endpoints privados) | | | | | |
| Almacenamiento y búsqueda vectorial | | | | | |
| Observabilidad | | | | | |
| Costos y facturación (tarifa por token del modelo elegido) | | | | | |
| Límites operativos (cuotas TPM/RPM del modelo elegido) | | | | | |
| Restricciones de la cuenta trial | | | | | |
| Dependencia del proveedor | | | | Recomendación | |
| Portabilidad | | | | Recomendación | |
| Complejidad operacional | | | | Recomendación | |

## Cálculos solicitados

1. Demanda del caso: ≈ 330.000 tokens/min en hora pico; ≈ 165 M tokens/mes (supuestos de la Unidad F).
2. Para el modelo elegido en cada nube: costo mensual estimado = tokens de entrada × precio + tokens de salida × precio, con **precio oficial y fecha de consulta**.
3. Cuota TPM disponible frente a la demanda pico.
4. Alternativa autogestionada: 2 réplicas × 720 h = 1.440 GPU-horas × precio oficial de la instancia GPU elegida.

## Entregable

Documento de 3–5 páginas con la matriz completa, los cálculos con fuentes, un diagrama por nube y una recomendación contextualizada para la universidad (ADR).

## Criterios de evaluación

Rúbrica de `sesiones/s01-arquitecturas-base/evaluacion/rubrica.md`, con énfasis en la distinción entre hechos y recomendaciones y en la trazabilidad de los precios.
