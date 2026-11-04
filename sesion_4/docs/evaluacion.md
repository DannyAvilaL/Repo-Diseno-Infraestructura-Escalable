# Evaluación — Sesión 4 (preguntas para estudiantes)

1. Explique por qué el balanceo por conexiones no equilibra trabajo en LLM y proponga una alternativa.
2. Describa la diferencia entre respuesta 429 y 503 en el gateway y su efecto sobre el SLO.
3. Calcule los pesos de un modelo de 8 000 M de parámetros en INT8 y explique por qué no basta para dimensionar la GPU.
4. Enumere los términos del cold start y una palanca para cada uno.
5. ¿Por qué se usa StatefulSet con volumeClaimTemplates y no Deployment con un PVC RWO?
6. ¿Por qué la profundidad de cola es mejor señal que la utilización de GPU?
7. Explique la curva 1/(1−ρ) y su implicación en la utilización objetivo.
8. Compare time-slicing, MIG y GPU entera en aislamiento y caso de uso.
9. ¿Qué agrega DRA frente al device plugin? ¿Qué riesgo de adopción tiene?
10. Identifique tres controles contra consumo ilimitado (OWASP LLM10:2025).
11. ¿Cómo mitigaría el SSRF hacia el endpoint de metadatos?
12. Construya la ecuación de costo por 1M tokens e indique la palanca principal.

**Rúbrica del informe** (resumen público): exactitud conceptual 30 %, justificación de decisiones y trade-offs 25 %, evidencia medida vs supuestos 20 %, seguridad 15 %, reproducibilidad 10 %. Solucionario y rúbrica detallada: repo privado.
