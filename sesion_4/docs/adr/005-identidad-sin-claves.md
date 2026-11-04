# ADR-005 — Identidad sin claves estáticas en los laboratorios cloud
**Estado:** Aceptada · **Fecha:** 2026-11-03
**Decisión:** Entra ID (`DefaultAzureCredential`/`az login`), ADC en GCP y roles/SSO en AWS; ninguna clave en código ni en repositorio; `.env` excluido por `.gitignore`.
**Consecuencias:** + elimina fuga de claves y facilita rotación; − requiere configurar identidades/roles (más pasos iniciales para estudiantes).
