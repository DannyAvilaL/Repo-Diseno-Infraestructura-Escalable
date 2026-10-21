// Genera S02-Topologias-Casos-Empresariales.pptx (notas del expositor en cada diapositiva).
// Uso: node build_deck.js  (requiere pptxgenjs; APPLY_THEME apunta a apply_theme.js del skill pptx)
const pptxgen = require("pptxgenjs");
const path = require("path");
const { applyTheme } = require(process.env.APPLY_THEME || "/mnt/skills/public/pptx/scripts/apply_theme.js");

// Misma paleta del curso (Sesión 1) para coherencia entre sesiones.
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
const HEX = { navy: "13324B", blue: "1F6F9F", teal: "2E9C8A", amber: "D98E2B", red: "B5443A", violet: "6B5B95", grey: "7A8794", light: "F2F4F6", line: "C9D1D9", ink: "1B1F24", sky: "DCEAF4", mint: "E3F2EF", sand: "FBEFD9", rose: "F6E1DF" };

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5 in
pres.title = "Sesión 2 · Diseño de Topologías y Casos de Uso Empresariales";
pres.subject = "Diseño de Infraestructura Escalable para LLMs";
pres.author = "Curso Diseño de Infraestructura Escalable para LLMs";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;

pres.defineSlideMaster({
  title: "PORTADA",
  background: { color: HEX.navy },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.1, w: 11.7, h: 1.7, fontSize: 40, bold: true, color: C.background1, align: "left" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 3.9, w: 11.7, h: 1.6, fontSize: 20, color: C.background2 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "SECCION",
  background: { color: HEX.blue },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.3, w: 11.7, h: 1.5, fontSize: 38, bold: true, color: C.background1, align: "left" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.8, y: 3.8, w: 11.7, h: 1.5, fontSize: 20, color: C.background2 }, text: "" } },
  ],
  slideNumber: { x: 12.4, y: 6.95, w: 0.7, h: 0.35, fontSize: 10, color: C.background1 },
});
pres.defineSlideMaster({
  title: "CONTENIDO",
  background: { color: "FFFFFF" },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.3, w: 12.1, h: 0.9, fontSize: 28, bold: true, color: C.text2, valign: "middle", align: "left" }, text: "" } },
    { text: { text: "Diseño de Infraestructura Escalable para LLMs · Sesión 2", options: { x: 0.6, y: 6.95, w: 8, h: 0.35, fontSize: 10, color: C.accent6 } } },
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
function divider(title, question, notesText) {
  const s = pres.addSlide({ masterName: "SECCION", sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  s.addText(question, { placeholder: "body" });
  s.addNotes(notesText);
  return s;
}
function bullets(s, items, opts = {}) {
  const x = opts.x ?? 0.6, y = opts.y ?? 1.4, w = opts.w ?? 12.1, h = opts.h ?? 5.3, fs = opts.fs ?? 18;
  s.addText(
    items.map((t, i) => {
      const sub = t.startsWith("  ");
      return { text: t.trim(), options: { bullet: sub ? { indent: 18 } : true, indentLevel: sub ? 1 : 0, fontSize: sub ? fs - 2 : fs, color: sub ? C.accent6 : C.text1, breakLine: i < items.length - 1, paraSpaceAfter: 6 } };
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
function callout(s, text, y = 6.15, color = HEX.teal) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y, w: 12.1, h: 0.62, rectRadius: 0.08, fill: { color }, line: { color } });
  s.addText(text, { x: 0.8, y, w: 11.7, h: 0.62, fontSize: 15, bold: true, color: "FFFFFF", valign: "middle", isTextBox: true, margin: 0 });
}
function box(s, x, y, w, h, text, fill = HEX.light, opts = {}) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: fill }, line: { color: opts.line ?? HEX.blue, width: opts.lineW ?? 1, dashType: opts.dash ?? "solid" } });
  s.addText(text, { x, y, w, h, fontSize: opts.fs ?? 13, bold: opts.bold ?? false, color: opts.color ?? HEX.ink, align: "center", valign: "middle", isTextBox: true, margin: 0.05 });
}
function circle(s, x, y, d, text, fill, color = "FFFFFF", fs = 14) {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill } });
  s.addText(text, { x, y, w: d, h: d, fontSize: fs, bold: true, color, align: "center", valign: "middle", isTextBox: true, margin: 0 });
}
function arrow(s, x1, y1, x2, y2, color = HEX.grey, dash = "solid") {
  s.addShape(pres.shapes.LINE, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1) || 0.001, h: Math.abs(y2 - y1) || 0.001, flipH: x2 < x1, flipV: y2 < y1, line: { color, width: 1.5, endArrowType: "triangle", dashType: dash } });
}
function label(s, x, y, w, h, text, opts = {}) {
  s.addText(text, { x, y, w, h, fontSize: opts.fs ?? 12, color: opts.color ?? HEX.grey, bold: opts.bold ?? false, italic: opts.italic ?? false, align: opts.align ?? "left", valign: opts.valign ?? "middle", isTextBox: true, margin: 0 });
}
function flow(s, steps, y = 2.0, h = 1.2, fills) {
  const n = steps.length, gap = 0.3, w = (12.1 - gap * (n - 1)) / n;
  steps.forEach((t, i) => {
    const x = 0.6 + i * (w + gap);
    box(s, x, y, w, h, t, fills ? fills[i] : (i === 0 ? HEX.sky : HEX.light), { fs: 13 });
    if (i < n - 1) arrow(s, x + w, y + h / 2, x + w + gap, y + h / 2);
  });
}
function chartBase(opts) {
  return {
    x: opts.x, y: opts.y, w: opts.w, h: opts.h,
    showTitle: true, title: opts.title, titleFontSize: 12, titleColor: HEX.ink, titleFontFace: "+mn-lt",
    showLegend: opts.legend ?? false, legendPos: "b", legendFontSize: 10, legendFontFace: "+mn-lt",
    catAxisLabelColor: HEX.grey, valAxisLabelColor: HEX.grey, catAxisLabelFontSize: 10, valAxisLabelFontSize: 10,
    catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
    showCatAxisTitle: !!opts.xTitle, catAxisTitle: opts.xTitle, catAxisTitleFontSize: 10, catAxisTitleColor: HEX.grey, catAxisTitleFontFace: "+mn-lt",
    showValAxisTitle: !!opts.yTitle, valAxisTitle: opts.yTitle, valAxisTitleFontSize: 10, valAxisTitleColor: HEX.grey, valAxisTitleFontFace: "+mn-lt",
    valGridLine: { color: "E5E8EB", size: 0.5 }, catGridLine: { style: "none" },
    dataLabelFontSize: 10, dataLabelFontFace: "+mn-lt", dataLabelColor: HEX.ink,
  };
}
const REF = "Fuentes: documentación oficial citada en docs/referencias.md (estado al 20-oct-2026) y bibliografía del curso.";
function notes(s, text) { s.addNotes(text + "\n\n" + REF); }

// ================================================================ APERTURA
addSection("Apertura");
{
  const s = pres.addSlide({ masterName: "PORTADA", sectionTitle: section });
  s.addText("Diseño de Topologías y Casos de Uso Empresariales", { placeholder: "title" });
  s.addText("Capítulo 1 · Fundamentos de Infraestructura para LLMs · Sesión 2 (180 min)\nInferencia online y por lotes · Multi-región y redundancia · Selección de servicios · Diseño preliminar", { placeholder: "body" });
  s.addNotes("Bienvenida. La Sesión 1 respondió qué hay entre el usuario y el modelo. Hoy respondemos dónde vive cada pieza, cuántas copias necesita y qué servicio la implementa. Igual que en la Sesión 1, la presentación es teórica; el código está en el repositorio (LOC-02, AZ-G, GCP-D, AWS-E). Al final, los equipos harán un diseño preliminar para un caso empresarial.");
}
{
  const s = contentSlide("Pregunta guía: ¿la misma topología sirve para todo?");
  bullets(s, [
    "El asistente universitario de la Sesión 1 ahora tiene tres cargas de trabajo distintas:",
    "  Estudiantes conversando en temporada de matrículas: alguien espera cada respuesta",
    "  20.000 PQRS al mes que se clasifican cada noche: nadie espera, importa el plazo",
    "  Reindexación semanal de documentos para RAG: volumen alto, sin urgencia",
    "Nuevo requisito institucional: el asistente debe seguir operando si cae una región de la nube",
    "Las cifras son hipótesis de diseño, no mediciones",
  ], { w: 7.2, fs: 18 });
  box(s, 8.3, 1.5, 4.4, 1.1, "Online · conversación\nSLO de latencia", HEX.sky, { fs: 14 });
  box(s, 8.3, 2.9, 4.4, 1.1, "Batch · PQRS nocturnas\nSLO de plazo", HEX.mint, { fs: 14 });
  box(s, 8.3, 4.3, 4.4, 1.1, "Batch · reindexación\nSLO de plazo y costo", HEX.sand, { fs: 14 });
  label(s, 8.3, 5.55, 4.4, 0.5, "¿Una topología, dos o tres?", { fs: 15, bold: true, color: HEX.navy, align: "center" });
  notes(s, "Presentar el caso ampliado. Pregunta a la clase (2 minutos): ¿pondrían las tres cargas en el mismo endpoint, con la misma cuota y el mismo SLO? Anotar respuestas. Al final de la Unidad A volveremos a ellas. Insistir en que 20.000 PQRS al mes y la temporada de matrículas son supuestos académicos.");
}
{
  const s = contentSlide("Resultados de aprendizaje y agenda");
  table(s, ["RA", "Al finalizar podrá…", "Bloque"], [
    ["RA1", "Distinguir inferencia online, asíncrona y por lotes por su SLO, costo y patrón de arquitectura", "Unidad A · Demo 1"],
    ["RA2", "Calcular la disponibilidad compuesta de una topología y relacionarla con RTO y RPO", "Unidad B"],
    ["RA3", "Diseñar topologías redundantes (multizona, activo-pasivo, activo-activo) con patrones de resiliencia", "Unidad B · Demo 2"],
    ["RA4", "Seleccionar servicios gestionados de Azure, Google Cloud y AWS según el caso de uso", "Unidad C · Demo 3"],
    ["RA5", "Evaluar residencia de datos, seguridad y costo de una topología multi-región", "Unidad D"],
    ["RA6", "Elaborar y justificar un diseño preliminar con un ADR", "Taller"],
  ], { colW: [0.8, 8.6, 2.7], fs: 14 });
  label(s, 0.6, 5.3, 12.1, 0.9, "Agenda: apertura 8 min · A 27 min · B 40 min · pausa 10 min · C 40 min · D 15 min · taller 30 min · cierre 10 min.\nDistribución ajustada a 60 % teoría, 16 % demostraciones y 24 % taller y discusión, porque el tema incluye un ejercicio de diseño.", { fs: 13 });
  notes(s, "Recorrer los resultados. Explicar el ajuste de la distribución 65/25/10 del curso: el tema incluye explícitamente un ejercicio práctico de diseño preliminar, por eso el taller pesa más. Laboratorios del repositorio: LOC-02 (local), AZ-G (Azure), GCP-D (Google Cloud), AWS-E (AWS).");
}
{
  const s = contentSlide("De la Sesión 1 a la Sesión 2: de componentes a topologías");
  box(s, 0.6, 1.5, 5.6, 4.3, "", "FFFFFF", { line: HEX.line });
  label(s, 0.85, 1.6, 5.1, 0.5, "Sesión 1 · qué componentes existen", { fs: 16, bold: true, color: HEX.navy });
  bullets(s, [
    "Arquitectura de referencia (D-06)",
    "Prefill, decode, KV cache, batching",
    "Gestionado vs. autogestionado",
    "Mapa de servicios en tres nubes",
    "OWASP LLM 2025 por capa",
    "TTFT, TPOT y costo por token",
  ], { x: 0.85, y: 2.2, w: 5.1, h: 3.4, fs: 16 });
  arrow(s, 6.3, 3.65, 7.0, 3.65, HEX.blue);
  box(s, 7.1, 1.5, 5.6, 4.3, "", HEX.sky, { line: HEX.blue });
  label(s, 7.35, 1.6, 5.1, 0.5, "Sesión 2 · dónde y cuántas copias", { fs: 16, bold: true, color: HEX.navy });
  bullets(s, [
    "Qué carga es online y cuál es batch",
    "Cuántas zonas y regiones, y con qué estrategia",
    "Quién conmuta: el proveedor, un gateway o el cliente",
    "Qué servicio implementa cada carga",
    "Qué cuesta la redundancia y dónde viajan los datos",
    "Diseño preliminar con ADR",
  ], { x: 7.35, y: 2.2, w: 5.1, h: 3.4, fs: 16 });
  callout(s, "Topología = componentes + ubicación + réplicas + rutas de tráfico + estrategia de falla");
  notes(s, "Conectar con la síntesis de la Sesión 1 (siete decisiones). Hoy profundizamos en tres de ellas: patrón de integración (online vs. batch), topología (zonas y regiones) y selección de servicios. Definir topología: no es solo el diagrama de cajas, sino dónde está cada componente, cuántas réplicas tiene, por dónde fluye el tráfico y qué pasa cuando algo falla.");
}

