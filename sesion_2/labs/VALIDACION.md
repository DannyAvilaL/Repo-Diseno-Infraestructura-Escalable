# Validación de los laboratorios (Sesión 1: 13-oct-2026 · Sesión 2: 20-oct-2026)

Qué se comprobó en la preparación del curso, con qué versiones y qué queda pendiente. Entorno de validación: Linux, Python 3.13 (los laboratorios apuntan a Python 3.12), cada laboratorio en su propio entorno virtual con su `requirements.txt`.

## Resultados

| Lab | Versiones fijadas | Qué se ejecutó | Resultado | Pendiente con cuenta real |
| --- | --- | --- | --- | --- |
| LOC-01 | FastAPI 0.143.0, OpenTelemetry 1.45.1 | 19 pruebas; backend y prueba de carga contra simulador; backend contra **Ollama 0.40.3 real** (sin modelo); build del frontend | ✅ Aprobado. La prueba con Ollama real encontró y corrigió 2 defectos | Inferencia con modelo real (registro de modelos inaccesible en el entorno); `docker compose` (Docker Hub inaccesible) |
| AZ-B | agent-framework 1.21.0 | Construcción con `FoundryChatClient` (firma verificada); bucle con herramientas contra simulador con `OpenAIChatCompletionClient` | ✅ El agente invoca la herramienta y usa su resultado | Autenticación, cuota y despliegue en Foundry |
| AZ-C | semantic-kernel 1.45.0 | `agente_sk.py` completo contra simulador HTTPS | ✅ Bucle con herramienta completo | Ídem |
| AZ-D | autogen-agentchat 0.7.5 | `agente_autogen.py` completo contra simulador | ✅ Bucle con herramienta completo | Ídem |
| AZ-E | langgraph 1.2.15, langchain-openai 1.7.1, langchain-azure-ai 1.2.10 | `grafo_langgraph.py` completo contra simulador; `hosted_agent.py` servido en local: `POST /responses` con estado `completed` y llamada a herramienta | ✅ | Despliegue como hosted agent en Foundry |
| GCP-B | google-adk 2.12.0 | Construcción de `root_agent`; adaptador FastAPI con 3 pruebas que ejecutan el bucle completo con un modelo simulado de ADK; instalación limpia de `requirements-dev.txt` | ✅ La instalación limpia detectó y corrigió un conflicto de versiones de FastAPI | Llamada a Gemini, `adk web`, despliegue en el runtime gestionado |
| AWS-B | strands-agents 1.60.0 | Construcción del agente con `BedrockModel` y herramientas | ✅ | Invocación a Bedrock con permisos de IAM |
| AWS-C | bedrock-agentcore 1.24.1 | Servidor local: `GET /ping` y `POST /invocations` en el puerto 8080; validación de entrada | ✅ | Despliegue en AgentCore Runtime |
| AZ-A, GCP-A, AWS-A | — | Laboratorios de consola | No ejecutables sin cuenta | Todo el procedimiento |

### Sesión 2 (20-oct-2026, Python 3.12)

| Lab | Versiones fijadas | Qué se ejecutó | Resultado | Pendiente con cuenta real |
| --- | --- | --- | --- | --- |
| LOC-02 | FastAPI 0.143.0 (mismo entorno que LOC-01) | 36 pruebas; dos regiones simuladas + gateway en procesos reales; prueba de conmutación bajo carga (120 solicitudes); lote de 200 PQRS con la primaria caída a mitad; frontend compilado y recorrido con Playwright | ✅ 0 errores en la conmutación; lote `completed` 200/200 | Modo híbrido con Ollama real; modo nube; `docker compose` |
| Lote PQRS (`common/lote_pqrs.py`) | — | 15 pruebas: generación reproducible, tres formatos de proveedor, UTF-8 sin BOM, parser y evaluación | ✅ | — |
| AZ-G | openai 3.35.1, azure-identity 1.26.0 | 8 pruebas con transporte HTTP simulado (`httpx2.MockTransport`): conmutación, pausa por 429, 4xx sin conmutación, flujo batch completo | ✅ | Dos recursos reales, rol, cuota trial; Batch solo con suscripción de pago; APIM |
| GCP-D | google-genai 2.31.0, google-cloud-storage 3.17.1 | 10 pruebas con clientes simulados: conmutación, reintentos del SDK desactivados, `service_tier`, flujo batch | ✅ | Identificador del modelo vigente, cuotas, permisos del agente de servicio, consola |
| AWS-E | boto3 1.43.116 | 8 pruebas con botocore Stubber (valida parámetros contra el modelo del servicio): Converse, `serviceTier`, conmutación, `CreateModelInvocationJob` con `Converse`, descarga | ✅ | Acceso a Nova Lite, CRIS en plan Paid, rol de servicio real, tiempos de cola |
| Diagramas D-01 a D-44 | @mermaid-js/mermaid-cli | Render de los 44 archivos `.mmd` | ✅ Sin errores | — |
| Presentación S2 | pptxgenjs | `validate.py` del skill pptx; render a PDF y revisión visual de las 56 diapositivas | ✅ | — |

## Herramientas de validación sin nube

- `common/mock_openai_tools.py`: simulador de Chat Completions con llamadas a herramientas (rutas de Azure OpenAI y OpenAI).
- `common/validar_agente_azure.py`: ejecuta un laboratorio Azure contra el simulador con credencial falsa.
- `00-local-ollama/scripts/mock_ollama.py`: simulador de Ollama para el backend y la prueba de carga.
- `01-local-gateway/scripts/mock_region.py`: región simulada compatible con Chat Completions, con modos de falla (caída, lentitud, 429, intermitente).

Para Semantic Kernel, que exige `https`, se generó un certificado local de un día y se lanzó el simulador con TLS:

```bash
openssl req -x509 -newkey rsa:2048 -nodes -keyout key.pem -out cert.pem -days 1 \
  -subj "/CN=127.0.0.1" -addext "subjectAltName=IP:127.0.0.1"
python -c "import sys; sys.path.insert(0,'labs/common'); import uvicorn, mock_openai_tools as m; \
uvicorn.run(m.app, host='127.0.0.1', port=8901, ssl_keyfile='key.pem', ssl_certfile='cert.pem')" &
SSL_CERT_FILE=$PWD/cert.pem MOCK_ENDPOINT=https://127.0.0.1:8901 \
  python labs/common/validar_agente_azure.py labs/20-azure/c-semantic-kernel-legado/agente_sk.py main
```

## Infraestructura

| Elemento | Validación | Resultado |
| --- | --- | --- |
| Manifiestos Kubernetes de LOC-01 (`labs/00-local-ollama/k8s`) | `kubeconform` 0.8.0, modo estricto, esquemas de Kubernetes 1.31 | ✅ 13 recursos válidos; no aplicados a un clúster |
| Terraform de Azure (`infra/terraform/azure-presupuesto`) | Ninguna: el registro de Terraform es inaccesible en el entorno | ⏳ Ejecutar `terraform validate` antes de usarlo |

## Lo que esta validación NO garantiza

Cuotas y disponibilidad de modelos por región, permisos de IAM, flujos de consola, calidad de las respuestas del modelo real, costos y comportamiento de los runtimes gestionados. Todo eso requiere ejecutar los laboratorios con una cuenta trial antes de asignarlos.
