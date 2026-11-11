# E5.5.2 · Agente en código: Strands Agents SDK + Bedrock AgentCore Runtime

**Estado:** código con verificación estática (imports/sintaxis) únicamente; **no ejecutado contra Bedrock**. Los nombres de paquetes (`strands-agents`, `bedrock-agentcore`) y el contrato `/invocations` deben confirmarse en la documentación oficial vigente antes de la clase; las versiones no se fijan aquí a propósito (cambian con rapidez).

## Pasos
```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r agent/requirements.txt
export AWS_REGION=<region> MODEL_ID=<modelo_habilitado>
python agent/app.py            # local
```
Despliegue (toolkit oficial, verificar sintaxis vigente con `agentcore --help`):
```bash
pip install bedrock-agentcore-starter-toolkit
agentcore configure -e agent/app.py
agentcore launch
agentcore invoke '{"prompt": "Cuanto es 12*7?"}'
```
## Seguridad
Rol de ejecución con permisos solo para el modelo; no registres prompts completos; trata la salida de herramientas como no confiable.
## Costos
AgentCore Runtime factura por consumo de CPU/memoria activa y Bedrock por tokens: consultar precios vigentes; sin cifras en este material.
## Limpieza
`agentcore destroy` (o eliminar el runtime y el repositorio ECR en consola).
## Reflexión
¿Qué ventaja tiene un runtime con aislamiento por sesión frente a una Lambda para agentes de larga duración?
