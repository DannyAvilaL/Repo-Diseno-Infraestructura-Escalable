# Troubleshooting general

| Síntoma | Causa probable | Acción |
| --- | --- | --- |
| `pytest` falla con `ModuleNotFoundError: app` | Ejecución fuera de `backend/` | `cd labs/00-local-ollama/backend && pytest` |
| `/readyz` 503 | Ollama detenido o modelo no descargado | Ver el `detail` de la respuesta: indica el comando |
| Puerto ocupado (8000, 5173, 11434) | Otro proceso | `ss -ltnp | grep <puerto>` y detenerlo |
| Azure: error de cuota al desplegar el modelo | Suscripción trial sin cuota para ese modelo o región | Probar gpt-5-mini GlobalStandard; consultar el nivel con la API `quotaTiers`; usar la ruta alternativa de Ollama |
| Azure: 401/403 desde el SDK | Falta rol en el proyecto Foundry | Asignar el rol de usuario de Foundry al usuario o identidad |
| AWS: `AccessDeniedException` al invocar el modelo | Permisos de IAM o acceso al modelo en la región | Verificar la política y la disponibilidad del modelo en la región |
| AWS: servicio no disponible en la cuenta | Plan Free restringe el servicio | Cambiar a plan Paid (los créditos se conservan) |
| Google: `PERMISSION_DENIED` | API no habilitada o rol faltante | Habilitar la API y asignar el rol indicado en el laboratorio |
| Google: cargos con la clave de AI Studio | El crédito trial no cubre la Gemini API de AI Studio | Usar la plataforma de agentes con ADC (Vertex) |
