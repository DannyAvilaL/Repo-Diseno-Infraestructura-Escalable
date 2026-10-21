# Seguridad y gestión de secretos en el repositorio

## Reglas

1. **Ningún secreto en el repositorio.** Solo `.env.example` con valores ficticios. `.gitignore` excluye `.env`, llaves y JSON de cuentas de servicio; la CI ejecuta gitleaks.
2. **Identidad antes que claves.** En la nube se usa `az login`, Application Default Credentials de Google y perfiles SSO de AWS. En despliegues: identidades gestionadas, cuentas de servicio y roles de IAM.
3. **Mínimo privilegio.** Cada laboratorio indica los roles mínimos. No use cuentas de propietario para ejecutar código.
4. **Servicios locales en 127.0.0.1.** Ollama no tiene autenticación: nunca `OLLAMA_HOST=0.0.0.0`.
5. **Logging seguro.** Los backends registran métricas y longitudes, no el contenido de las conversaciones.
6. **Herramientas de agentes de solo lectura** en los laboratorios. Ninguna herramienta escribe en sistemas externos.

## Si un secreto se filtra

1. Revóquelo de inmediato en la consola del proveedor.
2. Elimínelo del historial (`git filter-repo`) y fuerce el push con acuerdo del equipo.
3. Revise los registros de uso del proveedor durante la ventana de exposición.

## Referencias

- OWASP Top 10 for LLM Applications 2025.
- Documentación de identidad de cada proveedor (Microsoft Entra ID, Google Cloud IAM, AWS IAM).
