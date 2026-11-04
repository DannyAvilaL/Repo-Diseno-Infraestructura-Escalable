# ADR-003 — StatefulSet con un PVC por réplica y pesos fuera de la imagen
**Estado:** Aceptada · **Fecha:** 2026-11-03
**Contexto:** los volúmenes RWO no se comparten entre réplicas; los pesos pesan GB y cambian a ritmo distinto del código.
**Decisión:** `StatefulSet` + `volumeClaimTemplates`; initContainer descarga el modelo en el primer arranque; imagen del gateway pequeña.
**Alternativas:** RWX compartido (una copia; riesgo de rendimiento/bloqueos); pesos en la imagen (arranque más pesado, imágenes enormes); streaming desde objetos al arrancar.
**Consecuencias:** + aislamiento y simplicidad; − almacenamiento duplicado por réplica y primer arranque lento. En producción: sustituir la descarga pública por almacenamiento de objetos privado.
