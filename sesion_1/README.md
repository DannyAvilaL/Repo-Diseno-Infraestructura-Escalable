# Diseño de Infraestructura Escalable para LLMs

Materiales académicos, arquitectónicos y laboratorios del curso de maestría **Diseño de Infraestructura Escalable para Large Language Models**. El curso estudia cómo diseñar, desplegar, asegurar, medir y costear infraestructuras para servir LLMs en Microsoft Azure, Google Cloud y AWS, con un caso transversal: el **asistente institucional de conocimiento de una universidad**.

> Fecha de verificación de servicios y versiones: **13 de octubre de 2026**. Los servicios cloud de IA cambian de nombre y estado con frecuencia; cada laboratorio indica qué se verificó y qué queda pendiente.

## Contenido

| Carpeta | Contenido |
| --- | --- |
| [`sesiones/s01-arquitecturas-base`](sesiones/s01-arquitecturas-base) | Sesión 1: presentación .pptx con notas, marco teórico, planeación, guía del estudiante, caso, evaluación |
| [`docs/`](docs) | Prerrequisitos, entorno Ubuntu/WSL, seguridad, costos y limpieza, arquitectura, 5 ADR, 28 diagramas Mermaid, referencias verificadas |
| [`labs/00-local-ollama`](labs/00-local-ollama) | LOC-01: Ollama + FastAPI + React + OpenTelemetry + prueba de carga + manifiestos Kubernetes |
| [`labs/10-gcp`](labs/10-gcp) | GCP-A consola · GCP-B ADK con adaptador FastAPI · GCP-C arquitectura |
| [`labs/20-azure`](labs/20-azure) | AZ-A Foundry · AZ-B Agent Framework · AZ-C Semantic Kernel (legado) · AZ-D AutoGen (legado) · AZ-E LangGraph y hosted agent · AZ-F arquitectura |
| [`labs/30-aws`](labs/30-aws) | AWS-A AgentCore consola · AWS-B Strands · AWS-C AgentCore Runtime · AWS-D arquitectura |
| [`labs/40-comparativo-multicloud`](labs/40-comparativo-multicloud) | MC-01: enunciado del comparativo del caso en las tres nubes |
| [`labs/common`](labs/common) | Herramientas del caso compartidas por todos los agentes y simulador de Chat Completions para validar sin nube |
| [`labs/VALIDACION.md`](labs/VALIDACION.md) | Qué se probó, con qué versiones y qué queda pendiente |
| [`infra/terraform`](infra/terraform) | Grupo de recursos y presupuesto de Azure para cuentas trial |

El solucionario, la guía docente y las rúbricas con respuestas están en un repositorio privado separado (`llm-infra-escalable-docente`).

## Inicio rápido (laboratorio local)

Requisitos: Ubuntu 24.04 o WSL2, Python 3.12, Node.js 20+. Ollama es opcional para las pruebas.

```bash
git clone <url-del-repositorio> && cd llm-infra-escalable
make install          # entorno virtual + dependencias
make test             # 24 pruebas (backend + herramientas del caso), sin red
cp labs/00-local-ollama/.env.example labs/00-local-ollama/.env
make backend          # http://127.0.0.1:8000/readyz
make frontend         # http://127.0.0.1:5173
```

Instalación de Ollama, elección de modelo según el hardware, demos y limpieza: [`labs/00-local-ollama/README.md`](labs/00-local-ollama/README.md).

## Estado de validación

| Componente | Estado al 13-oct-2026 |
| --- | --- |
| Backend LOC-01 (19 pruebas, incluidas trazas OpenTelemetry) y herramientas del caso (5 pruebas) | ✅ Ejecutado y aprobado |
| Backend contra **Ollama 0.40.3 real** (salud, errores, API nativa y `/v1`) | ✅ Ejecutado; encontró y corrigió 2 defectos |
| Prueba de carga y frontend (build) | ✅ Ejecutados (prueba de carga contra el simulador; cifras sintéticas) |
| Presentación .pptx | ✅ Generada y validada (61 diapositivas con notas; gráficas nativas D-04, D-26 y D-27) |
| Laboratorios Azure (AZ-B a AZ-E), GCP-B y AWS-B/C | ✅ Instalación limpia por laboratorio, versiones fijadas y bucle con herramientas ejecutado **contra simuladores**; ver [`labs/VALIDACION.md`](labs/VALIDACION.md) |
| Manifiestos Kubernetes | ✅ Validados con kubeconform (no aplicados a un clúster) |
| Inferencia con modelo real en Ollama | ⏳ Pendiente en el equipo del docente (registro de modelos inaccesible en el entorno de preparación) |
| Laboratorios contra cuentas cloud reales y laboratorios de consola | ⏳ Pendientes: cuotas, permisos, flujos de consola y costos reales requieren una cuenta trial |
| Terraform y `docker compose` | ⏳ No ejecutados (registro de Terraform y Docker Hub inaccesibles en el entorno) |

## Cuentas trial

Los estudiantes usan cuentas trial. Restricciones verificadas en documentación oficial y su impacto se resumen en [`docs/03-costos-y-limpieza.md`](docs/03-costos-y-limpieza.md). Cree la cuenta de cada nube la semana de su bloque y configure un presupuesto antes del primer recurso.

## Convenciones

- Contrato de API común del asistente: `GET /healthz`, `GET /readyz`, `POST /v1/chat`, `POST /v1/chat/stream` (SSE).
- Configuración por variables de entorno; `.env` nunca se sube (ver `.gitignore` y gitleaks en CI).
- Servicios locales solo en `127.0.0.1`.
- Cada laboratorio incluye prerrequisitos, procedimiento, validación, seguridad, costos, troubleshooting, limpieza y preguntas de reflexión.

## Licencias

Código: MIT ([`LICENSE`](LICENSE)). Materiales didácticos: CC BY-SA 4.0 ([`LICENSE-docs.md`](LICENSE-docs.md)).
