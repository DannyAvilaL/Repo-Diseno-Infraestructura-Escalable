# Solucionario (PRIVADO — mover a `llm-infra-escalable-docente`)

1. Una conexión no equivale a una unidad de trabajo (generaciones de 20 vs 2000 tokens). Alternativa: balanceo L7 por solicitud, por cola/KV cache (consciente del modelo), limitar max_tokens.
2. 429 = cola llena (rechazo inmediato); 503 = expiró espera en cola. Ambos son degradación controlada; sostenidos indican falta de capacidad.
3. 8 GB (INT8). Faltan KV cache, activaciones y margen; el KV cache fija la concurrencia por réplica.
4. T_nodo (pods «pause»), T_imagen (imagen pequeña, caché), T_pesos (volumen poblado/NVMe), T_VRAM (keep-alive), T_warm-up (solicitud sintética).
5. RWO impide montar el mismo volumen en nodos distintos; StatefulSet crea un PVC por réplica con identidad estable.
6. Mide demanda insatisfecha; la utilización de GPU es alta aun con carga sana y no distingue saturación.
7. Cerca de ρ=1 la espera se dispara; operar a utilización objetivo con margen y cola acotada.
8. Time-slicing: sin aislamiento de memoria (dev); MIG: aislamiento fuerte (multiinquilino); entera: producción con SLO.
9. Selección por atributos, config por reclamo, base para compartición fina; riesgo: complejidad y madurez desigual de drivers; no mezclar con device plugin en el mismo nodo.
10. Cola acotada, límite de max_tokens, cuotas por usuario, máximo de réplicas.
11. Bloquear 169.254.169.254 por NetworkPolicy, identidad de carga de trabajo, validar URLs salientes.
12. USD/1M = USD_GPU_h ÷ (tok/s × 3600 × util) × 10⁶; palanca: utilización.

Ejercicios guía: (1) 26/13/6,5 GB. (2) λ = 200/75 ≈ 2,67/s; L = 2,67×25 ≈ 67; capacidad por réplica 3×0,7 = 2,1; ≈ 32 réplicas, 33 con N+1.
