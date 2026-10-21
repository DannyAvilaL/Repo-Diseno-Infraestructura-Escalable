# Rúbrica del taller y la tarea · Topología base

Escala: 4 = Excelente · 3 = Satisfactorio · 2 = En desarrollo · 1 = Insuficiente. Nota = suma ponderada sobre 4.

| Criterio (peso) | 4 · Excelente | 3 · Satisfactorio | 2 · En desarrollo | 1 · Insuficiente |
| --- | --- | --- | --- | --- |
| Componentes y flujos (20 %) | ≥ 8 componentes con responsabilidades claras, plano de control y de datos, flujos de consulta e ingesta | ≥ 8 componentes y flujo de consulta correcto | Faltan componentes críticos (identidad u observabilidad) | Diagrama sin flujos o con errores conceptuales |
| Decisión gestionado vs. autogestionado (20 %) | ADR con ≥ 3 criterios, alternativas y consecuencias con mitigaciones | ADR con 3 criterios y una alternativa | Decisión con 1–2 criterios | Decisión sin justificación |
| Cómputo, memoria y red (15 %) | Estimación correcta de memoria o tokens/min, HA multizona y red privada justificadas | Estimación con errores menores; HA considerada | Estimación incompleta o sin HA | Sin dimensionamiento |
| Seguridad (20 %) | ≥ 5 riesgos OWASP con control concreto; identidad sin secretos; filtrado por permisos en RAG | 5 riesgos con controles generales | 2–4 riesgos | Sin análisis de seguridad |
| Rendimiento y costo (15 %) | SLI y SLO medibles con percentiles; costo de orden de magnitud sin inventar precios; prácticas FinOps | SLO y costo cualitativo correcto | SLO sin indicador medible | Sin métricas ni costo |
| Comunicación (10 %) | Exposición clara en 3 min; supuestos explícitos | Clara con supuestos parciales | Confusa | No presenta |
