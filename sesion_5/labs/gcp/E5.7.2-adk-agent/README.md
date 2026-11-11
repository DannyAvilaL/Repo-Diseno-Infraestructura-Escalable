# E5.7.2 · Agente en código con Google ADK → Cloud Run

**Estado:** código verificado solo de forma estática (importa con `google-adk` instalado); **no ejecutado contra Google Cloud**. La plataforma de agentes de Google Cloud cambió de nombre (antes Vertex AI): confirma terminología, comandos `adk deploy` y modelos vigentes en la documentación oficial.

## Prerrequisitos
Python 3.12, `gcloud` autenticado (`gcloud auth application-default login`), proyecto de prueba con facturación y APIs de IA habilitadas.
## Ejecución local
```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example sllm_agent/.env   # completar valores
adk run sllm_agent                # CLI
adk web                           # UI de desarrollo (solo desarrollo, no producción)
```
## Despliegue en Cloud Run (serverless)
```bash
adk deploy cloud_run --project=$GOOGLE_CLOUD_PROJECT --region=$GOOGLE_CLOUD_LOCATION --service_name=sllm-agent sllm_agent
```
Para mitigar cold start: `gcloud run services update sllm-agent --min-instances=1 --cpu-boost` (min-instances tiene costo permanente).
## Seguridad
Cuenta de servicio dedicada con `roles/aiplatform.user` únicamente; despliega **sin** acceso público (`--no-allow-unauthenticated`) y llama con identity token.
## Costos
Cloud Run (CPU/memoria/solicitudes) + tokens del modelo; consultar precios vigentes. Fijar presupuesto y alertas.
## Limpieza
`gcloud run services delete sllm-agent --region=$GOOGLE_CLOUD_LOCATION`; borrar imágenes en Artifact Registry.
## Reflexión
¿Qué estado de sesión pierdes al escalar a cero y cómo lo externalizarías?
