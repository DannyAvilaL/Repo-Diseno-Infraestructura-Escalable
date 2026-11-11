# E5.7.1 · Agente simple desde la consola de Google Cloud

**Estado:** guion de consola; la plataforma de agentes de Google Cloud fue renombrada y evoluciona rápido (Agent Studio / Agent Designer). Valida nombres de menús el día previo.

1. Consola → proyecto de prueba → habilitar APIs de IA solicitadas por el asistente.
2. Abrir el estudio de agentes (Agent Studio / Agent Designer) → **Crear agente**.
3. Nombre `sllm-agente-demo`, modelo Gemini disponible, instrucciones: "Responde en español de forma breve".
4. Agregar una herramienta de ejemplo (búsqueda/grounding o función) y probar en el panel de chat; revisar trazas.
5. Desplegar/exponer según opción ofrecida (Agent Runtime) y probar una invocación.
**Seguridad:** rol de servicio mínimo; sin datos reales. **Costos:** tokens + runtime; sin cifras aquí. **Limpieza:** eliminar agente, runtime y buckets asociados.
**Reflexión:** ¿qué controlas más en consola vs código (versionado, pruebas, CI/CD)?
