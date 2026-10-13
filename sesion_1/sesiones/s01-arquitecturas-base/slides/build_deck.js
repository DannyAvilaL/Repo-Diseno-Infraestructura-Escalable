// Genera S01-Arquitecturas-Base-LLM.pptx (55 diapositivas, notas del expositor).
// Uso: node build_deck.js  (requiere pptxgenjs)
const pptxgen = require("pptxgenjs");
const path = require("path");
const { applyTheme } = require(process.env.APPLY_THEME || "/mnt/skills/public/pptx/scripts/apply_theme.js");

const THEME = {
  name: "Curso LLM Infra",
  headFontFace: "Calibri",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1B1F24", lt1: "FFFFFF", dk2: "13324B", lt2: "F2F4F6",
    accent1: "1F6F9F", accent2: "2E9C8A", accent3: "D98E2B", accent4: "B5443A",
    accent5: "6B5B95", accent6: "7A8794", hlink: "1F6F9F", folHlink: "6B5B95",
  },
};
const HEX = { navy: "13324B", blue: "1F6F9F", teal: "2E9C8A", amber: "D98E2B", red: "B5443A", grey: "7A8794", light: "F2F4F6", line: "C9D1D9", ink: "1B1F24" };

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 in
pres.title = "Sesión 1 · Arquitecturas Base para LLMs en la Nube";
pres.subject = "Diseño de Infraestructura Escalable para LLMs";
pres.author = "Curso Diseño de Infraestructura Escalable para LLMs";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;
const W = 13.33;

pres.defineSlideMaster({
  title: "PORTADA",
  background: { color: HEX.navy },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.2, w: 11.7, h: 1.6, fontSize: 40, bold: true, color: C.background1, align: "left" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 3.9, w: 11.7, h: 1.6, fontSize: 20, color: C.background2 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "SECCION",
  background: { color: HEX.blue },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.4, w: 11.7, h: 1.4, fontSize: 38, bold: true, color: C.background1, align: "left" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 3.8, w: 11.7, h: 1.4, fontSize: 20, color: C.background2 }, text: "" } },
  ],
  slideNumber: { x: 12.4, y: 6.95, w: 0.7, h: 0.35, fontSize: 10, color: C.background1 },
});
pres.defineSlideMaster({
  title: "CONTENIDO",
  background: { color: "FFFFFF" },
  objects: [
    { rect: { x: 0, y: 0, w: W, h: 0.12, fill: { color: HEX.blue } } },
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.3, w: 12.1, h: 0.9, fontSize: 28, bold: true, color: C.text2, valign: "middle", align: "left" }, text: "" } },
    { text: { text: "Diseño de Infraestructura Escalable para LLMs · Sesión 1", options: { x: 0.6, y: 6.95, w: 8, h: 0.35, fontSize: 10, color: C.accent6 } } },
  ],
  slideNumber: { x: 12.4, y: 6.95, w: 0.7, h: 0.35, fontSize: 10, color: C.accent6 },
});

let section = "Apertura";
function addSection(title) { section = title; pres.addSection({ title }); }
function contentSlide(title) {
  const s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  return s;
}
function bullets(s, items, opts = {}) {
  const x = opts.x ?? 0.6, y = opts.y ?? 1.4, w = opts.w ?? 12.1, h = opts.h ?? 5.3;
  s.addText(
    items.map((t, i) => {
      const sub = t.startsWith("  ");
      return { text: t.trim(), options: { bullet: sub ? { indent: 18 } : true, indentLevel: sub ? 1 : 0, fontSize: sub ? (opts.fs ?? 20) - 3 : (opts.fs ?? 20), color: sub ? C.accent6 : C.text1, breakLine: i < items.length - 1, paraSpaceAfter: 8 } };
    }),
    { x, y, w, h, valign: "top", isTextBox: true, margin: 0.05 }
  );
}
function table(s, head, rows, opts = {}) {
  const fs = opts.fs ?? (rows.length > 6 ? 12 : 14);
  const data = [head.map((h) => ({ text: h, options: { bold: true, color: "FFFFFF", fill: { color: HEX.navy } } }))].concat(
    rows.map((r, i) => r.map((c) => ({ text: c, options: { fill: { color: i % 2 ? "FFFFFF" : HEX.light } } })))
  );
  s.addTable(data, { x: opts.x ?? 0.6, y: opts.y ?? 1.4, w: opts.w ?? 12.1, fontSize: fs, color: HEX.ink, border: { type: "solid", pt: 0.5, color: HEX.line }, valign: "middle", margin: 0.06, colW: opts.colW });
}
function callout(s, text, y = 6.2, color = HEX.teal) {
  s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y, w: 12.1, h: 0.6, fill: { color }, line: { color } });
  s.addText(text, { x: 0.75, y, w: 11.8, h: 0.6, fontSize: 15, bold: true, color: "FFFFFF", valign: "middle", isTextBox: true, margin: 0 });
}
function box(s, x, y, w, h, text, fill = HEX.light, color = HEX.ink, fs = 13) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: fill }, line: { color: HEX.blue, width: 1 } });
  s.addText(text, { x, y, w, h, fontSize: fs, color, align: "center", valign: "middle", isTextBox: true, margin: 0.05 });
}
function arrow(s, x1, y1, x2, y2) {
  s.addShape(pres.shapes.LINE, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1) || 0.001, h: Math.abs(y2 - y1) || 0.001, flipH: x2 < x1, flipV: y2 < y1, line: { color: HEX.grey, width: 1.5, endArrowType: "triangle" } });
}
function flow(s, steps, y = 2.2, h = 1.2) {
  const n = steps.length, gap = 0.3, w = (12.1 - gap * (n - 1)) / n;
  steps.forEach((t, i) => {
    const x = 0.6 + i * (w + gap);
    box(s, x, y, w, h, t, i === 0 ? "DCEAF4" : HEX.light, HEX.ink, 13);
    if (i < n - 1) arrow(s, x + w, y + h / 2, x + w + gap, y + h / 2);
  });
}
function lineChart(s, opts) {
  s.addChart(pres.charts.LINE, opts.series, {
    x: opts.x, y: opts.y, w: opts.w, h: opts.h,
    showTitle: true, title: opts.title, titleFontSize: 12, titleColor: HEX.ink, titleFontFace: "+mn-lt",
    chartColors: opts.colors || [HEX.blue, HEX.amber],
    lineSize: 2, lineDataSymbol: "circle", lineDataSymbolSize: 6,
    showLegend: opts.series.length > 1, legendPos: "b", legendFontSize: 10, legendFontFace: "+mn-lt",
    catAxisLabelColor: HEX.grey, valAxisLabelColor: HEX.grey, catAxisLabelFontSize: 10, valAxisLabelFontSize: 10,
    catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
    showCatAxisTitle: true, catAxisTitle: opts.xTitle, catAxisTitleFontSize: 10, catAxisTitleColor: HEX.grey,
    showValAxisTitle: true, valAxisTitle: opts.yTitle, valAxisTitleFontSize: 10, valAxisTitleColor: HEX.grey,
    valGridLine: { color: "E5E8EB", size: 0.5 }, catGridLine: { style: "none" },
    showValue: opts.showValue || false, dataLabelFontSize: 9, dataLabelPosition: "t",
  });
}
const REF = "Fuentes: marco teórico Sesión 1 (docs/marco-teorico) y bibliografía del curso.";
function notes(s, text) { s.addNotes(text + "\n\n" + REF); }

// ============================ APERTURA ============================
addSection("Apertura");
{
  const s = pres.addSlide({ masterName: "PORTADA", sectionTitle: section });
  s.addText("Arquitecturas Base para LLMs en la Nube", { placeholder: "title" });
  s.addText("Capítulo 1 · Fundamentos de Infraestructura para LLMs · Sesión 1 (180 min)\nDiseño de Infraestructura Escalable para LLMs · Maestría", { placeholder: "body" });
  s.addNotes("Bienvenida. Presentar el curso y el enfoque: esta sesión es teórica y de diseño; el código vive en el repositorio y en los laboratorios. Anunciar que al final los equipos diseñarán una topología base para el caso universitario.");
}
{
  const s = contentSlide("¿Qué hay entre el usuario y el modelo?");
  bullets(s, [
    "Caso transversal: asistente institucional de conocimiento para una universidad",
    "  5.000 usuarios potenciales · 100 concurrentes (hipótesis de diseño)",
    "  Disponibilidad objetivo 99,9 % · acceso autenticado · auditoría",
    "  Documentos institucionales · protección de datos · presupuesto limitado",
    "Los valores son supuestos académicos, no mediciones de carga",
    "Pregunta guía de la sesión: ¿qué componentes deben existir, dónde viven y por qué?",
  ], { w: 7.4 });
  box(s, 8.4, 1.6, 4.3, 0.9, "Usuario institucional", "DCEAF4");
  box(s, 8.4, 3.0, 4.3, 0.9, "¿ ? ? ?  (esta sesión)", "FFF4E0");
  box(s, 8.4, 4.4, 4.3, 0.9, "Modelo de lenguaje", "DCEAF4");
  arrow(s, 10.55, 2.5, 10.55, 3.0); arrow(s, 10.55, 3.9, 10.55, 4.4);
  notes(s, "Presentar el caso. Insistir en que las cifras son hipótesis: el primer trabajo del arquitecto es convertirlas en requisitos medibles. Pregunta a la clase: ¿qué falla primero si 100 personas preguntan a la vez? Recoger 3-4 respuestas y volver a ellas en la Unidad F.");
}
{
  const s = contentSlide("Resultados de aprendizaje y agenda");
  table(s, ["RA", "Al finalizar podrá…", "Bloque"], [
    ["RA1", "Explicar el ciclo de vida de una solicitud: prefill, decode, KV cache", "Unidad A · Demo 1"],
    ["RA2", "Identificar componentes y plano de control vs. plano de datos", "Unidad B"],
    ["RA3", "Comparar inferencia gestionada y autogestionada con criterios", "B · C · Demo 2"],
    ["RA4", "Estimar memoria: pesos + KV cache según precisión y concurrencia", "Unidad C"],
    ["RA5", "Interpretar TTFT, TPOT, throughput y saturación", "F · Demo 4"],
    ["RA6", "Mapear categorías de servicio en AWS, Azure y Google Cloud", "Unidad D · Demo 3"],
    ["RA7", "Asociar riesgos OWASP LLM 2025 con controles por capa", "Unidad E"],
    ["RA8", "Diseñar y justificar una topología base para el caso", "Taller"],
  ], { colW: [0.8, 8.3, 3.0] });
  notes(s, "Recorrer los resultados. Explicar la agenda: 112 min de teoría, 38 min de demostraciones, 20 min de taller y evaluación, pausa de 10 min a la mitad. Los laboratorios completos de las tres nubes quedan en el repositorio GitHub.");
}

