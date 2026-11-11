# Troubleshooting general
| Síntoma | Causa probable | Acción |
|---|---|---|
| 401 | API key ausente/ inválida | Cabecera `X-API-Key` |
| 422 | Esquema (extra=forbid) | Revisar campos |
| 429 | Backpressure o rate limit | Respetar `Retry-After` |
| 503 `/readyz` | Proveedor no listo | Verificar Ollama/modelo |
| Mensajes duplicados en cola | At-least-once / visibility timeout corto | Idempotencia; aumentar timeout |
| Frontend sin datos | Proxy `/api` | Ver `vite.config.ts` |