// ================================================================ UNIDAD A
addSection("A · Online vs. por lotes");
divider("Unidad A · Inferencia online vs. por lotes", "¿Qué cambia en la arquitectura cuando nadie está esperando la respuesta?",
  "Pregunta de la unidad. Respuesta que construiremos: cambia el SLO (de latencia a plazo), y con él cambian el patrón de integración, la forma de usar la capacidad, el precio y los riesgos operativos.");
{
  const s = contentSlide("Un espectro de patrones de inferencia");
  const items = [
    ["Síncrono", "Solicitud → respuesta completa\nHTTP request/response", HEX.sky],
    ["Streaming", "Tokens a medida que se generan\nSSE o WebSocket", HEX.sky],
    ["Asíncrono", "Encolar → procesar → notificar\ncola + workers", HEX.mint],
    ["Micro-batch", "Agrupar cada N s o N ítems\nflujos casi en tiempo real", HEX.mint],
    ["Batch", "Archivo de miles de solicitudes\nventana de horas", HEX.sand],
  ];
  items.forEach((it, i) => {
    const x = 0.6 + i * 2.48;
    box(s, x, 1.6, 2.2, 0.7, it[0], it[2], { fs: 16, bold: true });
    label(s, x, 2.4, 2.2, 1.0, it[1], { fs: 12, color: HEX.ink, align: "center", valign: "top" });
  });
  arrow(s, 0.6, 3.7, 12.7, 3.7, HEX.blue);
  label(s, 0.6, 3.8, 6, 0.4, "Usuario esperando · SLO de latencia (TTFT, p95)", { fs: 13, bold: true, color: HEX.blue });
  label(s, 6.7, 3.8, 6, 0.4, "Nadie esperando · SLO de plazo y costo por ítem", { fs: 13, bold: true, color: HEX.amber, align: "right" });
  bullets(s, [
    "Online (síncrono y streaming): el usuario está en la línea; cada segundo de espera se percibe",
    "Asíncrono: el usuario no espera en la conexión, pero sí espera el resultado (minutos)",
    "Batch: el resultado se consume después, en bloque (horas); el plazo es parte del contrato del servicio",
  ], { y: 4.4, h: 1.8, fs: 16 });
  notes(s, "Definir con cuidado: la diferencia entre online y batch no es la tecnología sino quién espera y cuánto. El asíncrono queda en el medio: la conexión se libera, pero alguien espera el resultado. Ejemplos del caso: chat de estudiantes (streaming), resumen de un acta larga que llega por correo (asíncrono), clasificación nocturna de PQRS (batch). Diagrama D-29 en el repositorio.");
}
{
  const s = contentSlide("El SLO define la carga de trabajo");
  table(s, ["Dimensión", "Online (síncrono / streaming)", "Por lotes (batch)"], [
    ["Quién espera", "Una persona, en la conexión", "Un proceso o un equipo, mañana"],
    ["SLI principal", "TTFT y latencia p95; tasa de errores", "Tiempo hasta completar el lote; % de ítems exitosos"],
    ["Unidad de costo", "Costo por conversación o por 1.000 tokens", "Costo por 1.000 ítems procesados"],
    ["Capacidad", "Holgura para picos; utilización moderada", "Utilización alta; la cola es aceptable"],
    ["Falla de un ítem", "Error visible de inmediato", "Se reintenta; el lote puede terminar parcial"],
    ["Orden de resultados", "Uno a uno", "No garantizado: se empareja por identificador"],
    ["Ejemplo del caso", "Asistente de estudiantes", "Clasificación nocturna de PQRS"],
  ], { colW: [2.4, 4.85, 4.85], fs: 14 });
  callout(s, "Pregunta de diseño: ¿cuál es el costo de responder en 6 horas en vez de 6 segundos?", 6.15, HEX.navy);
  notes(s, "Recorrer la tabla fila por fila. Énfasis en el SLI: en batch no tiene sentido medir TTFT; se mide el tiempo hasta completar y la proporción de ítems exitosos. El orden no garantizado es un hecho documentado en Azure OpenAI Batch y en Bedrock batch: los resultados se emparejan por custom_id o recordId. La pregunta del recuadro introduce la siguiente diapositiva: relajar el plazo libera capacidad y por eso los proveedores cobran menos.");
}
{
  const s = contentSlide("Por qué el lote es más barato: utilización y cola");
  const rho = ["10", "20", "30", "40", "50", "60", "70", "80", "90", "95"];
  const r = [1.11, 1.25, 1.43, 1.67, 2.0, 2.5, 3.33, 5.0, 10.0, 20.0];
  s.addChart(pres.charts.LINE, [{ name: "Tiempo de respuesta / tiempo de servicio", labels: rho, values: r }], {
    ...chartBase({ x: 0.6, y: 1.4, w: 6.6, h: 4.6, title: "Modelo M/M/1: R/S = 1 / (1 − ρ)", xTitle: "Utilización ρ (%)", yTitle: "Veces el tiempo de servicio" }),
    chartColors: [HEX.blue], lineSize: 2, lineDataSymbol: "circle", lineDataSymbolSize: 6, showValue: true, dataLabelPosition: "t",
  });
  bullets(s, [
    "La espera en cola crece de forma no lineal con la utilización",
    "Online: para cumplir un p95 de latencia se opera con holgura (capacidad ociosa = costo)",
    "Batch: la espera es aceptable; el proveedor llena huecos y opera con utilización alta",
    "Por eso los servicios batch documentan descuentos del 50 % (Azure, Google Cloud, AWS) a cambio de una ventana de 24 h",
  ], { x: 7.5, y: 1.5, w: 5.2, h: 4.6, fs: 16 });
  label(s, 0.6, 6.15, 12.1, 0.6, "M/M/1 es una simplificación (llegadas de Poisson, un servidor). Un servidor LLM con continuous batching se comporta distinto, pero la forma de la curva explica la intuición. Ver Harchol-Balter (2013).", { fs: 11, italic: true });
  notes(s, "Teoría de colas mínima. Con un servidor y llegadas aleatorias, el tiempo de respuesta normalizado es 1/(1−ρ): al 50 % de utilización se espera el doble del tiempo de servicio; al 90 %, diez veces. Para garantizar latencia hay que dejar capacidad libre. El batch no tiene ese problema: puede esperar. Hechos documentados (20-oct-2026): Azure Batch cuesta 50 % menos que Global Standard; Google indica que los modelos Gemini están disponibles en modo batch con 50 % de descuento; la guía de costos de Bedrock indica 50 % de ahorro frente a on-demand. Advertir que el modelo M/M/1 es una idealización; no sirve para dimensionar un servidor LLM real.");
}
{
  const s = contentSlide("Patrones de arquitectura para lotes");
  const cols = [
    ["Batch gestionado", "Archivo JSONL en almacenamiento → trabajo del proveedor → archivo de resultados", "Azure OpenAI Batch · Gemini batch inference · Bedrock batch", "Mínimo esfuerzo; ventana de 24 h; límites de tamaño y de registros", HEX.mint],
    ["Cola + workers propios", "Mensajes en una cola → workers con concurrencia limitada → resultados en BD", "Service Bus · Pub/Sub · SQS + contenedores o funciones", "Control fino del ritmo y la prioridad; más operación", HEX.sky],
    ["Micro-batching", "Agrupar solicitudes cercanas en el tiempo y enviarlas juntas", "Ingesta de eventos, embeddings de documentos nuevos", "Latencia de segundos; mejor uso que uno a uno", HEX.sand],
  ];
  cols.forEach((c, i) => {
    const x = 0.6 + i * 4.1;
    box(s, x, 1.45, 3.8, 0.65, c[0], c[4], { fs: 17, bold: true });
    label(s, x + 0.1, 2.2, 3.6, 1.2, c[1], { fs: 14, color: HEX.ink, valign: "top" });
    label(s, x + 0.1, 3.45, 3.6, 0.35, "Ejemplos", { fs: 12, bold: true, color: HEX.blue });
    label(s, x + 0.1, 3.8, 3.6, 0.9, c[2], { fs: 13, color: HEX.ink, valign: "top" });
    label(s, x + 0.1, 4.75, 3.6, 0.35, "Trade-off", { fs: 12, bold: true, color: HEX.amber });
    label(s, x + 0.1, 5.1, 3.6, 0.9, c[3], { fs: 13, color: HEX.ink, valign: "top" });
  });
  callout(s, "Regla práctica: use el batch gestionado salvo que necesite controlar el ritmo, la prioridad o un plazo menor que la ventana");
  notes(s, "Tres patrones. El batch gestionado es lo más simple y lo más barato por token, pero impone la ventana de 24 h y formatos concretos. La cola con workers propios da control (por ejemplo, procesar primero las PQRS de prioridad alta) a costa de operar la cola, los reintentos y la idempotencia. El micro-batching es útil cuando los ítems llegan continuamente y se quiere una latencia de segundos. En LOC-02 el gateway implementa el segundo patrón a escala de laboratorio y reproduce el ciclo de vida del primero.");
}
{
  const s = contentSlide("Ciclo de vida común de un trabajo batch");
  const st = [["validating", 0.6, 2.2, HEX.sky], ["in_progress", 3.3, 2.2, HEX.sky], ["finalizing", 6.0, 2.2, HEX.sky], ["completed", 8.7, 2.2, HEX.mint]];
  st.forEach((v) => box(s, v[1], v[2], 2.3, 0.8, v[0], v[3], { fs: 15, bold: true }));
  arrow(s, 2.9, 2.6, 3.3, 2.6); arrow(s, 5.6, 2.6, 6.0, 2.6); arrow(s, 8.3, 2.6, 8.7, 2.6);
  box(s, 0.6, 3.8, 2.3, 0.8, "failed\n(entrada inválida)", HEX.rose, { fs: 13 });
  box(s, 3.3, 3.8, 2.3, 0.8, "expired\n(venció la ventana)", HEX.rose, { fs: 13 });
  box(s, 6.0, 3.8, 2.3, 0.8, "cancelling → cancelled", HEX.sand, { fs: 13 });
  arrow(s, 1.75, 3.0, 1.75, 3.8, HEX.red); arrow(s, 4.45, 3.0, 4.45, 3.8, HEX.red); arrow(s, 5.0, 3.0, 6.6, 3.8, HEX.amber);
  label(s, 11.2, 2.2, 1.5, 0.8, "resultados\n+ errores", { fs: 12, align: "center" });
  arrow(s, 11.0, 2.6, 11.2, 2.6);
  table(s, ["Estado (Azure)", "Gemini (google-genai)", "Bedrock"], [
    ["validating · in_progress", "JOB_STATE_PENDING · RUNNING", "Submitted · Validating · Scheduled · InProgress"],
    ["completed", "JOB_STATE_SUCCEEDED · PARTIALLY_SUCCEEDED", "Completed · PartiallyCompleted"],
    ["failed · expired · cancelled", "JOB_STATE_FAILED · EXPIRED · CANCELLED", "Failed · Expired · Stopped"],
  ], { y: 4.9, fs: 12, colW: [3.4, 4.3, 4.4] });
  notes(s, "Los tres proveedores comparten el mismo ciclo, con nombres distintos (nombres verificados en la documentación de Azure y en los enumerados de los SDK google-genai 2.31.0 y boto3 1.43.116). Ideas clave: 1) la validación ocurre antes de procesar: un archivo con BOM o un identificador duplicado falla el trabajo completo; 2) completed no significa que todos los ítems salieron bien: hay un archivo de errores; 3) expired y cancelled conservan resultados parciales y se factura lo procesado. Diagrama D-30.");
}
{
  const s = contentSlide("Batch gestionado en las tres nubes (20-oct-2026)");
  table(s, ["", "Azure OpenAI Batch", "Gemini batch inference", "Amazon Bedrock batch"], [
    ["Entrada", "JSONL (custom_id, method, url, body); hasta 100.000 solicitudes y 200 MB por archivo", "JSONL en Cloud Storage o tabla de BigQuery", "JSONL en S3 (recordId, modelInput); invocación InvokeModel o Converse"],
    ["Ventana", "24 h (objetivo; no expira automáticamente)", "Según el trabajo; sin SLA de latencia", "24 h"],
    ["Precio documentado", "50 % menos que Global Standard", "50 % de descuento en modo batch", "50 % de ahorro frente a on-demand"],
    ["Mínimos y cuota", "Cuota de tokens encolados separada de la online", "Cuotas del proyecto", "Mínimo 100 registros por trabajo"],
    ["Residencia", "Global Batch o Data Zone Batch", "Según la ubicación del trabajo", "Región única o perfil entre regiones"],
    ["Cuenta trial", "No disponible (cuota «N/A»)", "Disponible con el crédito de prueba (validar)", "Plan Paid recomendado"],
  ], { colW: [1.9, 3.4, 3.3, 3.5], fs: 12 });
  notes(s, "Fuentes: Azure 'Getting started with batch deployments' (actualizada 5-jun-2026) y 'Quotas and limits' (20-ago-2026); Google 'Pricing' y 'Batch inference with Gemini'; AWS 'Capacity, limits and cost optimization', 'Format and upload your batch inference data' y cuotas de Bedrock. Hecho importante para el curso: las suscripciones free trial y Azure for Students tienen cuota Global Batch N/A; por eso la parte batch de AZ-G es demostración del docente y los estudiantes ejecutan el mismo lote en LOC-02, GCP-D o AWS-E. Los límites cambian: verificar el día del laboratorio.");
}
{
  const s = contentSlide("Clases de servicio online: prioridad, estándar y flexible");
  table(s, ["", "Microsoft Foundry", "Gemini Enterprise Agent Platform", "Amazon Bedrock"], [
    ["Prioritaria", "Priority processing (por despliegue o por solicitud con service_tier); Global y Data Zone Standard US", "Priority PayGo", "Priority (service_tier = priority)"],
    ["Estándar", "Standard (pago por token)", "Standard PayGo", "Standard (default)"],
    ["Flexible", "Flex processing para cargas tolerantes a demora", "Flex PayGo", "Flex (service_tier = flex)"],
    ["Reservada", "Provisioned (PTU)", "Provisioned Throughput", "Reserved (1 o 3 meses)"],
  ], { colW: [1.8, 3.6, 3.2, 3.5], fs: 13 });
  bullets(s, [
    "La clase de servicio se elige por solicitud: el mismo endpoint atiende cargas con SLO distintos",
    "Flex es un punto intermedio entre online y batch: sin archivo ni ventana, pero puede tardar o limitarse",
    "Priority no aumenta la cuota: en Azure y en Bedrock comparte la cuota on-demand",
  ], { y: 4.55, h: 1.6, fs: 15 });
  notes(s, "Hechos documentados: Azure 'Priority processing' (22-sep-2026) indica que se activa por despliegue o por solicitud, que usa la misma cuota que el procesamiento estándar y que puede degradarse a estándar si el tráfico sube más de 50 % en menos de 15 minutos. Bedrock 'Service tiers' lista Reserved, Priority, Standard y Flex, con el parámetro service_tier, y que priority, default y flex comparten la cuota on-demand. Google lista Standard, Priority y Flex PayGo y Provisioned Throughput. Pregunta: ¿qué clase usaría para el lote de PQRS si necesita resultados antes de 2 horas? Respuesta esperada: Flex o una cola propia, porque la ventana del batch es de 24 h.");
}
{
  const s = contentSlide("Coexistencia: que el lote no degrade lo online");
  box(s, 0.6, 1.7, 2.0, 1.0, "Usuarios\n(online)", HEX.sky, { fs: 14 });
  box(s, 0.6, 3.9, 2.0, 1.0, "Lote PQRS\n(batch)", HEX.sand, { fs: 14 });
  box(s, 3.1, 2.6, 2.5, 1.5, "Control de admisión\nprioridad online\nlímite de concurrencia del lote", HEX.light, { fs: 13 });
  box(s, 6.1, 2.6, 2.0, 1.5, "Capacidad compartida\n(cuota o GPU)", HEX.mint, { fs: 14 });
  arrow(s, 2.6, 2.2, 3.1, 3.0, HEX.blue); arrow(s, 2.6, 4.4, 3.1, 3.7, HEX.amber); arrow(s, 5.6, 3.35, 6.1, 3.35);
  bullets(s, [
    "Separar cuotas: Azure Batch usa una cuota de tokens encolados distinta de la online",
    "Separar endpoints o despliegues por carga cuando la cuota es compartida",
    "Prioridad y ritmo: el lote cede capacidad cuando hay tráfico interactivo (LOC-02)",
    "Programar en horas valle: el lote nocturno aprovecha la capacidad ociosa",
    "Observar por separado: SLI online y SLI batch en tableros distintos",
  ], { x: 8.5, y: 1.45, w: 4.2, h: 4.6, fs: 15 });
  callout(s, "ADR-0006: separar los caminos online y batch, con prioridad explícita para lo interactivo");
  notes(s, "El riesgo clásico: un lote grande lanzado a las 10 a. m. agota la cuota o satura la GPU y los estudiantes ven 429 o latencias altas. Defensas: cuotas separadas (Azure lo hace por diseño para Global Batch), despliegues separados, control de admisión con prioridad (lo implementa el gateway de LOC-02: el procesador batch se detiene mientras haya solicitudes online en curso) y programación en horas valle. Diagrama D-31 y ADR-0006 en el repositorio.");
}
{
  const s = contentSlide("Riesgos propios de la inferencia por lotes");
  table(s, ["Riesgo", "Qué pasa", "Control"], [
    ["Idempotencia", "Un reintento procesa dos veces el mismo ítem", "Identificador por ítem (custom_id, recordId); reanudar sin repetir lo resuelto"],
    ["Resultados parciales", "El lote vence o se cancela a mitad", "Tratar completed, expired y cancelled como estados normales; reprocesar faltantes"],
    ["Calidad silenciosa", "Miles de respuestas mal formadas sin que nadie lo note", "Validar el formato de salida y medir exactitud contra una muestra etiquetada"],
    ["Inyección indirecta (LLM01)", "Un ítem contiene instrucciones para el modelo", "Tratar el contenido como dato; validar la salida contra un esquema"],
    ["Consumo sin límite (LLM10)", "Un archivo mal generado multiplica el costo", "Límites de registros y tamaño; presupuesto y alertas"],
    ["Datos en reposo (LLM02)", "Entradas y salidas quedan en almacenamiento", "Cifrado, caducidad (Azure: 14 a 30 días), acceso mínimo"],
  ], { colW: [2.6, 4.3, 5.2], fs: 13 });
  notes(s, "Estos riesgos no existen o son menores en el camino online. El lote PQRS del repositorio incluye un 2 % de mensajes con instrucciones incrustadas para practicar LLM01. La medición de calidad es obligatoria: en LOC-02 el simulador clasifica bien el área (100 %) pero se equivoca en el tipo en 10,5 % de los casos; sin la evaluación contra etiquetas, nadie lo habría notado. Las referencias OWASP corresponden al Top 10 for LLM Applications 2025.");
}
{
  const s = contentSlide("Demo 1 · Online y lote sobre la misma capacidad (LOC-02)");
  flow(s, ["Enviar lote de 200 PQRS\n(pestaña Lotes)", "Conversar a la vez\n(pestaña Online)", "Observar: el lote se detiene\nmientras hay tráfico online", "Evaluar resultados\ncontra etiquetas"], 1.8, 1.3, [HEX.sand, HEX.sky, HEX.light, HEX.mint]);
  bullets(s, [
    "Antes de ejecutar, prediga: ¿subirá el TTFT de la conversación mientras corre el lote?",
    "Observe en la tabla de lotes el progreso y las regiones usadas",
    "Descargue los resultados y ejecute evaluar_lote.py: JSON válidos, exactitud por tipo y por área",
    "Mismo archivo, mismo formato que Azure OpenAI Batch: la diferencia es quién opera la cola",
  ], { y: 3.5, h: 2.5, fs: 17 });
  callout(s, "Plan B: tabla de resultados sintéticos del README de LOC-02 (sección 9)", 6.15, HEX.grey);
  notes(s, "Duración: 7 minutos. Pasos en labs/01-local-gateway/README.md (secciones 6.4 y 6.5). Pedir la predicción antes de ejecutar. Resultado esperado: la latencia online se mantiene porque el procesador batch cede capacidad (APP_BATCH_YIELD_ONLINE_INFLIGHT). Mostrar luego evaluar_lote.py: 200 JSON válidos, exactitud de área 100 % y de tipo 89,5 % con el simulador. Si algo falla, usar la tabla del README.");
}