// ============================ UNIDAD A ============================
addSection("A · Fundamentos de inferencia");
{
  const s = pres.addSlide({ masterName: "SECCION", sectionTitle: section });
  s.addText("Unidad A · Fundamentos de inferencia", { placeholder: "title" });
  s.addText("¿Qué recurso se agota primero cuando un LLM atiende a muchos usuarios?", { placeholder: "body" });
  s.addNotes("Pregunta arquitectónica de la unidad. Respuesta que construiremos: la memoria (capacidad y ancho de banda), no el cómputo.");
}
{
  const s = contentSlide("Un LLM visto desde la infraestructura");
  bullets(s, [
    "Dos piezas: archivo de pesos (miles de millones de parámetros) + motor de inferencia",
    "Cada token generado ≈ una pasada completa por la red: ~2 × N operaciones para N parámetros",
    "Cada paso de decode lee prácticamente todos los pesos desde memoria",
    "Consecuencia: el tamaño del modelo fija la memoria necesaria y la velocidad por token",
    "Servir un modelo = mantener pesos en memoria rápida + ejecutar el motor por cada token",
  ], { w: 7.6 });
  box(s, 8.6, 1.6, 4.1, 1.2, "Pesos\n(VRAM / RAM)", "DCEAF4");
  box(s, 8.6, 3.3, 4.1, 1.2, "Motor de inferencia\n(scheduler, kernels)", HEX.light);
  box(s, 8.6, 5.0, 4.1, 0.9, "Tokens de salida", "E3F2EF");
  arrow(s, 10.65, 2.8, 10.65, 3.3); arrow(s, 10.65, 4.5, 10.65, 5.0);
  notes(s, "Analogía: una biblioteca donde para escribir cada palabra el bibliotecario recorre todos los estantes. El tamaño de la biblioteca (pesos) y la velocidad de los pasillos (ancho de banda) mandan más que la rapidez de escritura. Error frecuente: pensar que un LLM es 'una base de datos' que busca respuestas.");
}
{
  const s = contentSlide("Tokens y context window");
  table(s, ["El token es…", "Implicación de infraestructura"], [
    ["Unidad de facturación", "Las APIs gestionadas cobran por token de entrada y de salida"],
    ["Unidad de latencia", "Cada token de salida es un paso de decode"],
    ["Unidad de capacidad", "Cada token activo ocupa KV cache mientras la conversación vive"],
  ], { y: 1.4, colW: [3.6, 8.5] });
  bullets(s, [
    "Tokenizadores entrenados mayormente en inglés producen más tokens por palabra en español: medir con el tokenizador real",
    "Context window = máximo de tokens de entrada + salida por solicitud",
    "Una ventana grande no es gratis: cuesta dinero, alarga el prefill y ocupa memoria",
  ], { y: 3.6, h: 2.5, fs: 18 });
  notes(s, "Mostrar un ejemplo de tokenización de una frase del reglamento. Pregunta: ¿por qué el mismo documento puede costar distinto en dos modelos? Respuesta esperada: tokenizadores distintos producen distinto número de tokens.");
}
{
  const s = contentSlide("Ciclo de vida de una solicitud de inferencia");
  flow(s, ["Usuario\nHTTPS + identidad", "API Gateway\nauth, cuotas", "Backend\nconstruye prompt", "Scheduler\ncola", "Prefill\nentrada en paralelo", "Decode\ntoken a token", "Streaming\n+ guardrails"], 2.0, 1.4);
  bullets(s, [
    "Pasos 1–3 y posprocesamiento: infraestructura clásica (identidad, red, aplicación)",
    "Cola, prefill y decode: específicos de LLM → núcleo de las unidades C y F",
    "Cada flecha es un punto de latencia y un punto de control de seguridad",
  ], { y: 4.0, h: 2.2, fs: 18 });
  notes(s, "Diagrama D-02. Recorrerlo con el caso: un estudiante pregunta por homologaciones. Señalar dónde se autentica, dónde se agregan documentos (RAG), dónde se mide el TTFT. Este diagrama se reutiliza en todo el curso.");
}
{
  const s = contentSlide("Prefill y decode: dos fases, dos cuellos de botella");
  table(s, ["Fase", "Qué hace", "Recurso dominante", "Métrica", "Crece con"], [
    ["Prefill", "Procesa todos los tokens de entrada en paralelo y llena la KV cache", "Cómputo", "TTFT", "Longitud del prompt"],
    ["Decode", "Genera un token por paso, secuencialmente", "Ancho de banda de memoria", "TPOT", "Longitud de la respuesta"],
  ], { colW: [1.3, 4.5, 2.4, 1.3, 2.6], fs: 15 });
  callout(s, "RAG con documentos largos degrada el TTFT; respuestas largas degradan la latencia total por decode.", 4.2);
  notes(s, "Diagrama D-03. Concepto de intensidad aritmética: prefill hace muchas operaciones por byte leído; decode lee todos los pesos para producir un solo token. Por eso decode está limitado por memoria. Esto se verá en vivo en la Demo 1.");
}
{
  const s = contentSlide("KV cache: la memoria que limita la concurrencia");
  s.addText("KV bytes/token = 2 × capas × kv_heads × d_head × bytes de precisión", { x: 0.6, y: 1.4, w: 12.1, h: 0.8, fontSize: 22, bold: true, color: C.accent1, align: "center", isTextBox: true });
  bullets(s, [
    "Guarda keys y values de todos los tokens previos para no recalcularlos",
    "Crece linealmente con los tokens de contexto y con las secuencias simultáneas",
    "Por eso un servidor LLM suele quedarse sin memoria antes que sin cómputo",
    "Mitigaciones: grouped-query attention, PagedAttention, cuantización de la KV cache",
  ], { y: 2.5, h: 3.8, w: 6.2, fs: 17 });
  lineChart(s, { x: 7.0, y: 2.4, w: 5.7, h: 4.0, title: "D-04 · Modelo 8B FP16, contexto 4.096 (ejemplo académico)",
    xTitle: "Secuencias activas", yTitle: "GiB",
    series: [
      { name: "Pesos + KV cache", labels: ["1", "10", "25", "50", "75", "100"], values: [15.5, 20, 27.5, 40, 52.5, 65] },
      { name: "Solo pesos", labels: ["1", "10", "25", "50", "75", "100"], values: [15, 15, 15, 15, 15, 15] },
    ] });
  notes(s, "El factor 2 son keys y values. Anunciar que en la Unidad C se aplica con números reales. Referencia: Kwon et al. (2023), PagedAttention, SOSP. Error frecuente: dimensionar solo por pesos.");
}
{
  const s = contentSlide("Batching y concurrencia");
  table(s, ["Estrategia", "Funcionamiento", "Ventaja", "Limitación"], [
    ["Sin batching", "Una solicitud a la vez", "Latencia individual mínima", "GPU subutilizada, costo por token alto"],
    ["Batching estático", "Agrupa N y espera a que terminen todas", "Simple", "Las respuestas cortas esperan a las largas"],
    ["Batching continuo", "Entran y salen secuencias en cada paso de decode", "Alto throughput, latencia razonable", "Requiere motor especializado"],
  ], { colW: [2.2, 3.9, 3.0, 3.0], fs: 14 });
  callout(s, "Trade-off: más secuencias por lote → más throughput y menor costo por token, pero mayor TPOT por usuario.", 4.4);
  notes(s, "Referencia: Yu et al. (2022), Orca, OSDI, introdujo la programación por iteración. El punto de operación se elige con el SLO (Unidad F). Pregunta: ¿qué preferiría la universidad, más usuarios atendidos o respuestas más rápidas por usuario?");
}
{
  const s = contentSlide("Entrenamiento, fine-tuning e inferencia");
  table(s, ["Actividad", "Propósito", "Recursos", "Frecuencia", "En el caso"], [
    ["Preentrenamiento", "Aprender el modelo base", "Miles de aceleradores, semanas o meses", "Una vez", "No: se adquiere el modelo"],
    ["Fine-tuning", "Especializar comportamiento o formato", "Uno o pocos aceleradores (LoRA)", "Ocasional", "Probablemente no al inicio"],
    ["Inferencia", "Responder solicitudes", "Memoria y ancho de banda 24/7", "Continua", "Sí: directa o vía proveedor"],
  ], { colW: [2.1, 2.8, 3.2, 1.6, 2.4], fs: 14 });
  callout(s, "Recomendación: para conocimiento institucional cambiante, RAG antes que fine-tuning.", 4.6);
  notes(s, "Con RAG el conocimiento se actualiza reindexando documentos, no reentrenando, y la respuesta puede citar la fuente. Error frecuente: proponer fine-tuning para 'enseñar el reglamento' al modelo.");
}
{
  const s = contentSlide("Modelos propietarios, open-weight y open source");
  table(s, ["Tipo", "Acceso a pesos", "Ejecución", "Implicaciones"], [
    ["Propietario", "No", "Solo vía API del proveedor", "Mínima operación; dependencia y términos de datos del proveedor"],
    ["Open-weight", "Sí, con licencia que puede restringir usos", "Self-hosting o servicio gestionado", "Control y portabilidad; revisar la licencia para uso institucional"],
    ["Open source estricto", "Pesos, código e información de datos", "Igual que open-weight", "Menos común; Open Source AI Definition (OSI)"],
  ], { colW: [2.3, 3.2, 2.9, 3.7], fs: 14 });
  notes(s, "Error frecuente: llamar open source a cualquier modelo descargable. Pregunta: ¿qué cláusulas de una licencia open-weight revisaría la oficina jurídica de la universidad? (usos permitidos, atribución, umbrales de usuarios).");
}
{
  const s = contentSlide("¿Comprar o producir inferencia?");
  table(s, ["", "API gestionada (comprar)", "Self-hosting (producir)"], [
    ["Qué se paga", "Tokens de entrada y salida", "GPU por hora + operación del equipo"],
    ["Qué se opera", "Prompt, cuotas, integración", "GPU, motor de serving, escalado, parches"],
    ["Control de datos", "Según términos y región del proveedor", "Total, dentro de la red propia"],
    ["Tiempo a producción", "Días", "Semanas o meses"],
  ], { colW: [2.5, 4.8, 4.8], fs: 15 });
  callout(s, "La decisión no es binaria: la Unidad B la ubica dentro de una arquitectura completa.", 4.6);
  notes(s, "Puente hacia la Unidad B. No dar todavía una recomendación: se cerrará con los costos de la Unidad F y el taller.");
}
{
  const s = contentSlide("Demo 1 · Anatomía de una solicitud (Ollama local)");
  bullets(s, [
    "Modelo open-weight pequeño (1–3 B, cuantizado) ejecutado en CPU",
    "Pregunta corta → observar TTFT, TPOT y tokens/s en la interfaz",
    "Misma pregunta con 3 párrafos de reglamento delante → el TTFT sube, el TPOT casi no cambia",
    "Observar la RAM usada y compararla con el tamaño del modelo",
    "Repositorio: labs/00-local-ollama (simulador disponible si Ollama falla)",
  ]);
  notes(s, "10 minutos. Antes de ejecutar, pedir a la clase que prediga qué métrica cambiará con el prompt largo. Comando: ollama run qwen2.5:1.5b --verbose y la interfaz React. Si falla la red o Ollama, usar scripts/mock_ollama.py y aclarar que las cifras son sintéticas.");
}

