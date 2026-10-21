# Evaluación · Sesión 1

Las respuestas esperadas están en el repositorio del docente.

## A. Cuestionario de cierre (formativo, 5 preguntas, 6 minutos)

1. Al anteponer un documento largo a la pregunta, ¿qué métrica aumenta principalmente y por qué?
   a) TPOT, porque el decode procesa el documento · b) TTFT, porque el prefill procesa más tokens · c) Throughput, porque aumenta el lote · d) Ninguna
2. ¿Qué limita con mayor frecuencia la concurrencia de un servidor LLM autogestionado?
   a) Núcleos de CPU · b) Memoria de GPU ocupada por la KV cache · c) Ancho de banda de red · d) Disco
3. Un SLO de 99,9 % mensual admite aproximadamente:
   a) 4 min · b) 43 min · c) 7 h · d) 1 día
4. ¿Cuál es la relación correcta entre Strands Agents y Amazon Bedrock AgentCore?
   a) Son equivalentes · b) Strands es un SDK para escribir el agente; AgentCore incluye un runtime gestionado donde ejecutarlo · c) AgentCore es un modelo · d) Strands reemplaza a Bedrock
5. En un RAG institucional, ¿con qué identidad debe filtrarse la recuperación de documentos?
   a) La del backend · b) La del administrador · c) La del usuario final · d) Ninguna, el modelo filtra

## B. Preguntas de comprensión

1. Explique la diferencia entre prefill y decode en términos de recurso dominante y métrica asociada.
2. ¿Por qué la cuantización de los pesos no resuelve por sí sola la falta de memoria con alta concurrencia?
3. Distinga entre entrenamiento, fine-tuning e inferencia en recursos y frecuencia.

## C. Preguntas de análisis arquitectónico

1. Identifique tres puntos únicos de fallo en la arquitectura de referencia y proponga una mitigación para cada uno.
2. Compare streaming y procesamiento asíncrono con cola para (a) la conversación y (b) el resumen de un documento de 200 páginas.
3. Analice qué responsabilidades conserva la universidad si usa un runtime gestionado de agentes.

## D. Casos de selección tecnológica

1. **Caso D1.** Una universidad con 500 usuarios, uso esporádico, sin equipo de plataforma y con la identidad institucional en Microsoft Entra ID. Proponga la modalidad de inferencia y los servicios.
2. **Caso D2.** Un hospital universitario con datos clínicos que no pueden salir de su red y un volumen alto y sostenido. Proponga la modalidad y justifique.
3. **Caso D3.** Un equipo que desarrolló un agente con LangGraph y quiere desplegarlo de forma gestionada en Azure sin reescribirlo. ¿Qué opción tiene y qué limitaciones debe verificar?

## E. Ejercicios de dimensionamiento

1. Modelo de 8 B (32 capas, 8 kv_heads, d_head 128), FP16, 40 secuencias activas de 4.096 tokens. Calcule pesos, KV cache, total con 15 % de margen y la clase de GPU.
2. 200 usuarios concurrentes que preguntan una vez por minuto, con 2.000 tokens de entrada y 400 de salida. Calcule solicitudes por segundo y tokens por minuto.
3. Un servicio tarda en promedio 4 s por solicitud y recibe 5 solicitudes/s. ¿Cuántas solicitudes están en curso según la ley de Little?