// ================================================================ UNIDAD B
addSection("B · Topologías redundantes y multi-región");
divider("Unidad B · Topologías redundantes y multi-región", "¿Cuántas copias necesita el sistema y quién decide a cuál enviar el tráfico?",
  "Pregunta de la unidad. Respuesta que construiremos: depende del objetivo de disponibilidad, de RTO y RPO, de qué componentes tienen estado y de qué parte de la redundancia ya ofrece el proveedor.");
{
  const s = contentSlide("Vocabulario de continuidad");
  const terms = [
    ["Disponibilidad", "Proporción del tiempo en que el servicio cumple su función. 99,9 % ≈ 43 min de indisponibilidad al mes", HEX.sky],
    ["Dominio de falla", "Conjunto de recursos que fallan juntos: un host, una zona, una región, un proveedor, una cuota", HEX.sky],
    ["RTO", "Recovery Time Objective: máximo tiempo aceptable entre la interrupción y la restauración", HEX.mint],
    ["RPO", "Recovery Point Objective: máxima pérdida de datos aceptable, medida en tiempo", HEX.mint],
    ["Radio de impacto", "Cuántos usuarios o funciones afecta una falla (blast radius)", HEX.sand],
    ["Resiliencia", "Capacidad de resistir la falla y recuperarse: detectar, aislar, conmutar, degradar", HEX.sand],
  ];
  terms.forEach((t, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = 0.6 + col * 6.15, y = 1.45 + row * 1.55;
    box(s, x, y, 1.9, 1.3, t[0], t[2], { fs: 15, bold: true });
    label(s, x + 2.05, y, 3.85, 1.3, t[1], { fs: 14, color: HEX.ink });
  });
  label(s, 0.6, 6.2, 12.1, 0.5, "Definiciones de RTO y RPO según AWS Architecture Blog, «Disaster Recovery (DR) Architecture on AWS, Part I» (Eliot, 2021).", { fs: 11, italic: true });
  notes(s, "Definir cada término con un ejemplo del caso. Dominio de falla: en LLM gestionados aparece uno nuevo, la cuota de la suscripción o del proyecto: si se agota, fallan todas las regiones que la comparten. RTO: si cae la región, ¿en cuánto tiempo debe volver el asistente? RPO: ¿cuántas conversaciones podemos perder? Para un asistente sin estado crítico el RPO puede ser alto; para PQRS radicadas debe ser casi cero.");
}
{
  const s = contentSlide("Disponibilidad compuesta: serie y paralelo");
  label(s, 0.6, 1.4, 6.0, 0.45, "En serie (todos deben funcionar)", { fs: 16, bold: true, color: HEX.navy });
  label(s, 0.6, 1.85, 6.0, 0.45, "A = A₁ × A₂ × … × Aₙ", { fs: 18, color: HEX.ink });
  label(s, 0.6, 2.45, 6.0, 0.45, "En paralelo (basta con uno, fallas independientes)", { fs: 16, bold: true, color: HEX.navy });
  label(s, 0.6, 2.9, 6.0, 0.45, "A = 1 − (1 − A₁) × (1 − A₂)", { fs: 18, color: HEX.ink });
  table(s, ["Configuración (cifras hipotéticas)", "A", "Indisp./mes"], [
    ["Solo el endpoint del modelo (99,9 %)", "99,90 %", "43 min"],
    ["Una región: gateway 99,95 × backend 99,95 × modelo 99,9", "99,80 %", "86 min"],
    ["Dos regiones en paralelo", "99,9996 %", "0,2 min"],
    ["Dos regiones + enrutamiento global en serie (99,99 %)", "99,99 %", "4,5 min"],
  ], { y: 3.55, w: 6.6, colW: [4.3, 1.1, 1.2], fs: 12 });
  s.addChart(pres.charts.BAR, [{ name: "Indisponibilidad (min/mes)", labels: ["Modelo solo", "Una región", "2 regiones", "2 regiones + global"], values: [43.2, 86.3, 0.2, 4.5] }], {
    ...chartBase({ x: 7.5, y: 1.4, w: 5.2, h: 4.6, title: "Minutos de indisponibilidad al mes (30 días)", yTitle: "min/mes" }),
    barDir: "col", chartColors: [HEX.blue], showValue: true, dataLabelPosition: "outEnd", valAxisMinVal: 0,
  });
  callout(s, "Cada componente en serie resta; el componente global en serie se vuelve el techo", 6.15, HEX.navy);
  notes(s, "Cálculo en vivo. Las cifras son hipótesis didácticas, no SLA publicados. Una región con tres componentes en serie queda en 99,80 % (peor que el modelo solo). Dos regiones en paralelo suben a 99,9996 % suponiendo fallas independientes. Pero el componente que enruta entre regiones (DNS, balanceador global o gateway) queda en serie: con 99,99 % el total cae a 99,99 %. Lecciones: 1) la redundancia solo sirve si las fallas son independientes; una cuota compartida, una versión de modelo defectuosa o un plano de control común las correlacionan; 2) el componente global debe ser el más confiable del diseño. Diagrama D-33.");
}
{
  const s = contentSlide("Espectro de topologías");
  const tops = [
    ["Zona única", "1 zona · 1 región", "Fallas de host; no de zona", "$", HEX.light],
    ["Multizona", "≥ 2 zonas · 1 región", "Falla de zona; no de región", "$$", HEX.sky],
    ["Multi-región activo-pasivo", "Primaria + secundaria en espera", "Falla de región, con RTO de minutos a horas", "$$–$$$", HEX.mint],
    ["Multi-región activo-activo", "≥ 2 regiones con tráfico", "Falla de región con RTO cercano a cero", "$$$", HEX.sand],
  ];
  tops.forEach((t, i) => {
    const x = 0.6 + i * 3.08;
    box(s, x, 1.5, 2.8, 0.9, t[0], t[4], { fs: 15, bold: true });
    label(s, x, 2.5, 2.8, 0.7, t[1], { fs: 13, color: HEX.ink, align: "center" });
    label(s, x, 3.2, 2.8, 0.9, t[2], { fs: 13, color: HEX.ink, align: "center" });
    label(s, x, 4.1, 2.8, 0.5, t[3], { fs: 18, bold: true, color: HEX.amber, align: "center" });
    if (i < 3) arrow(s, x + 2.8, 1.95, x + 3.08, 1.95);
  });
  bullets(s, [
    "Multizona es la línea base razonable para producción; multi-región se justifica por RTO, regulación o riesgo del negocio",
    "Activo-activo exige que los datos con estado se repliquen y que los clientes toleren respuestas desde cualquier región",
  ], { y: 4.85, h: 1.3, fs: 15 });
  notes(s, "Recorrer de izquierda a derecha. Cada paso cubre un dominio de falla mayor y cuesta más (en dinero y en complejidad operativa). Para el caso: 99,9 % con una sola región multizona puede ser suficiente si el proveedor del modelo ya ofrece enrutamiento global; el requisito nuevo («seguir operando si cae una región») nos empuja a multi-región. Diagrama D-32.");
}
{
  const s = contentSlide("Estrategias de recuperación ante desastres");
  table(s, ["Estrategia (AWS)", "Equivalente (Microsoft)", "En la región secundaria", "RTO", "RPO", "Costo"], [
    ["Backup and restore", "Hot/cold", "Solo copias de datos", "Horas", "Horas", "Bajo"],
    ["Pilot light", "—", "Datos replicados; cómputo apagado", "Decenas de minutos", "Minutos", "Bajo-medio"],
    ["Warm standby", "Hot/warm", "Despliegue mínimo funcionando", "Minutos", "Segundos-minutos", "Medio-alto"],
    ["Multi-site active/active", "Hot/hot", "Despliegue completo con tráfico", "Cercano a cero", "Cercano a cero", "Alto"],
  ], { colW: [2.3, 1.9, 3.1, 1.6, 1.7, 1.5], fs: 13 });
  bullets(s, [
    "Microsoft da rangos aproximados para Foundry: hot/hot en minutos; hot/warm de 30 min a 2 h; hot/cold de 2 a 8 h",
    "En LLM gestionados, el «warm standby» es barato: un despliegue de pago por token sin tráfico no factura tokens",
    "En LLM autogestionados, la GPU en espera se paga por hora: el pilot light deja la GPU apagada y paga con arranque en frío",
  ], { y: 4.1, h: 2.0, fs: 15 });
  notes(s, "Fuentes: AWS Architecture Blog (Eliot, 2021) para las cuatro estrategias; guía de alta disponibilidad de Microsoft Foundry (actualizada 22-sep-2026) para hot/hot, hot/warm y hot/cold con sus rangos aproximados. Los RTO y RPO de la tabla son órdenes de magnitud cualitativos; Microsoft insiste en validarlos con pruebas propias. Idea central: la economía de la redundancia cambia radicalmente entre gestionado (paga por uso) y autogestionado (paga por hora de GPU). Diagrama D-34.");
}
{
  const s = contentSlide("¿Qué hay que replicar en un sistema LLM?");
  table(s, ["Componente", "Estado", "Estrategia de réplica", "RPO típico"], [
    ["Gateway, backend, workers", "Sin estado", "Desplegar en cada región desde el mismo artefacto (IaC + imagen)", "No aplica"],
    ["Configuración: prompts de sistema, guardrails, versión del modelo", "Estado de control", "Versionar en Git y desplegar a todas las regiones a la vez", "Cero"],
    ["Conversaciones y memoria de agentes", "Estado de usuario", "Base de datos con réplica entre regiones o aceptar pérdida", "Segundos a horas"],
    ["Documentos e índice vectorial (RAG)", "Estado derivado", "Replicar documentos; reconstruir o replicar el índice", "Horas"],
    ["Modelo gestionado", "Capacidad del proveedor", "Despliegue y cuota en cada región; misma versión", "No aplica"],
    ["Modelo autogestionado", "Pesos + GPU", "Registro de imágenes replicado; capacidad de GPU reservada o verificada", "No aplica"],
    ["Secretos e identidades", "Estado de control", "Gestor de secretos con réplica; identidades de carga por región", "Cero"],
  ], { colW: [3.3, 1.8, 5.2, 1.8], fs: 12 });
  notes(s, "Lo que no se replica no se recupera. En LLM aparecen dos elementos nuevos: la configuración del comportamiento (prompt de sistema, guardrails, versión del modelo), que debe ser idéntica en todas las regiones para que el usuario no note diferencias, y el índice vectorial, que puede reconstruirse a partir de los documentos (RPO de horas aceptable) o replicarse. Microsoft documenta que Foundry no replica proyectos, despliegues ni cuota entre regiones: el cliente los crea en cada región.");
}
{
  const s = contentSlide("Particularidades de los LLM en multi-región");
  const items = [
    ["Disponibilidad del modelo por región", "No todos los modelos ni versiones existen en todas las regiones. Verifique antes de elegir la secundaria"],
    ["Cuota compartida", "En Foundry, desde el 7-may-2026, la cuota de Global Standard es por suscripción y se comparte entre regiones"],
    ["Misma versión del modelo", "Conmutar a otra versión cambia las respuestas; la guía de gateways de Azure exige el mismo modelo y versión"],
    ["Capacidad de GPU escasa", "En autogestionado, la región secundaria puede no tener GPU disponible cuando se necesita"],
    ["Arranque en frío", "Cargar decenas de GB de pesos hace lenta la activación de una secundaria apagada"],
    ["Conversaciones largas", "Conmutar a mitad de una respuesta en streaming duplica o corta texto"],
  ];
  items.forEach((it, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = 0.6 + col * 6.15, y = 1.45 + row * 1.5;
    circle(s, x, y + 0.15, 0.7, String(i + 1), [HEX.blue, HEX.teal, HEX.amber, HEX.red, HEX.violet, HEX.navy][i], "FFFFFF", 16);
    label(s, x + 0.9, y, 5.0, 0.45, it[0], { fs: 15, bold: true, color: HEX.navy });
    label(s, x + 0.9, y + 0.45, 5.0, 0.9, it[1], { fs: 13, color: HEX.ink, valign: "top" });
  });
  notes(s, "Seis diferencias con un sistema web clásico. Subrayar la 2: en Azure, un segundo despliegue Global Standard en otra región NO duplica la cuota (hecho documentado en 'Quotas and limits', 20-ago-2026); protege contra la falla del endpoint regional, no contra el 429 por cuota. La guía de gateways de Azure dice que el balanceo entre instancias de una misma suscripción no agrega capacidad. Fuentes en docs/referencias.md.");
}
{
  const s = contentSlide("Dos capas de multi-región: la del proveedor y la propia");
  box(s, 0.6, 1.45, 5.9, 0.7, "Capa del proveedor (dentro del servicio de modelos)", HEX.mint, { fs: 15, bold: true });
  table(s, ["Nube", "Mecanismo", "Alcance del procesamiento"], [
    ["Azure", "Global / Data Zone Standard", "Cualquier región / zona de datos"],
    ["Google Cloud", "Endpoint global / multirregional", "Cualquier ubicación / jurisdicción"],
    ["AWS", "Cross-Region inference", "Geografía (us., eu.…) o global"],
  ], { x: 0.6, y: 2.3, w: 5.9, colW: [1.4, 2.4, 2.1], fs: 12 });
  box(s, 6.8, 1.45, 5.9, 0.7, "Capa propia (antes del servicio de modelos)", HEX.sky, { fs: 15, bold: true });
  bullets(s, [
    "Backend y gateway en dos regiones",
    "Conmutación entre endpoints regionales",
    "Datos con estado replicados",
    "Enrutamiento global de usuarios",
  ], { x: 6.9, y: 2.3, w: 5.7, h: 1.9, fs: 15 });
  bullets(s, [
    "Microsoft: el enrutamiento de Global y Data Zone «no reemplaza el failover regional a nivel de aplicación»",
    "Google: el endpoint global no ofrece aislamiento regional ni garantías de residencia",
    "AWS: CRIS no cambia dónde se almacenan los datos; las SCP deben permitir todas las regiones de destino",
  ], { y: 4.35, h: 1.7, fs: 14 });
  callout(s, "La capa del proveedor mejora la capacidad; la capa propia protege su endpoint, sus datos y su aplicación", 6.15, HEX.navy);
  notes(s, "Esta es la idea más importante de la unidad. Fuentes: Microsoft 'Deployment types' (12-ago-2026) y guía de alta disponibilidad de Foundry (22-sep-2026); Google 'Where your data lives and is processed'; AWS Machine Learning Blog 'Securing Amazon Bedrock cross-Region inference' (13-ene-2026). Error frecuente: creer que usar Global Standard o un perfil global ya hace al sistema multi-región. Si cae la región del endpoint, del backend o de la base de datos, el usuario no recibe respuesta. Diagrama D-35.");
}
{
  const s = contentSlide("Enrutamiento global: ¿cómo llega el usuario a la región sana?");
  table(s, ["Mecanismo", "Ejemplos", "Detección y conmutación", "Consideraciones"], [
    ["DNS con health checks", "Route 53 failover · Traffic Manager · Cloud DNS routing policies", "Health check + TTL del registro", "Los clientes y resolvers guardan en caché: la conmutación tarda lo que el TTL o más"],
    ["Balanceador global (anycast)", "Azure Front Door · Cloud Load Balancing global · Global Accelerator", "Segundos; la IP no cambia", "Un punto de entrada global con WAF; es otro componente en serie"],
    ["Gateway de IA", "API Management · Apigee · gateway propio (LOC-02)", "Por solicitud (circuit breaker)", "Ve errores 429 y 5xx del modelo; puede ser punto único de falla"],
    ["Cliente o SDK", "Lógica de conmutación en la aplicación (AZ-G, GCP-D, AWS-E)", "Por solicitud", "Repite lógica en cada cliente; útil en prototipos"],
  ], { colW: [2.4, 3.6, 2.6, 3.5], fs: 12 });
  callout(s, "Combinación habitual: balanceador global para los usuarios + gateway por región para los modelos", 6.15, HEX.teal);
  notes(s, "Dos problemas distintos: llevar al usuario a una región sana (DNS o anycast) y llevar cada solicitud a un endpoint de modelo sano (gateway). La guía de gateways de Azure recomienda desplegar el gateway en la misma región que los modelos y no usar un gateway de una sola región frente a backends de varias regiones para cargas críticas, porque vuelve a crear un punto único de falla. Mencionar el TTL de DNS: un TTL de 60 s no garantiza conmutación en 60 s por cachés intermedias.");
}
{
  const s = contentSlide("Patrones de resiliencia para la ruta de inferencia");
  const pats = [
    ["Timeouts", "Límite de conexión y de primer byte; sin él, una región lenta retiene recursos"],
    ["Reintentos con backoff y jitter", "Esperas crecientes y aleatorias; respetar Retry-After en 429"],
    ["Presupuesto de reintentos", "Máximo de intentos por solicitud y por capa"],
    ["Circuit breaker", "Dejar de enviar tráfico a una región que falla y probar su recuperación"],
    ["Bulkhead", "Aislar capacidad por carga (online, batch) o por cliente"],
    ["Degradación", "Modelo más pequeño, respuesta en caché o mensaje claro de indisponibilidad"],
    ["Load shedding", "Rechazar con 429 o 503 lo que no se puede atender, antes de saturarse"],
    ["Idempotencia", "Repetir sin efectos duplicados (lotes, herramientas de agentes)"],
  ];
  pats.forEach((p, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = 0.6 + col * 6.15, y = 1.4 + row * 1.18;
    box(s, x, y, 2.6, 0.95, p[0], i < 4 ? HEX.sky : HEX.mint, { fs: 14, bold: true });
    label(s, x + 2.75, y, 3.2, 0.95, p[1], { fs: 13, color: HEX.ink });
  });
  label(s, 0.6, 6.2, 12.1, 0.5, "Referencias: Nygard, «Release It!» (2.ª ed., 2018); Beyer et al., «Site Reliability Engineering» (2016), cap. 21–22.", { fs: 11, italic: true });
  notes(s, "Patrones clásicos de sistemas distribuidos aplicados a la inferencia. Los cuatro primeros detectan y contienen la falla; los cuatro últimos limitan su impacto. En LOC-02 están implementados: timeout de primer byte, conmutación entre regiones, presupuesto de intentos (APP_MAX_ATTEMPTS), circuit breaker que respeta Retry-After, bulkhead entre online y batch, reintentos con backoff y jitter en el lote, e idempotencia por custom_id.");
}
{
  const s = contentSlide("Circuit breaker: tres estados");
  circle(s, 1.2, 2.2, 2.0, "Cerrado\nel tráfico fluye", HEX.teal, "FFFFFF", 15);
  circle(s, 5.65, 2.2, 2.0, "Abierto\nno se envía tráfico", HEX.red, "FFFFFF", 15);
  circle(s, 10.1, 2.2, 2.0, "Semiabierto\nuna prueba", HEX.amber, "FFFFFF", 15);
  arrow(s, 3.2, 2.8, 5.65, 2.8, HEX.red);
  label(s, 3.25, 2.25, 2.4, 0.5, "N fallas en la ventana\no 429 con Retry-After", { fs: 12, color: HEX.ink, align: "center" });
  arrow(s, 7.65, 2.8, 10.1, 2.8, HEX.amber);
  label(s, 7.7, 2.25, 2.4, 0.5, "vence el tiempo\nde apertura", { fs: 12, color: HEX.ink, align: "center" });
  arrow(s, 10.6, 4.2, 6.15, 4.2, HEX.red, "dash");
  label(s, 7.3, 4.25, 2.4, 0.4, "la prueba falla", { fs: 12, color: HEX.ink, align: "center" });
  arrow(s, 11.1, 4.2, 11.1, 4.9, HEX.teal); arrow(s, 11.1, 4.9, 2.2, 4.9, HEX.teal); arrow(s, 2.2, 4.9, 2.2, 4.2, HEX.teal);
  label(s, 5.4, 4.95, 2.6, 0.4, "la prueba tiene éxito", { fs: 12, color: HEX.ink, align: "center" });
  bullets(s, [
    "Evita insistir sobre una región caída y da tiempo a que se recupere",
    "Un 429 con Retry-After abre el circuito exactamente ese tiempo (no adivinar el throttling)",
  ], { y: 5.5, h: 0.9, fs: 15 });
  notes(s, "Explicar la máquina de estados con LOC-02 (circuit_breaker.py). Parámetros: umbral de fallas, ventana, tiempo de apertura y tope. La guía de gateways de Azure recomienda usar los códigos de respuesta (429, 500, 503) para enrutar y no intentar predecir el throttling, y respetar Retry-After, que en Azure OpenAI puede ser largo. API Management implementa la misma idea como regla de circuit breaker por backend (no disponible en el nivel Consumption). Diagrama D-36.");
}
{
  const s = contentSlide("Tormentas de reintentos: la amplificación");
  s.addChart(pres.charts.BAR, [{ name: "Solicitudes al modelo por cada solicitud del usuario", labels: ["1 capa", "2 capas", "3 capas", "4 capas"], values: [3, 9, 27, 81] }], {
    ...chartBase({ x: 0.6, y: 1.4, w: 6.2, h: 4.6, title: "Peor caso con 3 intentos por capa (1 + 2 reintentos)", xTitle: "Capas que reintentan", yTitle: "Solicitudes" }),
    barDir: "col", chartColors: [HEX.red], showValue: true, dataLabelPosition: "outEnd", valAxisMinVal: 0,
  });
  bullets(s, [
    "Frontend, gateway, backend y SDK pueden reintentar cada uno por su cuenta",
    "Durante un incidente, la carga se multiplica justo cuando el proveedor está limitado",
    "Reintentar en una sola capa; las demás fallan rápido",
    "Desactivar los reintentos automáticos del SDK cuando un gateway conmuta (AZ-G, GCP-D y AWS-E lo hacen)",
    "Presupuesto global: por ejemplo, reintentos ≤ 10 % del tráfico",
  ], { x: 7.1, y: 1.5, w: 5.6, h: 4.6, fs: 15 });
  notes(s, "Cálculo: si cada capa hace hasta 3 intentos, el peor caso es 3 elevado al número de capas. Con 4 capas, una pregunta puede producir 81 llamadas al modelo. Ejemplo real del repositorio: el SDK de OpenAI reintenta 2 veces por defecto, google-genai 5 intentos por defecto según su documentación del tipo HttpRetryOptions, y botocore también tiene reintentos; los laboratorios los limitan a un intento porque la conmutación ocurre en otra capa. El presupuesto de reintentos (retry budget) proviene de la práctica de SRE de Google.");
}
{
  const s = contentSlide("Streaming y conmutación: solo antes del primer token");
  box(s, 0.6, 1.5, 1.9, 0.7, "Cliente", HEX.sky, { fs: 14, bold: true });
  box(s, 3.4, 1.5, 1.9, 0.7, "Gateway", HEX.light, { fs: 14, bold: true });
  box(s, 6.4, 1.5, 2.4, 0.7, "Región A", HEX.rose, { fs: 14, bold: true });
  box(s, 9.9, 1.5, 2.4, 0.7, "Región B", HEX.mint, { fs: 14, bold: true });
  [1.55, 4.35, 7.6, 11.1].forEach((x) => s.addShape(pres.shapes.LINE, { x, y: 2.2, w: 0.001, h: 3.2, line: { color: HEX.line, width: 1, dashType: "dash" } }));
  arrow(s, 1.55, 2.6, 4.35, 2.6, HEX.blue); label(s, 1.6, 2.3, 2.7, 0.3, "POST /v1/chat/stream", { fs: 11, color: HEX.ink });
  arrow(s, 4.35, 3.0, 7.6, 3.0, HEX.blue); label(s, 4.4, 2.7, 3.1, 0.3, "intento 1", { fs: 11, color: HEX.ink });
  arrow(s, 7.6, 3.4, 4.35, 3.4, HEX.red); label(s, 4.4, 3.1, 3.1, 0.3, "503 o timeout antes del primer byte", { fs: 11, color: HEX.red });
  arrow(s, 4.35, 3.85, 11.1, 3.85, HEX.blue); label(s, 4.4, 3.55, 6.6, 0.3, "intento 2 en la región B", { fs: 11, color: HEX.ink });
  arrow(s, 11.1, 4.3, 4.35, 4.3, HEX.teal); label(s, 4.4, 4.0, 6.6, 0.3, "tokens", { fs: 11, color: HEX.teal });
  arrow(s, 4.35, 4.7, 1.55, 4.7, HEX.teal); label(s, 1.6, 4.4, 2.7, 0.3, "evento region + tokens", { fs: 11, color: HEX.teal });
  bullets(s, [
    "Si la región falla después del primer token, conmutar duplicaría o mezclaría texto: se informa el error",
    "El estado de la conversación debe estar fuera de la región para que la siguiente pregunta funcione en B",
  ], { y: 5.55, h: 0.9, fs: 15 });
  notes(s, "Diagrama de secuencia (D-37). La regla de LOC-02 y de la Sesión 1: reintentar solo antes del primer byte. Discusión: ¿qué haría para continuar una respuesta cortada? Opciones: regenerar completa en B (el usuario ve que se reinicia), o pedir a B que continúe a partir del texto recibido (cambia la respuesta y cuesta más tokens). En ambos casos el historial de la conversación debe estar replicado o en un almacén accesible desde B.");
}
{
  const s = contentSlide("El gateway de IA: ventajas y riesgos");
  box(s, 0.6, 1.45, 5.9, 0.6, "Lo que aporta", HEX.mint, { fs: 16, bold: true });
  bullets(s, [
    "Conmutación y circuit breaker en un solo lugar",
    "Límites de tokens por cliente (p. ej., llm-token-limit en APIM)",
    "Observabilidad central: tokens, latencia, región",
    "Prioridad entre cargas y entre despliegues (PTU primero, pago por uso después)",
    "Contrato propio: cambiar de proveedor sin tocar clientes",
  ], { x: 0.6, y: 2.15, w: 5.9, h: 3.6, fs: 15 });
  box(s, 6.8, 1.45, 5.9, 0.6, "Lo que arriesga", HEX.rose, { fs: 16, bold: true });
  bullets(s, [
    "Nuevo componente en serie: su disponibilidad es el techo",
    "Si vive en una sola región, vuelve a ser punto único de falla",
    "Latencia adicional por salto",
    "Un gateway unificado entre jurisdicciones puede violar la residencia",
    "Más superficie de ataque y más operación",
  ], { x: 6.8, y: 2.15, w: 5.9, h: 3.6, fs: 15 });
  callout(s, "Microsoft: no implementar un gateway unificado entre regiones geopolíticas cuando aplica residencia de datos", 6.15, HEX.navy);
  notes(s, "Fuente principal: Azure Architecture Center, 'Use a gateway in front of multiple Azure OpenAI deployments' (actualizada 21-sep-2026). Recomendaciones citadas: desplegar el gateway en la misma región que el modelo, no usar un gateway de una región para cargas críticas, no implementar un gateway unificado solo para aumentar cuota (usar Global Standard), y un gateway aislado por geografía cuando aplica residencia. Discusión: ¿gateway propio (LOC-02) o gestionado (APIM, Apigee)? ADR-0008.");
}
{
  const s = contentSlide("Probar la conmutación antes del incidente");
  flow(s, ["Definir hipótesis\n«si cae A, p95 < 3 s\ny errores < 1 %»", "Inyectar la falla\ncaída, lentitud, 429", "Medir detección,\nconmutación y\nrecuperación", "Corregir y\nautomatizar\nel ensayo"], 1.6, 1.5, [HEX.sky, HEX.rose, HEX.light, HEX.mint]);
  bullets(s, [
    "Microsoft recomienda verificar periódicamente (por ejemplo, cada trimestre) despliegues, conexiones, RBAC, DNS y una prueba de punta a punta en la región secundaria",
    "Una secundaria que nunca recibió tráfico no está probada: cuota, permisos o versión del modelo pueden diferir",
    "Las pruebas se hacen primero en un entorno de laboratorio (LOC-02) y luego como game days controlados",
  ], { y: 3.5, h: 2.6, fs: 16 });
  notes(s, "Ingeniería del caos aplicada con prudencia. La guía de alta disponibilidad de Foundry recomienda revisiones de preparación periódicas. Una región secundaria nunca usada suele fallar por detalles: el despliegue tiene otro nombre, falta un rol, la cuota es cero o el modelo se retiró. La Demo 2 hace exactamente este ejercicio a escala de laboratorio.");
}
{
  const s = contentSlide("Demo 2 · Falla regional bajo carga (LOC-02)");
  const windows = ["0–2", "2–4", "4–6", "6–8", "8–10", "10–12", "12–14", "14–16", "16–18", "18–20", "20–22", "22–24", "24–26", "26–28", "28–30"];
  const a = [8, 8, 8, 8, 0, 0, 0, 0, 0, 0, 0, 1, 8, 8, 8];
  const b = [0, 0, 0, 0, 8, 8, 8, 8, 8, 8, 8, 7, 0, 0, 0];
  s.addChart(pres.charts.BAR, [{ name: "region-a", labels: windows, values: a }, { name: "region-b", labels: windows, values: b }], {
    ...chartBase({ x: 0.6, y: 1.4, w: 7.4, h: 4.6, title: "Solicitudes atendidas por región (cifras sintéticas, 20-oct-2026)", xTitle: "Ventana (s) · caída a los 8 s, recuperación a los 18 s", yTitle: "Solicitudes", legend: true }),
    barDir: "col", barGrouping: "stacked", chartColors: [HEX.blue, HEX.amber], showValue: false,
  });
  bullets(s, [
    "120 solicitudes, 0 errores, 3 conmutaciones",
    "La primaria vuelve 4–6 s después de recuperarse: circuito abierto (15 s) e intervalo del health check (5 s)",
    "Pregunta: ¿qué detectó primero la falla, el health check o el circuit breaker?",
  ], { x: 8.3, y: 1.5, w: 4.4, h: 4.5, fs: 15 });
  notes(s, "Duración: 10 minutos. Comando: python load-tests/failover_test.py --duracion 40 --falla-en 10 --recupera-en 25 (labs/01-local-gateway). La gráfica muestra el resultado obtenido en el entorno de preparación con --duracion 30 --falla-en 8 --recupera-en 18: cifras sintéticas del simulador. Discutir la demora en volver a la primaria: es deliberada para evitar oscilaciones (flapping). Variante: modo slow, en el que las solicitudes esperan el timeout de primer byte (15 s) antes de conmutar; muestra por qué el timeout es parte del RTO.");
}