// ============================ UNIDAD B ============================
addSection("B · Arquitecturas base");
{
  const s = pres.addSlide({ masterName: "SECCION", sectionTitle: section });
  s.addText("Unidad B · Arquitecturas base", { placeholder: "title" });
  s.addText("¿Qué debe existir entre el usuario y el modelo para que el asistente sea seguro, observable y escalable?", { placeholder: "body" });
  s.addNotes("La mayor parte de los fallos en producción ocurren alrededor del modelo, no dentro de él.");
}
{
  const s = contentSlide("Arquitectura de referencia (D-06)");
  box(s, 0.6, 1.6, 1.8, 1.0, "Cliente web\nReact", "DCEAF4");
  box(s, 0.6, 3.1, 1.8, 1.0, "Identidad\nOIDC / SSO");
  box(s, 2.9, 1.6, 2.0, 1.0, "API Gateway\nauth, cuotas, WAF");
  box(s, 5.4, 1.6, 2.2, 1.0, "Backend /\norquestador");
  box(s, 5.4, 3.1, 2.2, 0.9, "Guardrails");
  box(s, 8.1, 1.6, 2.1, 1.0, "Gateway de\nmodelos");
  box(s, 10.6, 1.6, 2.1, 1.0, "Serving\nAPI o motor propio", "DCEAF4");
  box(s, 8.1, 3.1, 2.1, 0.9, "Vector store", "E3F2EF");
  box(s, 10.6, 3.1, 2.1, 0.9, "Objetos\ndocumentos", "E3F2EF");
  box(s, 8.1, 4.4, 2.1, 0.9, "Estado de sesión", "E3F2EF");
  box(s, 0.6, 5.6, 12.1, 0.7, "Transversal: observabilidad (logs, métricas, trazas) · secretos e identidades de carga · auditoría", "FFF4E0");
  arrow(s, 2.4, 2.1, 2.9, 2.1); arrow(s, 4.9, 2.1, 5.4, 2.1); arrow(s, 7.6, 2.1, 8.1, 2.1); arrow(s, 10.2, 2.1, 10.6, 2.1);
  arrow(s, 6.5, 2.6, 6.5, 3.1); arrow(s, 7.6, 2.4, 8.1, 3.5); arrow(s, 7.6, 2.5, 8.1, 4.8); arrow(s, 10.6, 3.55, 10.2, 3.55);
  arrow(s, 1.5, 2.6, 1.5, 3.1);
  notes(s, "Diagrama base de todo el curso. Recorrer de izquierda a derecha con una solicitud del caso. La flecha de Objetos a Vector store es la ingesta (fuera de línea). Pregunta: ¿qué caja eliminaría en un prototipo y cuál nunca? (nunca identidad ni observabilidad).");
}
{
  const s = contentSlide("Responsabilidad de cada componente");
  table(s, ["Componente", "Responsabilidad", "Falla típica", "Métrica clave"], [
    ["API Gateway", "Autenticación, límites por usuario, perímetro", "Rate limit mal dimensionado", "Rechazos 429"],
    ["Backend / orquestador", "Construir el prompt, recuperar contexto, invocar herramientas", "Prompts excesivos, timeouts encadenados", "Latencia end-to-end"],
    ["Guardrails", "Filtrar entradas y salidas indebidas", "Falsos positivos o negativos", "Tasa de bloqueo"],
    ["Gateway de modelos", "Enrutar modelos o proveedores, reintentos, cuotas", "Punto único de fallo", "Errores por proveedor"],
    ["Serving", "Ejecutar la inferencia", "Saturación de memoria, colas", "TTFT, TPOT, cola"],
    ["Vector store", "Búsqueda semántica del contexto", "Índice desactualizado o sin permisos", "Relevancia y latencia"],
    ["Observabilidad", "Trazabilidad y diagnóstico", "Registrar datos personales", "Cobertura de trazas"],
  ], { colW: [2.4, 4.1, 3.3, 2.3], fs: 13 });
  notes(s, "Enfatizar la columna 'falla típica': diseñar es anticipar cómo falla cada componente. Esta tabla será la plantilla del taller.");
}
{
  const s = contentSlide("Plano de control y plano de datos");
  box(s, 0.6, 1.6, 5.8, 3.2, "", HEX.light);
  s.addText([{ text: "Plano de control", options: { bold: true, fontSize: 20, color: C.accent1, breakLine: true } }, { text: "Despliegue de modelos · versiones de prompts · políticas · cuotas · identidades · configuración", options: { fontSize: 16 } }], { x: 0.8, y: 1.8, w: 5.4, h: 2.8, isTextBox: true, valign: "top" });
  box(s, 6.9, 1.6, 5.8, 3.2, "", "DCEAF4");
  s.addText([{ text: "Plano de datos", options: { bold: true, fontSize: 20, color: C.accent1, breakLine: true } }, { text: "Cada solicitud de usuario: gateway → backend → serving → vector store → respuesta", options: { fontSize: 16 } }], { x: 7.1, y: 1.8, w: 5.4, h: 2.8, isTextBox: true, valign: "top" });
  callout(s, "Separarlos permite escalar el plano de datos sin exponer la administración, con permisos distintos en cada uno.", 5.3);
  notes(s, "En servicios gestionados, el proveedor opera gran parte del plano de control. Pregunta: ¿quién en la universidad debería poder cambiar el prompt de sistema del asistente en producción? Relacionar con mínimo privilegio (Unidad E).");
}
{
  const s = contentSlide("Monolítico o distribuido");
  table(s, ["Criterio", "Monolito", "Distribuido"], [
    ["Complejidad inicial", "Baja", "Mayor: red, contratos, despliegues"],
    ["Escalado", "Todo escala junto", "Cada componente según su cuello de botella"],
    ["Aislamiento de fallos", "Un fallo afecta a todo", "Contenido con timeouts y circuit breakers"],
    ["Adecuado para", "Prototipo, laboratorio local", "Producción con cargas variables"],
  ], { colW: [3.0, 4.2, 4.9], fs: 15 });
  callout(s, "Recomendación: separar el serving del backend desde el inicio (perfiles GPU/memoria vs. CPU/E/S).", 4.6);
  notes(s, "Separar el serving es también lo que permite cambiar de proveedor de modelo sin tocar la aplicación: es el principio del repositorio del curso.");
}
{
  const s = contentSlide("Espectro: gestionado ↔ autogestionado");
  table(s, ["Modalidad", "Quién opera la inferencia", "Qué controla la organización", "Cuándo conviene"], [
    ["VM con GPU", "La organización", "Todo", "Investigación, aislamiento extremo"],
    ["Kubernetes con GPU", "La organización, sobre clúster gestionado", "Motor, escalado, red", "Varios modelos propios, equipo de plataforma"],
    ["Contenedores serverless", "Proveedor escala; organización aporta imagen", "Imagen y configuración", "Cargas variables, modelos pequeños"],
    ["API de modelos (MaaS)", "Proveedor", "Prompt, parámetros, cuotas, región", "Mayoría de casos al inicio"],
    ["Runtime gestionado de agentes", "Proveedor ejecuta agente, sesiones, memoria", "Lógica, herramientas, políticas", "Agentes con estado en producción"],
  ], { colW: [2.6, 3.4, 3.0, 3.1], fs: 13 });
  notes(s, "Diagrama D-08. Cuanto más hacia la API, menor costo operativo y menor control. El taller analizará el caso en ambos extremos.");
}
{
  const s = contentSlide("Patrones de integración");
  table(s, ["Patrón", "Ventaja", "Limitación", "Uso en el caso"], [
    ["Síncrono", "Simple", "El usuario espera toda la generación", "Llamadas internas cortas"],
    ["Streaming (SSE / WebSocket)", "Latencia percibida baja", "Conexiones largas, timeouts de proxies", "Conversación del asistente"],
    ["Asíncrono con cola", "Absorbe picos, reintentos", "Mayor latencia, más componentes", "Resúmenes de documentos largos"],
    ["Event-driven", "Desacoplamiento", "Trazabilidad más difícil", "Reindexar al publicar un reglamento"],
  ], { colW: [3.0, 2.8, 3.4, 2.9], fs: 15 });
  notes(s, "Diagrama D-09. Pregunta: ¿qué pasa con el streaming si el balanceador tiene un timeout de inactividad de 30 s? Respuesta: se cortan respuestas largas; hay que ajustarlo.");
}
{
  const s = contentSlide("RAG como carga de trabajo");
  flow(s, ["Documentos\nfuente", "Extraer y\ndividir", "Embeddings", "Indexar en\nvector store"], 1.6, 1.0);
  flow(s, ["Pregunta", "Embedding de\nla pregunta", "Búsqueda con\nfiltro de permisos", "Prompt con\ncontexto", "Modelo"], 3.3, 1.0);
  s.addText("Ingesta (por lotes, por eventos)", { x: 0.6, y: 1.2, w: 6, h: 0.35, fontSize: 13, bold: true, color: C.accent2, isTextBox: true });
  s.addText("Consulta (en línea, añade latencia y tokens)", { x: 0.6, y: 2.9, w: 6, h: 0.35, fontSize: 13, bold: true, color: C.accent1, isTextBox: true });
  callout(s, "Nuevos riesgos: documentos con permisos distintos e inyección indirecta a través del contenido recuperado.", 5.0, HEX.amber);
  notes(s, "Diagrama D-10. Referencia: Lewis et al. (2020), NeurIPS. Señalar que el filtro de permisos debe aplicarse por usuario final, no por el backend. Se desarrollará en la sesión de RAG.");
}
{
  const s = contentSlide("Agentes como carga de trabajo");
  table(s, ["Cambio", "Por qué importa a la infraestructura"], [
    ["Duración", "Una tarea puede tomar muchos pasos y minutos: los timeouts de chat no sirven"],
    ["Estado", "Memoria de sesión y, a veces, de largo plazo"],
    ["Identidad", "Actúa sobre sistemas reales: identidad propia con mínimo privilegio"],
    ["Costo variable", "Número de llamadas al modelo por solicitud no fijo"],
  ], { colW: [2.4, 9.7], fs: 16 });
  callout(s, "Por eso los tres proveedores ofrecen runtimes gestionados específicos para agentes (Unidad D).", 4.6);
  notes(s, "Diagrama D-11. Un agente es un LLM en un bucle que decide qué herramienta usar. Referencia: Yao et al. (2023), ReAct. Ejemplo: un agente que consulta el estado de una solicitud en el sistema académico necesita permisos de lectura, nunca de escritura.");
}
{
  const s = contentSlide("Puntos únicos de fallo y límites de escalabilidad");
  bullets(s, [
    "Candidatos a punto único de fallo en D-06:",
    "  Gateway de modelos sin réplicas",
    "  Un solo proveedor o región de modelo",
    "  Vector store sin réplica multizona",
    "  Proveedor de identidad",
    "Los límites más frecuentes son contractuales: cuotas TPM (tokens/min) y RPM del proveedor",
    "Recomendación: documentar las cuotas como requisito no funcional, con alertas antes de alcanzarlas",
  ]);
  notes(s, "En la Unidad F calcularemos la demanda del caso en tokens por minuto y la compararemos con cuotas reales.");
}
{
  const s = contentSlide("Demo 2 · Misma API, dos backends");
  bullets(s, [
    "Backend FastAPI con contrato común: /v1/chat/stream (SSE), /readyz",
    "Paso 1: proveedor = API nativa de Ollama",
    "Paso 2: cambiar solo variables de entorno a un endpoint compatible con OpenAI (/v1)",
    "El frontend, el contrato y las pruebas no cambian; cambia el adaptador",
    "Lección: aislar el proveedor reduce la dependencia y facilita la comparación multicloud",
  ]);
  notes(s, "8 minutos. APP_PROVIDER=openai_compat, APP_OPENAI_BASE_URL=http://127.0.0.1:11434/v1. Si hay cuota en Azure, repetir contra el endpoint de Foundry (verificar URL y autenticación vigentes). Mostrar app/providers en el repositorio sin leer el código en detalle.");
}

