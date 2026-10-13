# Validación de los laboratorios (13-oct-2026)

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

## Herramientas de validación sin nube

- `common/mock_openai_tools.py`: simulador de Chat Completions con llamadas a herramientas (rutas de Azure OpenAI y OpenAI).
- `common/validar_agente_azure.py`: ejecuta un laboratorio Azure contra el simulador con credencial falsa.
- `00-local-ollama/scripts/mock_ollama.py`: simulador de Ollama para el backend y la prueba de carga.

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