// ================================================================ UNIDAD C
addSection("C · Selección de servicios gestionados");
divider("Unidad C · Selección de servicios gestionados según el caso de uso", "¿Con qué criterios se elige el servicio, el tipo de despliegue y la modalidad de consumo?",
  "Pausa de 10 minutos antes de esta unidad. Pregunta: elegir un servicio es elegir región, residencia, modelo de precio, SLA y forma de operar al mismo tiempo. Construiremos un procedimiento y lo aplicaremos a las tres nubes.");
{
  const s = contentSlide("Criterios de selección");
  table(s, ["Familia", "Criterio", "Pregunta de diseño"], [
    ["Funcional", "Modelos y capacidades", "¿Está el modelo (y la versión) que necesito, con herramientas, JSON estructurado y contexto suficiente?"],
    ["Ubicación", "Regiones y residencia", "¿Dónde se procesa y dónde se almacena? ¿Hay una segunda región con el mismo modelo?"],
    ["Rendimiento", "Latencia, cuota y throughput", "¿La cuota cubre el pico en tokens por minuto? ¿Qué latencia p95 obtengo?"],
    ["Economía", "Modalidad de consumo", "¿Pago por token, prioridad, flex, batch, reservado o GPU propia?"],
    ["Confiabilidad", "SLA y madurez", "¿Es GA o vista previa? ¿Qué SLA publica el proveedor para esa modalidad?"],
    ["Seguridad", "Red, identidad, cifrado", "¿Endpoints privados, identidad sin secretos, claves propias, registro de auditoría?"],
    ["Operación", "Ecosistema y habilidades", "¿Qué nube usa ya la institución y qué sabe operar el equipo?"],
    ["Estrategia", "Portabilidad", "¿Qué tan costoso es cambiar? ¿Uso APIs y estándares compatibles?"],
  ], { colW: [1.8, 2.7, 7.6], fs: 13 });
  notes(s, "Ocho familias de criterios. Ningún criterio decide solo. Error frecuente: elegir por el modelo de moda sin verificar región, cuota y residencia. En la Sesión 1 vimos la madurez de los frameworks (por ejemplo, Bedrock Agents Classic no admite clientes nuevos desde el 30-jul-2026); el mismo análisis aplica a los modelos: Google anunció el retiro de Gemini 2.5 en la plataforma, y una arquitectura que fija un modelo sin plan de migración acumula riesgo.");
}
{
  const s = contentSlide("Árbol de decisión de la modalidad de consumo");
  box(s, 0.6, 1.5, 3.2, 0.8, "¿Alguien espera la respuesta?", HEX.navy, { fs: 14, bold: true, color: "FFFFFF", line: HEX.navy });
  box(s, 4.4, 1.5, 3.6, 0.8, "¿Carga sostenida y predecible?", HEX.navy, { fs: 14, bold: true, color: "FFFFFF", line: HEX.navy });
  box(s, 8.6, 1.5, 4.1, 0.8, "Reservada: PTU · Provisioned Throughput · Reserved", HEX.mint, { fs: 13 });
  box(s, 8.6, 2.6, 4.1, 0.8, "Estándar o prioritaria por solicitud", HEX.sky, { fs: 13 });
  box(s, 0.6, 3.4, 3.2, 0.8, "¿Plazo menor que 24 h?", HEX.navy, { fs: 14, bold: true, color: "FFFFFF", line: HEX.navy });
  box(s, 4.4, 3.4, 3.6, 0.8, "Flex o cola propia con workers", HEX.sand, { fs: 13 });
  box(s, 4.4, 4.5, 3.6, 0.8, "Batch gestionado (−50 %)", HEX.sand, { fs: 13 });
  box(s, 8.6, 4.0, 4.1, 1.3, "Transversal: ¿datos restringidos?\n→ Data Zone, regional o perfil geográfico\n¿modelo propio u open-weight ajustado?\n→ autogestionado o modelos importados", HEX.light, { fs: 12 });
  arrow(s, 3.8, 1.9, 4.4, 1.9, HEX.blue); label(s, 3.8, 1.5, 0.6, 0.35, "sí", { fs: 12, bold: true, color: HEX.blue, align: "center" });
  arrow(s, 8.0, 1.9, 8.6, 1.9, HEX.blue); label(s, 8.0, 1.5, 0.6, 0.35, "sí", { fs: 12, bold: true, color: HEX.blue, align: "center" });
  arrow(s, 6.2, 2.3, 8.6, 3.0, HEX.grey); label(s, 6.3, 2.45, 0.6, 0.3, "no", { fs: 11, bold: true, color: HEX.grey });
  arrow(s, 2.2, 2.3, 2.2, 3.4, HEX.grey); label(s, 2.3, 2.7, 0.6, 0.3, "no", { fs: 11, bold: true, color: HEX.grey });
  arrow(s, 3.8, 3.8, 4.4, 3.8, HEX.blue); label(s, 3.8, 3.4, 0.6, 0.35, "sí", { fs: 12, bold: true, color: HEX.blue, align: "center" });
  arrow(s, 2.2, 4.2, 4.4, 4.9, HEX.grey); label(s, 2.4, 4.55, 0.6, 0.3, "no", { fs: 11, bold: true, color: HEX.grey });
  label(s, 0.6, 5.6, 12.1, 0.5, "La guía de costos de Bedrock sugiere evaluar la capacidad reservada cuando la carga sostenida supera aproximadamente el 40 % del costo on-demand; calcule su propio punto de equilibrio.", { fs: 12, italic: true });
  callout(s, "Una misma aplicación suele combinar dos o tres modalidades", 6.15, HEX.teal);
  notes(s, "Recorrer el árbol con las tres cargas del caso: asistente (alguien espera; en temporada de matrículas la carga es predecible pero estacional: estándar con prioridad en picos, o reservada solo si el volumen lo justifica); PQRS (nadie espera; plazo mayor que 24 h: batch); reindexación (batch). El umbral del 40 % es una heurística de la guía de AWS 'Capacity, limits and cost optimization'; no es un valor universal. Diagrama D-38.");
}
{
  const s = contentSlide("Mapa de servicios por caso de uso (20-oct-2026)");
  table(s, ["Caso de uso", "Microsoft Azure", "Google Cloud", "AWS"], [
    ["Conversación online", "Foundry · Global/Data Zone/Standard; Priority processing", "Gemini en Agent Platform · global, multirregional o regional", "Bedrock on-demand · CRIS · Priority"],
    ["Lote nocturno", "Azure OpenAI Batch (Global o Data Zone Batch)", "Gemini batch inference (Cloud Storage, BigQuery)", "Bedrock batch inference (S3)"],
    ["Plazo intermedio", "Flex processing · Service Bus + Container Apps", "Flex PayGo · Pub/Sub + Cloud Run", "Flex · SQS + Lambda o ECS"],
    ["Carga sostenida alta", "Provisioned (PTU) Global, Data Zone o regional", "Provisioned Throughput", "Reserved tier"],
    ["Gateway de IA", "API Management", "Apigee o gateway en Cloud Run", "API Gateway + Lambda o gateway en ECS"],
    ["Enrutamiento global", "Front Door · Traffic Manager", "Cloud Load Balancing global · Cloud DNS", "Route 53 · Global Accelerator · CloudFront"],
    ["Modelo autogestionado", "AKS · Container Apps con GPU", "GKE · Cloud Run con GPU", "EKS · ECS · SageMaker"],
  ], { colW: [2.3, 3.4, 3.2, 3.2], fs: 12 });
  notes(s, "Mapa de categorías, no recomendación de producto. Los nombres de servicios y modalidades se verificaron en la documentación oficial el 20-oct-2026 (excepto los servicios genéricos de enrutamiento y colas, conocidos y estables). Recordar el cambio de nombre: Vertex AI se presenta como Gemini Enterprise Agent Platform desde el 22-abr-2026. Antes de usar el mapa, verifique disponibilidad regional y estado GA del modelo concreto.");
}
{
  const s = contentSlide("Azure: tipo de despliegue = residencia + precio + SLA");
  table(s, ["", "Standard (pago por token)", "Provisioned (PTU)", "Batch"], [
    ["Global", "Inferencia en cualquier región; mayor cuota predeterminada", "Capacidad reservada, latencia más estable", "−50 % frente a Global Standard; objetivo 24 h"],
    ["Data Zone (EE. UU., UE, APAC)", "Inferencia dentro de la zona de datos", "Reservada dentro de la zona", "−50 %; dentro de la zona"],
    ["Regional (Standard)", "Inferencia dentro de la geografía elegida", "Reservada en la región", "—"],
  ], { colW: [2.6, 3.4, 2.9, 3.2], fs: 13 });
  bullets(s, [
    "Los datos en reposo permanecen en la geografía designada en todos los tipos",
    "Con Global y Data Zone Standard, si la región primaria se interrumpe, se afecta todo el tráfico enrutado a ella",
    "Priority processing: atributo del despliegue o de la solicitud (Global Standard y Data Zone Standard US)",
    "Developer: sin SLA ni garantía de residencia; solo para evaluar modelos ajustados",
  ], { y: 3.5, h: 2.6, fs: 15 });
  notes(s, "Fuente: Microsoft Learn 'Deployment types for Microsoft Foundry Models' (actualizada 12-ago-2026) y 'Priority processing' (22-sep-2026). Pregunta: si la política de la universidad exige que la inferencia ocurra en EE. UU., ¿qué tipo elegiría? Respuesta: Data Zone Standard US o Standard en una región de EE. UU.; no Global. Demo 3 usa Global Standard porque es el que tiene cuota en cuentas trial; documentar la diferencia.");
}
{
  const s = contentSlide("Google Cloud: ubicación del endpoint y modalidad de consumo");
  table(s, ["Ubicación del endpoint", "Dónde se procesa", "Uso típico"], [
    ["Global", "Cualquier ubicación de Google Cloud; sin garantías de residencia", "Máxima disponibilidad cuando no hay restricción de datos"],
    ["Multirregional (us, eu)", "Dentro de la jurisdicción; eu excluye Reino Unido y Suiza", "Residencia con más capacidad que una región"],
    ["Regional (p. ej., us-central1)", "Dentro de la jurisdicción de la región", "Residencia estricta; menor disponibilidad"],
  ], { colW: [3.0, 5.0, 4.1], fs: 13 });
  table(s, ["Modalidad", "Para qué"], [
    ["Standard PayGo", "Tráfico general"],
    ["Priority PayGo", "Cargas críticas con tráfico fluctuante"],
    ["Flex PayGo", "Cargas no críticas tolerantes a la latencia"],
    ["Provisioned Throughput", "Capacidad reservada"],
    ["Batch inference", "Lotes desde Cloud Storage o BigQuery, −50 %"],
  ], { y: 3.75, w: 7.0, colW: [2.6, 4.4], fs: 13 });
  box(s, 7.9, 3.75, 4.8, 2.2, "Los modelos anteriores a Gemini 3 no se admiten en los endpoints multirregionales jurisdiccionales.\nGemini 2.5 tiene retiro anunciado: actualice los laboratorios de la Sesión 1.", HEX.sand, { fs: 13, line: HEX.amber });
  notes(s, "Fuentes: 'Where your data lives and is processed', 'Supported capabilities by endpoint', 'Priority PayGo' y 'Flex PayGo' de la documentación de Gemini Enterprise Agent Platform; notas de versión (Gemini 3.8 Flash GA el 2-sep-2026; Priority PayGo añadió endpoints us y eu el 9-sep-2026). Advertencia honesta: varias páginas de Google no permitieron extraer las tablas de soporte por endpoint; verificar en la consola qué modalidades admite el modelo elegido en cada ubicación.");
}
{
  const s = contentSlide("AWS: perfiles de inferencia y niveles de servicio");
  table(s, ["Opción", "Comportamiento", "Consideraciones"], [
    ["Modelo en una región", "Se procesa en la región de origen", "Máximo control de residencia; capacidad de una región"],
    ["Perfil geográfico (us., eu., jp., au.)", "Bedrock elige una región dentro de la geografía", "IAM y SCP deben permitir todas las regiones de destino"],
    ["Perfil global (global.)", "Cualquier región comercial", "Mayor capacidad; sin restricción geográfica"],
    ["Niveles Priority, Standard, Flex", "Se elige por solicitud con service_tier", "Comparten la cuota on-demand"],
    ["Reserved", "Capacidad de tokens por minuto reservada por 1 o 3 meses", "Mínimos de 100.000 TPM de entrada y 10.000 de salida; desborda a Standard"],
    ["Batch", "S3 → trabajo → S3", "Mínimo 100 registros; −50 %"],
  ], { colW: [3.2, 4.3, 4.6], fs: 13 });
  callout(s, "El plan Free de AWS no admite funciones multirregión ni entre regiones: para CRIS use el plan Paid con presupuesto", 6.15, HEX.amber);
  notes(s, "Fuentes: AWS 'Service tiers for optimizing performance and cost', 'Securing Amazon Bedrock cross-Region inference: Geographic and global' (AWS ML Blog, 13-ene-2026), cuotas de Bedrock, y 'Supported AWS services for Sign up for AWS (new)', que indica que las funciones multirregión o entre regiones no se admiten en el plan Free. Nota: CRIS no cambia dónde se almacenan los datos; los logs y configuraciones permanecen en la región de origen.");
}
{
  const s = contentSlide("Gestionado vs. autogestionado en una topología multi-región");
  table(s, ["Aspecto", "Modelo gestionado (API)", "Modelo autogestionado (GPU propia)"], [
    ["Región secundaria en espera", "Despliegue sin tráfico: sin cargo por tokens", "GPU encendida = costo por hora; apagada = arranque en frío"],
    ["Capacidad en el incidente", "Cuota de la suscripción o proyecto", "Disponibilidad de GPU en la región secundaria"],
    ["Conmutación", "Cambio de endpoint o capa del proveedor", "Cambio de clúster; pesos e imágenes replicados"],
    ["Versión del modelo", "Decide el proveedor (retiros programados)", "Decide usted (fija los pesos)"],
    ["Residencia", "Según tipo de despliegue o endpoint", "Total: usted elige dónde corre"],
  ], { colW: [3.0, 4.5, 4.6], fs: 13 });
  bullets(s, [
    "Con el caso de la Sesión 1: 2 instancias L4 24/7 en Cloud Run ≈ US$1.507 al mes; el asistente con gpt-5-mini ≈ US$67,50 al mes",
    "La redundancia multi-región amplía esa diferencia: duplicar GPU duplica el costo fijo",
  ], { y: 4.6, h: 1.5, fs: 15 });
  notes(s, "Retomar las cifras de la Sesión 1 (precios oficiales consultados el 13-oct-2026): Cloud Run con GPU L4 ≈ US$1,047 por hora por instancia (2 × 720 h ≈ US$1.507 al mes) frente a ≈ US$67,50 al mes del asistente con gpt-5-mini Global. En multi-región autogestionado, un warm standby con GPU duplica el costo fijo; un pilot light lo evita pero alarga el RTO por la carga de pesos. Por eso, para el caso, la recomendación de partida es gestionado multi-región, y autogestionado solo si un requisito (modelo propio, residencia estricta, volumen muy alto) lo justifica.");
}
{
  const s = contentSlide("Portabilidad: reducir el costo de cambiar");
  flow(s, ["Clientes\n(web, móvil, agentes)", "Contrato propio\n/v1/chat · /v1/batches", "Gateway con\nadaptadores", "Foundry · Agent Platform\n· Bedrock · Ollama"], 1.6, 1.3, [HEX.sky, HEX.mint, HEX.light, HEX.sand]);
  bullets(s, [
    "Contrato de API propio (Sesión 1): los clientes no conocen al proveedor",
    "APIs compatibles con Chat Completions: el mismo gateway de LOC-02 habla con Ollama, con Foundry (/openai/v1) o con un simulador",
    "Formatos de lote equivalentes: un generador produce los tres formatos (lote_pqrs.py)",
    "OpenTelemetry con convenciones GenAI: la misma telemetría en cualquier nube",
    "El lock-in no desaparece: cuotas, identidad, red y datos siguen siendo propios de cada nube",
  ], { y: 3.2, h: 2.9, fs: 16 });
  notes(s, "La portabilidad tiene un costo (una capa más) y un beneficio (negociación, continuidad, multi-nube por regulación). La recomendación del curso es portabilidad en el contrato y en la telemetría, no en todo. Ejemplo concreto del repositorio: el mismo archivo JSONL de lote sirve en LOC-02 y en Azure OpenAI Batch; Gemini y Bedrock requieren otro formato, generado desde la misma fuente.");
}
{
  const s = contentSlide("Demo 3 · Azure: dos regiones y conmutación (AZ-G)");
  flow(s, ["Portal: cuota por\nsuscripción\n(AZ-G.1)", "Dos recursos Foundry\nEast US 2 y\nSweden Central (AZ-G.2)", "online_failover.py\n10 repeticiones\n(AZ-G.4)", "Primaria inválida:\nconmutación\n(AZ-G.5)"], 1.6, 1.5, [HEX.sky, HEX.light, HEX.mint, HEX.rose]);
  bullets(s, [
    "Prediga: con la primaria inaccesible, ¿cuántos intentos verá en la primera y en la segunda solicitud?",
    "Observe: la segunda región responde, pero ambas comparten la cuota de Global Standard de la suscripción",
    "Si hay suscripción de pago: mostrar Azure OpenAI Batch con el mismo lote (AZ-G.6)",
  ], { y: 3.4, h: 2.6, fs: 16 });
  callout(s, "Plan B: grabación del docente + pruebas sin red del laboratorio (pytest)", 6.15, HEX.grey);
  notes(s, "Duración: 10 minutos. Preparar los dos recursos y el rol antes de la clase. Resultado esperado: primera solicitud con 2 intentos desde swedencentral, las siguientes con 1 intento mientras la primaria está en pausa (30 s). Recordar que la parte batch no está disponible en cuentas trial (cuota N/A). Si la cuenta trial no tiene cuota para gpt-5-mini, usar la grabación y la ruta alternativa con Ollama de la Sesión 1.");
}