// ============================ UNIDAD C ============================
addSection("C · Infraestructura");
{
  const s = pres.addSlide({ masterName: "SECCION", sectionTitle: section });
  s.addText("Unidad C · Infraestructura", { placeholder: "title" });
  s.addText("Si la universidad aloja su propio modelo, ¿cuánta GPU necesita y dónde se ubica en la red?", { placeholder: "body" });
  s.addNotes("Esta unidad da un método reproducible de cálculo. El resultado es académico y se contrasta con mediciones en el laboratorio.");
}
{
  const s = contentSlide("CPU, GPU y jerarquía de memoria");
  table(s, ["Recurso", "Fortaleza", "Papel en inferencia LLM"], [
    ["CPU", "Pocos núcleos potentes", "Backend, tokenización, RAG; inferencia solo de modelos pequeños cuantizados"],
    ["GPU", "Miles de unidades paralelas + VRAM de alto ancho de banda", "Prefill y decode de modelos medianos y grandes"],
    ["RAM", "Capacidad alta, menor ancho de banda", "Inferencia en CPU, carga de pesos, offloading lento"],
    ["Disco / objetos", "Capacidad muy alta, lento", "Guardar pesos; determina el arranque en frío"],
  ], { colW: [2.0, 4.3, 5.8], fs: 15 });
  callout(s, "Límite superior con batch 1: tokens/s ≈ ancho de banda de memoria / tamaño de los pesos", 4.8);
  notes(s, "Ejemplo académico: un modelo de 2 GB con unos 50 GB/s de ancho de banda no supera unas 25 tokens/s. Contrastar con lo visto en la Demo 1. Por eso la GPU es necesaria para modelos de miles de millones de parámetros.");
}
{
  const s = contentSlide("Método de dimensionamiento de memoria");
  s.addText("M ≈ N × b  +  S × L × KV(bytes/token)  +  M runtime", { x: 0.6, y: 1.5, w: 12.1, h: 0.9, fontSize: 26, bold: true, color: C.accent1, align: "center", isTextBox: true });
  table(s, ["Símbolo", "Significado"], [
    ["N × b", "Pesos: parámetros × bytes por parámetro (FP16 = 2, INT8 = 1, INT4 ≈ 0,5 + escalas)"],
    ["S", "Secuencias activas simultáneas"],
    ["L", "Tokens de contexto por secuencia"],
    ["KV(bytes/token)", "2 × capas × kv_heads × d_head × bytes"],
    ["M runtime", "Activaciones, buffers y fragmentación: margen del 10–20 %"],
  ], { y: 2.7, colW: [2.6, 9.5], fs: 15 });
  notes(s, "Pedir a los estudiantes que copien la fórmula: la usarán en el ejercicio de dimensionamiento y en el taller.");
}
{
  const s = contentSlide("Ejemplo resuelto: el asistente universitario");
  bullets(s, [
    "Supuestos: modelo de 8 B tipo Llama 3.1 8B (32 capas, 8 kv_heads, d_head 128)",
    "25 % de 100 usuarios generando a la vez (S = 25) · L = 4.096 tokens · KV en FP16",
    "KV/token = 2 × 32 × 8 × 128 × 2 B = 128 KiB · KV/secuencia = 512 MiB",
  ], { h: 1.6, fs: 17 });
  table(s, ["Escenario", "Pesos", "KV cache", "Margen", "Total", "GPU que cabe"], [
    ["FP16 · 25 activas", "~15 GiB", "12,5 GiB", "~4 GiB", "~31 GiB", "Una de 40–48 GB"],
    ["INT4 · 25 activas", "~4,5 GiB", "12,5 GiB", "~2,5 GiB", "~20 GiB", "Una de 24 GB"],
    ["FP16 · 100 activas", "~15 GiB", "50 GiB", "~10 GiB", "~75 GiB", "Una de 80 GB o dos"],
  ], { y: 3.2, colW: [2.6, 1.6, 1.8, 1.6, 1.6, 2.9], fs: 15 });
  callout(s, "Para 99,9 %: dos réplicas en zonas distintas → el doble de GPU. Ejemplo académico, no medición.", 5.5, HEX.amber);
  notes(s, "Lecturas: (1) la KV cache domina el peor caso; (2) cuantizar pesos no reduce la KV cache; (3) la alta disponibilidad duplica el costo; (4) error frecuente: 'un modelo de 8B cabe en 16 GB' sin considerar concurrencia. Confirmar la configuración en el config.json del modelo elegido.");
}
{
  const s = contentSlide("Cuantización");
  table(s, ["Precisión", "Bytes por parámetro", "Modelo de 8 B", "Efecto"], [
    ["FP16 / BF16", "2", "~15 GiB", "Referencia de calidad"],
    ["INT8 / FP8", "1", "~7,5 GiB", "Menos memoria, decode más rápido"],
    ["INT4", "~0,5 + metadatos", "~4,5 GiB", "Permite CPU o GPU pequeñas; posible pérdida de calidad"],
  ], { colW: [2.4, 2.8, 2.6, 4.3], fs: 16 });
  callout(s, "Trade-off: la pérdida de calidad depende del método, del modelo y de la tarea → medir con evaluación propia.", 4.4);
  notes(s, "Referencia: Frantar et al. (2023), GPTQ. En el laboratorio local la cuantización a 4 bits es lo que permite correr un modelo de 1–3 B en un portátil sin GPU.");
}
{
  const s = contentSlide("Red: dónde vive cada componente");
  box(s, 0.6, 1.5, 12.1, 4.3, "", "F8FAFC");
  s.addText("Red virtual (VPC / VNet)", { x: 0.8, y: 1.55, w: 5, h: 0.4, fontSize: 14, bold: true, color: C.accent1, isTextBox: true });
  box(s, 0.9, 2.1, 3.4, 3.4, "Subred pública\n\nBalanceador L7\nAPI Gateway / WAF", "FFF4E0");
  box(s, 4.8, 2.1, 3.6, 3.4, "Subred privada\n\nBackend\nServing / GPU\nVector store", "DCEAF4");
  box(s, 8.9, 2.1, 3.5, 1.5, "Endpoints privados\nAPI de modelos gestionada", "E3F2EF");
  box(s, 8.9, 4.0, 3.5, 1.5, "NAT\nsalida controlada", HEX.light);
  arrow(s, 4.3, 3.8, 4.8, 3.8); arrow(s, 8.4, 2.85, 8.9, 2.85); arrow(s, 8.4, 4.75, 8.9, 4.75);
  callout(s, "Ajustar timeouts de inactividad del balanceador para streaming.", 6.0);
  notes(s, "Diagrama D-13. Solo el balanceador y el gateway en subred pública. Los endpoints privados evitan que el tráfico a la API de modelos pase por Internet; verificar soporte por servicio y región. El NAT también es un costo.");
}
{
  const s = contentSlide("Almacenamiento y vector stores");
  table(s, ["Tipo", "Contenido", "Consideración"], [
    ["Almacenamiento de objetos", "Documentos fuente; pesos en self-hosting", "Versionado, permisos; tamaño de pesos = arranque en frío"],
    ["Volúmenes de bloque", "Caché local de pesos en nodos GPU", "Acelera arranque; atado a la zona"],
    ["Vector store dedicado o búsqueda gestionada", "Embeddings e índice semántico", "Escala, búsqueda híbrida; otro servicio que operar"],
    ["Extensión vectorial (pgvector)", "Embeddings con metadatos y permisos", "Simple si ya existe PostgreSQL; evaluar escala"],
  ], { colW: [3.3, 4.1, 4.7], fs: 14 });
  callout(s, "Para el caso: priorizar el filtrado por permisos sobre el rendimiento bruto de búsqueda.", 4.9);
  notes(s, "No introducir bases de datos artificialmente: pgvector solo si ya hay PostgreSQL o si el volumen lo permite. La decisión se documenta en un ADR.");
}
{
  const s = contentSlide("Docker, Kubernetes y serverless");
  table(s, ["Criterio", "Contenedores serverless", "Kubernetes gestionado", "Funciones serverless"], [
    ["Carga operativa", "Baja", "Alta", "Muy baja"],
    ["Escalado a cero", "Sí, con arranque en frío", "Posible con componentes adicionales", "Sí"],
    ["GPU", "En algunos servicios y regiones", "Sí, con mayor control", "No para modelos medianos"],
    ["Duración de solicitudes", "Limitada por el servicio", "Sin límite propio", "Limitada"],
    ["Adecuado para", "Backend; modelos pequeños", "Plataforma de varios modelos", "Ingesta por eventos"],
  ], { colW: [2.5, 3.2, 3.2, 3.2], fs: 14 });
  callout(s, "Docker es la unidad común: el mismo contenedor corre en el portátil, en serverless o en Kubernetes.", 5.4);
  notes(s, "Ejemplos verificados: Cloud Run ofrece GPU NVIDIA L4 de 24 GB; Azure Container Apps ofrece GPU serverless. Arranque en frío: cargar 15 GB de pesos toma tiempo, lo que afecta el escalado a cero.");
}
{
  const s = contentSlide("Alta disponibilidad y despliegue multizona");
  table(s, ["Componente", "Estrategia", "Costo relativo"], [
    ["Backend sin estado", "Réplicas en varias zonas detrás del balanceador", "Bajo"],
    ["Serving propio con GPU", "Al menos dos réplicas en zonas distintas", "Alto: duplica GPU"],
    ["API de modelos gestionada", "Redundancia del proveedor; modelo o región de respaldo", "Bajo en infraestructura"],
    ["Vector store y estado", "Servicio con réplicas multizona", "Medio"],
  ], { colW: [3.2, 6.4, 2.5], fs: 15 });
  callout(s, "99,9 % mensual ≈ 43 minutos de indisponibilidad: menos que una falla típica de zona.", 4.6);
  notes(s, "Una zona de disponibilidad es un conjunto de centros de datos con energía y red independientes. Diagrama D-14. Pregunta: ¿cumple 99,9 % un asistente que depende de un solo modelo en una sola región?");
}
{
  const s = contentSlide("Dos topologías de referencia para el caso");
  box(s, 0.6, 1.5, 5.8, 4.4, "", "DCEAF4");
  s.addText([{ text: "A · Gestionada", options: { bold: true, fontSize: 20, color: C.accent1, breakLine: true } },
    { text: "Gateway + backend en contenedores serverless multizona\nAPI de modelos gestionada vía endpoint privado\nBúsqueda vectorial gestionada con filtros por permisos\nIdentidad institucional + identidades gestionadas\n\nMenor operación · costo variable · dependencia del proveedor", options: { fontSize: 15 } }], { x: 0.8, y: 1.6, w: 5.4, h: 4.2, isTextBox: true, valign: "top" });
  box(s, 6.9, 1.5, 5.8, 4.4, "", HEX.light);
  s.addText([{ text: "B · Self-hosted", options: { bold: true, fontSize: 20, color: C.accent1, breakLine: true } },
    { text: "Kubernetes con nodos GPU en dos zonas\nModelo open-weight con motor de serving propio\npgvector o vector store en la red privada\nObservabilidad y autoscaling por cola\n\nMás control · costo fijo · equipo de plataforma", options: { fontSize: 15 } }], { x: 7.1, y: 1.6, w: 5.4, h: 4.2, isTextBox: true, valign: "top" });
  notes(s, "Diagrama D-15. No elegir aún: el taller pide a cada equipo decidir con criterios. Pista: con 50.000 solicitudes al mes, la topología A suele ser más económica; la B se justifica con volumen alto o requisitos de control.");
}

