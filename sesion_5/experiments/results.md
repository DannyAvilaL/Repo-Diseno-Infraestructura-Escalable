# Resultados de los experimentos de la Sesión 5 (SIMULADOS)

- Máquina: Linux-6.18.44-fc-v338-x86_64-with-glibc2.39 · CPU lógicas: 2 · Python 3.12.13
- Proveedor: `mock` (cold start simulado 1,5 s; TTFT 120 ms; TPOT 15 ms)


## E1 · Cold start: lazy vs eager

| Estrategia | 1ª petición (ms) | 2ª (ms) | 3ª (ms) | 4ª (ms) | 5ª (ms) |
|---|---|---|---|---|---|
| Lazy init (sin mitigación) | 1708 | 183 | 185 | 184 | 184 |
| Eager init (precarga en arranque) | 186 | 184 | 184 | 183 | 184 |


## E2 · Efecto del caché

| Escenario | Peticiones | Concurrencia | RPS | p50 ms | p95 ms | p99 ms | Caché | Error | Códigos |
|---|---|---|---|---|---|---|---|---|---|
| Pool 1000 prompts (≈0 % repetición) | 400 | 16 | 33.11 | 480.1 | 484.2 | 508.9 | 0% | 0% | {'200': 400} |
| Pool 50 prompts | 400 | 16 | 209.53 | 13.9 | 481.6 | 503.6 | 88% | 0% | {'200': 400} |
| Pool 5 prompts | 400 | 16 | 424.64 | 23.4 | 82.9 | 274.5 | 99% | 0% | {'200': 400} |


## E3 · Backpressure (40 clientes concurrentes, capacidad 4)

| Escenario | Peticiones | Concurrencia | RPS | p50 ms | p95 ms | p99 ms | Caché | Error | Códigos |
|---|---|---|---|---|---|---|---|---|---|
| Sin límite de espera (cola crece) | 200 | 40 | 16.53 | 2406.5 | 2411.8 | 2458.6 | 0% | 0% | {'200': 200} |
| Backpressure (espera ≤ 0,3 s) | 200 | 40 | 101.88 | 320.8 | 509.5 | 543.4 | 0% | 84% | {'200': 32, '429': 168} |

