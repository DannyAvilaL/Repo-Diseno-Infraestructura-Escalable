# E5.7.3 · Pub/Sub → Cloud Run function → Gemini

**Estado:** código verificado de forma estática; **no desplegado**. Confirma flags de `gcloud functions deploy` en la documentación vigente.

```bash
export PROJECT=<proyecto> REGION=<region> GEMINI_MODEL=<modelo>
gcloud pubsub topics create sllm-jobs
gcloud pubsub topics create sllm-jobs-dlq
gcloud functions deploy sllm-worker --gen2 --runtime=python312 --region=$REGION \
  --source=. --entry-point=procesar --trigger-topic=sllm-jobs --max-instances=5 \
  --set-env-vars=GOOGLE_CLOUD_PROJECT=$PROJECT,GOOGLE_CLOUD_LOCATION=$REGION,GEMINI_MODEL=$GEMINI_MODEL \
  --retry
gcloud pubsub topics publish sllm-jobs --message='{"job_id":"1","prompt":"Define serverless en una frase"}'
gcloud functions logs read sllm-worker --gen2 --region=$REGION --limit=20
```
**Dead-letter:** configura una política de dead letter en la suscripción creada por el trigger (`gcloud pubsub subscriptions update ... --dead-letter-topic=sllm-jobs-dlq --max-delivery-attempts=5`) y otorga al servicio de Pub/Sub los permisos de publisher/subscriber que pide la documentación.
**Seguridad:** cuenta de servicio dedicada con `roles/aiplatform.user`. **Costos:** por invocación/CPU/memoria + tokens (sin cifras aquí). `--max-instances` actúa como backpressure.
**Limpieza:** `gcloud functions delete sllm-worker --gen2 --region=$REGION`; borrar tópicos y suscripciones.
**Reflexión:** at-least-once en Pub/Sub ¿cómo garantizas idempotencia del resultado?
