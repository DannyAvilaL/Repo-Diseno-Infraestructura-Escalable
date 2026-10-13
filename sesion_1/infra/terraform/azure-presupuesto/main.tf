# Grupo de recursos exclusivo del curso + presupuesto con alertas.
# Todo laboratorio de Azure se crea dentro de este grupo para poder
# eliminarlo completo (docs/03-costos-y-limpieza.md).

resource "azurerm_resource_group" "curso" {
  name     = "rg-llm-curso-${var.usuario}"
  location = var.location
  tags = {
    curso = "llm-infra"
  }
}

resource "azurerm_consumption_budget_resource_group" "curso" {
  name              = "presupuesto-llm-curso-${var.usuario}"
  resource_group_id = azurerm_resource_group.curso.id
  amount            = var.presupuesto_mensual_usd
  time_grain        = "Monthly"

  time_period {
    start_date = var.inicio_presupuesto
  }

  notification {
    enabled        = true
    threshold      = 50
    operator       = "GreaterThan"
    threshold_type = "Actual"
    contact_emails = [var.correo_alertas]
  }

  notification {
    enabled        = true
    threshold      = 90
    operator       = "GreaterThan"
    threshold_type = "Forecasted"
    contact_emails = [var.correo_alertas]
  }
}
