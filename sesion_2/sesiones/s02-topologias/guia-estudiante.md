# Guía del estudiante · Sesión 2 · Diseño de topologías y casos de uso empresariales

Esta guía resume el marco conceptual de la sesión, define el vocabulario y propone ejercicios y lecturas. Complementa la presentación (`slides/`) y los laboratorios LOC-02, AZ-G, GCP-D y AWS-E.

## 1. Marco conceptual

### 1.1 La carga de trabajo se define por su SLO

Una **carga de trabajo** es un conjunto de solicitudes con el mismo propósito y el mismo objetivo de servicio. El mismo modelo puede atender cargas muy distintas:

| Patrón | Quién espera | SLI principal | Ejemplo del caso |
| --- | --- | --- | --- |
| Síncrono / streaming | Una persona, en la conexión | TTFT, latencia p95, tasa de errores | Asistente de estudiantes |
| Asíncrono | Una persona, el resultado (minutos) | Tiempo hasta notificar | Resumen de un acta enviado por correo |
| Micro-batch | Un proceso (segundos) | Retraso de procesamiento | Embeddings de documentos nuevos |
| Batch | Un proceso o un equipo (horas) | Tiempo hasta completar, % de ítems exitosos, costo por 1.000 ítems | Clasificación nocturna de PQRS |

La pregunta de diseño es: **¿qué cuesta responder en 6 horas en lugar de 6 segundos?** Si la respuesta es «nada», la carga debe ir por el camino batch.

### 1.2 Por qué el lote es más barato

En un sistema con cola, el tiempo de respuesta crece de forma no lineal con la utilización. En el modelo idealizado M/M/1, el tiempo de respuesta normalizado es 1/(1 − ρ): al 50 % de utilización se espera el doble del tiempo de servicio y al 90 %, diez veces. Para cumplir un SLO de latencia, lo online necesita holgura, es decir, capacidad ociosa. Un lote puede esperar, por lo que el proveedor lo programa en los huecos y opera con utilización alta.

Los tres proveedores documentan un descuento del 50 % para su servicio batch, a cambio de una ventana de unas 24 horas (Azure OpenAI Batch, Gemini batch inference y Amazon Bedrock batch; consultado el 20-oct-2026).

### 1.3 Clases de servicio online

Entre el online estándar y el batch hay modalidades intermedias que se eligen **por solicitud**:

- **Prioritaria** (Azure *priority processing*, Google *Priority PayGo*, AWS *Priority*): menor latencia a un precio mayor.
- **Flexible** (Azure *Flex processing*, Google *Flex PayGo*, AWS *Flex*): menor precio para cargas tolerantes a demora, sin archivo ni ventana de 24 h.
- **Reservada** (Azure *Provisioned/PTU*, Google *Provisioned Throughput*, AWS *Reserved*): capacidad dedicada para carga sostenida.

En Azure y en AWS, la clase prioritaria **no aumenta la cuota**: comparte la cuota on-demand.

### 1.4 Disponibilidad compuesta

- Componentes **en serie** (todos deben funcionar): A = A₁ × A₂ × … × Aₙ.
- Componentes **en paralelo** (basta uno, fallas independientes): A = 1 − (1 − A₁)(1 − A₂).

Ejemplo con cifras hipotéticas: gateway 99,95 %, backend 99,95 % y modelo 99,9 % dan 99,80 % por región. Dos regiones en paralelo dan 99,9996 %. Pero si el enrutamiento global (99,99 %) queda en serie, el total baja a ≈ 99,99 %, unos 4,5 minutos de indisponibilidad al mes. **El componente global en serie es el techo.**

La fórmula del paralelo supone fallas independientes. Una cuota compartida, una versión defectuosa del modelo o un plano de control común **correlacionan** las fallas y anulan parte del beneficio.

### 1.5 RTO, RPO y estrategias de recuperación

- **RTO** (Recovery Time Objective): máximo tiempo aceptable sin servicio.
- **RPO** (Recovery Point Objective): máxima pérdida de datos aceptable, medida en tiempo.

| Estrategia | En la región secundaria | RTO aproximado |
| --- | --- | --- |
| Backup and restore (hot/cold) | Solo copias de datos | Horas |
| Pilot light | Datos replicados, cómputo apagado | Decenas de minutos |
| Warm standby (hot/warm) | Despliegue mínimo funcionando | Minutos |
| Multi-site active/active (hot/hot) | Despliegue completo con tráfico | Cercano a cero |

En LLM **gestionados**, mantener un despliegue en espera es barato: si no recibe tráfico no factura tokens. En LLM **autogestionados**, la GPU en espera se paga por hora.

### 1.6 Dos capas de multi-región

1. **Capa del proveedor:** Azure Global y Data Zone; endpoints `global` y multirregionales de Google; Cross-Region inference de AWS. Aumentan la capacidad y la disponibilidad *dentro* del servicio de modelos.
2. **Capa propia:** backend, gateway, datos y enrutamiento de usuarios en varias regiones.

Microsoft lo dice explícitamente: el enrutamiento de Global y Data Zone «no reemplaza el failover regional a nivel de aplicación». Si cae la región de su endpoint, de su backend o de su base de datos, el usuario se queda sin respuesta.

### 1.7 Patrones de resiliencia

