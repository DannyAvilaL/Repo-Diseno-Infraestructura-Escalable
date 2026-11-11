# E5.7.4 · Cloud Run con GPU + Ollama (inferencia autogestionada serverless)

**Estado:** Dockerfile de referencia, **no construido ni desplegado**. La disponibilidad de GPU en Cloud Run depende de región/cuotas y estado (GA/preview): verifícalo en la documentación oficial. Requiere cuota de GPU, normalmente no disponible en cuentas de prueba gratuitas: úsalo como demostración conceptual si no hay cuota.

```bash
gcloud run deploy sllm-ollama --source . --region=$REGION --port=8080 \
  --gpu=1 --gpu-type=<tipo-disponible> --cpu=<n> --memory=<m> --no-cpu-throttling \
  --max-instances=1 --no-allow-unauthenticated
```
**Qué enseña:** modelo en la imagen vs descarga en runtime; `OLLAMA_KEEP_ALIVE=-1` mantiene el modelo en VRAM mientras la instancia vive; escalar a cero implica cold start de GPU + carga del modelo.
**Seguridad:** sin acceso público; invocar con identity token. **Costos:** GPU facturada mientras la instancia está activa; consultar precios vigentes.
**Limpieza:** `gcloud run services delete sllm-ollama --region=$REGION`; borrar imagen.
**Reflexión:** ¿a partir de qué utilización sostenida conviene una VM/GKE con GPU frente a Cloud Run GPU? (ver cálculo de break-even en `docs/finops.md`).