// ============================ UNIDAD D ============================
addSection("D · Comparación multicloud");
{
  const s = pres.addSlide({ masterName: "SECCION", sectionTitle: section });
  s.addText("Unidad D · Comparación multicloud", { placeholder: "title" });
  s.addText("Comparar por categoría de servicio, no por catálogo de productos. Ninguna nube es ganadora en abstracto.", { placeholder: "body" });
  s.addNotes("La arquitectura D-06 es la misma en las tres nubes; solo cambia qué servicio ocupa cada caja.");
}
{
  const s = contentSlide("Mapa de categorías de servicio (13-oct-2026)");
  table(s, ["Categoría", "AWS", "Microsoft Azure", "Google Cloud"], [
    ["Plataforma de modelos", "Amazon Bedrock", "Microsoft Foundry", "Gemini Enterprise Agent Platform (antes Vertex AI)"],
    ["Runtime gestionado de agentes", "Bedrock AgentCore Runtime", "Foundry Agent Service", "Agent Engine / Agent Runtime"],
    ["SDK de agentes del proveedor", "Strands Agents", "Microsoft Agent Framework 1.x", "Agent Development Kit (ADK)"],
    ["Contenedores serverless con GPU", "ECS/EKS con instancias GPU", "Azure Container Apps (GPU)", "Cloud Run (GPU L4)"],
    ["Kubernetes gestionado", "Amazon EKS", "AKS", "GKE"],
    ["RAG / vectores gestionados", "Knowledge Bases + S3 Vectors / OpenSearch", "Azure AI Search", "Vector Search; AlloyDB/Cloud SQL + pgvector"],
    ["Identidad de cargas", "Roles de IAM", "Identidades gestionadas (Entra ID)", "Cuentas de servicio + Workload Identity"],
    ["Guardrails gestionados", "Bedrock Guardrails", "Azure AI Content Safety", "Model Armor"],
    ["Observabilidad", "CloudWatch + AgentCore Observability", "Azure Monitor + App Insights", "Cloud Logging / Monitoring / Trace"],
  ], { colW: [2.8, 3.0, 3.0, 3.3], fs: 11 });
  notes(s, "Tabla fechada: los nombres cambian. En 2026 Vertex AI pasó a llamarse Gemini Enterprise Agent Platform; Microsoft Agent Framework 1.0 es GA desde abril de 2026 y sucede a Semantic Kernel y AutoGen; Bedrock Agents pasó a Agents Classic (sin clientes nuevos desde el 30-jul-2026) y AWS recomienda AgentCore. Reverificar antes de cada cohorte.");
}
{
  const s = contentSlide("Google Cloud: arquitectura de referencia del caso");
  flow(s, ["Usuario\nIdentidad institucional", "Cloud Run\nbackend multizona", "Gemini Enterprise\nAgent Platform", "Gemini\n(modelo gestionado)"], 1.8, 1.2);
  bullets(s, [
    "Agente con ADK desplegado en Agent Engine / Agent Runtime (gestionado)",
    "Vector Search o AlloyDB/Cloud SQL con pgvector para RAG",
    "Secret Manager, cuentas de servicio con Workload Identity, Model Armor",
    "Trial: el crédito no cubre la Gemini API de AI Studio ni GPUs → usar la plataforma",
  ], { y: 3.5, h: 2.6, fs: 17 });
  notes(s, "Diagrama D-17. Laboratorios GCP-A (consola), GCP-B (ADK) y GCP-C (arquitectura) en el repositorio. Verificar la ruta de consola tras el renombre de Vertex AI.");
}
{
  const s = contentSlide("Microsoft Azure: arquitectura de referencia del caso");
  flow(s, ["Usuario\nMicrosoft Entra ID", "Container Apps\nbackend", "Foundry Agent Service\nprompt / hosted agents", "Foundry Models\n(gpt-5-mini en Tier 0)"], 1.8, 1.2);
  bullets(s, [
    "Agent Framework 1.x para agentes en código; Semantic Kernel y AutoGen en mantenimiento",
    "LangGraph puede ejecutarse como hosted agent: framework externo, no oficial de Microsoft",
    "Azure AI Search para RAG · Key Vault · identidades gestionadas · API Management como AI gateway",
    "Trial: validar cuota (Free Tier / Tier 0) antes del laboratorio",
  ], { y: 3.5, h: 2.6, fs: 17 });
  notes(s, "Diagrama D-18. Es la nube de la Demo 3 en esta cohorte. La documentación oficial de cuotas (20-ago-2026) define un Tier 0 con gpt-5-mini y gpt-4.1-mini; hay reportes de trials con cuota 0, por eso se valida antes.");
}
{
  const s = contentSlide("AWS: arquitectura de referencia del caso");
  flow(s, ["Usuario\nproveedor OIDC", "API Gateway +\nECS / Lambda", "Bedrock AgentCore\nRuntime, Identity, Gateway", "Amazon Bedrock\nmodelos"], 1.8, 1.2);
  bullets(s, [
    "Agente con Strands Agents desplegado en AgentCore Runtime (sesiones aisladas)",
    "Bedrock Knowledge Bases con S3 Vectors u OpenSearch para RAG",
    "Roles de IAM de mínimo privilegio · Secrets Manager · Bedrock Guardrails",
    "Cuentas nuevas: usar AgentCore; Bedrock Agents Classic ya no admite clientes nuevos",
  ], { y: 3.5, h: 2.6, fs: 17 });
  notes(s, "Diagrama D-19. Recomendar el plan Paid con presupuesto en AWS Budgets porque el plan Free excluye algunos servicios. Laboratorios AWS-A a AWS-D en el repositorio.");
}
{
  const s = contentSlide("SDK, runtime y servicio de modelos: tres capas distintas");
  box(s, 2.0, 1.5, 9.3, 1.1, "Código del agente — SDK o framework\nStrands · Agent Framework · ADK · LangGraph", "DCEAF4", HEX.ink, 15);
  box(s, 2.0, 3.1, 9.3, 1.1, "Runtime de ejecución — gestionado o propio\nAgentCore · Foundry Agent Service · Agent Engine · contenedor", HEX.light, HEX.ink, 15);
  box(s, 2.0, 4.7, 9.3, 1.1, "Servicio de modelos — quién hace la inferencia\nBedrock · Foundry Models · Gemini · Ollama local", "E3F2EF", HEX.ink, 15);
  arrow(s, 6.65, 2.6, 6.65, 3.1); arrow(s, 6.65, 4.2, 6.65, 4.7);
  notes(s, "Diagrama D-20. Error frecuente: comparar Strands con Bedrock, o ADK con Gemini. Son capas combinables: un agente LangGraph puede correr en Foundry con un modelo de Azure; un agente Strands puede usar Ollama en local y Bedrock en producción.");
}
{
  const s = contentSlide("Responsabilidades y criterios de selección");
  table(s, ["Responsabilidad", "API de modelos", "Runtime de agentes", "Self-hosting"], [
    ["Capacidad GPU y escalado", "Proveedor", "Proveedor", "Organización"],
    ["Sesiones y memoria del agente", "Organización", "Proveedor", "Organización"],
    ["Identidad, red, datos, prompts", "Organización", "Organización", "Organización"],
    ["Calidad y seguridad de las respuestas", "Organización", "Organización", "Organización"],
  ], { colW: [3.9, 2.7, 2.7, 2.8], fs: 14 });
  bullets(s, [
    "Criterios: ecosistema existente · modelos y región · residencia de datos · capacidades del equipo · costo total · portabilidad",
    "Estándares abiertos que reducen el lock-in: MCP (herramientas), A2A (agentes), OpenTelemetry (trazas)",
  ], { y: 4.4, h: 1.8, fs: 16 });
  notes(s, "Lección central: ninguna modalidad traslada al proveedor la responsabilidad por lo que el asistente responde. Recomendación: contrato de API propio + herramientas como MCP para poder cambiar de proveedor.");
}
{
  const s = contentSlide("Demo 3 · Agente gestionado en Microsoft Foundry");
  bullets(s, [
    "Proyecto Foundry y despliegue de un modelo pequeño (gpt-5-mini)",
    "Prompt agent: instrucciones del asistente universitario",
    "Una herramienta de consulta (p. ej., calendario académico de ejemplo)",
    "Probar en el playground y revisar la traza de la ejecución",
    "Señalar los límites de confianza: identidad, herramienta, datos, modelo",
  ]);
  notes(s, "12 minutos. Ejecutar desde una suscripción con cuota validada. Si la cuota falla en vivo, usar la grabación preparada. Laboratorio completo AZ-A en el repositorio, con limpieza de recursos.");
}

