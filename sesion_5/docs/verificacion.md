# Matriz de verificación (fecha de preparación: 2026-11-10)

| Elemento | Prueba | Resultado |
|---|---|---|
| Gateway, Python 3.12 | `pytest` (51), `ruff`, `mypy --strict` | Pasa (proveedor mock) |
| Smoke con servidor real | curl: chat, stream SSE, job + idempotencia, /metrics | Pasa |
| Experimentos E1–E3 | `experiments/` | Ejecutados con mock (simulados) |
| Frontend | `npm run build` (Vite 6) | Pasa; prueba manual en navegador **pendiente** |
| `docker compose config` | validación estática (con y sin perfil ollama) | Pasa |
| Build de imágenes Docker | — | **Pendiente** (sin daemon Docker en el entorno de preparación) |
| Ollama real | — | **Pendiente** |
| AWS SAM | `cfn-lint` | Pasa; **no desplegado** |
| AWS Strands/AgentCore | `py_compile` | Sin ejecución contra Bedrock |
| Azure 4 frameworks | construcción de agentes offline (`smoke_static.py`) | Pasa; **sin llamadas reales** |
| Azure Functions / Service Bus | `py_compile` + import | **No desplegado** |
| GCP ADK | import + herramienta local | Sin modelo real |
| GCP Pub/Sub function | import | **No desplegado** |
| Cloud Run GPU | — | **No construido** |
| Consolas (E5.5.1, E5.6.1, E5.7.1) | — | **Pendiente**: validar menús el día previo |

Versiones usadas en la verificación: ver `requirements*.txt` y `labs/azure/E5.6.2-agentes-4-frameworks/requirements.txt`. Advertencia: `google-adk` instalado en el entorno de verificación fue 1.25.1; confirmar la versión vigente.

## Mediciones del docente (completar tras ejecutar E5.1 con Ollama)
| Fecha | Modelo | Hardware | 1.ª petición (ms) | Siguientes (ms) | Notas |
|---|---|---|---|---|---|
