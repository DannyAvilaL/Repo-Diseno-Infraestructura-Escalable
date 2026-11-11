# ADR-002: Caché de respuestas solo con temperature=0 y clave por tenant
**Estado:** aceptada. **Decisión:** `make_cache_key` incluye tenant, modelo, parámetros y prompt normalizado. **Consecuencias:** + costo/latencia; − riesgo de respuestas obsoletas (TTL) y fuga entre tenants si se omite el tenant en la clave.