// ============================ UNIDAD E ============================
addSection("E · Seguridad");
{
  const s = pres.addSlide({ masterName: "SECCION", sectionTitle: section });
  s.addText("Unidad E · Seguridad", { placeholder: "title" });
  s.addText("En un LLM, los datos y las instrucciones viajan por el mismo canal.", { placeholder: "body" });
  s.addNotes("Cualquier texto que llegue al prompt (documento recuperado, salida de herramienta) puede intentar comportarse como instrucción. Se diseña suponiendo que el modelo puede ser engañado.");
}
{
  const s = contentSlide("Responsabilidad compartida en aplicaciones LLM");
  table(s, ["Siempre del proveedor", "Siempre de la organización"], [
    ["Seguridad física e infraestructura", "Identidades y permisos"],
    ["En gestionados: modelo y disponibilidad", "Clasificación y protección de datos"],
    ["Parches de la plataforma gestionada", "Configuración de red"],
    ["", "Prompts, documentos y herramientas del agente"],
    ["", "Evaluación de lo que el sistema responde"],
  ], { colW: [6.05, 6.05], fs: 16 });
  notes(s, "Diagrama D-21. Pregunta: si el asistente revela notas de otro estudiante usando un modelo gestionado, ¿de quién es la responsabilidad? De la universidad: el fallo está en permisos y en la recuperación.");
}
{
  const s = contentSlide("Identidad sin secretos estáticos y mínimo privilegio");
  table(s, ["Identidad", "Mecanismo recomendado", "Riesgo que evita"], [
    ["Usuario", "SSO institucional con OIDC; RBAC por perfil", "Acceso anónimo; información de otro perfil"],
    ["Carga de trabajo", "Identidad gestionada o workload identity", "Claves de API en código o repositorios"],
    ["Herramienta del agente", "Credenciales de alcance mínimo; acceso en nombre del usuario", "Agente con más permisos que el usuario"],
  ], { colW: [2.6, 5.0, 4.5], fs: 15 });
  callout(s, "RAG: filtrar la recuperación por los permisos del usuario final, no por los del backend.", 4.4, HEX.red);
  notes(s, "Diagrama D-22. Si el índice contiene actas restringidas y la búsqueda no filtra, el modelo las citará a quien pregunte. Es el riesgo más frecuente en asistentes institucionales.");
}
{
  const s = contentSlide("Red, cifrado y protección de datos");
  bullets(s, [
    "Inferencia y datos en subredes privadas; endpoints privados hacia servicios gestionados",
    "TLS en todos los saltos; cifrado en reposo con llaves gestionadas por el cliente si la política lo exige",
    "Minimización: no enviar al modelo datos personales que la respuesta no necesite",
    "Residencia: algunos despliegues 'globales' pueden procesar fuera de la región del recurso",
    "Colombia: Ley Estatutaria 1581 de 2012 y decretos reglamentarios; análisis jurídico de la oficina competente",
  ]);
  notes(s, "No dar asesoría jurídica: identificar el requisito y remitir a la oficina de protección de datos de la universidad. Relacionar residencia con la elección del tipo de despliegue (global, zona de datos, regional).");
}
{
  const s = contentSlide("OWASP Top 10 para aplicaciones LLM 2025");
  table(s, ["Riesgo", "En el asistente", "Control principal"], [
    ["LLM01 Prompt Injection", "Instrucciones en la pregunta o en un documento", "Separar instrucciones y datos, guardrails, mínimo privilegio"],
    ["LLM02 Sensitive Info Disclosure", "Datos de otros estudiantes", "Filtrado por permisos, minimización"],
    ["LLM03 Supply Chain", "Modelo o dependencia comprometidos", "Fuentes verificadas, versiones fijadas"],
    ["LLM04 Data/Model Poisoning", "Documento alterado en el corpus", "Procedencia y control de cambios"],
    ["LLM05 Improper Output Handling", "Salida ejecutada sin validar", "Tratar la salida como no confiable"],
    ["LLM06 Excessive Agency", "Agente con permisos de escritura", "Mínimo privilegio, aprobación humana"],
    ["LLM07 System Prompt Leakage", "Exposición de instrucciones", "Sin secretos ni autorización en el prompt"],
    ["LLM08 Vector/Embedding Weaknesses", "Acceso indebido al índice", "Control de acceso en el vector store"],
    ["LLM09 Misinformation", "Respuesta incorrecta de reglamento", "RAG con citas, evaluación"],
    ["LLM10 Unbounded Consumption", "Abuso que agota cuota", "Rate limiting, límites de tokens"],
  ], { colW: [3.5, 3.9, 4.7], fs: 11 });
  notes(s, "OWASP Top 10 for LLM Applications 2025 (v2.0). Para agentes, OWASP publicó el Top 10 for Agentic Applications for 2026 (anunciado en diciembre de 2025) (ASI01 secuestro de objetivo, ASI02 mal uso de herramientas, ASI03 abuso de identidad y privilegios). Ambas listas son complementarias.");
}
{
  const s = contentSlide("Inyección indirecta a través de RAG");
  flow(s, ["Atacante inserta\ninstrucción en\nun documento", "Usuario legítimo\npregunta", "Backend recupera\nel fragmento", "Prompt =\ninstrucciones +\npregunta + fragmento", "Respuesta\ninfluida por\nel atacante"], 1.8, 1.5);
  bullets(s, [
    "No existe hoy un control que elimine por completo la inyección de prompts",
    "Objetivo de diseño: limitar el daño posible cuando ocurre",
    "Controles: procedencia de documentos, delimitación de datos, guardrails de salida, herramientas de mínimo privilegio",
  ], { y: 3.8, h: 2.4, fs: 17 });
  notes(s, "Diagrama D-23. Referencia: Greshake et al. (2023), AISec. Ejemplo: un PDF publicado por terceros en el repositorio institucional con texto oculto. La defensa más efectiva es que el agente no tenga permisos peligrosos.");
}
{
  const s = contentSlide("Defensa en profundidad, auditoría y gobierno");
  table(s, ["Capa", "Controles"], [
    ["Perímetro", "WAF, autenticación en el gateway, rate limiting"],
    ["Entrada", "Guardrails, límites de longitud, detección de inyección"],
    ["Contexto", "Filtrado por permisos, procedencia de documentos"],
    ["Modelo y agente", "Instrucciones de sistema, herramientas de mínimo privilegio, aprobación humana"],
    ["Salida", "Guardrails de salida, validación antes de ejecutar o mostrar"],
    ["Operación", "Logging seguro, trazas por solicitud, auditoría, respuesta a incidentes"],
  ], { colW: [2.4, 9.7], fs: 14 });
  callout(s, "Gobierno: NIST AI RMF y perfil de IA generativa · ISO/IEC 42001 (sistemas de gestión de IA)", 5.6);
  notes(s, "Diagrama D-24. Logging seguro: registrar metadatos completos (usuario seudónimo, tokens, latencias, documentos citados) y contenido solo enmascarado y con retención limitada. El laboratorio local ya lo aplica: no registra el contenido de las conversaciones.");
}

