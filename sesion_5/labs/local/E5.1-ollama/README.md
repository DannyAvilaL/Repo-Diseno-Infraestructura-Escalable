# E5.1 · Laboratorio local: Ollama + gateway FastAPI + React

**Estado:** el gateway, las pruebas y el frontend se verificaron con el proveedor `mock`. **La integración real con Ollama NO se probó** en la preparación (sin acceso a modelos): ejecútala antes de clase y registra tus mediciones.

## Objetivo y competencias
Medir cold start (carga del modelo), TTFT y efecto del caché/backpressure en un gateway con semántica serverless, sin depender de una nube.
## Requisitos
Ubuntu 24.04+, Python 3.12, Node 20+, 8 GB RAM (modelo 1B cuantizado; CPU basta), Ollama instalado (https://ollama.com).
## Pasos
```bash
ollama serve &                       # si no corre como servicio
ollama pull llama3.2:1b              # o el modelo open-weight que elijas
cp .env.example .env && sed -i 's/SLLM_PROVIDER=mock/SLLM_PROVIDER=ollama/' .env
make install && set -a && . ./.env && set +a && make run     # gateway :8000
make web                                                        # React :5173
```
## Experimentos
1. **Cold start real:** `ollama stop llama3.2:1b` (descarga el modelo) y envía una petición; compara contra la segunda (`timings.load_ms`, `cold_start`).
2. **keep_alive:** cambia `SLLM_OLLAMA_KEEP_ALIVE=10s`, espera y repite: ¿reaparece la carga?
3. **Caché:** `python -m loadtest.run_loadtest --unique-prompts 5 --requests 100` vs `--unique-prompts 1000`.
4. **Backpressure:** `SLLM_MAX_CONCURRENCY=1`, `--concurrency 20`: observa 429.
Registra resultados en `docs/verificacion.md` (sección "mediciones del docente").
## Seguridad
Ollama escucha solo en localhost; no lo expongas. Cambia `dev-key-change-me` (el gateway lo rechaza fuera de `SLLM_ENV=local`).
## Costos
Ninguno en la nube; consumo de CPU/RAM local.
## Troubleshooting
`/readyz` 503 → Ollama no responde o el modelo no está descargado; timeouts en la 1.ª petición → subir `SLLM_QUEUE_WAIT_TIMEOUT_S`; poca RAM → modelo más pequeño.
## Limpieza
`ollama rm llama3.2:1b`; `docker compose down -v`.
## Reflexión
¿Qué parte del cold start local equivale a la carga de pesos en GPU en la nube? ¿Por qué temperature=0 es condición para cachear?