// ================================================================ UNIDAD D
addSection("D · Seguridad, residencia y costo");
divider("Unidad D · Seguridad, residencia y costo de la redundancia", "¿Qué se rompe en seguridad y en presupuesto cuando el sistema se vuelve multi-región?",
  "Unidad corta pero obligatoria: cada copia del sistema es una copia de su superficie de ataque y de su factura.");
{
  const s = contentSlide("Residencia de datos: qué viaja y qué se queda");
  table(s, ["Mecanismo", "Inferencia (datos en uso)", "Datos en reposo"], [
    ["Azure Global / Data Zone / Standard", "Cualquier región / zona de datos / geografía", "Geografía designada"],
    ["Google endpoint global / multirregional / regional", "Cualquier ubicación / jurisdicción / región", "Ubicación del recurso"],
    ["AWS perfil global / geográfico / región", "Cualquier región comercial / geografía / región", "Región de origen (logs, configuración)"],
  ], { colW: [4.2, 4.5, 3.4], fs: 13 });
  bullets(s, [
    "Defina la clasificación de los datos antes de elegir el tipo de despliegue",
    "Las PQRS contienen datos personales: la base legal y las transferencias deben revisarse con la oficina jurídica (Ley 1581 de 2012)",
    "Documente en un ADR la combinación elegida y por qué es compatible con la política institucional",
  ], { y: 3.4, h: 2.7, fs: 16 });
  notes(s, "Distinguir datos en uso (lo que viaja para la inferencia) de datos en reposo (lo que se almacena). Fuentes: Microsoft 'Deployment types'; Google 'Where your data lives and is processed'; AWS ML Blog sobre CRIS. Sobre la Ley 1581 de 2012: no dar asesoría legal; señalar que la transferencia y el tratamiento por encargados en otros países tienen reglas propias y que la decisión es de la oficina jurídica. Los decretos reglamentarios vigentes deben revisarse con ella.");
}
{
  const s = contentSlide("Seguridad en una topología multi-región");
  const items = [
    ["Identidad", "Identidades de carga en cada región; mismos roles mínimos. Una SCP o política regional puede romper la conmutación"],
    ["Red", "Endpoints privados en cada región; la secundaria con los mismos controles que la primaria"],
    ["Secretos", "Gestor de secretos replicado; sin claves en archivos de configuración de regiones"],
    ["Configuración", "Prompts de sistema y guardrails idénticos en todas las regiones, desplegados desde Git"],
    ["Registro y auditoría", "Telemetría centralizada sin contenido de conversaciones; región y modalidad en cada traza"],
    ["Lotes", "Buckets cifrados y privados, rol de servicio con mínimo privilegio, caducidad de archivos"],
  ];
  items.forEach((it, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = 0.6 + col * 6.15, y = 1.45 + row * 1.55;
    box(s, x, y, 2.1, 1.3, it[0], [HEX.sky, HEX.sky, HEX.mint, HEX.mint, HEX.sand, HEX.sand][i], { fs: 15, bold: true });
    label(s, x + 2.25, y, 3.7, 1.3, it[1], { fs: 13, color: HEX.ink });
  });
  label(s, 0.6, 6.2, 12.1, 0.5, "Principio: la región secundaria no puede ser la menos protegida (Zero Trust, NIST SP 800-207).", { fs: 13, italic: true, color: HEX.navy });
  notes(s, "Error frecuente: la región secundaria se crea deprisa, con acceso público o con claves, porque «solo es respaldo». En un incidente se convierte en la región principal. AWS documenta que las políticas IAM y SCP deben permitir todas las regiones de destino de un perfil CRIS: una política demasiado estricta rompe la conmutación; una demasiado amplia abre regiones no deseadas. En los laboratorios: AZ-G usa Entra ID y el rol Cognitive Services OpenAI User; AWS-E usa un rol de servicio con aws:SourceAccount y aws:SourceArn y acceso solo al prefijo pqrs/.");
}
{
  const s = contentSlide("FinOps: ¿cuánto cuesta cada modalidad para el lote de PQRS?");
  s.addChart(pres.charts.BAR, [{ name: "US$ al mes", labels: ["Online estándar", "Batch (−50 %)", "GPU L4 1 h por noche*"], values: [5.10, 2.55, 31.41] }], {
    ...chartBase({ x: 0.6, y: 1.4, w: 6.4, h: 4.6, title: "Lote de PQRS: costo mensual estimado (US$)", yTitle: "US$ al mes" }),
    barDir: "col", chartColors: [HEX.blue], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "$#,##0.00", valAxisMinVal: 0,
  });
  bullets(s, [
    "Supuestos: 20.000 PQRS al mes · 350 tokens de entrada y 60 de salida por PQRS → 7,0 M y 1,2 M tokens",
    "Precios publicados de Gemini 2.5 Flash (US$ por 1 M): 0,30 / 2,50 estándar y 0,15 / 1,25 batch, consultados el 20-oct-2026, usados solo para ilustrar la proporción",
    "* Cloud Run con GPU L4 a ≈ US$1,047 por hora (Sesión 1), 30 noches; supone que un modelo pequeño procesa el lote en 1 h (hipótesis no medida)",
  ], { x: 7.3, y: 1.5, w: 5.4, h: 4.6, fs: 13 });
  callout(s, "A este volumen, el batch gestionado es la opción más barata; la GPU solo compite con volúmenes mucho mayores", 6.15, HEX.navy);
  notes(s, "Cálculo en vivo: 20.000 × 350 = 7,0 M tokens de entrada; 20.000 × 60 = 1,2 M de salida. Estándar: 7,0 × 0,30 + 1,2 × 2,50 = 2,10 + 3,00 = US$5,10. Batch: la mitad, US$2,55. GPU programada 1 h por noche: 1,047 × 30 = US$31,41, sin contar almacenamiento, operación ni el riesgo de que el lote no quepa en una hora. Advertencias: 1) Gemini 2.5 tiene retiro anunciado; se usa porque su tabla de precios estándar y batch está publicada; repita el cálculo con el modelo vigente; 2) el número de tokens por PQRS es una hipótesis: mídalo con el tokenizador real.");
}
{
  const s = contentSlide("FinOps de la redundancia y de la topología");
  table(s, ["Fuente de costo", "Comportamiento", "Palanca"], [
    ["Región secundaria gestionada", "Sin tokens, sin cargo por tokens", "Mantenerla lista y probada; no reservar capacidad salvo necesidad"],
    ["Región secundaria con GPU", "Costo por hora aunque no reciba tráfico", "Pilot light, escalado a cero o reserva compartida"],
    ["Capacidad reservada", "Pago fijo mensual", "Dimensionar la base; desbordar a estándar"],
    ["Gateway y balanceador global", "Cargo por hora o por solicitud", "Compartir entre aplicaciones; elegir nivel según funciones"],
    ["Tráfico entre regiones", "Transferencia de datos y replicación", "Replicar solo lo necesario; índices reconstruibles"],
    ["Priority", "Precio superior al estándar", "Solo para las solicitudes que lo necesitan"],
    ["Batch y Flex", "Descuento a cambio de plazo", "Mover toda carga sin usuario esperando"],
  ], { colW: [3.0, 4.0, 5.1], fs: 13 });
  notes(s, "Tabla para el taller. La regla FinOps de la sesión: pague latencia solo donde hay una persona esperando. Cada fila es un parámetro que los equipos deben estimar en su diseño. Los precios de transferencia entre regiones y de los gateways varían por nube y región: consúltelos en las páginas oficiales; el curso no fija cifras que puedan quedar desactualizadas.");
}

