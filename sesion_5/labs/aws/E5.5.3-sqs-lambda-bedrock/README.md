# E5.5.3 · SQS → Lambda → Bedrock Converse (AWS SAM)

**Estado de verificación:** plantilla validada estáticamente con `cfn-lint` (ver `docs/verificacion.md`). **No desplegada** contra una cuenta real en la preparación del material.

## Arquitectura
Cliente → API Gateway HTTP → `SubmitFunction` → SQS (+DLQ) → `WorkerFunction` (SnapStart, partial batch response, `MaximumConcurrency=5`) → Bedrock Converse → DynamoDB (resultado, TTL).

## Prerrequisitos
AWS CLI v2 y SAM CLI; cuenta de prueba; acceso al modelo habilitado en Bedrock (consola → *Model access*); región con ese modelo. Python 3.12.

## Despliegue
```bash
cd labs/aws/E5.5.3-sqs-lambda-bedrock
sam build
sam deploy --guided --parameter-overrides ModelId=<TU_MODEL_ID_O_INFERENCE_PROFILE> --stack-name sllm-e553
```
## Validación
```bash
API=$(aws cloudformation describe-stacks --stack-name sllm-e553 --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text)
curl -s -X POST $API/jobs -H 'content-type: application/json' -d '{"prompt":"Resume serverless en una frase"}'
curl -s $API/jobs/<job_id>
```
Para observar la DLQ: pon un `ModelId` inexistente, envía un job y revisa `DlqUrl` tras 3 recepciones.

## Seguridad / mínimo privilegio
La política de Bedrock usa `Resource: "*"` por simplicidad didáctica: **restríngela** al ARN del modelo/perfil. La API no tiene autenticación en este laboratorio: añade un authorizer (IAM/JWT) antes de exponerla. Cola y tabla cifradas.

## Costos (advertencia)
Pago por solicitud en Lambda, SQS, API Gateway, DynamoDB y por tokens en Bedrock. No se incluyen cifras: consulta la página de precios vigente y fija un AWS Budget antes de ejecutar pruebas de carga.

## Troubleshooting
- `AccessDeniedException` en Bedrock: modelo no habilitado o región distinta.
- Mensajes reaparecen: `VisibilityTimeout` menor que el tiempo de procesamiento.
- `ValidationException` por modelId: algunos modelos exigen *inference profile*.

## Limpieza
```bash
sam delete --stack-name sllm-e553
```
## Reflexión
1) ¿Por qué `MaximumConcurrency` y no solo el límite de Bedrock? 2) ¿Qué pasa si el worker muere tras escribir `RUNNING`? 3) ¿Cómo diseñarías la reintentabilidad de jobs `FAILED`?
