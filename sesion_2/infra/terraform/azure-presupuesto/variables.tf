variable "subscription_id" {
  description = "Suscripción de Azure (trial del estudiante)"
  type        = string
}

variable "usuario" {
  description = "Identificador corto del estudiante, usado en los nombres"
  type        = string
  validation {
    condition     = can(regex("^[a-z0-9]{3,12}$", var.usuario))
    error_message = "Use de 3 a 12 caracteres en minúscula o dígitos."
  }
}

variable "location" {
  description = "Región con cuota para el modelo elegido"
  type        = string
  default     = "eastus2"
}

variable "presupuesto_mensual_usd" {
  description = "Tope de alerta mensual en USD"
  type        = number
  default     = 20
}

variable "correo_alertas" {
  description = "Correo que recibe las alertas de presupuesto"
  type        = string
}

variable "inicio_presupuesto" {
  description = "Primer día del mes de inicio, formato AAAA-MM-01T00:00:00Z"
  type        = string
}
