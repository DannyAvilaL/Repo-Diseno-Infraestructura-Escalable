# Laboratorios AWS (AWS-A a AWS-D)

> **Estado de validación (13-oct-2026):** AWS-B se construye con strands-agents 1.60.0 y el servidor local de AWS-C responde en `/ping` e `/invocations` con bedrock-agentcore 1.24.1 (ver `labs/VALIDACION.md`). **No se ha ejecutado contra una cuenta real** ni contra Bedrock.
>
> **Cambio relevante:** Amazon Bedrock Agents se renombró **Agents Classic** y, desde el 30-jul-2026, no admite clientes nuevos; AWS recomienda AgentCore para desarrollo nuevo ([fuente](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-classic-maintenance-mode.html)). Como las cuentas de los estudiantes son nuevas, todos los laboratorios usan **AgentCore**.

| Lab | Tema | Duración |
| --- | --- | --- |
| AWS-A | Agente desde la consola de AgentCore | 60 min |
| AWS-B | Strands Agents SDK con Amazon Bedrock | 90 min |
| AWS-C | Despliegue en AgentCore Runtime | 90 min |
| AWS-D | Arquitectura, seguridad, escalabilidad y costos | 60 min |

## SDK, runtime y servicio gestionado

| Capa | En AWS | Qué hace |
| --- | --- | --- |
| SDK del agente | Strands Agents | Código del agente: modelo, instrucciones, herramientas, bucle |
| Runtime gestionado | AgentCore Runtime (+ Identity, Gateway, Memory, Observability) | Ejecuta el agente en sesiones aisladas, con identidad y trazas |
| Servicio de modelos | Amazon Bedrock | Inferencia del modelo |

## Cuenta trial

Elija el **plan Paid** al registrarse (los créditos de bienvenida aplican igual): el plan Free excluye algunos servicios y se cierra a los 6 meses o al agotar créditos. Cree un presupuesto en AWS Budgets antes del primer recurso. Fuente: [AWS Free Tier](https://aws.amazon.com/blogs/aws/aws-free-tier-update-new-customers-can-get-started-and-explore-aws-with-up-to-200-in-credits).

## Preparación

```bash
aws configure sso --profile llm-curso       # identidad sin claves de larga duración
aws sso login --profile llm-curso
cd labs/30-aws && cp .env.example .env      # región y modelo disponibles
```

Permisos mínimos para AWS-B: invocar el modelo elegido (`bedrock:InvokeModel`, `bedrock:InvokeModelWithResponseStream`) sobre su ARN o perfil de inferencia. Verifique en la consola de Bedrock que el modelo está disponible en la región.

## AWS-A · Agente desde la consola

1. Abra la consola de Amazon Bedrock AgentCore en la región elegida.
2. Cree un agente con la opción de configuración guiada disponible para cuentas nuevas (modelo, instrucciones y herramientas declaradas como configuración). El flujo exacto de consola debe verificarse en la documentación vigente.
3. Instrucciones: `INSTRUCCIONES_ASISTENTE` de `labs/common/universidad_tools.py`.
4. Pruebe preguntas y revise la observabilidad (trazas, tokens, latencia).
5. Identifique los costos: tokens del modelo y tiempo de ejecución del runtime.

## AWS-B · Strands Agents

```bash
cd b-strands
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python agente_strands.py "¿Qué dice el reglamento sobre asistencia y cuándo terminan las clases?"
```

**Resultado esperado:** el agente invoca `buscar_reglamento` y `consultar_calendario_academico` y responde citando el art. 27 ficticio y la fecha del 28-may-2027.

## AWS-C · AgentCore Runtime

```bash
cd c-agentcore-runtime
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
set -a && . ../.env && set +a
python app.py &                                   # servidor local
curl -s -X POST http://127.0.0.1:8080/invocations \
  -H 'Content-Type: application/json' -d '{"prompt":"¿Cuándo inician las clases?"}'
```

El puerto y las rutas locales (`8080`, `/ping`, `/invocations`) se verificaron con bedrock-agentcore 1.24.1. Para desplegar en AgentCore Runtime, siga la guía oficial «Get started with AgentCore Runtime» (CLI o APIs). Antes de empaquetar, copie `labs/common` dentro de esta carpeta como `common/`.

## AWS-D · Arquitectura

1. Dibuje el caso en AWS (D-19): API Gateway + WAF, ECS/Fargate o Lambda, Bedrock, AgentCore, Knowledge Bases con S3 Vectors u OpenSearch, Secrets Manager, roles de IAM, Bedrock Guardrails, CloudWatch.
2. Analice seguridad: identidad del agente (AgentCore Identity), VPC y endpoints privados, mínimo privilegio de herramientas.
3. Evalúe escalabilidad y costos frente a Google Cloud y Azure (MC-01).

## Seguridad

Perfiles SSO; sin claves de acceso en archivos. Rol de ejecución del runtime con permisos solo para el modelo usado. Herramientas de solo lectura. El entrypoint valida longitud de la entrada.

## Costos

Tokens del modelo en Bedrock; tiempo de ejecución y servicios de AgentCore si se despliega. No medido en la preparación: revise el panel de facturación tras el laboratorio.

## Solución de problemas

| Síntoma | Acción |
| --- | --- |
| `AccessDeniedException` | Revisar política de IAM y disponibilidad del modelo en la región |
| `ValidationException` sobre el modelo | Usar el ID de perfil de inferencia indicado en la consola para su región |
| Servicio no disponible en la cuenta | La cuenta está en plan Free: cambiar a Paid |
| Sesión SSO expirada | `aws sso login --profile llm-curso` |

## Limpieza

1. Elimine el agente y el runtime de AgentCore desde la consola o con el comando de eliminación de la herramienta de despliegue usada.
2. Elimine repositorios de ECR y roles de IAM creados para el laboratorio.
3. Verifique en el panel de facturación, filtrando por la etiqueta `curso=llm-infra`, que no quedan recursos activos.

## Preguntas de reflexión

1. ¿Qué cambió en AWS con el paso de Bedrock Agents a AgentCore, y por qué importa para una cuenta nueva?
2. ¿Qué responsabilidades asume AgentCore Runtime que en AWS-B estaban en su equipo?
3. ¿Cómo aplicaría mínimo privilegio a una herramienta que consulta el sistema académico?