// ================================================================ UNIDAD E (TALLER)
addSection("E · Taller de diseño preliminar");
divider("Taller · Diseño preliminar de una topología", "Aplicar la unidad completa a un caso empresarial y defender las decisiones",
  "30 minutos: 5 de explicación, 18 de trabajo en equipos de 3 o 4 personas y 7 de exposición de dos equipos. Plantilla y rúbrica en sesiones/s02-topologias/taller.");
{
  const s = contentSlide("Método de diseño preliminar en ocho pasos");
  const steps = ["1 · Requisitos y supuestos", "2 · Clasificar cargas: online, asíncrona, batch", "3 · SLO, RTO y RPO por carga", "4 · Datos: clasificación y residencia", "5 · Topología: zonas, regiones, estrategia", "6 · Servicios y modalidades por nube", "7 · Riesgos y controles", "8 · Costo estimado y ADR"];
  steps.forEach((t, i) => {
    const col = i % 4, row = Math.floor(i / 4);
    const x = 0.6 + col * 3.08, y = 1.6 + row * 1.9;
    box(s, x, y, 2.8, 1.4, t, row === 0 ? HEX.sky : HEX.mint, { fs: 15, bold: true });
    if (col < 3) arrow(s, x + 2.8, y + 0.7, x + 3.08, y + 0.7);
  });
  arrow(s, 11.6, 3.0, 11.6, 3.5, HEX.grey);
  label(s, 0.6, 5.4, 12.1, 0.7, "Un diseño preliminar no busca precisión: busca hacer explícitos los supuestos, las decisiones y sus trade-offs para poder validarlos.", { fs: 15, italic: true, color: HEX.navy });
  notes(s, "Explicar el método. El paso 2 es el que más se omite: diseñar una sola topología para cargas con SLO distintos. El paso 8 cierra con un ADR (formato de la Sesión 1: contexto, decisión, alternativas, consecuencias). Diagrama D-44 con la plantilla.");
}
{
  const s = contentSlide("Tres casos empresariales (elija uno por equipo)");
  const cases = [
    ["A · Universidad", "Asistente 24/7 para 5.000 estudiantes con picos en matrículas; 20.000 PQRS al mes clasificadas cada noche; reindexación semanal. Requisito: operar si cae una región; datos personales.", HEX.sky],
    ["B · Retail regional", "Chat de soporte en 4 países de Latinoamérica con 2.000 conversaciones concurrentes en temporada alta; generación nocturna de 50.000 descripciones de productos. Requisito: p95 < 3 s en el chat; presupuesto ajustado.", HEX.mint],
    ["C · Entidad financiera", "Análisis de solicitudes de crédito (documentos de 30 páginas) con respuesta en menos de 10 minutos; auditoría completa. Requisitos: inferencia solo en el país o la zona de datos; RTO 1 h; RPO 0 para las decisiones.", HEX.sand],
  ];
  cases.forEach((c, i) => {
    const y = 1.45 + i * 1.6;
    box(s, 0.6, y, 2.6, 1.35, c[0], c[2], { fs: 16, bold: true });
    label(s, 3.4, y, 9.3, 1.35, c[1], { fs: 14, color: HEX.ink });
  });
  label(s, 0.6, 6.3, 12.1, 0.45, "Las cifras son supuestos del ejercicio. Si falta un dato, regístrelo como supuesto y continúe.", { fs: 12, italic: true });
  notes(s, "Los tres casos obligan a decisiones distintas: A combina online, batch y multi-región; B prioriza latencia, picos y costo en varios países; C prioriza residencia, auditoría y un RTO/RPO exigente con una carga asíncrona (10 minutos: ni online ni batch de 24 h). Soluciones de referencia en el repositorio privado del docente. Asignar casos para que al menos dos equipos tengan casos distintos.");
}
{
  const s = contentSlide("Plantilla del diseño preliminar");
  table(s, ["Sección", "Qué entregar"], [
    ["Cargas de trabajo", "Lista de cargas con su patrón (online, asíncrona, batch) y su SLO"],
    ["Objetivos de continuidad", "Disponibilidad, RTO y RPO por carga, con la justificación"],
    ["Datos", "Clasificación y restricciones de residencia"],
    ["Topología", "Diagrama: regiones, zonas, enrutamiento global, gateway, datos replicados"],
    ["Servicios", "Servicio, tipo de despliegue o endpoint y modalidad de consumo, en una nube principal"],
    ["Resiliencia", "Patrones aplicados: timeouts, reintentos, circuit breaker, degradación"],
    ["Riesgos", "Tres riesgos principales con su control (incluido al menos uno de OWASP LLM)"],
    ["Costo", "Estimación por modalidad con supuestos explícitos"],
    ["ADR", "Una decisión con contexto, alternativas y consecuencias"],
  ], { colW: [3.0, 9.1], fs: 13 });
  notes(s, "La plantilla está en sesiones/s02-topologias/taller/plantilla-diseno.md. Pedir que el diagrama sea a mano o en Mermaid. Para el costo, no es necesario consultar precios en clase: usar las cifras de la Unidad D o variables.");
}
{
  const s = contentSlide("Rúbrica y preguntas guía");
  table(s, ["Criterio", "Peso"], [
    ["Clasificación de cargas y SLO coherentes", "20 %"],
    ["Topología justificada con RTO, RPO y dominios de falla", "25 %"],
    ["Selección de servicios y modalidades con criterios", "20 %"],
    ["Residencia, seguridad y riesgos", "15 %"],
    ["Costo con supuestos explícitos", "10 %"],
    ["ADR claro y defendible", "10 %"],
  ], { w: 6.2, colW: [4.9, 1.3], fs: 14 });
  bullets(s, [
    "¿Qué carga sobrevive a la caída de una región y cuál no? ¿Es aceptable?",
    "¿Quién conmuta: el proveedor, el gateway o el cliente?",
    "¿Qué componente global quedó en serie?",
    "¿Dónde se procesa cada dato personal?",
    "¿Qué pagaría aunque no hubiera tráfico?",
  ], { x: 7.1, y: 1.5, w: 5.6, h: 4.6, fs: 15 });
  notes(s, "Circular entre los equipos con estas preguntas. Seleccionar para exponer dos equipos con casos distintos. La rúbrica detallada por niveles está en sesiones/s02-topologias/taller/rubrica.md.");
}