// ============================ UNIDAD F ============================
addSection("F · Rendimiento y FinOps");
{
  const s = pres.addSlide({ masterName: "SECCION", sectionTitle: section });
  s.addText("Unidad F · Rendimiento, SLO y FinOps", { placeholder: "title" });
  s.addText("¿Es suficientemente rápido? ¿Cuánto costará? Traducir supuestos a solicitudes y tokens.", { placeholder: "body" });
  s.addNotes("Con dos cifras (solicitudes por segundo y tokens por minuto) se dimensiona tanto una cuota gestionada como un despliegue propio.");
}
{
  const s = contentSlide("Latencia end-to-end y métricas de inferencia");
  flow(s, ["Red", "Gateway", "Recuperación\nRAG", "Cola", "Prefill", "Decode", "Posproceso"], 1.5, 0.9);
  table(s, ["Métrica", "Definición", "Lo que percibe el usuario"], [
    ["TTFT", "Tiempo hasta el primer token", "Tarda en empezar a responder"],
    ["TPOT", "(Latencia total − TTFT) / (tokens de salida − 1)", "Velocidad del texto en pantalla"],
    ["Throughput", "Tokens o solicitudes por segundo del sistema", "No lo percibe; determina el costo"],
  ], { y: 2.9, colW: [2.0, 5.8, 4.3], fs: 15 });
  callout(s, "Reportar percentiles (p50, p95, p99), nunca solo promedios.", 5.4);
  notes(s, "Diagrama D-25. El promedio oculta a los usuarios que esperan más. El backend del laboratorio calcula TTFT y TPOT con esta fórmula.");
}
{
  const s = contentSlide("Concurrencia, colas y saturación");
  s.addText("Ley de Little:  L = λ × W", { x: 0.6, y: 1.3, w: 12.1, h: 0.6, fontSize: 22, bold: true, color: C.accent1, align: "center", isTextBox: true });
  table(s, ["Magnitud del caso", "Cálculo", "Resultado"], [
    ["Tasa de llegada λ", "100 usuarios / 60 s", "≈ 1,7 solicitudes/s"],
    ["Solicitudes en curso L", "1,7 × 10 s", "≈ 17 (coherente con S = 25)"],
    ["Tokens de entrada por minuto", "100 × 3.000", "300.000"],
    ["Tokens de salida por minuto", "100 × 300", "30.000"],
    ["Demanda en hora pico", "", "≈ 330.000 tokens/min"],
  ], { y: 2.1, colW: [4.0, 4.0, 4.1], fs: 15 });
  callout(s, "El 90 % de los tokens son de entrada: recortar el contexto RAG ahorra más que acortar respuestas.", 5.5);
  notes(s, "Supuestos: cada usuario pregunta una vez por minuto, respuesta de ~10 s, 3.000 tokens de entrada y 300 de salida. Esta cifra se compara con la cuota TPM del proveedor. Cuando λ se acerca a la capacidad, la cola crece de forma no lineal (curva D-26).");
}
{
  const s = contentSlide("SLI, SLO y SLA");
  table(s, ["Concepto", "Definición", "Ejemplo para el asistente"], [
    ["SLI", "Indicador medido", "Proporción de solicitudes exitosas; TTFT p95"],
    ["SLO", "Objetivo interno", "99,9 % mensual; TTFT p95 ≤ 2 s (propuesta a validar)"],
    ["SLA", "Acuerdo contractual con consecuencias", "Lo que el proveedor garantiza a la universidad"],
  ], { colW: [1.8, 4.3, 6.0], fs: 16 });
  callout(s, "Presupuesto de error: 0,1 % × 43.200 min ≈ 43 min al mes.", 4.0);
  bullets(s, ["Si el SLA del proveedor de modelos es menor que el SLO del asistente, el objetivo es inalcanzable sin redundancia"], { y: 4.9, h: 1, fs: 16 });
  notes(s, "Referencia: Google SRE Book. El SLA concreto de cada servicio se verificará en los laboratorios cloud. Pregunta: ¿qué SLI elegirían para medir la calidad de las respuestas, no solo la disponibilidad?");
}
{
  const s = contentSlide("Costo por token frente a costo de infraestructura");
  table(s, ["", "API gestionada", "Self-hosting"], [
    ["Fórmula", "Σ (tokens entrada × precio + tokens salida × precio)", "réplicas × horas × precio GPU-hora + operación"],
    ["Naturaleza", "Variable, proporcional al uso", "Fija por réplica y hora, se use o no"],
    ["Caso (sin precios)", "50.000 solicitudes/mes ≈ 165 M tokens", "2 réplicas × 720 h = 1.440 GPU-horas"],
  ], { colW: [2.4, 4.9, 4.8], fs: 15 });
  lineChart(s, { x: 0.6, y: 3.6, w: 6.4, h: 3.2, title: "D-27 · Unidades ilustrativas, sin precios",
    xTitle: "Millones de tokens al mes", yTitle: "Costo relativo",
    series: [
      { name: "API por token (variable)", labels: ["0", "100", "200", "300", "400", "500", "600"], values: [0, 17, 33, 50, 67, 83, 100] },
      { name: "GPU propia, 2 réplicas (fija)", labels: ["0", "100", "200", "300", "400", "500", "600"], values: [60, 60, 60, 60, 60, 60, 60] },
    ] });
  bullets(s, [
    "El punto de cruce depende de precios reales: calcularlo con tarifas oficiales fechadas (MC-01)",
    "FinOps: etiquetas · presupuestos y alertas · límites de tokens por usuario",
    "Optimizar: recortar contexto RAG · modelo pequeño para preguntas simples · caché",
  ], { x: 7.3, y: 3.7, w: 5.4, h: 3.0, fs: 14 });
  notes(s, "Diagrama D-27. Con volúmenes bajos y variables la API suele ser más económica; el self-hosting se justifica con volumen alto y sostenido o requisitos de control. Los precios reales se calculan con tarifas oficiales fechadas en el laboratorio MC-01, no en la clase.");
}
{
  const s = contentSlide("Demo 4 · Concurrencia frente a latencia");
  table(s, ["Conc.", "TTFT p95 (ms)", "E2E p95 (ms)", "Sol./s"], [
    ["1", "132,0", "1.110,8", "0,91"],
    ["2", "118,7", "1.095,7", "1,83"],
    ["4", "1.212,8", "2.187,8", "1,83"],
    ["8", "3.394,2", "4.372,0", "1,83"],
  ], { w: 5.8, colW: [1.0, 1.7, 1.7, 1.4], fs: 14 });
  lineChart(s, { x: 6.8, y: 1.3, w: 5.9, h: 4.4, title: "D-26 · TTFT p95 frente a concurrencia",
    xTitle: "Solicitudes concurrentes", yTitle: "ms", showValue: true,
    series: [{ name: "TTFT p95", labels: ["1", "2", "4", "8"], values: [132, 119, 1213, 3394] }] });
  callout(s, "Cifras sintéticas del simulador (capacidad 2): el throughput se estanca y el exceso se convierte en cola.", 6.0, HEX.amber);
  notes(s, "8 minutos. Ejecutar: python load-tests/loadtest.py --levels 1 2 4 8 --requests 8 contra Ollama real; si no está disponible, mostrar esta tabla del simulador (13-oct-2026) aclarando que no mide un modelo real. Pregunta: ¿cuál es la capacidad de este servidor y qué SLO de TTFT cumple?");
}