Timeouts, reintentos con backoff y jitter, presupuesto de reintentos, circuit breaker, bulkhead, degradación, load shedding e idempotencia. Dos reglas propias de los LLM:

- **Conmutar solo antes del primer token.** Después, conmutar duplicaría o mezclaría texto.
- **Reintentar en una sola capa.** Si cuatro capas reintentan tres veces, una pregunta puede generar 81 llamadas.

### 1.8 Selección de servicios

Ocho familias de criterios: funcional, ubicación (regiones y residencia), rendimiento (latencia y cuota), economía (modalidad de consumo), confiabilidad (SLA y madurez), seguridad, operación y portabilidad. El árbol de decisión de la diapositiva 34 (diagrama D-38) ordena la elección de la modalidad.

## 2. Glosario

| Término | Definición |
| --- | --- |
| Batch inference | Procesamiento asíncrono de un archivo con muchas solicitudes, con resultados en un archivo de salida |
| `custom_id` / `recordId` | Identificador por solicitud para emparejar resultados que no conservan el orden |
| Ventana de finalización | Plazo objetivo del trabajo batch (24 h en Azure y Bedrock) |
| Dominio de falla | Conjunto de recursos que fallan juntos (zona, región, cuota, proveedor) |
| Warm standby | Región secundaria con un despliegue mínimo funcionando |
| Circuit breaker | Mecanismo que deja de enviar tráfico a un destino que falla y prueba su recuperación |
| Retry-After | Cabecera con la que el proveedor indica cuándo reintentar tras un 429 |
| Cross-Region inference (CRIS) | Enrutamiento de Bedrock a otras regiones mediante perfiles de inferencia |
| Data Zone | Tipo de despliegue de Azure que limita el procesamiento a EE. UU., la UE o APAC |
| Endpoint global | Endpoint de Google que puede procesar en cualquier ubicación, sin garantía de residencia |
| Gateway de IA | Componente que centraliza enrutamiento, límites de tokens y observabilidad frente a los modelos |
| Residencia de datos | Restricción sobre dónde se procesan y almacenan los datos |

## 3. Arquitecturas de referencia

- D-39: topología neutral multi-región del caso universitario (warm standby para el asistente, lote en una región).
- D-40, D-41 y D-42: la misma topología en Azure, Google Cloud y AWS.
- D-43: el laboratorio LOC-02.

## 4. Ejercicios

1. **Clasificación de cargas.** Para el caso universitario, liste cinco cargas que usen el modelo (además de las tres de la sesión) y clasifíquelas como online, asíncrona o batch. Justifique el SLO de cada una.
2. **Disponibilidad.** Una topología tiene un balanceador global (99,99 %), un gateway por región (99,95 %), un backend por región (99,95 %) y el servicio de modelos con capa global del proveedor (99,9 %), en dos regiones. Calcule la disponibilidad y los minutos de indisponibilidad al mes. ¿Qué componente mejoraría primero?
3. **Costo.** Con los supuestos de la diapositiva 45, calcule el costo mensual del lote de PQRS si el volumen crece a 500.000 PQRS al mes. ¿A partir de qué volumen la GPU programada 1 hora por noche sería más barata que el batch gestionado? ¿Qué supuesto es el más débil?
4. **Residencia.** La política institucional exige que la inferencia de datos personales ocurra en EE. UU. Elija el tipo de despliegue o de endpoint en cada nube y explique qué renuncia en disponibilidad.
5. **Laboratorio.** En LOC-02, ejecute la prueba de conmutación con `--modo-falla slow` y compárela con `down`. Explique la diferencia de latencia usando `APP_FIRST_BYTE_TIMEOUT_S`.

## 5. Lecturas complementarias

- Azure Architecture Center. *Use a gateway in front of multiple Azure OpenAI deployments*.
- Microsoft Learn. *Deployment types for Microsoft Foundry Models* y *Getting started with Azure OpenAI batch deployments*.
- Google Cloud. *Where your data lives and is processed* (Gemini Enterprise Agent Platform).
- AWS. *Service tiers for optimizing performance and cost* y *Securing Amazon Bedrock cross-Region inference*.
- Eliot, S. (2021). *Disaster Recovery (DR) Architecture on AWS, Part I*. AWS Architecture Blog.
- Beyer, B. et al. (2016). *Site Reliability Engineering*, capítulos 21 y 22 (sobrecarga y fallas en cascada).
- Nygard, M. T. (2018). *Release It!* (2.ª ed.), patrones de estabilidad.

Enlaces y fecha de verificación en `docs/referencias.md`.

## 6. Autoevaluación

1. Una aplicación clasifica 1 millón de correos al mes y los resultados se usan al día siguiente. ¿Qué modalidad elegiría y por qué?
2. ¿Por qué un segundo despliegue Global Standard en otra región de la misma suscripción de Azure no resuelve los 429 por cuota?
3. ¿Qué diferencia hay entre el endpoint `global` de Google y un perfil `us.` de Bedrock en términos de residencia?
4. ¿Por qué el gateway de LOC-02 no conmuta cuando una región falla después de haber enviado tokens?
5. Explique con un ejemplo la diferencia entre RTO y RPO para el asistente y para las PQRS.
6. ¿Qué riesgo de OWASP LLM 2025 es más relevante en un lote de miles de documentos externos y cómo lo controlaría?
