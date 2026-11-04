# Guía del estudiante — Sesión 4

## Marco conceptual
Un servidor de inferencia tiene **capacidad finita** (slots de concurrencia, VRAM para KV cache). La infraestructura reconcilia esa capacidad con una demanda variable mediante: red (reparte y protege), almacenamiento (pesos listos), autoscaling (ajusta oferta) y planificación de GPU (asigna lo escaso).

## Glosario
- **TTFT**: tiempo hasta el primer token. **TPOT**: tiempo por token de salida.
- **KV cache**: claves/valores de tokens previos reutilizados en decodificación; crece con contexto × concurrencia.
- **Backpressure / load shedding**: limitar la entrada y rechazar explícitamente (429/503) para proteger la latencia.
- **Cold start**: tiempo hasta que una réplica nueva está lista (nodo + imagen + pesos + VRAM + warm-up).
- **HPA / KEDA / VPA / Cluster Autoscaler**: escalado horizontal, por eventos/métricas externas, vertical y de nodos.
- **Device plugin / DRA / MIG / MPS / time-slicing**: mecanismos de exposición y compartición de GPU.
- **RWO / RWX**: modos de acceso de volúmenes (un nodo / varios).

## Fórmulas
- Pesos ≈ parámetros × bytes por parámetro (FP16 = 2, INT8 = 1, INT4 ≈ 0,5).
- Ley de Little: L = λ · W.
- Costo por 1M tokens = USD_GPU_hora ÷ (tok/s × 3600 × utilización) × 10⁶.
- Cold start: T_listo = T_nodo + T_imagen + T_pesos + T_VRAM + T_warm-up.

## Ejercicios
1. Calcule los GB de pesos de un modelo de 13 000 M de parámetros en FP16, INT8 e INT4.
2. Con 200 usuarios concurrentes, 25 s por generación y 50 s de lectura, estime L (generaciones simultáneas). Con 3 generaciones por réplica y utilización objetivo 70 %, ¿cuántas réplicas (más N+1)?
3. Mida con `loadtest.py` la concurrencia a la que aparece cola en su máquina y calcule su costo por 1M tokens con un precio vigente que usted consulte.
4. Escriba la política de autoscaling (señal, umbral, ventanas, mínimo, máximo) y justifíquela.
5. Diseñe la NetworkPolicy conceptual del caso e identifique la deuda de egress.

## Autoevaluación
Ver `evaluacion.md` (preguntas). Las respuestas están en el repositorio privado del docente.

## Lecturas
Ver `bibliografia.md`.
