# Mapeo ejemplos del repositorio ↔ slides

| ID | Ejemplo | Ubicación | Tipo | Estado de verificación |
|---|---|---|---|---|
| E5.1 | Ollama local | `labs/local/E5.1-ollama` | Lab | Mock probado; Ollama real **pendiente** |
| E5.2 | Gateway FastAPI serverless-like | `src/serverless_llm` | Código | 51 tests, ruff, mypy OK |
| E5.3 | Frontend React 18 + Vite 6 | `frontend/` | Código | Build OK; prueba manual **pendiente** |
| E5.4 | Pruebas de carga y experimentos | `loadtest/`, `experiments/` | Código | Ejecutado con mock |
| E5.5.1 | Bedrock Agent (consola) | `labs/aws/E5.5.1-…` | Guion | **Pendiente** |
| E5.5.2 | Strands + AgentCore | `labs/aws/E5.5.2-…` | Código | Compilación; **no ejecutado** |
| E5.5.3 | SQS→Lambda→Bedrock (SAM) | `labs/aws/E5.5.3-…` | IaC+código | `cfn-lint` OK; **no desplegado** |
| E5.6.1 | Agente en portal Foundry | `labs/azure/E5.6.1-…` | Guion | **Pendiente** (demo inicia aquí) |
| E5.6.2 a–e | MAF, SK, AutoGen, LangGraph, Agent Service | `labs/azure/E5.6.2-…` | Código | Construcción offline OK (a–d); **sin llamadas reales** |
| E5.6.3 | Service Bus→Functions Flex | `labs/azure/E5.6.3-…` | Código | Import OK; **no desplegado** |
| E5.6.4 | Container Apps GPU | `labs/azure/E5.6.4-…` | Nota | Conceptual |
| E5.7.1 | Agente en consola GCP | `labs/gcp/E5.7.1-…` | Guion | **Pendiente** |
| E5.7.2 | ADK → Cloud Run | `labs/gcp/E5.7.2-…` | Código | Import y herramienta OK; **sin modelo real** |
| E5.7.3 | Pub/Sub→Cloud Run function | `labs/gcp/E5.7.3-…` | Código | Import OK; **no desplegado** |
| E5.7.4 | Cloud Run GPU + Ollama | `labs/gcp/E5.7.4-…` | Dockerfile | **No construido** |
| E5.8 | Pruebas de seguridad | `tests/test_security.py` | Tests | OK |