// ================================================================ CIERRE
addSection("Cierre");
{
  const s = contentSlide("Síntesis: seis ideas de la sesión");
  const ideas = [
    "El SLO define la carga: latencia para lo online, plazo y costo por ítem para el lote",
    "Lo que puede esperar, debe esperar: batch y flex cuestan menos",
    "La disponibilidad compuesta se calcula; el componente global en serie es el techo",
    "La multi-región del proveedor no reemplaza la propia: endpoint, datos y aplicación son suyos",
    "Conmutar solo antes del primer token y con presupuesto de reintentos",
    "Cada región copia también la superficie de ataque, la residencia y la factura",
  ];
  ideas.forEach((t, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = 0.6 + col * 6.15, y = 1.45 + row * 1.55;
    circle(s, x, y + 0.2, 0.8, String(i + 1), [HEX.blue, HEX.teal, HEX.amber, HEX.red, HEX.violet, HEX.navy][i], "FFFFFF", 18);
    label(s, x + 1.0, y, 4.9, 1.2, t, { fs: 15, color: HEX.ink });
  });
  notes(s, "Retomar la pregunta inicial: ¿la misma topología sirve para todo? No: el asistente, el lote de PQRS y la reindexación tienen SLO, modalidades y estrategias de continuidad distintas, aunque compartan componentes.");
}
{
  const s = contentSlide("Autoevaluación (5 minutos)");
  table(s, ["#", "Pregunta"], [
    ["1", "Una aplicación clasifica 1 millón de correos al mes y los resultados se usan al día siguiente. ¿Qué modalidad elegiría y por qué?"],
    ["2", "Gateway 99,95 %, backend 99,95 % y modelo 99,9 % en serie, duplicados en dos regiones, más un DNS global de 99,99 %. ¿Cuál es la disponibilidad?"],
    ["3", "¿Por qué un segundo despliegue Global Standard en otra región de la misma suscripción no resuelve los 429 por cuota?"],
    ["4", "¿Qué ocurre si el SDK, el gateway y el backend reintentan cada uno 3 veces?"],
    ["5", "¿Qué tipo de despliegue o endpoint usaría si la inferencia debe ocurrir solo en EE. UU.? Responda para las tres nubes."],
  ], { colW: [0.6, 11.5], fs: 14 });
  notes(s, "Respuestas: 1) batch gestionado (o flex si el plazo fuera menor que 24 h): nadie espera, 50 % de descuento; 2) ≈ 99,99 % (el DNS en serie es el techo; 99,9896 % con las cifras de la Unidad B); 3) desde el 7-may-2026 la cuota de Global Standard es por suscripción y se comparte entre regiones; 4) hasta 27 llamadas por solicitud: tormenta de reintentos; 5) Azure: Data Zone Standard US o Standard en región de EE. UU.; Google: endpoint multirregional us o regional en EE. UU.; AWS: modelo en una región de EE. UU. o perfil geográfico us.");
}
{
  const s = contentSlide("Laboratorios y próxima sesión");
  table(s, ["Laboratorio", "Contenido", "Cuenta trial"], [
    ["LOC-02", "Gateway multi-región: failover, circuit breaker, API batch, React", "No requiere nube"],
    ["AZ-G", "Dos regiones de Foundry, conmutación, Azure OpenAI Batch, APIM", "Sí (batch: solo con suscripción de pago)"],
    ["GCP-D", "Ubicaciones de Gemini, conmutación, batch inference", "Sí, con presupuesto"],
    ["AWS-E", "CRIS, niveles de servicio, conmutación, batch con rol de servicio", "Plan Paid recomendado"],
  ], { colW: [1.8, 6.9, 3.4], fs: 14 });
  bullets(s, [
    "Tarea: completar el diseño preliminar del taller con su ADR y la estimación de costos",
    "Lectura: guía de gateways frente a múltiples despliegues (Azure Architecture Center) y estrategias de DR (AWS)",
    "Próxima sesión: sistemas distribuidos y contenedorización (Docker y Kubernetes) para servir LLMs",
  ], { y: 4.2, h: 1.9, fs: 15 });
  notes(s, "Recordar la limpieza de recursos de cada laboratorio y revisar el panel de costos 24 horas después. La próxima sesión continúa el eje del curso: sistemas distribuidos y contenedorización; el gateway de LOC-02 será uno de los servicios que se empaquetará y desplegará.");
}
{
  const s = contentSlide("Referencias (1/2) · Documentación oficial");
  bullets(s, [
    "Microsoft Learn. Deployment types for Microsoft Foundry Models (12-ago-2026); Getting started with Azure OpenAI batch deployments (5-jun-2026); Quotas and limits (20-ago-2026); Priority processing (22-sep-2026)",
    "Microsoft. High availability and resiliency for Microsoft Foundry (22-sep-2026); Azure Architecture Center, gateway frente a múltiples despliegues (2026); API Management backends (20-may-2026)",
    "Google Cloud. Batch inference with Gemini; Where your data lives and is processed; Priority PayGo y Flex PayGo; Pricing; notas de versión de Gemini Enterprise Agent Platform",
    "AWS. Service tiers for optimizing performance and cost; Capacity, limits and cost optimization; batch inference (formato, rol de servicio, modelos); Securing cross-Region inference (13-ene-2026)",
    "AWS Architecture Blog. Eliot, S. (2021). Disaster Recovery (DR) Architecture on AWS, Part I",
  ], { fs: 14 });
  notes(s, "Enlaces completos y estado de verificación en docs/referencias.md, sección Sesión 2.");
}
{
  const s = contentSlide("Referencias (2/2) · Libros, estándares y artículos");
  bullets(s, [
    "Beyer, B., Jones, C., Petoff, J. y Murphy, N. R. (2016). Site Reliability Engineering. O'Reilly",
    "Nygard, M. T. (2018). Release It! Design and Deploy Production-Ready Software (2.ª ed.). Pragmatic Bookshelf",
    "Harchol-Balter, M. (2013). Performance Modeling and Design of Computer Systems: Queueing Theory in Action. Cambridge University Press",
    "Kleppmann, M. (2017). Designing Data-Intensive Applications. O'Reilly",
    "OWASP. Top 10 for LLM Applications 2025 · NIST SP 800-207 (2020) · ISO/IEC 42001:2023 · Ley 1581 de 2012",
    "Agrawal et al. (2024). Sarathi-Serve, OSDI · Zhong et al. (2024). DistServe, OSDI",
  ], { fs: 14 });
  notes(s, "Lecturas recomendadas para la semana: capítulos 21 y 22 del libro de SRE (sobrecarga y fallas en cascada) y el capítulo de estabilidad de Release It! (circuit breaker, bulkhead, timeouts).");
}

(async () => {
  const out = path.join(__dirname, "S02-Topologias-Casos-Empresariales.pptx");
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  console.log("OK", out);
})();
