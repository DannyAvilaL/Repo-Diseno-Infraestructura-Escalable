# E5.6.1 · Agente simple desde el portal de Microsoft Foundry (**demo en vivo: inicia con Azure**)

**Estado:** guion de portal; la interfaz y los nombres de menús cambian con frecuencia: valida el día previo con tu cuenta de prueba.
## Pasos (≈15 min)
1. Portal de Foundry → crear/seleccionar **proyecto** (crea grupo de recursos y recurso de Foundry).
2. **Model catalog** → desplegar un modelo de chat disponible en la región (anota el *deployment name*).
3. **Agents → New agent**: nombre `soporte-demo`; instrucciones del ejemplo `common.py`; modelo = tu deployment.
4. Agregar herramienta (p. ej. *Code interpreter* o función) y probar en el **Playground**.
5. Revisar **Traces/Monitoring** (latencia por llamada, tokens).
6. Copiar el **project endpoint** para usarlo en E5.6.2.
## Qué observar
Qué es administrado (hilos, ejecución de herramientas) vs. lo que controlas en código.
## Seguridad
RBAC con identidades de Entra ID; evita claves; content filters del despliegue. **Costos:** tokens + herramientas usadas; sin cifras. **Limpieza:** eliminar agente, deployment y el grupo de recursos.
## Reflexión
¿Qué pierdes de portabilidad al usar un agente administrado frente a un framework de código abierto?
