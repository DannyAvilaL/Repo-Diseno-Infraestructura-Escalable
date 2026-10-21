# Costos, cuentas trial y limpieza de recursos

## Restricciones de las cuentas trial (verificadas el 13-oct-2026)

| Nube | Oferta | Restricción relevante | Decisión del curso | Fuente |
| --- | --- | --- | --- | --- |
| Azure | Cuenta gratuita con crédito por tiempo limitado (30 días según documentación de Azure) | La cuota de modelos depende del *quota tier*. La documentación oficial define un Free Tier / Tier 0 con gpt-4.1-mini, gpt-5-mini, o4-mini y text-embedding-3-small (GlobalStandard). Hay reportes de trials con cuota 0 | Usar solo modelos de Tier 0 (gpt-5-mini). Validar con una trial nueva antes del bloque. Ruta alternativa con Ollama | [Quotas and limits](https://learn.microsoft.com/en-us/azure/foundry/openai/quotas-limits) |
| AWS | Plan Free (6 meses o hasta agotar créditos) o plan Paid; US$100 + hasta US$100 por actividades | El plan Free excluye algunos servicios | Recomendar plan Paid con AWS Budgets; verificar AgentCore en plan Free | [AWS Free Tier](https://aws.amazon.com/blogs/aws/aws-free-tier-update-new-customers-can-get-started-and-explore-aws-with-up-to-200-in-credits) |
| Google Cloud | US$300 por 90 días | Sin GPU ni modelos de terceros como servicio durante la trial; el crédito no cubre la Gemini API de AI Studio | Gemini vía la plataforma de agentes (no AI Studio); sin GPU | [Free Trial](https://docs.cloud.google.com/free/docs/free-cloud-features) |

Las condiciones de las ofertas trial cambian: verifíquelas el día que cree la cuenta.

### Restricciones adicionales relevantes para la Sesión 2 (verificadas el 20-oct-2026)

| Nube | Restricción | Impacto | Fuente |
| --- | --- | --- | --- |
| Azure | Cuota Global Batch y Data Zone Batch «N/A» para *free trial* y *Azure for Students* | AZ-G.6 es una demostración del docente con suscripción de pago | [Quotas and limits](https://learn.microsoft.com/en-us/azure/foundry/openai/quotas-limits) |
| Azure | Cuota de Global Standard por suscripción, compartida entre regiones (desde el 7-may-2026) | El segundo recurso de AZ-G no duplica la cuota | Misma fuente |
| AWS | El plan Free no admite funciones multirregión o entre regiones | Los perfiles CRIS (`us.`, `global.`) pueden fallar; use el plan Paid | [Servicios del plan Free](https://docs.aws.amazon.com/accounts/latest/reference/supported-services-sign-up-new.html) |
| AWS | Mínimo de 100 registros por trabajo batch | El lote de AWS-E tiene 200 registros | Cuotas de Bedrock |
| Google Cloud | El crédito no cubre la Gemini API de AI Studio | GCP-D usa la plataforma con `enterprise=True` | [Free Trial](https://docs.cloud.google.com/free/docs/free-cloud-features) |

## Antes del primer recurso

- **Azure:** crear un presupuesto en Cost Management con alerta al 50 % del crédito.
- **AWS:** crear un presupuesto en AWS Budgets (por ejemplo, US$10) con alerta por correo.
- **Google Cloud:** crear un presupuesto en Billing con alertas al 50 % y 90 %.

## Regla de limpieza

Todo recurso de laboratorio se crea en **un grupo, proyecto o etiqueta exclusivos** para poder eliminarlo completo:

| Nube | Contenedor de limpieza | Comando |
| --- | --- | --- |
| Azure | Grupo de recursos `rg-llm-curso-<usuario>` | `az group delete -n rg-llm-curso-<usuario> --yes --no-wait` |
| Google Cloud | Proyecto `llm-curso-<usuario>` | `gcloud projects delete llm-curso-<usuario>` |
| AWS | Etiqueta `curso=llm-infra` + región única | Ver la sección de limpieza de cada laboratorio AWS; AgentCore y Bedrock no se agrupan como un grupo de recursos |

Después de limpiar, revise la factura o el panel de costos 24 horas después: algunos cargos aparecen con retraso.
