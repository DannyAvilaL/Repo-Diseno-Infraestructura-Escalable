# E5.5.1 · Agente simple desde la consola de Amazon Bedrock

**Estado:** guion de consola. La interfaz cambia con frecuencia: valida los nombres de menús el día previo.

## Pasos (≈15 min)
1. Consola AWS → región con Bedrock → **Bedrock → Agents → Create agent**.
2. Nombre `sllm-agente-demo`; modelo: uno habilitado en *Model access*.
3. **Instructions for the agent:** "Eres un asistente conciso que responde en español. Si no sabes, dilo."
4. Crear rol de servicio nuevo (revisar que solo tenga permiso sobre el modelo elegido).
5. **Add action group** (opcional): *Define with function details* → función `consultar_estado(pedido_id: string)` → Lambda nueva (el asistente de consola genera una plantilla; devuelve datos ficticios).
6. **Prepare** → probar en el panel *Test*; activar **Trace** y observar *Orchestration* y *Pre/Post-processing*.
7. Crear **Alias** y probar con el mismo panel.
## Qué observar (conexión con slides)
Cold start de la Lambda del action group; trazas de razonamiento; tokens consumidos.
## Seguridad
Guardrails de Bedrock (asociar uno al agente); no uses datos reales.
## Costos
Por tokens y por invocaciones Lambda; sin cifras aquí.
## Limpieza
Eliminar alias, agente, Lambda del action group, rol IAM y log groups.
## Reflexión
¿Qué parte del flujo del agente es determinista y cuál no? ¿Dónde pondrías un límite de pasos?
