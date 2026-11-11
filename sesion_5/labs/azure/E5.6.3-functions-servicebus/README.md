# E5.6.3 · Service Bus → Azure Functions (Flex Consumption) → Azure OpenAI/Foundry

**Estado:** código verificado de forma estática (`py_compile` + imports); **no desplegado**. Confirma en la documentación oficial los comandos `az functionapp create --flexconsumption-location` y el estado de disponibilidad por región.

## Arquitectura
Productor → cola `jobs` (Service Bus) → Function (trigger) → modelo → persistencia. Fallos → reintento → DLQ. Concurrencia acotada con `maxConcurrentCalls` y *maximum instance count* del plan (backpressure).
## Pasos (resumen)
```bash
az group create -n rg-sllm -l <region>
az servicebus namespace create -g rg-sllm -n <ns> --sku Standard
az servicebus queue create -g rg-sllm --namespace-name <ns> -n jobs --max-delivery-count 5
az storage account create -g rg-sllm -n <stg> --sku Standard_LRS
az functionapp create -g rg-sllm -n <app> --storage-account <stg> --flexconsumption-location <region> --runtime python --runtime-version 3.12
az functionapp identity assign -g rg-sllm -n <app>
# Roles (mínimo privilegio): "Azure Service Bus Data Receiver" sobre la cola y "Cognitive Services OpenAI User" sobre el recurso del modelo.
func azure functionapp publish <app>
```
Enviar mensaje de prueba desde el portal (Service Bus Explorer) con `{"job_id":"1","prompt":"Define serverless"}`.
## Mitigación de cold start
Flex Consumption permite *always ready instances* (costo continuo). Cliente global reutilizado. Evita dependencias pesadas en import.
## Seguridad
Identidad administrada, **sin cadenas de conexión ni claves**; red privada opcional (VNet integration + private endpoints).
## Costos
Ejecuciones/memoria + Service Bus + tokens; always-ready añade costo fijo. Sin cifras aquí.
## Troubleshooting
Mensajes en DLQ → revisar `DeadLetterReason`; 401/403 → falta rol RBAC (la propagación puede tardar minutos); trigger inactivo → revisar `ServiceBusConnection__fullyQualifiedNamespace`.
## Limpieza
`az group delete -n rg-sllm --yes --no-wait`
## Reflexión
¿Por qué la cola protege al modelo de picos mejor que un trigger HTTP? ¿Qué ocurre con mensajes duplicados?
