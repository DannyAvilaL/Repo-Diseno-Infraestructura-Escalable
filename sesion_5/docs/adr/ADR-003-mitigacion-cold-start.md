# ADR-003: Mitigación de cold start por capas
**Decisión:** (1) inicialización fuera del handler, (2) SnapStart/min-instances/always-ready solo donde el SLO lo exija, (3) keep_alive en inferencia autogestionada. **Trade-off:** costo fijo vs latencia de cola. **Evidencia local:** `experiments/results.md` (simulada).
