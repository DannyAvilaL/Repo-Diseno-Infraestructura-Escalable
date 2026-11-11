# FinOps serverless para LLMs (fórmulas; sin precios inventados)

- Costo por solicitud LLM = tokens_in·P_in + tokens_out·P_out (precios del proveedor vigentes).
- Costo serverless de cómputo ≈ GB·s·P_gbs + invocaciones·P_inv.
- Con caché con tasa de acierto h: costo_efectivo = (1−h)·costo_LLM + h·costo_caché.
- Break-even serverless vs autogestionado con GPU: N* = Costo_fijo_mensual_GPU / costo_variable_por_solicitud_serverless (solicitudes/mes sobre las cuales el fijo se amortiza). Rellena con precios vigentes del día.
- Palancas: caché, modelos más pequeños, límite de max_tokens, batching asíncrono, min-instances solo si el costo de cold start > costo de la reserva.
- Controles: presupuestos y alertas por cuenta, etiquetas por tenant, límites de concurrencia.