// ============================ CIERRE ============================
addSection("Cierre");
{
  const s = contentSlide("Taller · Topología base del asistente universitario");
  bullets(s, [
    "Equipos de 3–4 personas · 14 minutos · plantilla D-28",
    "Entregable:",
    "  Diagrama con al menos 8 componentes, límites de red y de confianza",
    "  Decisión gestionado vs. autogestionado con 3 criterios (formato ADR)",
    "  Un SLO, una estimación de memoria o de tokens/min y 5 riesgos OWASP con su control",
    "Dos equipos exponen 3 minutos cada uno",
    "Rúbrica: componentes · justificación · seguridad · rendimiento y costo · comunicación",
  ]);
  notes(s, "Circular entre los equipos. Preguntas guía: ¿dónde está la identidad? ¿qué pasa si cae una zona? ¿cuántos tokens por minuto necesitan? La rúbrica completa está en sesiones/s01-arquitecturas-base/evaluacion.");
}
{
  const s = contentSlide("Síntesis: siete decisiones de una topología base");
  table(s, ["#", "Decisión", "Criterio principal"], [
    ["1", "Comprar o producir inferencia", "Volumen, control de datos, capacidad del equipo"],
    ["2", "Patrón de integración", "Streaming para conversación; colas para tareas largas"],
    ["3", "Dimensionamiento", "Pesos + KV cache + concurrencia + réplicas para HA"],
    ["4", "Topología de red", "Componentes privados; endpoints privados"],
    ["5", "Identidad", "OIDC para usuarios; sin secretos estáticos para cargas"],
    ["6", "Datos y RAG", "Filtrado por permisos del usuario final"],
    ["7", "SLO y costos", "Percentiles, presupuesto de error, tokens por minuto"],
  ], { colW: [0.6, 4.6, 6.9], fs: 15 });
  notes(s, "Cerrar retomando la pregunta inicial: lo que hay entre el usuario y el modelo son estas siete decisiones. Cuestionario de cierre de 5 preguntas (evaluación formativa).");
}
{
  const s = contentSlide("Próxima sesión y laboratorios");
  bullets(s, [
    "Repositorio: llm-infra-escalable (GitHub)",
    "  LOC-01 · Ollama + FastAPI + React + prueba de carga",
    "  GCP-A/B/C · Azure AZ-A a AZ-F · AWS-A a AWS-D · MC-01 comparativo",
    "Cuentas trial: crear la de cada nube la semana de su bloque; configurar presupuesto y limpiar recursos",
    "Tarea: completar el ADR del taller y la tabla de mapeo multicloud",
    "Sesión 2: continuidad sobre model serving, escalado y rendimiento",
  ]);
  notes(s, "Recordar las limitaciones de las cuentas trial verificadas: Azure con cuota a validar, AWS con plan Paid recomendado y GCP sin GPU ni modelos de terceros en la trial.");
}
{
  const s = contentSlide("Referencias (1/2) · Documentación oficial y estándares");
  bullets(s, [
    "Microsoft. Microsoft Agent Framework 1.0 (3-abr-2026). devblogs.microsoft.com/agent-framework",
    "Microsoft Learn. Foundry Agent Service overview; Azure OpenAI in Foundry Models quotas and limits (ago-2026)",
    "Google Cloud. Agent Development Kit overview; GPU support for Cloud Run services",
    "AWS. Amazon Bedrock AgentCore documentation; Bedrock Agents Classic maintenance mode; S3 Vectors GA (dic-2025)",
    "Strands Agents. Python Quickstart. strandsagents.com",
    "OWASP. Top 10 for LLM Applications 2025 (v2.0); Top 10 for Agentic Applications for 2026",
    "NIST AI 100-1 (AI RMF 1.0, ene-2023) y AI 600-1 (jul-2024) · NIST SP 800-207 (2020) · ISO/IEC 42001:2023 · Ley 1581 de 2012",
  ], { fs: 15 });
  notes(s, "Enlaces completos y estado de verificación en docs/referencias.md del repositorio. Las referencias marcadas como 'por verificar' no se citan como definitivas.");
}
{
  const s = contentSlide("Referencias (2/2) · Literatura académica");
  bullets(s, [
    "Vaswani et al. (2017). Attention Is All You Need. NeurIPS.",
    "Yu et al. (2022). Orca: A Distributed Serving System for Transformer-Based Generative Models. OSDI.",
    "Pope et al. (2023). Efficiently Scaling Transformer Inference. MLSys.",
    "Kwon et al. (2023). Efficient Memory Management for LLM Serving with PagedAttention. SOSP.",
    "Frantar et al. (2023). GPTQ. ICLR.",
    "Lewis et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. NeurIPS.",
    "Yao et al. (2023). ReAct. ICLR · Greshake et al. (2023). Indirect Prompt Injection. AISec.",
  ], { fs: 15 });
  notes(s, "Lecturas recomendadas para la semana: Kwon et al. (PagedAttention) y OWASP LLM Top 10 2025.");
}

(async () => {
  const out = path.join(__dirname, "S01-Arquitecturas-Base-LLM.pptx");
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log("OK", out);
})();
