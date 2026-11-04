# Guía docente — Sesión 4 (180 min)

Las notas detalladas, con tiempos y respuestas esperadas, están en las **notas del expositor** del PPTX. Esta guía resume el plan.

| Min | Bloque | Diapositivas | Idea que debe quedar |
|---|---|---|---|
| 0–14 | Apertura, caso, idea central | 1–5 | Capacidad finita, demanda variable |
| 14–46 | Redes | 6–16 | Balancear trabajo, no conexiones; backpressure; Zero Trust |
| 46–71 | Almacenamiento | 17–24 | Pesos = parámetros × bytes; cold start; PVC por réplica |
| 71–81 | Descanso | 25 | — |
| 81–108 | Autoscaling | 26–34 | Señal = cola; Little; estabilidad |
| 108–133 | GPU | 35–41 | Entera / MIG / time-slicing / DRA; costo por 1M tokens |
| 133–173 | Seguridad, demos, labs | 42–46 | Predecir → medir |
| 173–180 | Cierre | 47–53 | ADR, síntesis, evaluación |

Distribución: ~65 % teoría, ~25 % demos, ~10 % discusión (ajustada al descanso).

## Preparación previa (obligatoria)
1. Ejecutar `labs/00-ollama-local` y anotar SUS mediciones (no hay valores de referencia en el material).
2. Ejecutar al menos el laboratorio Azure (demo en vivo comienza por Azure) y confirmar modelo/región.
3. Confirmar el ID de modelo Gemini vigente en Vertex AI.
4. Estudiantes: cuentas de prueba (sin pasar a pago por uso).

## Errores frecuentes de los estudiantes
- Escalar por CPU/GPU en lugar de cola.
- Confundir usuarios concurrentes con generaciones concurrentes (think time).
- Creer que la VRAM se «escala verticalmente» en caliente.
- Pensar que time-slicing aísla memoria.
- Poner pesos dentro de la imagen del contenedor.
- Dejar el puerto del servidor de inferencia expuesto o el egress abierto.
- Presentar un cálculo teórico como resultado medido.

## Analogías sugeridas
Cola acotada = restaurante que no acepta más mesas de las que su cocina soporta; cold start = abrir una cocina nueva (local, equipo, ingredientes, calentar); DRA = pedir almacenamiento con PVC pero para dispositivos.
