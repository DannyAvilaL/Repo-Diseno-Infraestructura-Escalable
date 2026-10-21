# Sesión 1 · Fase 1: Planeación académica

Curso: Diseño de Infraestructura Escalable para LLMs · Capítulo 1, Sesión 1: Arquitecturas Base para LLMs en la Nube · Oct 13, 2026 · @Andres Rojas

## Resumen ejecutivo y alertas de vigencia

La Sesión 1 es viable en 180 minutos solo si se reduce a un objetivo arquitectónico único —diseñar y justificar una topología base de inferencia— y se trasladan los 13 laboratorios multicloud al repositorio como material complementario. En vivo se ejecutan tres demostraciones cortas (Ollama local, una llamada gestionada y un agente gestionado) y un taller de diseño sobre el caso universitario.

La verificación de fuentes (13-oct-2026) obliga a ajustar cuatro supuestos del prompt maestro antes de producir materiales:

| Supuesto del prompt | Estado verificado | Impacto en el diseño |
| --- | --- | --- |
| “Vertex AI” como plataforma de Google | En Cloud Next 2026 (22-abr-2026) Vertex AI se renombró como **Gemini Enterprise Agent Platform**; sus servicios continúan dentro de la nueva plataforma ([HPCwire](https://www.hpcwire.com/aiwire/2026/04/23/google-unveils-gemini-enterprise-agent-platform/)). | Usar el nombre nuevo, mencionar “antes Vertex AI”. Verificar en Fase 5 la ruta de consola (Agent Studio) y el nombre vigente de Agent Engine/Agent Runtime. |
| Semantic Kernel y AutoGen como frameworks equivalentes | Microsoft Agent Framework 1.0 es GA desde el 3-abr-2026 para .NET y Python, y es el sucesor de ambos ([Microsoft DevBlogs](https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/)). SK y AutoGen quedan en modo mantenimiento ([Visual Studio Magazine](https://visualstudiomagazine.com/articles/2026/04/06/microsoft-ships-production-ready-agent-framework-1-0-for-net-and-python.aspx)). | Labs de SK y AutoGen se presentan como **legado y ruta de migración**, no como alternativas para proyectos nuevos. |
| Foundry Agent Service | Soporta prompt agents, workflow agents y hosted agents; el framework de los hosted agents puede ser Agent Framework, LangGraph o código propio ([Microsoft Learn](https://learn.microsoft.com/azure/foundry/agents/overview)). Hosted Agents figura como GA en la documentación de hosting ([Microsoft Learn](https://learn.microsoft.com/en-us/agent-framework/hosting/foundry-hosted-agent)). | LangGraph en Azure se enmarca como “framework externo alojado en Foundry”, no como framework oficial de Microsoft. |
| “Crear agente desde Amazon Bedrock” (Bedrock Agents) | Bedrock Agents pasó a llamarse **Agents Classic**, en modo mantenimiento y cerrado a clientes nuevos desde el 30-jul-2026; AWS recomienda AgentCore para desarrollo nuevo ([AWS Docs](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-classic-maintenance-mode.html)). | Las cuentas de estudiantes serán nuevas: el laboratorio de consola de AWS debe construirse sobre **AgentCore**, no sobre Agents Classic. |

Estas alertas son hechos documentados a la fecha; los nombres de consola y las rutas exactas de cada laboratorio se reverifican en la Fase 5, porque los tres proveedores están publicando cambios mensuales.

## 1. Análisis crítico del alcance y los objetivos

El alcance declarado (6 unidades, 45 temas, 13 laboratorios, 3 nubes) equivale a 3 o 4 sesiones de 3 horas. La sesión debe priorizar **profundidad en los fundamentos** que todas las sesiones posteriores reutilizan, y tratar el resto como “introducción con anclaje”: se nombra, se ubica en el diagrama de referencia y se remite a la sesión o laboratorio que lo desarrolla.

### Fortalezas del planteamiento

- El objetivo de desempeño (diseñar una topología base) es verificable con un producto concreto: un diagrama justificado.
- El caso universitario transversal permite comparar nubes con supuestos homogéneos.
- La orientación “teoría en diapositivas, código en el repositorio” responde directamente a la retroalimentación de los estudiantes.

### Riesgos detectados y decisión propuesta

| Riesgo | Evidencia | Decisión de planeación |
| --- | --- | --- |
| Sobrecarga de contenidos | 45 temas en \~117 min de teoría dan menos de 3 min por tema | Tres niveles de profundidad: **N1 dominio** (inferencia, componentes, managed vs. self-hosted, dimensionamiento de memoria), **N2 comprensión** (multicloud, seguridad, métricas), **N3 exposición** (RAG, agentes, Kubernetes avanzado) |
| Laboratorios en vivo de 3 nubes | Cada consola exige cuenta, cuotas, IAM y acceso a modelos | En vivo solo demostraciones de 5–12 min preparadas por el docente; los labs completos quedan en GitHub |
| Volatilidad de servicios | Ver alertas: renombres y cambios de estado en 2026 | Las diapositivas enseñan **categorías de servicio** (gateway de modelos, runtime de agentes, vector store); los nombres comerciales viven en una tabla de mapeo fechada y actualizable |
| Agentes antes de fundamentos | El ecosistema empuja a empezar por frameworks agenticos | RAG y agentes se presentan como **cargas de trabajo** con requisitos de infraestructura distintos, no como tema de programación; su desarrollo profundo va a sesiones posteriores |
| Acceso desigual a hardware | No se puede asumir GPU NVIDIA | Laboratorio Ollama con ruta CPU-only y modelos de 0,5–4 B parámetros cuantizados (modelo exacto a confirmar en Fase 6) |
| Costos inesperados para estudiantes | Servicios gestionados facturan por token y por recurso | Cada lab declara costo estimado, límites de presupuesto y procedimiento de limpieza obligatorio |

### Ajuste del objetivo de desempeño

Se propone una redacción más medible: *“Al final de la sesión, el estudiante diseña, en equipo, una topología base para el asistente universitario que identifique al menos ocho componentes, ubique los límites de red y de confianza, y justifique por escrito la elección entre inferencia gestionada y autogestionada con al menos tres criterios (costo, control de datos, operación).”*

### Supuestos académicos del caso

Los parámetros del caso (5.000 usuarios, 100 concurrentes, 99,9 %) son **hipótesis de diseño**, no mediciones. Un 99,9 % mensual equivale a unos 43 minutos de indisponibilidad al mes; se usará este cálculo para introducir presupuesto de error en la Unidad F.

## 2. Estructura de los 180 minutos

La sesión se organiza en seis bloques teóricos, cuatro demostraciones cortas y un taller final, con una pausa de 10 minutos. Sobre los 170 minutos efectivos, la distribución resultante es **66 % teoría (112 min), 22 % demostraciones (38 min) y 12 % discusión y evaluación (20 min)**. Se cede un 3 % de demostración al taller porque el objetivo de desempeño es de diseño, no de implementación.

| Minuto | Bloque | Tipo | Propósito y actividad | RA |
| --- | --- | --- | --- | --- |
| 0:00–0:07 | Apertura: el problema del asistente universitario | Teoría (7) | Presentar el caso, la pregunta guía “¿qué debe existir entre el usuario y el modelo?” y los resultados de aprendizaje | — |
| 0:07–0:32 | Unidad A · Fundamentos de inferencia | Teoría (25) | Tokens, context window, prefill/decode, KV cache, batching; entrenamiento vs. fine-tuning vs. inferencia; modelos propietarios vs. open-weight | RA1 |
| 0:32–0:42 | Demo 1 · Anatomía de una solicitud con Ollama | Demostración (10) | Inferencia local en CPU; observar TTFT, tokens/s y consumo de RAM; mostrar el efecto de un prompt largo sobre el prefill | RA1, RA5 |
| 0:42–1:04 | Unidad B · Arquitecturas base | Teoría (22) | Componentes de referencia, plano de control vs. plano de datos, patrones síncrono/streaming/asíncrono, puntos únicos de fallo; RAG y agentes como cargas de trabajo | RA2 |
| 1:04–1:12 | Demo 2 · Misma API, dos backends | Demostración (8) | Backend FastAPI con streaming apuntando a Ollama y luego a un modelo gestionado; comparar latencia y responsabilidades | RA3, RA5 |
| 1:12–1:22 | Pausa | — | — | — |
| 1:22–1:42 | Unidad C · Infraestructura | Teoría (20) | CPU vs. GPU, VRAM, cuantización, ejemplo resuelto de dimensionamiento de memoria, red privada, almacenamiento y vector stores, Docker/Kubernetes/serverless, multizona | RA4 |
| 1:42–1:56 | Unidad D · Comparación multicloud | Teoría (14) | Mapa de categorías de servicio en AWS, Azure y Google Cloud; responsabilidades operativas; criterios de selección | RA3, RA6 |
| 1:56–2:08 | Demo 3 · Un agente gestionado en consola | Demostración (12) | Recorrido en una sola nube (rotativa entre cohortes): identidad, modelo, instrucciones, herramienta, traza; señalar dónde están los límites de confianza | RA3, RA7 |
| 2:08–2:22 | Unidad E · Seguridad | Teoría (14) | Responsabilidad compartida, identidad sin secretos estáticos, aislamiento de red, OWASP LLM Top 10 2025 y riesgos agenticos, guardrails, auditoría | RA7 |
| 2:22–2:32 | Unidad F · Rendimiento y FinOps | Teoría (10) | Latencia end-to-end, TTFT, TPOT, throughput, saturación; SLI/SLO/SLA y presupuesto de error; costo por token vs. costo por hora de GPU | RA5, RA8 |
| 2:32–2:40 | Demo 4 · Concurrencia vs. latencia | Demostración (8) | Prueba de carga breve contra el backend local; observar la cola y el crecimiento de TTFT al subir la concurrencia | RA5 |
| 2:40–2:54 | Taller · Topología base del asistente | Discusión (14) | Equipos de 3–4 dibujan la topología y eligen managed vs. self-hosted; dos equipos exponen 3 minutos cada uno | RA6, RA8 |
| 2:54–3:00 | Cierre y evaluación formativa | Discusión (6) | Cuestionario de 5 preguntas, síntesis y conexión con la Sesión 2 | Todos |

**Plan de contingencia.** Si una demo falla (red, cuota, credenciales), el docente usa la grabación preparada y las capturas del laboratorio; si el tiempo se comprime, la Demo 4 se convierte en un resultado pregrabado y la Unidad D se reduce a la tabla de mapeo.

## 3. Resultados de aprendizaje medibles

Ocho resultados de aprendizaje (RA) cubren la sesión; cada uno tiene un verbo observable de la taxonomía de Bloom revisada, un criterio de logro y una evidencia que el docente puede calificar.

| RA | Al finalizar, el estudiante podrá… | Nivel Bloom | Criterio de logro | Evidencia |
| --- | --- | --- | --- | --- |
| RA1 | Explicar el ciclo de vida de una solicitud de inferencia, desde la tokenización hasta la respuesta en streaming, diferenciando prefill, decode y el papel de la KV cache | Comprender | Describe las fases en orden y relaciona cada una con un recurso (cómputo o memoria) | Pregunta de cierre; diagrama anotado en la guía del estudiante |
| RA2 | Identificar los componentes de una arquitectura LLM empresarial y su responsabilidad, distinguiendo plano de control y plano de datos | Analizar | Ubica correctamente al menos 8 componentes y sus dependencias en un diagrama | Taller de topología |
| RA3 | Comparar inferencia gestionada (API de modelos) y autogestionada (self-hosting) mediante criterios de costo, control de datos, latencia, operación y portabilidad | Evaluar | Justifica una elección con al menos 3 criterios y reconoce 1 trade-off | Decisión escrita tipo ADR en el taller |
| RA4 | Estimar la memoria necesaria para servir un modelo según número de parámetros, precisión (cuantización), longitud de contexto y concurrencia | Aplicar | Calcula pesos + KV cache con error menor al 20 % frente al solucionario y elige una clase de hardware coherente | Ejercicio de dimensionamiento |
| RA5 | Interpretar TTFT, TPOT, throughput y latencia end-to-end, y explicar cómo la concurrencia y las colas los degradan | Analizar | Lee una tabla de resultados de carga y explica el punto de saturación | Pregunta sobre la salida de la Demo 4 |
| RA6 | Relacionar categorías de servicio (gateway de modelos, runtime de agentes, contenedores, serverless, vector store) con servicios equivalentes en AWS, Azure y Google Cloud | Analizar | Completa la tabla de mapeo sin confundir SDK, framework y servicio gestionado | Actividad de la guía del estudiante |
| RA7 | Identificar controles de seguridad por capa (identidad, red, datos, aplicación LLM, observabilidad) y asociarlos a riesgos del OWASP Top 10 para aplicaciones LLM 2025 | Analizar | Asocia al menos 5 riesgos con un control concreto cada uno | Matriz de amenazas del taller |
| RA8 | Diseñar una topología base para el asistente universitario que integre cómputo, red, almacenamiento, seguridad, un SLO y una estimación de costo de orden de magnitud | Crear | Cumple la rúbrica del taller con nivel “satisfactorio” o superior | Entregable del taller + tarea posterior |

RA1–RA5 se evalúan dentro de la sesión; RA6–RA8 se inician en la sesión y se completan con la tarea posterior y los laboratorios del repositorio.

## 4. Índice detallado de la presentación

La presentación tendrá **55 diapositivas**: 43 de contenido teórico, 4 de guión de demostración, 5 de apertura y cierre, 1 de taller y 2 de referencias. Cada unidad sigue el patrón del prompt maestro (problema → conceptos → explicación → gráfico → alternativas → trade-offs → ejemplo → recomendación). Ninguna diapositiva lleva más de 5 líneas de código; las notas del expositor amplían cada una con explicación, pregunta de discusión y referencia. Los códigos D-xx remiten al inventario de diagramas (sección 5).

| # | Diapositiva | Contenido clave | Visual |
| --- | --- | --- | --- |
| 1 | Portada | Curso, capítulo, sesión, docente, fecha | — |
| 2 | ¿Qué hay entre el usuario y el modelo? | Pregunta guía; caso del asistente universitario y sus supuestos | Ficha del caso |
| 3 | Resultados de aprendizaje y agenda | RA1–RA8, bloques y ubicación de la sesión en el curso | Agenda visual |
| **A** | **Fundamentos de inferencia** |  |  |
| 4 | Un LLM visto desde la infraestructura | Pesos, cómputo y memoria; por qué servir un modelo es un problema de ancho de banda | D-01 |
| 5 | Tokens y context window | Tokenización, token como unidad de costo y latencia; límites de contexto | Ejemplo tokenizado |
| 6 | Ciclo de vida de una solicitud | Del cliente a la respuesta: autenticación, prompt, tokenización, prefill, decode, streaming | D-02 |
| 7 | Prefill vs. decode | Fase limitada por cómputo vs. fase limitada por ancho de banda de memoria; relación con TTFT y TPOT | D-03 |
| 8 | KV cache | Qué almacena, cómo crece con contexto y concurrencia, por qué limita usuarios simultáneos | D-04 |
| 9 | Batching y concurrencia | Batching estático vs. continuo; throughput vs. latencia individual | D-05 |
| 10 | Entrenamiento, fine-tuning e inferencia | Perfiles de recursos, frecuencia y costo de cada actividad | Tabla comparativa |
| 11 | Propietarios, abiertos y open-weight | Diferencias de licencia, acceso a pesos y responsabilidades | Tabla comparativa |
| 12 | API vs. self-hosting: primera aproximación | Qué se compra y qué se opera en cada opción | Tabla de decisión |
| 13 | Demo 1 · Anatomía de una solicitud | Qué observar: TTFT, tokens/s, RAM, efecto del prompt largo | Captura de métricas |
| **B** | **Arquitecturas base** |  |  |
| 14 | Arquitectura de referencia | Cliente, API gateway, backend/orquestador, serving, modelo, datos, observabilidad | D-06 |
| 15 | Responsabilidad de cada componente | Función, falla típica y métrica clave por componente | Tabla |
| 16 | Plano de control vs. plano de datos | Qué se configura y qué transporta solicitudes; implicaciones de seguridad | D-07 |
| 17 | Monolítico vs. distribuido | Cuándo separar serving, orquestación y datos | Comparación gráfica |
| 18 | Espectro gestionado ↔ autogestionado | VM con GPU, Kubernetes, contenedores serverless, API de modelos, runtime de agentes | D-08 |
| 19 | Patrones de integración | Síncrono, streaming, asíncrono con cola, event-driven; tabla de decisión | D-09 |
| 20 | RAG como carga de trabajo | Ingesta vs. consulta; qué añade a la infraestructura | D-10 |
| 21 | Agentes como carga de trabajo | Bucle de razonamiento, herramientas, estado, ejecución larga; nuevos límites de confianza | D-11 |
| 22 | Puntos únicos de fallo y límites | Cuotas, rate limits, dependencia del proveedor, cuellos de botella | D-06 anotado |
| 23 | Demo 2 · Misma API, dos backends | Qué cambia y qué no al pasar de Ollama a un modelo gestionado | — |
| **C** | **Infraestructura** |  |  |
| 24 | CPU vs. GPU y jerarquía de memoria | Paralelismo, VRAM, RAM, disco y su ancho de banda | D-12 |
| 25 | Cómo dimensionar la memoria | Pesos = parámetros × bytes por parámetro; KV cache por token y por sesión | Fórmula |
| 26 | Ejemplo resuelto de dimensionamiento | Un modelo de tamaño medio en dos precisiones, con contexto y concurrencia del caso | Tabla de cálculo |
| 27 | Cuantización | Trade-off memoria, velocidad y calidad; cuándo es aceptable | Gráfico conceptual |
| 28 | Red | VPC/VNet, subredes privadas, endpoints privados, NAT, balanceadores | D-13 |
| 29 | Almacenamiento y vector stores | Objetos (pesos y documentos), volúmenes, base vectorial dedicada vs. extensión (pgvector) | Tabla de decisión |
| 30 | Docker, Kubernetes y serverless | Criterios: control, escalado a cero, GPU, carga operativa | Tabla de decisión |
| 31 | Alta disponibilidad | Multizona, multirregión, qué se replica en cada patrón | D-14 |
| 32 | Dos topologías de referencia | Topología gestionada vs. self-hosted lado a lado | D-15 |
| **D** | **Comparación multicloud** |  |  |
| 33 | Mapa de categorías de servicio | Tabla fechada: categoría → servicio en AWS, Azure y Google Cloud | D-16 |
| 34 | Google Cloud | Gemini Enterprise Agent Platform, ADK, Cloud Run, GKE | D-17 |
| 35 | Microsoft Azure | Microsoft Foundry, Agent Service, Agent Framework, Container Apps, AKS | D-18 |
| 36 | AWS | Amazon Bedrock, AgentCore, Strands, Lambda, ECS, EKS | D-19 |
| 37 | SDK, framework, runtime gestionado | No confundir capas: código del agente vs. dónde se ejecuta vs. qué modelo usa; legado vs. vigente | D-20 |
| 38 | Criterios de selección y lock-in | Portabilidad, estándares abiertos (MCP, A2A, OpenTelemetry), costo de salida | Matriz de criterios |
| 39 | Demo 3 · Agente gestionado en consola | Identidad, modelo, instrucciones, herramienta, traza | — |
| **E** | **Seguridad** |  |  |
| 40 | Responsabilidad compartida en LLM | Qué asegura el proveedor y qué la organización en cada modalidad | D-21 |
| 41 | Identidad sin secretos estáticos | Identidades gestionadas, workload identity, mínimo privilegio, RBAC | D-22 |
| 42 | Red y protección de datos | Aislamiento, cifrado, residencia de datos, Ley 1581 de 2012 (Colombia) | D-13 anotado |
| 43 | OWASP Top 10 LLM 2025 | Los 10 riesgos y su control de infraestructura | Matriz riesgo-control |
| 44 | Prompt injection y riesgos agenticos | Inyección directa e indirecta (RAG, herramientas); OWASP Top 10 para aplicaciones agenticas | D-23 |
| 45 | Defensa en profundidad | Guardrails de entrada y salida, auditoría, logging seguro, trazabilidad | D-24 |
| **F** | **Rendimiento y FinOps** |  |  |
| 46 | Latencia end-to-end | Desglose: red, gateway, recuperación, cola, prefill, decode | D-25 |
| 47 | TTFT, TPOT, throughput y saturación | Curva latencia vs. concurrencia; ley de Little como intuición | D-26 |
| 48 | SLI, SLO, SLA y presupuesto de error | 99,9 % mensual ≈ 43 min; qué SLI elegir para un asistente | Tabla |
| 49 | Costo por token vs. costo de infraestructura | Punto de equilibrio conceptual; costos ocultos de operar | D-27 |
| 50 | Demo 4 · Concurrencia vs. latencia | Lectura de resultados de la prueba de carga | Gráfico de resultados |
| **Cierre** |  |  |  |
| 51 | Taller · Topología base | Consignas, entregable y rúbrica resumida | Plantilla D-28 |
| 52 | Síntesis | Las siete decisiones de una topología base | Lista de decisiones |
| 53 | Próxima sesión y laboratorios | Conexión con la Sesión 2 y ruta de laboratorios en GitHub | QR al repositorio |
| 54–55 | Referencias | Documentación oficial, estándares y artículos (sección 8) | — |

## 5. Inventario de diagramas

Se requieren **28 diagramas**. Cada uno se produce una sola vez en dos formatos coherentes: forma nativa editable en PowerPoint para la presentación y fuente Mermaid en `docs/diagrams/` del repositorio, para que guías y laboratorios reutilicen exactamente la misma arquitectura. Los diagramas de nube usan iconografía neutral por categoría y el nombre comercial como etiqueta, de modo que un renombre solo cambia texto.

| Código | Diagrama | Tipo | Dónde se usa |
| --- | --- | --- | --- |
| D-01 | Un LLM como sistema: pesos, cómputo, memoria y E/S | Conceptual | Diap. 4, guía del estudiante |
| D-02 | Ciclo de vida de una solicitud de inferencia | Secuencia | Diap. 6, Demo 1, Lab Ollama |
| D-03 | Prefill vs. decode en el tiempo, con TTFT y TPOT marcados | Línea de tiempo | Diap. 7, Unidad F |
| D-04 | Crecimiento de la KV cache con contexto y sesiones concurrentes | Conceptual cuantitativo | Diap. 8, ejercicio de dimensionamiento |
| D-05 | Batching estático vs. continuo | Comparación temporal | Diap. 9 |
| D-06 | Arquitectura de referencia LLM empresarial (componente base de todo el curso) | Arquitectura | Diap. 14 y 22, taller, todas las sesiones |
| D-07 | Plano de control vs. plano de datos | Arquitectura por capas | Diap. 16 |
| D-08 | Espectro de responsabilidad gestionado ↔ autogestionado | Matriz de capas | Diap. 18, Unidad E |
| D-09 | Patrones síncrono, streaming, asíncrono y event-driven | Cuatro secuencias | Diap. 19 |
| D-10 | RAG: pipeline de ingesta y pipeline de consulta | Flujo | Diap. 20, sesiones posteriores |
| D-11 | Bucle de un agente con herramientas, memoria y límites de confianza | Flujo con bucle | Diap. 21, labs agenticos |
| D-12 | Jerarquía de memoria CPU/GPU y anchos de banda relativos | Conceptual | Diap. 24 |
| D-13 | Topología de red: subredes públicas y privadas, endpoints privados, NAT, balanceador | Red | Diap. 28 y 42 |
| D-14 | Despliegue multizona y alcance de una falla | Disponibilidad | Diap. 31 |
| D-15 | Topología gestionada vs. topología self-hosted del caso universitario | Arquitectura comparada | Diap. 32, taller, solucionario |
| D-16 | Mapa de categorías de servicio en las tres nubes | Matriz | Diap. 33, comparativo multicloud |
| D-17 | Arquitectura de referencia del caso en Google Cloud | Arquitectura cloud | Diap. 34, Lab GCP-C |
| D-18 | Arquitectura de referencia del caso en Azure | Arquitectura cloud | Diap. 35, Lab AZ-F |
| D-19 | Arquitectura de referencia del caso en AWS | Arquitectura cloud | Diap. 36, Lab AWS-D |
| D-20 | Capas: SDK/framework, runtime gestionado, servicio de modelos | Capas | Diap. 37, guía docente |
| D-21 | Responsabilidad compartida por modalidad de inferencia | Matriz | Diap. 40 |
| D-22 | Flujo de identidad sin secretos (usuario, workload, herramienta) | Secuencia | Diap. 41, labs cloud |
| D-23 | Inyección indirecta a través de un documento recuperado | Flujo de ataque | Diap. 44 |
| D-24 | Defensa en profundidad con controles por capa | Capas | Diap. 45, análisis de seguridad |
| D-25 | Desglose de latencia end-to-end | Barra apilada conceptual | Diap. 46 |
| D-26 | Latencia vs. concurrencia: zona estable, rodilla y saturación | Curva conceptual | Diap. 47, Demo 4 |
| D-27 | Costo por token vs. costo fijo de infraestructura según volumen | Curva conceptual | Diap. 49, FinOps |
| D-28 | Plantilla en blanco para la topología del taller | Plantilla | Diap. 51, guía del estudiante |

D-26 y D-27 son curvas **conceptuales**: no llevarán cifras hasta que existan mediciones propias o precios verificados en las fases 5 y 6.

## 6. Arquitectura inicial del repositorio GitHub

Se propone un **monorepo por sesiones y laboratorios**, con un contrato de API único para el asistente universitario que todos los backends implementan. Así, cambiar de Ollama a Bedrock, Foundry o Gemini cambia un adaptador y la configuración, no la aplicación, y la comparación multicloud se hace sobre la misma interfaz.

```
llm-infra-escalable/
├── README.md                      # Mapa del curso, rutas de aprendizaje, requisitos
├── LICENSE                        # Código y documentación (ver decisión pendiente)
├── .gitignore  .env.example  .pre-commit-config.yaml   # incluye detección de secretos
├── pyproject.toml  requirements.txt  Makefile
├── .github/workflows/ci.yml       # lint, tipos, pruebas unitarias; sin credenciales cloud
├── docs/
│   ├── 00-prerrequisitos.md
│   ├── 01-entorno-ubuntu-24.04-wsl.md
│   ├── 02-seguridad-y-secretos.md
│   ├── 03-costos-y-limpieza.md
│   ├── 04-troubleshooting.md
│   ├── diagrams/                  # D-01 … D-28 en Mermaid
│   ├── adr/                       # ADR-0001 … decisiones del caso
│   └── referencias.md
├── sesiones/
│   └── s01-arquitecturas-base/
│       ├── README.md  slides/  guia-estudiante.md
│       ├── caso-universitario/    # requisitos funcionales y no funcionales
│       └── evaluacion/            # preguntas y rúbricas (sin solucionario)
├── shared/llm_course_common/      # config, logging estructurado, OpenTelemetry, contrato de API
├── labs/
│   ├── 00-local-ollama/           # backend FastAPI, frontend React+Vite, pruebas de carga, compose
│   ├── 10-gcp/                    # a-consola, b-adk, c-arquitectura
│   ├── 20-azure/                  # a-consola, b-agent-framework, c-semantic-kernel-legado,
│   │                              # d-autogen-legado, e-langgraph-foundry, f-arquitectura
│   ├── 30-aws/                    # a-consola-agentcore, b-strands, c-agentcore-runtime, d-arquitectura
│   └── 40-comparativo-multicloud/
└── infra/terraform/               # opcional, ejemplos avanzados por nube
```

### Decisiones de diseño del repositorio

| Decisión | Justificación |
| --- | --- |
| Contrato único: `POST /v1/chat` (con streaming SSE), `GET /healthz`, `GET /readyz` | Permite comparar proveedores sobre la misma interfaz y reutilizar frontend y pruebas de carga |
| Cada laboratorio es autocontenido (README, `.env.example`, dependencias, pruebas, limpieza) | Un estudiante puede ejecutar solo el laboratorio de su nube sin instalar SDKs de las otras dos |
| Pruebas unitarias con proveedores simulados; pruebas de integración marcadas y omitidas sin credenciales | La CI del repositorio corre sin cuentas cloud ni costos |
| Autenticación por identidad del entorno (Azure CLI, gcloud ADC, perfiles AWS SSO) en lugar de claves en archivos | Coherente con la Unidad E: sin secretos estáticos en el código |
| Ollama enlazado solo a `127.0.0.1` y nunca publicado en `docker-compose` hacia el exterior | Evita la exposición pública accidental exigida en el prompt maestro |
| Labs de Semantic Kernel y AutoGen etiquetados como “legado y migración” | Refleja su estado de mantenimiento verificado |
| Solucionario, rúbricas con respuestas y guía docente en un repositorio privado de GitHub de la misma organización | Protege la integridad de la evaluación |
| Versiones de SDK fijadas por laboratorio y fecha de verificación en cada README | Los SDKs agenticos cambian mensualmente; la fecha indica cuándo reverificar |

## 7. Inventario de laboratorios

Se planifican **15 laboratorios**: 1 local, 3 de Google Cloud, 6 de Azure, 4 de AWS y 1 comparativo. Solo el laboratorio local alimenta demostraciones en vivo; los demás se ejecutan después de la sesión. Las duraciones son estimaciones de diseño y se validarán al ejecutar cada laboratorio en la Fase 6. Ningún costo se cuantifica todavía: se verificarán precios oficiales por región antes de publicarlos.

| ID | Laboratorio | Tecnología principal | Uso en sesión | Duración estimada | Tipo de costo | Vigencia a verificar en Fase 5 |
| --- | --- | --- | --- | --- | --- | --- |
| LOC-01 | Inferencia local: Ollama + FastAPI + React + prueba de carga | Ollama, FastAPI, React 18, Vite 6, Docker Compose | Demos 1, 2 y 4 | 120 min | Ninguno (hardware propio) | Modelo liviano y versión de Ollama; ruta CPU-only |
| GCP-A | Agente desde la consola | Gemini Enterprise Agent Platform (Agent Studio) | Demo 3 (cohorte GCP) | 60 min | Consumo por tokens | Nombre y ruta de consola tras el renombre de Vertex AI |
| GCP-B | Agente con ADK y Gemini, ejecución local y despliegue gestionado | Google ADK (Python), Agent Engine / Agent Runtime | Complementario | 120 min | Tokens + runtime gestionado | Nombre vigente del runtime y regiones disponibles |
| GCP-C | Análisis de arquitectura del caso en Google Cloud | D-17, Cloud Run, GKE | Complementario | 60 min | Ninguno | — |
| AZ-A | Agente desde Microsoft Foundry | Foundry Agent Service (prompt agent) | Demo 3 (cohorte Azure) | 60 min | Consumo por tokens | Portal “Foundry (new)” vs. clásico |
| AZ-B | Agente con Microsoft Agent Framework | Agent Framework 1.x (Python) + modelo en Foundry | Complementario | 90 min | Consumo por tokens | Versión 1.x y funciones en preview |
| AZ-C | Semantic Kernel: ejemplo y migración | Semantic Kernel (mantenimiento) → Agent Framework | Complementario | 60 min | Consumo por tokens | Estado de soporte y guía de migración |
| AZ-D | AutoGen: ejemplo y migración | AutoGen (mantenimiento) → Agent Framework | Complementario | 60 min | Consumo por tokens | Estado de soporte y guía de migración |
| AZ-E | LangGraph con modelos de Azure | LangGraph + modelo en Foundry; opción de hosted agent | Complementario | 90 min | Tokens + hosting opcional | Soporte de red privada en hosted agents |
| AZ-F | Análisis de arquitectura y comparación de enfoques en Azure | D-18, Container Apps, AKS | Complementario | 60 min | Ninguno | — |
| AWS-A | Agente desde la consola sobre AgentCore | Amazon Bedrock AgentCore (no Agents Classic) | Demo 3 (cohorte AWS) | 60 min | Consumo por tokens + runtime | Flujo de consola disponible para cuentas nuevas |
| AWS-B | Agente con Strands Agents SDK y Bedrock | Strands Agents (Python) + Amazon Bedrock | Complementario | 90 min | Consumo por tokens | Modelo por defecto y acceso a modelos en la región |
| AWS-C | Despliegue en AgentCore Runtime | AgentCore Runtime, Identity, Observability | Complementario | 90 min | Runtime gestionado + tokens | Regiones y SDK `bedrock-agentcore` |
| AWS-D | Análisis de arquitectura del caso en AWS | D-19, Lambda, ECS, EKS | Complementario | 60 min | Ninguno | — |
| MC-01 | Comparativo multicloud del caso universitario | Resultados de los labs + D-16 | Tarea posterior | 90 min | Ninguno | Tabla de mapeo actualizada |

Todos los laboratorios cloud incluirán alerta de presupuesto, permisos mínimos, verificación de recursos residuales y un script o procedimiento de limpieza probado.

## 8. Bibliografía oficial

La bibliografía combina documentación oficial de proveedores, estándares y artículos académicos de referencia. La columna Estado distingue fuentes **abiertas y verificadas en esta fase** de fuentes conocidas cuyo enlace, versión y fecha se confirmarán en la Fase 2; ninguna referencia por verificar se usará en materiales finales sin ese paso.

### Documentación oficial de plataformas y frameworks

| Fuente | Sustenta | Estado |
| --- | --- | --- |
| [Microsoft Agent Framework 1.0 — anuncio GA (3-abr-2026)](https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/) | Unidad D, labs AZ-B a AZ-D | Verificada |
| [Migración de Semantic Kernel y AutoGen a Agent Framework (19-feb-2026)](https://devblogs.microsoft.com/semantic-kernel/migrate-your-semantic-kernel-and-autogen-projects-to-microsoft-agent-framework-release-candidate/) | Labs AZ-C, AZ-D | Verificada |
| [Foundry Agent Service — overview](https://learn.microsoft.com/azure/foundry/agents/overview) | Unidad D, lab AZ-A | Verificada |
| [Foundry hosted agents con Agent Framework](https://learn.microsoft.com/en-us/agent-framework/hosting/foundry-hosted-agent) | Lab AZ-E | Verificada |
| [Google ADK — overview](https://docs.cloud.google.com/agent-builder/agent-development-kit/overview) | Lab GCP-B | Verificada |
| Anuncio oficial de Gemini Enterprise Agent Platform (blog de Google Cloud, 22-abr-2026) | Unidad D, labs GCP | Por verificar: solo se consultó cobertura secundaria ([HPCwire](https://www.hpcwire.com/aiwire/2026/04/23/google-unveils-gemini-enterprise-agent-platform/)) |
| [Amazon Bedrock AgentCore — documentación](https://docs.aws.amazon.com/bedrock-agentcore/index.md) | Unidad D, labs AWS-A y AWS-C | Verificada |
| [Amazon Bedrock Agents Classic — modo mantenimiento](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-classic-maintenance-mode.html) | Decisión del lab AWS-A | Verificada |
| [Strands Agents — quickstart](https://strandsagents.com/docs/user-guide/quickstart/overview/index.md) | Lab AWS-B | Verificada |
| AWS Well-Architected Generative AI Lens; Azure Well-Architected para cargas de IA; Google Cloud Architecture Framework (perspectiva IA/ML) | Unidades B, C, D | Por verificar (versión vigente) |
| Documentación de Ollama (GitHub ollama/ollama), FastAPI y OpenTelemetry Semantic Conventions for GenAI | Lab LOC-01, Unidad F | Por verificar (versión y estado de la especificación) |

### Estándares y marcos de referencia

| Fuente | Sustenta | Estado |
| --- | --- | --- |
| [OWASP Top 10 for LLM Applications 2025 (v2.0)](https://docs.modulos.ai/frameworks/owasp-top-10-llm) | Unidad E | Contenido verificado; enlazar el PDF oficial de genai.owasp.org en Fase 2 |
| OWASP Top 10 for Agentic Applications for 2026 | Unidad E, riesgos agenticos | Verificado en fuente secundaria ([Promptfoo](https://www.promptfoo.dev/docs/red-team/owasp-agentic-ai)); enlazar fuente OWASP |
| NIST AI RMF 1.0 (NIST AI 100-1, 2023) y perfil de IA generativa NIST AI 600-1 (2024) | Unidad E, gobierno | Por verificar |
| NIST SP 800-207, Zero Trust Architecture (2020) | Unidad E | Por verificar |
| ISO/IEC 42001:2023 (sistemas de gestión de IA) e ISO/IEC 27001:2022 | Unidad E, gobierno | Por verificar |
| Ley Estatutaria 1581 de 2012 (protección de datos personales, Colombia) | Unidad E, caso universitario | Por verificar (texto y decretos reglamentarios vigentes) |
| FinOps Framework (FinOps Foundation) | Unidad F | Por verificar (edición vigente) |
| Google SRE Book y SRE Workbook (sre.google) | Unidad F: SLI, SLO, presupuesto de error | Por verificar |

### Literatura académica

| Referencia | Sustenta | Estado |
| --- | --- | --- |
| Vaswani et al. (2017). Attention Is All You Need. NeurIPS. [arXiv:1706.03762](https://arxiv.org/abs/1706.03762) | Unidad A | Por verificar enlace |
| Pope et al. (2023). Efficiently Scaling Transformer Inference. MLSys. [arXiv:2211.05102](https://arxiv.org/abs/2211.05102) | Prefill/decode, memoria | Por verificar enlace |
| Yu et al. (2022). Orca: A Distributed Serving System for Transformer-Based Generative Models. OSDI | Batching continuo | Por verificar |
| Kwon et al. (2023). Efficient Memory Management for LLM Serving with PagedAttention. SOSP. [arXiv:2309.06180](https://arxiv.org/abs/2309.06180) | KV cache, vLLM | Por verificar enlace |
| Agrawal et al. (2024). Sarathi-Serve. OSDI; Zhong et al. (2024). DistServe. OSDI | Trade-off throughput-latencia | Por verificar |
| Frantar et al. (2023). GPTQ. ICLR. [arXiv:2210.17323](https://arxiv.org/abs/2210.17323) | Cuantización | Por verificar enlace |
| Lewis et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. NeurIPS. [arXiv:2005.11401](https://arxiv.org/abs/2005.11401) | RAG | Por verificar enlace |
| Yao et al. (2023). ReAct: Synergizing Reasoning and Acting in Language Models. ICLR. [arXiv:2210.03629](https://arxiv.org/abs/2210.03629) | Agentes | Por verificar enlace |
| Greshake et al. (2023). Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection. AISec. [arXiv:2302.12173](https://arxiv.org/abs/2302.12173) | Inyección indirecta | Por verificar enlace |

## 9. Matriz de trazabilidad

Cada resultado de aprendizaje tiene al menos un contenido, una actividad en sesión y una evidencia evaluable; ninguno depende solo de la tarea posterior. Las competencias (C1–C12) remiten a la sección 4 del prompt maestro.

| RA | Competencia del curso | Contenido (unidad · diapositivas) | Actividad en sesión | Laboratorio de refuerzo | Evaluación | Instrumento |
| --- | --- | --- | --- | --- | --- | --- |
| RA1 | C1 | A · 4–9 | Demo 1 con preguntas de predicción (“¿qué pasará con el TTFT si duplico el prompt?”) | LOC-01 | Formativa: cuestionario de cierre (P1–P2) | Clave de respuestas |
| RA2 | C1, C5 | B · 14–17, 22 | Identificación de puntos únicos de fallo en D-06 | GCP-C, AZ-F, AWS-D | Sumativa: taller | Rúbrica, criterio “componentes” |
| RA3 | C2, C4 | A · 12; B · 18; C · 32 | Demo 2: misma API con dos backends | LOC-01, GCP-A, AZ-A, AWS-A | Sumativa: ADR del taller | Rúbrica, criterio “justificación” |
| RA4 | C3 | C · 24–27 | Ejemplo resuelto en clase + cálculo individual de 5 min | LOC-01 (medir RAM real vs. estimada) | Formativa: ejercicio de dimensionamiento | Solucionario con tolerancia ±20 % |
| RA5 | C9, C10 | A · 7; F · 46–47 | Demo 4: lectura de la curva de saturación | LOC-01 (prueba de carga) | Formativa: cuestionario (P3–P4) | Clave de respuestas |
| RA6 | C4, C6 | D · 33–38 | Demo 3: recorrido de consola y ubicación en D-16 | Todos los labs cloud, MC-01 | Sumativa: tabla de mapeo de la tarea | Lista de cotejo |
| RA7 | C7 | E · 40–45 | Matriz de amenazas del caso durante el taller | AWS-C, AZ-E (identidad y red) | Sumativa: sección de seguridad del taller | Rúbrica, criterio “seguridad” |
| RA8 | C3, C11, C12 | Todas · 32, 48–49, 51–52 | Taller de topología base en equipos | MC-01 | Sumativa: diagrama + ADR + SLO + costo de orden de magnitud | Rúbrica analítica completa (4 niveles) |

La competencia C8 (RAG y agentes) se introduce en las diapositivas 20–21 sin evaluación sumativa en esta sesión; se evalúa cuando se desarrolle en sesiones posteriores.

## 10. Contenidos que quedan como material complementario

El criterio de corte es simple: queda en la sesión lo que se necesita para **razonar** la topología base; pasa al repositorio lo que se necesita para **implementarla** o profundizar en un proveedor.

| Contenido | En la sesión | Pasa a | Razón |
| --- | --- | --- | --- |
| Instalación y configuración de Ollama, FastAPI y React | Solo resultado en Demo 1 | LOC-01 | Procedimiento, no concepto |
| Laboratorios de consola en las tres nubes | Una nube, 12 min (Demo 3) | GCP-A, AZ-A, AWS-A | Requieren cuentas, cuotas e IAM previos |
| Código de agentes con ADK, Agent Framework, Strands, LangGraph | Solo la diapositiva de capas (37) | GCP-B, AZ-B, AZ-E, AWS-B | Programación; la sesión enseña dónde encaja cada uno |
| Semantic Kernel y AutoGen | Una mención como legado | AZ-C, AZ-D | Modo mantenimiento; valor principal es la migración |
| Despliegue en runtimes gestionados de agentes | Concepto en diapositiva 18 | GCP-B, AZ-E, AWS-C | Alto costo de tiempo y riesgo de fallo en vivo |
| Kubernetes con GPU, operadores y autoscaling de inferencia | Criterios de selección (30) | Sesiones posteriores del Capítulo 2 | Requiere fundamentos de esta sesión |
| Motores de serving (vLLM, TGI y equivalentes), paged attention a detalle | Intuición de KV cache y batching | Sesión de model serving | Profundidad propia de una sesión completa |
| Implementación de RAG (chunking, embeddings, evaluación de recuperación) | RAG como carga de trabajo (20) | Sesión de RAG y vector stores | Fuera del objetivo de desempeño |
| Terraform por nube | No | `infra/terraform/` (avanzado) | Opcional, aporta reproducibilidad pero no concepto |
| Cálculo de costos con precios reales por región | Modelo conceptual (49) | MC-01 y sesión de FinOps | Precios cambian; exigen verificación con fecha |
| Pruebas de carga sistemáticas y observabilidad con OpenTelemetry | Demo 4 corta | LOC-01 y sesión de rendimiento | Requiere instrumentación y análisis extensos |
| Red teaming de prompt injection | Concepto y diagrama D-23 | Sesión de seguridad LLM | Requiere entorno controlado |

## 11. Decisiones confirmadas e implicaciones

Las cinco decisiones quedaron confirmadas el 13-oct-2026. La más delicada es el uso de cuentas trial: en Azure, la suscripción Free Trial puede no tener cuota para desplegar modelos, lo que obliga a preparar la Demo 3 y los labs de Azure con una ruta alternativa.

| Decisión | Respuesta | Implicación para las fases siguientes |
| --- | --- | --- |
| Nube de la Demo 3 | Azure en la primera cohorte | Demo con Foundry Agent Service (lab AZ-A); el docente la ejecuta desde una suscripción con cuota de modelos, no desde una trial |
| Acceso de estudiantes | Cuentas trial en las tres nubes | Cada lab declara qué permite la trial, ventana de uso y ruta si la trial no alcanza (tabla siguiente) |
| Modelo local | Open-weight de 1–4 B cuantizado, 8 GB RAM, CPU-only | Selección y prueba en la Fase 6 |
| Licencias | MIT (código) y CC BY-SA 4.0 (materiales) | Archivos LICENSE en la raíz y en `docs/` |
| Solucionario | Todo en GitHub | Se propone un segundo repositorio **privado** en la misma organización (`llm-infra-escalable-docente`) con solucionario, rúbricas con respuestas y guía docente; el repositorio público enlaza a él. Pendiente de confirmar |

### Restricciones de las cuentas trial verificadas

| Nube | Qué ofrece la trial | Restricción relevante | Ajuste en los laboratorios | Fuente |
| --- | --- | --- | --- | --- |
| Azure | Crédito de bienvenida por 30 días | La documentación oficial define un nivel **Free Tier / Tier 0** con cuota para gpt-4.1-mini, gpt-5-mini, o4-mini y text-embedding-3-small (GlobalStandard). Hay reportes contradictorios sobre si toda trial nueva recibe ese nivel o queda en 0 TPM | Labs de Azure diseñados solo con modelos de Tier 0 (gpt-5-mini como principal). Validación empírica previa con una trial nueva. Ruta alternativa con Ollama si la trial no tiene cuota (ver plan abajo) | [Microsoft Learn, cuotas de Azure OpenAI en Foundry (act. 20-ago-2026)](https://learn.microsoft.com/en-us/azure/foundry/openai/quotas-limits); [Microsoft Q&A, trial en Free Tier (sep-2026)](https://learn.microsoft.com/en-gb/answers/questions/5993422/remain-on-free-tier-disable-automatic-upgrade-to-p); [Microsoft Q&A, trial sin cuota (jun-2026)](https://learn.microsoft.com/en-us/answers/a/12804121) |
| AWS | US$100 al registrarse y hasta US$100 adicionales por actividades, incluida una de Amazon Bedrock | El plan Free dura 6 meses o hasta agotar créditos y excluye algunos servicios; el plan Paid accede a todos y aplica los créditos | Recomendar plan Paid con AWS Budgets desde el primer día; verificar en Fase 5 si AgentCore está disponible en el plan Free | [AWS News Blog](https://aws.amazon.com/blogs/aws/aws-free-tier-update-new-customers-can-get-started-and-explore-aws-with-up-to-200-in-credits) |
| Google Cloud | US$300 por 90 días | Durante la trial no se pueden añadir GPU a VMs ni usar modelos de terceros como servicio; el crédito no cubre la Gemini API de AI Studio | Labs de Google solo con modelos Gemini a través de Gemini Enterprise Agent Platform (no con clave de AI Studio); ningún lab de Google usa GPU | [Google Cloud Docs](https://docs.cloud.google.com/free/docs/free-cloud-features.md.txt) |

### Plan de viabilidad con la trial de Azure

Trabajar con la trial de Azure es **probablemente viable**, a condición de usar solo modelos pequeños y validar antes del curso. La documentación oficial de cuotas (actualizada el 20-ago-2026) incluye un Tier 0 con gpt-5-mini a 500.000 TPM y gpt-4.1-mini a 200.000 TPM, holgado para laboratorios individuales. Un caso de septiembre de 2026 en Microsoft Q&A muestra una suscripción Free Trial asignada a “Free Tier”, y el moderador confirma que subir de nivel de cuota no convierte la trial en pay-as-you-go. En contra, un caso de junio de 2026 reportó 0 TPM en una trial; la página oficial no dice explícitamente qué nivel recibe una trial nueva.

| Paso | Qué se hace | Criterio de éxito | Si falla |
| --- | --- | --- | --- |
| 1. Validación previa | El docente o un monitor crea una cuenta trial nueva y consulta su nivel de cuota con la API `quotaTiers` | `currentTierName` = Free Tier o Tier 0 | Pasar a la ruta alternativa |
| 2. Despliegue de prueba | Desplegar gpt-5-mini (GlobalStandard) en Foundry y crear un prompt agent | El agente responde en el playground | Probar gpt-4.1-mini y otra región; si persiste, ruta alternativa |
| 3. Ensayo de laboratorios | Ejecutar AZ-A, AZ-B y AZ-E completos con esa cuenta y medir el crédito consumido | Consumo muy por debajo del crédito de la trial | Reducir el alcance de los labs |
| 4. Calendario | Los estudiantes crean su cuenta Azure la semana del bloque de Azure | Labs completados dentro de la ventana de 30 días | Reordenar el bloque de nubes |

**Ruta alternativa si la trial no tiene cuota.** Los labs de código (Agent Framework, Semantic Kernel, AutoGen, LangGraph) apuntan al modelo local de Ollama mediante su API compatible con OpenAI; solo cambia la configuración. El lab de consola AZ-A se reemplaza por la demostración del docente grabada, más un análisis guiado. Esta ruta conserva los objetivos de arquitectura y frameworks, pero pierde la experiencia de servicio gestionado en Azure; la compatibilidad de cada framework con Ollama se verificará en la Fase 6.

Con esto, la Fase 2 desarrollará el marco teórico completo por unidad, empezando por la Unidad A y los diagramas D-02, D-03, D-04 y D-06, que son la base conceptual de todo el curso.
