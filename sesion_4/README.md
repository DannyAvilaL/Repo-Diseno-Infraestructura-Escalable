# Sesión 4 — Redes, almacenamiento y autoscaling en entornos de inferencia

Curso **Diseño de Infraestructura Escalable para LLMs** · Capítulo 2 · Maestría · 3 h.
Código: licencia MIT (`LICENSE`). Materiales docentes: CC BY-SA 4.0.

**Objetivo de desempeño:** servidor de inferencia LLM contenedorizado con red, almacenamiento y autoscaling.

## Estructura
| Ruta | Contenido |
|---|---|
| `presentacion/` | PPTX teórico (53 diapositivas, notas del expositor con tiempos). Generador: `deck/build.js` |
| `docs/` | `arquitectura.md` (teoría + Mermaid), `guia-docente.md`, `guia-estudiante.md`, `evaluacion.md`, `bibliografia.md`, `guia-gpu.md`, `comparacion-frameworks.md`, `adr/001-006` |
| `backend/` | Gateway FastAPI (admisión con cola acotada, métricas Prometheus, SSE) + 11 pruebas |
| `frontend/` | React 18 + Vite 6 (chat con streaming y ráfaga de prueba) |
| `loadtest/` | Prueba de carga con barrido de concurrencia |
| `k8s/`, `monitoring/` | Manifiestos (StatefulSet, NetworkPolicy, KEDA, PDB, SLO) |
| `labs/00-ollama-local` | Laboratorio local (Docker + Ollama) |
| `labs/01-gcp-vertex-adk`, `02-azure-foundry`, `03-aws-bedrock` | Agentes por consola y por código |
| `docente-privado/` | **Mover al repo privado `llm-infra-escalable-docente`**: solucionario y rúbricas. No publicar. |

## Inicio rápido (local, Ubuntu 24.04+, Python 3.12)
```bash
cp .env.example .env
docker compose --profile setup run --rm model-pull   # descarga el modelo una vez
docker compose up -d                                  # UI en http://localhost:8080
cd backend && python -m venv .venv && . .venv/bin/activate
pip install -r ../requirements-dev.txt && pytest -q
python ../loadtest/loadtest.py --help
```
Limpieza: `docker compose down -v`.

## Estado de validación (honesto)
- **Verificado:** 11 pruebas del gateway y 7 de la herramienta de capacidad pasan; `npm run build` compila; los YAML parsean; los scripts de agentes importan y construyen sus objetos (MAF, SK, AutoGen, LangGraph, Strands, AgentCore); el PPTX valida.
- **No verificado:** llamadas reales a modelos en Google/Azure/AWS; manifiestos en un clúster real; ejemplo DRA; interfaz en navegador; rendimiento (no se incluyen cifras: se miden en el laboratorio).
- **Confirmar antes de clase:** ID del modelo Gemini vigente, nombre/estado de la plataforma Vertex AI, versión vigente de OWASP LLM Top 10.

## Seguridad
Sin secretos en el repo (`.env` ignorado), identidades sin claves estáticas (Entra ID / ADC / IAM), servidor de inferencia en loopback, NetworkPolicy deny-by-default.
