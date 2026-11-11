# Seguridad en LLMs serverless (mapeo a controles del repositorio)

Marco: OWASP Top 10 for LLM Applications (edición vigente al preparar el material; **verificar versión y numeración** en https://genai.owasp.org), OWASP Agentic Top 10, NIST AI RMF 1.0 y NIST AI 600-1, ISO/IEC 42001.

| Riesgo (categoría) | Control en `src/serverless_llm` | Límite conocido |
|---|---|---|
| Prompt injection | `InputGuard` (normalización NFKC, regex ES/EN, política off/flag/block) | Heurística: no sustituye guardrails gestionados ni separación de privilegios |
| Divulgación de información sensible | `redact_pii`, logs con `fingerprint` | Regex no cubre todo PII |
| Manejo inseguro de salida | `sanitize_output` (quita imágenes markdown externas y HTML activo) | En streaming, patrones partidos entre chunks pueden escapar |
| Consumo desmedido / DoS de costo | límites de prompt/tokens, rate limit por tenant, semáforo + 429 | Rate limit en memoria: usar almacén compartido en multi-instancia |
| Autenticación | API keys en tiempo constante; rechazo de clave por defecto fuera de `local` | En nube: IAM/JWT, no API keys |
| Aislamiento multi-tenant | clave de caché y jobs por tenant | — |
| Agencia excesiva | herramientas con mínimo privilegio (labs), límite de pasos | Requiere aprobación humana en acciones sensibles |
Responsabilidad compartida: el proveedor protege la plataforma; tú, identidades, datos, prompts, herramientas y configuración.
