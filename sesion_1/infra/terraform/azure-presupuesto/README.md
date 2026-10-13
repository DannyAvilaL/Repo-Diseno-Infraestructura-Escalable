# Terraform · Grupo de recursos y presupuesto de Azure para el curso

Crea el grupo de recursos `rg-llm-curso-<usuario>` y un presupuesto mensual con alertas al 50 % (gasto real) y al 90 % (gasto previsto). Es la primera barrera de costos para cuentas trial.

> **Estado:** escrito con el proveedor `hashicorp/azurerm` 4.x. **No se ejecutó `terraform validate`**: el entorno de preparación no tiene acceso al registro de Terraform. Valídelo antes del bloque de Azure.

## Uso

```bash
az login
cp terraform.tfvars.example terraform.tfvars    # complete; no lo suba al repositorio
terraform init
terraform validate
terraform plan -out plan.tfplan
terraform apply plan.tfplan
```

Los recursos de los laboratorios (proyecto de Foundry, despliegues) se crean después dentro de este grupo, desde el portal o la CLI.

## Limpieza

```bash
terraform destroy
```

Elimina el presupuesto y el grupo de recursos **con todo su contenido**.

## Alternativa sin Terraform

```bash
az group create -n rg-llm-curso-<usuario> -l eastus2 --tags curso=llm-infra
# Presupuesto: Cost Management > Presupuestos en el portal, con alertas al 50 % y 90 %.
```
