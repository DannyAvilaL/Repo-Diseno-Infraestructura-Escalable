const pptxgen = require("pptxgenjs");
const { applyTheme } = require("/mnt/skills/public/pptx/scripts/apply_theme.js");
const { THEME, icon } = require("./lib.js");

const OUT = process.argv[2] || "Sesion04_Redes_Almacenamiento_Autoscaling_LLM.pptx";
const HEX = THEME.colors;

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  pres.title = "Sesión 4 — Redes, Almacenamiento y Autoscaling en Entornos de Inferencia";
  pres.author = "Curso Diseño de Infraestructura Escalable para LLMs";
  const C = pres.SchemeColor;

  // ---------- Layouts ----------
  const FOOT = "Sesión 4 · Redes, Almacenamiento y Autoscaling en Inferencia";
  pres.defineSlideMaster({
    title: "CONTENT", background: { color: C.background1 },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.3, w: 9.0, h: 0.8, fontSize: 28, bold: true, color: C.text1, valign: "middle", margin: 0 }, text: "" } },
      { text: { text: FOOT, options: { x: 0.5, y: 5.27, w: 7.5, h: 0.28, fontSize: 10, color: C.text2, margin: 0 } } },
    ],
    slideNumber: { x: 9.0, y: 5.27, w: 0.5, h: 0.28, fontSize: 10, color: C.text2, align: "right" },
  });
  pres.defineSlideMaster({
    title: "DARK", background: { color: C.text1 },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 1.5, w: 8.8, h: 1.5, fontSize: 38, bold: true, color: C.background1, valign: "middle", margin: 0 }, text: "" } },
      { placeholder: { options: { name: "body", type: "body", x: 0.6, y: 3.15, w: 8.8, h: 1.2, fontSize: 18, color: C.background2, valign: "top", margin: 0 }, text: "" } },
    ],
  });

  // ---------- Iconos ----------
  const names = ["FaNetworkWired", "FaServer", "FaDatabase", "FaMicrochip", "FaShieldAlt", "FaChartLine", "FaClock", "FaBalanceScale",
    "FaLock", "FaCloud", "FaCubes", "FaHdd", "FaRoute", "FaTachometerAlt", "FaExclamationTriangle", "FaDollarSign", "FaUniversity",
    "FaComments", "FaLayerGroup", "FaSearch", "FaCheckCircle", "FaQuestionCircle", "FaBook", "FaFlask", "FaBolt", "FaSnowflake",
    "FaUsers", "FaCodeBranch", "FaBoxOpen", "FaKey", "FaEye", "FaFire", "FaMemory", "FaPlug", "FaTasks", "FaStream"];
  const IC = {};
  for (const n of names) IC[n] = await icon(n, "FFFFFF");

  // ---------- Helpers ----------
  let sectionOpen = null;
  const section = (t) => { pres.addSection({ title: t }); sectionOpen = t; };
  const S = (title, notes) => {
    const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: sectionOpen });
    s.addText(title, { placeholder: "title" });
    s.addNotes(notes);
    return s;
  };
  const badge = (s, n, x, y, color = C.accent1, d = 0.42) => {
    s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color }, line: { color, width: 0 }, objectName: "badge-" + n });
    s.addText(String(n), { x, y, w: d, h: d, align: "center", valign: "middle", fontSize: 14, bold: true, color: C.background1, margin: 0, isTextBox: true });
  };
  const iconCircle = (s, nm, x, y, color = C.accent1, d = 0.5) => {
    s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color }, line: { color, width: 0 }, objectName: "ic-bg-" + nm });
    s.addImage({ data: IC[nm], x: x + d * 0.22, y: y + d * 0.22, w: d * 0.56, h: d * 0.56, altText: nm });
  };
  const card = (s, { x, y, w, h, title, body, ic, color = C.accent1, fs = 14 }) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: C.background2 }, line: { color: C.background2, width: 0 }, objectName: "card" });
    let tx = x + 0.18, tw = w - 0.36;
    if (ic) { iconCircle(s, ic, x + 0.18, y + 0.18, color); tx = x + 0.82; tw = w - 1.0; }
    s.addText(title, { x: tx, y: y + 0.12, w: tw, h: 0.55, fontSize: 16, bold: true, color: C.text1, valign: "middle", margin: 0, isTextBox: true });
    s.addText(body, { x: x + 0.18, y: y + 0.75, w: w - 0.36, h: h - 0.85, fontSize: fs, color: C.text1, valign: "top", margin: 0, isTextBox: true });
  };
  const tbl = (s, rows, { x = 0.5, y = 1.35, w = 9.0, colW, fs = 12, rowH = 0.4 } = {}) => {
    const data = rows.map((r, i) => r.map((c) => ({
      text: c,
      options: i === 0
        ? { bold: true, color: C.background1, fill: { color: C.text2 }, fontSize: fs, valign: "middle" }
        : { color: C.text1, fill: { color: i % 2 ? C.background1 : C.background2 }, fontSize: fs, valign: "middle", bold: false },
    })));
    s.addTable(data, { x, y, w, colW, rowH, border: { type: "solid", pt: 0.5, color: C.background2 }, margin: [0.04, 0.08, 0.04, 0.08], autoPage: false });
  };
  const box = (s, text, { x, y, w, h, fill = C.accent1, color = C.background1, fs = 14, bold = true }) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.06, fill: { color: fill }, line: { color: fill, width: 0 }, objectName: "box" });
    s.addText(text, { x, y, w, h, fontSize: fs, bold, color, align: "center", valign: "middle", margin: 0.05, isTextBox: true });
  };
  const arrow = (s, x1, y1, x2, y2, color = C.accent4) => {
    s.addShape(pres.shapes.LINE, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1), flipH: x2 < x1, flipV: y2 < y1, line: { color, width: 1.75, endArrowType: "triangle" } });
  };
  const flow = (s, steps, { x = 0.5, y = 2.2, w = 9.0, h = 0.9, gap = 0.28, fills } = {}) => {
    const n = steps.length, bw = (w - gap * (n - 1)) / n;
    steps.forEach((t, i) => {
      const bx = x + i * (bw + gap);
      box(s, t, { x: bx, y, w: bw, h, fill: fills ? fills[i % fills.length] : C.accent1, fs: 14 });
      if (i < n - 1) arrow(s, bx + bw + 0.03, y + h / 2, bx + bw + gap - 0.03, y + h / 2);
    });
  };
  const formula = (s, text, { x = 0.5, y = 1.4, w = 9.0, h = 0.8, fs = 20 } = {}) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: C.text2 }, line: { color: C.text2, width: 0 }, objectName: "formula" });
    s.addText(text, { x, y, w, h, fontSize: fs, italic: true, color: C.background1, align: "center", valign: "middle", margin: 0.1, isTextBox: true });
  };
  const stat = (s, { x, y, w = 2.0, big, label, color = C.accent1 }) => {
    s.addText(big, { x, y, w, h: 0.9, fontSize: 44, bold: true, color, align: "left", valign: "middle", margin: 0, isTextBox: true });
    s.addText(label, { x, y: y + 0.9, w, h: 0.7, fontSize: 14, color: C.text1, valign: "top", margin: 0, isTextBox: true });
  };
  const bullets = (s, items, { x = 0.5, y = 1.4, w = 9.0, h = 3.6, fs = 16 } = {}) => {
    const runs = items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 8 } }));
    s.addText(runs, { x, y, w, h, fontSize: fs, color: C.text1, valign: "top", margin: 0, isTextBox: true });
  };
  const note = (s, text, y = 4.75) =>
    s.addText(text, { x: 0.5, y, w: 9.0, h: 0.4, fontSize: 12, italic: true, color: C.accent4, margin: 0, valign: "middle", isTextBox: true });
  const divider = (num, title, sub, notes) => {
    const s = pres.addSlide({ masterName: "DARK", sectionTitle: sectionOpen });
    s.addText(num, { x: 0.6, y: 0.7, w: 3, h: 0.8, fontSize: 54, bold: true, color: C.accent2, margin: 0, isTextBox: true });
    s.addText(title, { placeholder: "title" });
    s.addText(sub, { placeholder: "body" });
    s.addNotes(notes);
    return s;
  };

  // =========================================================================
  // PORTADA
  // =========================================================================
  section("Apertura");
  {
    const s = pres.addSlide({ masterName: "DARK", sectionTitle: sectionOpen });
    s.addText("CAPÍTULO 2 · SISTEMAS DISTRIBUIDOS Y CONTENEDORES · SESIÓN 4", { x: 0.6, y: 0.7, w: 8.8, h: 0.4, fontSize: 14, bold: true, color: C.accent2, margin: 0, isTextBox: true });
    s.addText("Redes, almacenamiento y autoscaling en inferencia", { placeholder: "title", fontSize: 28 });
    s.addText("Diseño de Infraestructura Escalable para LLMs · Maestría · 3 horas", { placeholder: "body" });
    s.addNotes(`[0:00 · 3 min] Bienvenida. Mensaje de apertura: en las sesiones anteriores vimos arquitecturas base, contenedores y orquestación. Hoy respondemos tres preguntas que determinan si un servicio de LLM sobrevive al uso real: (1) ¿cómo llega el tráfico al modelo?, (2) ¿dónde viven los pesos y cómo llegan a la memoria de la GPU?, (3) ¿cómo se agrega y se quita capacidad —incluida la GPU— sin romper la experiencia ni el presupuesto?
Aclare el formato: esta sesión es deliberadamente teórica, con diagramas y criterios de decisión. El código vive en el repositorio y en los laboratorios; solo se muestra en las demostraciones.
Recordatorio de transparencia académica: distinguiremos HECHOS documentados (con fuente), SUPUESTOS del caso universitario y RECOMENDACIONES de diseño.`);
  }

  // 2 Objetivos
  {
    const s = S("Resultados de aprendizaje", `[0:03 · 3 min] Lea los cuatro resultados como verbos medibles: se evaluarán en la actividad final y en el cuestionario. Enfatice que el objetivo de desempeño del capítulo (despliegue contenedorizado con red, almacenamiento y autoscaling) se logra con la combinación de la teoría de hoy y el laboratorio.
Pregunta de calibración (30 s): ¿quién ha configurado un balanceador o un HPA? Ajuste la profundidad de las explicaciones según la respuesta.`);
    const items = [
      ["FaNetworkWired", "Diseñar la ruta de red", "Justificar L4/L7, algoritmos de balanceo, timeouts, streaming y segmentación Zero Trust para tráfico de LLM."],
      ["FaHdd", "Dimensionar el almacenamiento", "Calcular el tamaño de pesos y KV cache; elegir objeto/bloque/archivo/NVMe y reducir el cold start."],
      ["FaChartLine", "Definir una política de autoscaling", "Elegir señales, umbrales y ventanas; estimar capacidad con la ley de Little."],
      ["FaMicrochip", "Planificar GPU", "Comparar device plugin, time-slicing, MIG, MPS y DRA; controlar la colocación y la fragmentación."],
    ];
    items.forEach((it, i) => card(s, { x: 0.5 + (i % 2) * 4.6, y: 1.3 + Math.floor(i / 2) * 1.95, w: 4.4, h: 1.8, title: it[1], body: it[2], ic: it[0], color: [C.accent1, C.accent3, C.accent2, C.accent6][i] }));
  }

  // 3 Agenda
  {
    const s = S("Agenda y distribución del tiempo", `[0:06 · 2 min] Distribución pedagógica del curso: 65 % teoría y análisis arquitectónico (≈ 117 min), 25 % demostraciones (≈ 45 min) y 10 % discusión y evaluación (≈ 18 min). El descanso de 10 minutos se descuenta del bloque teórico.
Muestre que la teoría va ANTES de la demo: la demo deberá confirmar o refutar lo que predijimos. Anuncie dos predicciones que verificaremos: "la profundidad de cola anticipa la degradación mejor que la CPU" y "una cola ilimitada convierte un pico en indisponibilidad".`);
    const rows = [["Bloque", "Contenido", "Min"], ["1", "Redes: balanceo, streaming, backpressure, Zero Trust", "35"], ["2", "Almacenamiento: pesos, KV cache, cold start, volúmenes", "30"], ["—", "Descanso", "10"], ["3", "Autoscaling: señales, Little, estabilidad, escala a cero", "35"], ["4", "GPU scheduling: device plugin, MIG, DRA, colocación", "25"], ["5", "Demostraciones en vivo (Ollama, cola, 429, KEDA)", "30"], ["6", "Laboratorios multicloud, discusión y cierre", "15"]];
    tbl(s, rows, { colW: [0.9, 7.2, 0.9], fs: 14, rowH: 0.43, y: 1.3 });
  }

  // 4 Caso
  {
    const s = S("Caso transversal: asistente institucional", `[0:08 · 3 min] Este caso nos acompaña todo el curso. Todos los números son SUPUESTOS académicos, no mediciones. Insista en el contraste: 5 000 usuarios potenciales no son 5 000 usuarios concurrentes; la infraestructura se dimensiona por concurrencia y por tokens por segundo.
Disponibilidad 99,9 %: calcule en voz alta: 0,1 % de 30 días × 24 h × 60 min = 43,2 minutos al mes. Eso obliga a ≥ 2 réplicas en dominios de falla distintos y a probes correctos.
Pregunta: ¿qué ocurre con el SLA si una sola réplica con GPU falla un viernes por la noche? Respuesta esperada: no hay presupuesto de error; hace falta N+1.`);
    stat(s, { x: 0.5, y: 1.35, w: 2.1, big: "5 000", label: "usuarios potenciales (supuesto)", color: C.accent4 });
    stat(s, { x: 2.8, y: 1.35, w: 2.1, big: "100", label: "usuarios concurrentes iniciales (supuesto)", color: C.accent1 });
    stat(s, { x: 5.1, y: 1.35, w: 2.1, big: "99,9 %", label: "disponibilidad objetivo ≈ 43 min/mes de indisponibilidad", color: C.accent2 });
    stat(s, { x: 7.4, y: 1.35, w: 2.1, big: "N+1", label: "redundancia mínima para tolerar la caída de una réplica", color: C.accent6 });
    tbl(s, [["Requisito", "Consecuencia de diseño en esta sesión"], ["Acceso autenticado y datos protegidos", "Red privada, egress controlado, identidad sin claves"], ["Restricción presupuestal", "Escalar por demanda real; mínimo y máximo de réplicas"], ["Trazabilidad y observabilidad", "Métricas de cola, TTFT y rechazos como SLIs"]], { y: 3.3, colW: [3.8, 5.2], fs: 13, rowH: 0.42 });
  }

  // 5 Idea central
  {
    const s = S("Idea central: capacidad finita, demanda variable", `[0:11 · 3 min] Mensaje clave de la sesión. Un servidor de inferencia es un recurso de capacidad FINITA (slots de concurrencia, memoria de GPU para el KV cache). La demanda es VARIABLE y a ráfagas. La infraestructura es el conjunto de mecanismos que reconcilian ambas cosas: red (reparte y protege), almacenamiento (hace que haya modelo listo), autoscaling (ajusta la oferta) y planificación de GPU (asigna el recurso más escaso y caro).
Pida a los estudiantes que, durante la sesión, ubiquen cada tema en el diagrama. Al final lo retomaremos para las decisiones del caso.`);
    box(s, "Demanda variable\n(usuarios, ráfagas)", { x: 0.5, y: 1.55, w: 2.4, h: 1.0, fill: C.accent4 });
    box(s, "Capacidad finita\n(slots, VRAM, tokens/s)", { x: 7.1, y: 1.55, w: 2.4, h: 1.0, fill: C.accent5 });
    arrow(s, 2.95, 2.05, 7.05, 2.05);
    const four = [["FaNetworkWired", "Red", "reparte y protege", C.accent1], ["FaHdd", "Almacenamiento", "modelo listo", C.accent3], ["FaChartLine", "Autoscaling", "ajusta la oferta", C.accent2], ["FaMicrochip", "GPU scheduling", "asigna lo escaso", C.accent6]];
    four.forEach((f, i) => {
      const x = 0.5 + i * 2.28;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 3.0, w: 2.1, h: 1.85, rectRadius: 0.08, fill: { color: C.background2 }, line: { color: C.background2, width: 0 }, objectName: "pilar" });
      iconCircle(s, f[0], x + 0.8, 3.12, f[3]);
      s.addText(f[1], { x, y: 3.7, w: 2.1, h: 0.4, fontSize: 16, bold: true, color: C.text1, align: "center", margin: 0, isTextBox: true });
      s.addText(f[2], { x, y: 4.1, w: 2.1, h: 0.6, fontSize: 14, color: C.text1, align: "center", valign: "top", margin: 0, isTextBox: true });
    });
  }

  // =========================================================================
  // BLOQUE 1: REDES
  // =========================================================================
  section("1. Redes");
  divider("01", "Redes para inferencia", "Balanceo · streaming · backpressure · segmentación Zero Trust", `[0:14 · 1 min] Abrimos el bloque de redes (35 min). Guía de preguntas del bloque: ¿por qué una solicitud a un LLM rompe los supuestos del balanceo web clásico? ¿Qué hacemos cuando la capacidad se agota? ¿Cómo evitamos que el servidor de inferencia sea una superficie de ataque?`);

  // 7 comparación
  {
    const s = S("Una solicitud LLM no es una solicitud web", `[0:15 · 3 min] Este es el cambio de modelo mental más importante del bloque. Una API web típica responde en milisegundos con costo casi uniforme por solicitud. Una generación de LLM: dura segundos o minutos, su costo depende de los tokens de salida (que no se conocen de antemano), mantiene la conexión abierta mientras transmite tokens y consume un recurso caro y escaso (memoria de GPU) durante todo ese tiempo.
Consecuencias que desarrollaremos: el balanceo por conexiones no equilibra trabajo; los timeouts por defecto cortan generaciones largas; el buffering del proxy rompe el streaming; y una sola réplica saturada no se recupera hasta terminar sus generaciones en curso.
Error frecuente: pensar que "más CPU en el balanceador" resuelve la latencia del modelo.`);
    tbl(s, [["Dimensión", "API web tradicional", "Generación con LLM"], ["Duración", "milisegundos", "segundos a minutos"], ["Costo por solicitud", "casi uniforme", "proporcional a tokens de salida (desconocido)"], ["Conexión", "corta", "larga, con streaming de tokens (SSE)"], ["Recurso limitante", "CPU / E/S", "VRAM (KV cache) y cómputo de GPU"], ["Efecto de la saturación", "latencia sube gradualmente", "cola crece; aparecen rechazos y timeouts"]], { y: 1.35, colW: [2.2, 3.0, 3.8], fs: 14, rowH: 0.55 });
    note(s, "Fuente conceptual: Kwon et al., PagedAttention (SOSP 2023); Yu et al., Orca (OSDI 2022).", 4.85);
  }

  // 8 ruta de red
  {
    const s = S("La ruta de red de una pregunta al modelo", `[0:18 · 3 min] Recorra la ruta de izquierda a derecha y señale en cada salto QUÉ puede fallar y QUÉ timeout aplica: DNS (TTL y failover), balanceador L7 (terminación TLS, WAF, idle timeout), Ingress/Gateway (enrutamiento, buffering), gateway de aplicación (autenticación, admisión), servidor de inferencia (cola interna, KV cache).
Idea fuerza: el timeout efectivo extremo a extremo es el MÍNIMO de todos los saltos. Un balanceador con timeout ocioso de 60 s (valor por defecto documentado en varios balanceadores de aplicación; verifíquelo en su proveedor) cortará una generación larga aunque todos los demás saltos permitan 5 minutos.
Pregunta: ¿dónde conviene terminar TLS y por qué? Respuesta: en el borde (L7) para inspección y WAF; mTLS interno si hay requisito de cifrado en tránsito dentro del clúster.`);
    flow(s, ["Usuario\n(navegador)", "DNS", "LB L7\nTLS · WAF", "Ingress /\nGateway API", "Gateway de\naplicación", "Servidor de\ninferencia"], { y: 1.5, h: 1.0, gap: 0.2, fills: [C.accent4, C.accent3, C.accent1, C.accent1, C.accent2, C.accent5] });
    const rows = [["Salto", "Qué controla", "Fallo típico"], ["LB L7", "TLS, WAF, límites de tasa, idle timeout", "corta generaciones largas"], ["Ingress", "enrutamiento, buffering, timeouts", "buffering rompe SSE"], ["Gateway de aplicación", "autenticación, admisión, métricas", "cola sin límite"], ["Servidor de inferencia", "batching, KV cache", "VRAM agotada → rechazos"]];
    tbl(s, rows, { y: 2.85, colW: [2.4, 3.8, 2.8], fs: 13, rowH: 0.42 });
  }

  // 9 L4 vs L7
  {
    const s = S("Balanceo L4 frente a L7", `[0:21 · 3 min] L4 (transporte) decide por IP/puerto y reparte CONEXIONES: es rápido y simple, pero ciego al contenido. L7 (aplicación) entiende HTTP: puede enrutar por ruta, cabecera o incluso por el campo "model" del cuerpo, reintentar, aplicar límites y repartir SOLICITUDES.
Punto fino: con HTTP/1.1 keep-alive o HTTP/2, muchas solicitudes comparten una conexión. Un balanceador L4 las fijará todas a la misma réplica; por eso el tráfico de LLM se balancea en L7 (por solicitud) o con un cliente que cree conexiones nuevas.
Cuándo usar L4: tráfico TCP/gRPC puro entre servicios internos donde el servidor ya se autorregula. Cuándo L7: todo lo expuesto a usuarios y todo lo que requiera inspección o políticas.`);
    card(s, { x: 0.5, y: 1.35, w: 4.4, h: 3.5, title: "L4 — transporte", ic: "FaPlug", color: C.accent4, body: "• Decide por IP y puerto\n• Reparte conexiones\n• Baja latencia, bajo costo\n• Ciego a rutas, cabeceras y cuerpo\n• Riesgo: conexiones persistentes fijan al cliente a una réplica" });
    card(s, { x: 5.1, y: 1.35, w: 4.4, h: 3.5, title: "L7 — aplicación", ic: "FaRoute", color: C.accent1, body: "• Entiende HTTP\n• Reparte solicitudes\n• TLS, WAF, límites de tasa, reintentos\n• Enruta por ruta, cabecera o modelo\n• Costo y latencia algo mayores" });
  }

  // 10 algoritmos
  {
    const s = S("Algoritmos de balanceo y su señal", `[0:24 · 3 min] Lea la tabla de arriba hacia abajo como una escalera de sofisticación. Round-robin y least-connections miden conexiones, no trabajo. EWMA usa latencia reciente: reacciona a réplicas lentas pero con retraso. El balanceo consciente del modelo usa la señal correcta: cola, uso del KV cache y coincidencia de prefijo.
Ejemplo documentado: GKE Inference Gateway enruta con métricas como uso de KV cache, utilización del acelerador y longitud de cola, y ofrece enrutamiento consciente de prefijo; se apoya en la extensión de inferencia de Gateway API, un proyecto abierto de Kubernetes SIG. Otras nubes: verifique la oferta vigente antes de afirmar equivalentes.
Pregunta de discusión: si dos réplicas reciben el mismo número de conexiones, ¿pueden estar igual de ocupadas? Respuesta: no; una puede tener generaciones de 2000 tokens y otra de 20.`);
    tbl(s, [["Algoritmo", "Reparte según", "Límite en LLM"], ["Round-robin", "turno", "ignora el costo de cada generación"], ["Least-connections", "conexiones activas", "una conexión no equivale a una unidad de trabajo"], ["EWMA / latencia", "latencia reciente", "señal con retraso"], ["Consciente del modelo", "cola, KV cache, prefijo", "requiere métricas del servidor y un endpoint picker"]], { y: 1.4, colW: [2.4, 2.6, 4.0], fs: 14, rowH: 0.6 });
    note(s, "Hecho documentado: GKE Inference Gateway + Gateway API Inference Extension (kubernetes-sigs). Ver referencias.", 4.55);
  }

  // 11 round robin visual
  {
    const s = S("Repartir conexiones no es repartir trabajo", `[0:27 · 2 min] Ilustración con dos réplicas que reciben 4 solicitudes cada una por round-robin. Las barras muestran la duración de cada generación: la réplica A recibe por mala suerte las tres largas. Aunque el reparto es "perfecto" en número, A acumula cola y B queda ociosa.
Conecte con "The Tail at Scale" (Dean y Barroso, 2013): en sistemas con muchos componentes, la latencia de cola (p99) la dominan los eventos raros pero lentos. Con LLM, esos eventos son las generaciones largas.
Pida que sugieran remedios: enrutar por cola, limitar max_tokens, separar tráfico corto y largo, reintentar con cuidado (¡los reintentos pueden amplificar la sobrecarga!).`);
    const bars = (y, label, lens, color) => {
      s.addText(label, { x: 0.5, y, w: 1.5, h: 0.5, fontSize: 14, bold: true, color: C.text1, valign: "middle", margin: 0, isTextBox: true });
      let x = 2.0;
      lens.forEach((l, i) => { s.addShape(pres.shapes.RECTANGLE, { x, y: y + 0.05, w: l * 0.62, h: 0.4, fill: { color }, line: { color: C.background1, width: 1 }, objectName: "gen" }); x += l * 0.62; });
    };
    bars(1.5, "Réplica A", [4, 3, 4, 2], C.accent5);
    bars(2.3, "Réplica B", [1, 1, 1, 1], C.accent6);
    s.addText("Unidades de tiempo de generación (ilustrativo): A recibió las generaciones largas; B termina y queda ociosa.", { x: 0.5, y: 3.0, w: 9.0, h: 0.4, fontSize: 12, italic: true, color: C.accent4, margin: 0, isTextBox: true });
    card(s, { x: 0.5, y: 3.5, w: 4.4, h: 1.5, title: "Síntoma", ic: "FaExclamationTriangle", color: C.accent5, body: "p99 alto con CPU y GPU promedio «normales»." });
    card(s, { x: 5.1, y: 3.5, w: 4.4, h: 1.5, title: "Remedio", ic: "FaBalanceScale", color: C.accent1, body: "Enrutar por cola/KV cache y limitar max_tokens." });
  }

  // 12 streaming
  {
    const s = S("Streaming (SSE), timeouts y buffering", `[0:29 · 3 min] El streaming es una decisión de experiencia de usuario: TTFT (tiempo hasta el primer token) se percibe como "respuesta inmediata" aunque la generación total dure 20 s. Pero impone requisitos de red.
Tres trampas: (1) buffering del proxy: acumula la respuesta y la entrega de golpe, el usuario ve "nada" y luego todo; se desactiva en el Ingress/proxy. (2) Timeouts de lectura/ocioso: deben exceder la generación más larga permitida (max_tokens es el control natural). (3) HTTP/1.1 permite pocas conexiones concurrentes por origen en navegadores; HTTP/2 multiplexa.
Cierre: las tres se prueban en el laboratorio 0 con un navegador y curl -N.`);
    tbl(s, [["Trampa", "Síntoma", "Control"], ["Buffering del proxy", "tokens llegan «de golpe»", "desactivar buffering para la ruta SSE"], ["Idle/read timeout bajo", "corte a mitad de respuesta", "timeout > generación máxima; limitar max_tokens"], ["Conexiones persistentes con L4", "una réplica saturada, otra libre", "balanceo L7 por solicitud"], ["Reintentos automáticos", "amplifican la sobrecarga", "reintentar solo con backoff y presupuesto de reintentos"]], { y: 1.4, colW: [2.7, 3.0, 3.3], fs: 14, rowH: 0.7 });
  }

  // 13 consciente del modelo
  {
    const s = S("Balanceo consciente del modelo", `[0:32 · 3 min] Qué añade un balanceador consciente del modelo: (1) observa la cola y el KV cache de cada réplica; (2) puede mandar solicitudes con prefijo común (mismo prompt de sistema o misma conversación) a la réplica que ya tiene ese prefijo en caché, ahorrando prefill; (3) puede priorizar tráfico (interactivo sobre lotes) y enrutar por nombre de modelo.
Hecho documentado: GKE Inference Gateway implementa esto sobre Gateway API con recursos InferencePool e InferenceObjective y se integra con Model Armor para filtrado de seguridad. En esta sesión NO lo desplegamos: nuestro laboratorio usa Ingress L7 con EWMA más control de admisión en cada réplica, y el balanceo consciente del modelo se presenta como evolución natural.
Advertencia de vigencia: el proyecto de extensión de inferencia evoluciona rápido; confirme versión y estado en su documentación.`);
    flow(s, ["Cliente", "Gateway\n(proxy L7)", "Endpoint picker\n(cola · KV cache · prefijo)", "Réplica\nseleccionada"], { y: 1.5, h: 1.1, gap: 0.35, fills: [C.accent4, C.accent1, C.accent2, C.accent5] });
    card(s, { x: 0.5, y: 3.0, w: 2.9, h: 1.9, title: "Cola y KV cache", ic: "FaLayerGroup", color: C.accent1, body: "Elige la réplica con más capacidad real." });
    card(s, { x: 3.55, y: 3.0, w: 2.9, h: 1.9, title: "Prefijo en caché", ic: "FaMemory", color: C.accent3, body: "Reutiliza prefill de prompts comunes." });
    card(s, { x: 6.6, y: 3.0, w: 2.9, h: 1.9, title: "Prioridad", ic: "FaTasks", color: C.accent6, body: "Interactivo antes que lotes." });
  }

  // 14 backpressure
  {
    const s = S("Backpressure y load shedding", `[0:35 · 4 min] Idea central del bloque. Si se acepta tráfico sin límite, la cola crece sin cota y la latencia también: el sistema "acepta" todo y no sirve a nadie a tiempo. Diseño correcto: cola ACOTADA + timeout en cola + rechazo explícito (429 si la cola está llena, 503 si el tiempo de espera expiró) con Retry-After. Es degradar a propósito, para proteger a la mayoría.
Conexión con seguridad: OWASP LLM10:2025 (Unbounded Consumption) incluye el consumo ilimitado de recursos como riesgo; el control de admisión es una mitigación directa, junto con límites de max_tokens y cuotas por usuario.
Conexión con autoscaling: la profundidad de cola es la señal que usaremos para escalar. Demo posterior: lanzaremos una ráfaga y veremos 200, 429 y 503.
Pregunta: ¿por qué NO contamos los 429 como indisponibilidad en el SLI? Respuesta: son rechazo intencional por capacidad; pero un 429 sostenido es una alerta de capacidad.`);
    flow(s, ["Solicitud", "¿Hay slot\nlibre?", "Cola acotada\n(max_queue)", "Slot de\ninferencia"], { y: 1.45, h: 1.0, gap: 0.4, fills: [C.accent4, C.accent3, C.accent2, C.accent1] });
    box(s, "429 · cola llena", { x: 4.55, y: 3.0, w: 2.2, h: 0.7, fill: C.accent5 });
    box(s, "503 · timeout en cola", { x: 6.95, y: 3.0, w: 2.55, h: 0.7, fill: C.accent5 });
    arrow(s, 5.65, 2.5, 5.65, 2.95, C.accent5); arrow(s, 7.7, 2.5, 7.9, 2.95, C.accent5);
    bullets(s, ["La cola acotada protege la latencia de las solicitudes aceptadas", "Retry-After orienta el reintento del cliente y evita tormentas de reintentos", "Métricas: queue_depth, rejected_total, queue_wait"], { x: 0.5, y: 3.0, w: 3.9, h: 2.0, fs: 14 });
  }

  // 15 Zero Trust red
  {
    const s = S("Segmentación y Zero Trust de red", `[0:39 · 4 min] Zero Trust = nunca confiar por ubicación de red; verificar identidad y autorización en cada salto. En Kubernetes, el primer paso práctico es NetworkPolicy en modo "denegar por defecto" y abrir solo lo necesario: Ingress controller hacia el gateway, Prometheus hacia /metrics, DNS y el egress mínimo. Requiere un CNI que implemente NetworkPolicy.
Capa extra que usamos en el repositorio: el servidor de inferencia escucha solo en 127.0.0.1 dentro del Pod; no existe ruta de red hacia él desde fuera, por lo que no necesita autenticación propia (Ollama no la tiene).
Otras capas: TLS en el borde; mTLS interno si hay malla; endpoints privados hacia servicios cloud; WAF y límites de tasa en el borde.
Error frecuente: publicar el puerto del servidor de inferencia "solo para probar" y dejarlo expuesto.`);
    const layers = [["Borde", "TLS · WAF · límites de tasa · autenticación", C.accent3], ["Clúster", "NetworkPolicy deny-by-default · Pod Security", C.accent1], ["Pod", "Servidor de inferencia en loopback · sin root", C.accent2], ["Datos", "Cifrado · endpoints privados · identidad sin claves", C.accent6]];
    layers.forEach((l, i) => {
      const w = 9.0 - i * 1.2;
      s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.5 + i * 0.6, y: 1.4 + i * 0.85, w, h: 0.75, rectRadius: 0.06, fill: { color: l[2] }, line: { color: l[2], width: 0 }, objectName: "capa" });
      s.addText([{ text: l[0] + ":  ", options: { bold: true } }, { text: l[1] }], { x: 0.5 + i * 0.6, y: 1.4 + i * 0.85, w, h: 0.75, fontSize: 14, color: C.background1, align: "center", valign: "middle", margin: 0.05, isTextBox: true });
    });
    note(s, "Requiere un CNI con soporte de NetworkPolicy (Calico, Cilium, Azure CNI + NPM/Cilium, GKE Dataplane V2…).", 4.85);
  }

  // 16 Egress
  {
    const s = S("Egress, endpoints privados y SSRF", `[0:43 · 3 min] La salida (egress) suele olvidarse. Riesgos: (1) exfiltración de datos desde un componente comprometido; (2) descarga de modelos o paquetes de fuentes no controladas (cadena de suministro); (3) SSRF contra el endpoint de metadatos de la nube (169.254.169.254) para robar credenciales de la identidad del nodo.
Controles: denegar egress por defecto; excepciones mínimas; bloquear el rango de metadatos para Pods de aplicación; endpoints privados (Private Endpoint en Azure, PrivateLink en AWS, Private Service Connect en GCP) para acceder a almacenamiento y APIs de modelos sin salir a Internet.
Honestidad técnica: NetworkPolicy NO filtra por nombre de dominio. En nuestro manifiesto el initContainer necesita HTTPS para descargar el modelo la primera vez: es una DEUDA explícita (ADR-004) y en producción se reemplaza por almacenamiento de objetos privado o un proxy con lista de FQDN permitidos.`);
    tbl(s, [["Amenaza", "Vector", "Control"], ["Exfiltración", "egress abierto", "deny-by-default + allowlist"], ["Robo de credenciales", "SSRF a 169.254.169.254", "bloquear rango de metadatos; identidad de carga de trabajo"], ["Cadena de suministro", "modelo/paquete no verificado", "fuente privada + checksum + versión fija"], ["Fuga por la API pública", "tráfico a Internet", "Private Endpoint / PrivateLink / PSC"]], { y: 1.4, colW: [2.2, 2.9, 3.9], fs: 14, rowH: 0.65 });
  }

  // =========================================================================
  // BLOQUE 2: ALMACENAMIENTO
  // =========================================================================
  section("2. Almacenamiento");
  divider("02", "Almacenamiento para inferencia", "Pesos · KV cache · cold start · volúmenes · gobierno de modelos", `[0:46 · 1 min] Bloque de almacenamiento (30 min). Pregunta guía: un modelo no sirve hasta que sus pesos están en la memoria de la GPU. ¿Cuánto tarda llegar ahí y qué decisiones de almacenamiento lo aceleran o lo retrasan? Esa respuesta determina qué tan rápido puede escalar el sistema.`);

  // 18 pesos
  {
    const s = S("El tamaño de los pesos es aritmética", `[0:47 · 3 min] Fórmula: bytes ≈ parámetros × bytes por parámetro. FP16 usa 2 bytes; INT8, 1; INT4, aproximadamente 0,5 (más metadatos de cuantización). Para un modelo de 8 mil millones de parámetros: 16 GB, 8 GB y ≈ 4 GB. Esto solo cuenta pesos.
Mensaje: la cuantización reduce almacenamiento, tiempo de descarga y VRAM de pesos, a costa de posible pérdida de calidad que debe evaluarse con tareas reales del caso.
Ejercicio rápido (1 min): ¿cabe un modelo de 70 mil millones en FP16 en una GPU de 80 GB? Solo los pesos son 140 GB: no; requeriría varias GPU (paralelismo) o cuantización agresiva, y aún faltaría el KV cache.
Aviso: las cifras son cálculo, no medición. No incluyen KV cache ni activaciones.`);
    formula(s, "bytes de pesos ≈ parámetros × bytes por parámetro", { y: 1.35, h: 0.7, fs: 20 });
    s.addChart(pres.charts.BAR, [{ name: "GB de pesos (8 000 M parámetros)", labels: ["FP16", "INT8", "INT4 (≈)"], values: [16, 8, 4] }], {
      x: 0.5, y: 2.2, w: 4.6, h: 2.7, barDir: "col", chartColors: [HEX.accent1], showTitle: true, title: "Modelo de 8 000 M de parámetros (solo pesos, GB)", titleFontSize: 12, titleColor: HEX.dk1, titleFontFace: "+mn-lt",
      showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 12, dataLabelColor: HEX.dk1, dataLabelFontFace: "+mn-lt", catAxisLabelColor: HEX.dk1, valAxisLabelColor: HEX.dk1, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", catAxisLabelFontSize: 12, valAxisLabelFontSize: 12,
      valGridLine: { color: HEX.lt2, size: 0.5 }, catGridLine: { style: "none" }, showLegend: false, valAxisMaxVal: 20, valAxisMinVal: 0 });
    tbl(s, [["Parámetros", "FP16", "INT8", "INT4 (≈)"], ["1 000 M", "2 GB", "1 GB", "0,5 GB"], ["8 000 M", "16 GB", "8 GB", "4 GB"], ["70 000 M", "140 GB", "70 GB", "35 GB"]], { x: 5.3, y: 2.35, w: 4.2, colW: [1.35, 0.95, 0.95, 0.95], fs: 12, rowH: 0.5 });
    note(s, "Cálculo teórico solo de pesos; sin KV cache ni activaciones.", 5.0);
  }

  // 19 KV cache
  {
    const s = S("La memoria total: pesos + KV cache + activaciones", `[0:50 · 3 min] En la fase de decodificación, el modelo reutiliza las claves y valores (K y V) de todos los tokens previos para no recalcularlos: eso es el KV cache. Crece LINEALMENTE con la longitud del contexto y con el número de secuencias concurrentes.
Fórmula (por secuencia): 2 (K y V) × capas × cabezas KV × dimensión de cabeza × bytes por elemento × tokens. No se espera que memoricen cifras; sí que entiendan que contexto largo × alta concurrencia consume VRAM rápidamente y que la cantidad de secuencias concurrentes que una GPU sostiene depende de la VRAM libre tras cargar los pesos.
Conexión con la sesión: esto fija el techo de max_concurrency de cada réplica y por tanto de la capacidad; PagedAttention (Kwon et al., SOSP 2023) gestiona el KV cache en bloques para reducir fragmentación y aumentar el número de secuencias servibles.`);
    formula(s, "KV cache ≈ 2 × capas × cabezas KV × dim. cabeza × bytes × tokens", { y: 1.35, h: 0.75, fs: 18 });
    const parts = [["Pesos", "constantes por réplica; se cargan una vez", C.accent3], ["KV cache", "crece con contexto × concurrencia", C.accent2], ["Activaciones", "temporales durante el cómputo", C.accent4]];
    parts.forEach((p, i) => card(s, { x: 0.5 + i * 3.05, y: 2.4, w: 2.9, h: 1.55, title: p[0], body: p[1], color: p[2], ic: ["FaCubes", "FaMemory", "FaBolt"][i] }));
    note(s, "VRAM disponible para KV cache = VRAM total − pesos − activaciones − margen. Ese valor limita la concurrencia por réplica.", 4.2);
    note(s, "Fuente: Kwon et al., «Efficient Memory Management for LLM Serving with PagedAttention», SOSP 2023.", 4.65);
  }

  // 20 tipos de almacenamiento
  {
    const s = S("Tipos de almacenamiento y su rol", `[0:53 · 4 min] Cada tipo resuelve una parte. Objetos (S3, Blob Storage, Cloud Storage): fuente de verdad versionada, durable y barata, pero su descarga contribuye al cold start. Bloque (EBS, Managed Disks, Persistent Disk): volumen por réplica, baja latencia, atado a una zona y normalmente a un Pod a la vez (ReadWriteOnce). Archivos compartidos (EFS, Azure Files, Filestore): una copia para N réplicas (ReadWriteMany) con costo y rendimiento variables. NVMe local o efímero: la caché más rápida, pero se pierde con el nodo.
Criterio de decisión: ¿cuántas réplicas hay y con qué frecuencia escalan? Pocas y estables → bloque por réplica. Muchas y elásticas → caché compartida o NVMe local poblado desde objetos.
Pregunta: ¿por qué no poner los pesos en la imagen del contenedor? Respuesta: imágenes de decenas de GB, registro lento, rebuild por cada cambio de modelo y duplicación en cada nodo.`);
    tbl(s, [["Tipo", "Rol", "Ventaja", "Riesgo"], ["Objetos", "fuente de verdad versionada", "durable, barato, políticas", "descarga lenta → cold start"], ["Bloque (RWO)", "volumen por réplica", "baja latencia", "atado a zona y a un Pod"], ["Archivos (RWX)", "caché compartida", "una copia para N réplicas", "rendimiento variable, costo"], ["NVMe local", "caché rápida", "máxima velocidad", "se pierde con el nodo"]], { y: 1.4, colW: [1.7, 2.5, 2.4, 2.4], fs: 13, rowH: 0.62 });
  }

  // 21 cold start
  {
    const s = S("Anatomía del cold start de una réplica", `[0:57 · 4 min] El tiempo que tarda una réplica nueva en estar lista define cuánta demanda puede absorber el autoscaling a tiempo. Descomponga: T_listo = T_nodo + T_imagen + T_descarga_pesos + T_carga_VRAM + T_calentamiento. Si el nodo ya existe se elimina el primer término; si la imagen ya está en caché, el segundo.
Dato honesto: NO damos cifras en esta diapositiva porque dependen de proveedor, tipo de nodo, tamaño del modelo y red; los estudiantes medirán las suyas en el laboratorio (tiempo desde "Pending" hasta "Ready" con kubectl).
Consecuencia de diseño: el cold start fija el mínimo de réplicas calientes y el colchón de capacidad (headroom) necesario para absorber picos mientras se escala.
Pregunta: si T_listo es de varios minutos y los picos duran 30 segundos, ¿sirve el autoscaling reactivo? Respuesta: no para ese pico; hace falta capacidad precalentada, cola acotada o escalado programado.`);
    formula(s, "T_listo = T_nodo + T_imagen + T_pesos + T_VRAM + T_warm-up", { y: 1.35, h: 0.7, fs: 20 });
    flow(s, ["Nodo GPU\ndisponible", "Descarga de\nimagen", "Pesos desde\nobjetos/volumen", "Carga a\nVRAM", "Warm-up\n(1ª inferencia)", "Ready"], { y: 2.5, h: 1.0, gap: 0.2, fills: [C.accent4, C.accent3, C.accent2, C.accent5, C.accent1, C.accent6] });
    note(s, "Sin cifras: dependen del proveedor, el nodo, el modelo y la red. Mídalas en su laboratorio (Pending → Ready).", 3.8);
    bullets(s, ["Cold start largo ⇒ más réplicas mínimas y más margen", "Cada término tiene su palanca (ver siguiente diapositiva)"], { x: 0.5, y: 4.2, w: 9.0, h: 0.8, fs: 14 });
  }

  // 22 palancas
  {
    const s = S("Palancas para reducir el cold start", `[1:01 · 3 min] Una palanca por término de la fórmula. Nodo: sobreaprovisionamiento con Pods de baja prioridad ("pause") que se desalojan al llegar carga real, o pools con nodos calientes. Imagen: imágenes pequeñas, registro cercano, caché de imágenes en el nodo. Pesos: volúmenes ya poblados, caché local NVMe, descarga paralela, formatos que permiten carga rápida. VRAM y warm-up: mantener el modelo cargado (OLLAMA_KEEP_ALIVE alto) y precalentar con una solicitud sintética antes de marcar Ready (la readiness probe verifica que el modelo exista; un warm-up explícito es una mejora).
Compromiso: cada palanca cuesta dinero (capacidad ociosa) o complejidad. FinOps entra aquí: el costo de la capacidad caliente se compara con el costo de incumplir el SLO.`);
    const pal = [["FaServer", "Nodo", "Sobreaprovisionar con Pods «pause» desalojables", C.accent4], ["FaBoxOpen", "Imagen", "Pequeña, sin pesos, registro cercano", C.accent3], ["FaDatabase", "Pesos", "Volumen poblado o caché NVMe", C.accent2], ["FaFire", "VRAM y warm-up", "KV-alive alto y solicitud de calentamiento", C.accent5]];
    pal.forEach((p, i) => card(s, { x: 0.5 + (i % 2) * 4.6, y: 1.35 + Math.floor(i / 2) * 1.8, w: 4.4, h: 1.65, title: p[1], body: p[2], ic: p[0], color: p[3] }));
    note(s, "Todo precalentamiento cuesta capacidad ociosa: compárelo con el costo de incumplir el SLO.", 4.95);
  }

  // 23 volúmenes K8s
  {
    const s = S("Volúmenes en Kubernetes: PV, PVC y StorageClass", `[1:04 · 4 min] Modelo mental: el desarrollador pide almacenamiento con un PersistentVolumeClaim (PVC); la StorageClass define cómo se aprovisiona dinámicamente un PersistentVolume (PV) con el driver CSI del proveedor (Azure Disk/Files, EBS/EFS, Persistent Disk/Filestore). Modos de acceso: ReadWriteOnce (un nodo), ReadWriteMany (varios), ReadOnlyMany.
Por qué StatefulSet y no Deployment (ADR-003): un Deployment con réplicas comparte la misma plantilla; si el PVC es RWO, las réplicas en otros nodos no pueden montarlo. StatefulSet con volumeClaimTemplates crea un PVC propio por réplica y mantiene identidad estable. Alternativa: RWX compartido (una copia de los pesos) con los riesgos de rendimiento.
Detalle operativo: los PVC de un StatefulSet NO se borran al reducir réplicas por defecto; al escalar de nuevo, la réplica recupera su volumen (y su modelo) sin descargar otra vez: ventaja para el cold start; costo: almacenamiento persistente cobrado aunque la réplica no exista (FinOps).
Zonas: un volumen de bloque vive en una zona; el Pod debe programarse en esa zona (topología). Tenerlo presente al diseñar alta disponibilidad multizona.`);
    flow(s, ["Pod /\nStatefulSet", "PVC\n(solicitud)", "StorageClass\n(política)", "PV\n(disco real)"], { y: 1.45, h: 1.0, gap: 0.4, fills: [C.accent1, C.accent3, C.accent2, C.accent6] });
    tbl(s, [["Modo", "Significado", "Uso en inferencia"], ["ReadWriteOnce", "un nodo a la vez", "un volumen por réplica (StatefulSet)"], ["ReadWriteMany", "varios nodos", "caché compartida de pesos"], ["ReadOnlyMany", "varios, solo lectura", "pesos inmutables y versionados"]], { y: 2.9, colW: [2.2, 2.6, 4.2], fs: 14, rowH: 0.5 });
    note(s, "Los volúmenes de bloque son zonales: alta disponibilidad multizona exige réplicas con su propio volumen en cada zona.", 4.95);
  }

  // 24 gobierno
  {
    const s = S("Gobierno de modelos: versión, integridad, cifrado", `[1:08 · 3 min] Los pesos son un artefacto de software crítico y, a la vez, datos con propiedad intelectual y licencias. Prácticas: (1) versionado inmutable y registro de qué versión sirve cada réplica (trazabilidad exigida en el caso); (2) verificación de integridad con checksum o firma antes de cargar: un modelo alterado es un vector de ataque a la cadena de suministro; (3) cifrado en reposo con claves gestionadas por el cliente si el requisito normativo lo pide; (4) control de acceso mínimo a los repositorios de modelos; (5) revisión de licencia (uso comercial, restricciones).
Marcos aplicables: NIST AI RMF 1.0 y su Perfil de IA Generativa (NIST AI 600-1) tratan la procedencia y la integridad de componentes; ISO/IEC 42001:2023 exige gobierno del sistema de gestión de IA.
Pregunta: ¿qué pasa si dos réplicas sirven versiones distintas del modelo durante un despliegue? Respuesta: respuestas inconsistentes; usar despliegues graduales con versión explícita y métricas por versión.`);
    const g = [["FaCodeBranch", "Versionado", "inmutable y trazable por réplica", C.accent1], ["FaCheckCircle", "Integridad", "checksum o firma antes de cargar", C.accent6], ["FaLock", "Cifrado", "en reposo y en tránsito; claves del cliente si aplica", C.accent3], ["FaKey", "Acceso", "mínimo privilegio sobre repositorios de modelos", C.accent2]];
    g.forEach((p, i) => card(s, { x: 0.5 + (i % 2) * 4.6, y: 1.35 + Math.floor(i / 2) * 1.8, w: 4.4, h: 1.65, title: p[1], body: p[2], ic: p[0], color: p[3] }));
    note(s, "Marcos: NIST AI RMF 1.0 y AI 600-1 (Perfil IA Generativa); ISO/IEC 42001:2023.", 4.95);
  }

  // 25 descanso
  {
    const s = pres.addSlide({ masterName: "DARK", sectionTitle: sectionOpen });
    s.addText("Descanso · 10 minutos", { placeholder: "title" });
    s.addText("Al volver: autoscaling. Piense en qué señal escalaría usted y por qué.", { placeholder: "body" });
    s.addNotes(`[1:11 · 10 min] Descanso. Pregunta para pensar durante el descanso: si su servicio de LLM está lento, ¿qué métrica miraría primero: CPU, GPU, latencia, cola? Recoja respuestas al volver; las contrastaremos con la evidencia.
Aproveche para verificar que los estudiantes tengan listos Docker y el repositorio clonado para las demostraciones.`);
  }

  // =========================================================================
  // BLOQUE 3: AUTOSCALING
  // =========================================================================
  section("3. Autoscaling");
  divider("03", "Autoscaling de inferencia", "Señales · ley de Little · estabilidad · escala a cero", `[1:21 · 1 min] Bloque de autoscaling (35 min). Retome las respuestas de la pregunta del descanso. Anuncie la predicción a verificar: "la profundidad de cola anticipa la degradación mejor que la CPU".`);

  // 27 hockey stick
  {
    const s = S("Utilización y latencia: la curva de palo de hockey", `[1:22 · 4 min] Modelo teórico clásico de colas M/M/1: el tiempo en el sistema relativo al tiempo de servicio es 1/(1−ρ), con ρ la utilización. A 50 % la espera es el doble del servicio; a 90 %, diez veces; a 95 %, veinte. No es lineal: pequeñas subidas de carga cerca de saturación producen grandes degradaciones.
Advertencia: es un modelo idealizado (llegadas Poisson, servicio exponencial, un servidor); la inferencia con batching continuo se comporta distinto en detalle, pero la forma cualitativa se mantiene y es la razón de operar con margen (headroom) en lugar de a 100 %.
Mensaje de diseño: no se dimensiona para utilización 100 %; se escoge una utilización objetivo (p. ej. 60–70 %, valor a validar con pruebas de carga) y se escala antes de llegar al codo de la curva. Y cuando se supera la capacidad, la cola acotada rechaza en lugar de crecer sin fin.`);
    s.addChart(pres.charts.LINE, [{ name: "Tiempo en sistema relativo", labels: ["10 %", "30 %", "50 %", "70 %", "80 %", "90 %", "95 %"], values: [1.11, 1.43, 2.0, 3.33, 5.0, 10.0, 20.0] }], {
      x: 0.5, y: 1.3, w: 5.6, h: 3.6, chartColors: [HEX.accent2], lineSize: 3, lineDataSymbolSize: 8, showTitle: true, title: "Tiempo en el sistema ÷ tiempo de servicio = 1/(1−ρ)", titleFontSize: 12, titleColor: HEX.dk1, titleFontFace: "+mn-lt",
      showValue: true, dataLabelPosition: "t", dataLabelFontSize: 12, dataLabelColor: HEX.dk1, dataLabelFontFace: "+mn-lt", catAxisLabelColor: HEX.dk1, valAxisLabelColor: HEX.dk1, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", catAxisLabelFontSize: 12, valAxisLabelFontSize: 12,
      showCatAxisTitle: true, catAxisTitle: "Utilización ρ", catAxisTitleFontSize: 12, catAxisTitleColor: HEX.dk1, catAxisTitleFontFace: "+mn-lt", valGridLine: { color: HEX.lt2, size: 0.5 }, catGridLine: { style: "none" }, showLegend: false, valAxisMinVal: 0 });
    card(s, { x: 6.3, y: 1.3, w: 3.2, h: 1.75, title: "Lección", ic: "FaFire", color: C.accent2, body: "Cerca del 100 % la espera se dispara." });
    card(s, { x: 6.3, y: 3.2, w: 3.2, h: 1.7, title: "Diseño", ic: "FaBalanceScale", color: C.accent1, body: "Utilización objetivo + margen + cola acotada." });
  }

  // 28 Little
  {
    const s = S("Ley de Little: cuántas solicitudes hay en el sistema", `[1:26 · 4 min] L = λ · W. Es una identidad general de sistemas estables (J. D. C. Little, 1961) que no exige supuestos sobre las distribuciones. L: número promedio de solicitudes en el sistema; λ: tasa de llegada; W: tiempo medio en el sistema.
Ejemplo SUPUESTO del caso: si 100 usuarios generan solicitudes de forma continua y cada generación dura 20 s, entonces λ = 100/20 = 5 solicitudes/s y L = λ·W = 100 (coherente: cada usuario tiene una generación en curso). Si cada réplica sostiene c = 2 generaciones concurrentes con utilización objetivo 70 %, la capacidad efectiva por réplica es 1,4 y harían falta ≈ 72 réplicas. Cuidado: ese resultado asume que cada usuario mantiene una generación activa permanentemente, lo cual es un caso extremo irreal; con tiempo de lectura/pausa del usuario (think time) la concurrencia real de generaciones es una fracción de los usuarios concurrentes.
Trabaje con los estudiantes el efecto del think time: si el usuario lee 40 s por cada 20 s de generación, solo 1/3 de los usuarios concurrentes están generando a la vez → L ≈ 33. De ahí que la concurrencia de GENERACIÓN, no de usuarios, dimensione la flota. Pida que lo calculen con sus supuestos en la actividad.`);
    formula(s, "L = λ · W", { y: 1.35, h: 0.75, fs: 28 });
    tbl(s, [["Símbolo", "Significado", "Ejemplo supuesto (caso)"], ["λ", "tasa de llegada (solicitudes/s)", "5 /s si cada usuario encadena solicitudes sin pausa"], ["W", "tiempo en el sistema (s)", "20 s por generación"], ["L", "solicitudes en el sistema", "L = 5 × 20 = 100 generaciones simultáneas (caso extremo)"], ["think time", "pausa del usuario", "con 40 s de lectura → ≈ 33 generaciones simultáneas"]], { y: 2.3, colW: [1.4, 3.0, 4.6], fs: 13, rowH: 0.5 });
    note(s, "Todos los valores son supuestos académicos; la concurrencia que dimensiona la flota es la de GENERACIÓN, no la de usuarios.", 4.95);
  }

  // 29 señales
  {
    const s = S("Señales de autoscaling: de peor a mejor", `[1:30 · 4 min] Esta es la diapositiva que responde a la pregunta del descanso. CPU: en inferencia sobre CPU se satura con una sola solicitud; en GPU casi no refleja la saturación. Utilización de GPU: aparece alta aunque la carga se sirva bien (la GPU "ocupada" es lo deseable) y no distingue saturación de eficiencia. Profundidad de cola: mide demanda INSATISFECHA directamente; es la señal que usaremos. KV cache y TTFT/latencia: presión de memoria y síntoma percibido; útiles como guardrail pero llegan tarde (el usuario ya lo nota).
Hecho documentado: la guía de Amazon EKS para escalar inferencia de IA con HPA y KEDA usa profundidad de cola y latencia p95 end-to-end como disparadores. Otras guías técnicas recomiendan la cola de solicitudes del servidor (p. ej. requests en espera de vLLM) sobre CPU.
Dato a verificar en la demo: abrir /metrics durante la ráfaga y comparar queue_depth con CPU en htop.`);
    tbl(s, [["Señal", "Qué mide", "Veredicto para LLM"], ["CPU / memoria", "uso del nodo", "engañosa: satura de inmediato o no refleja la cola"], ["Utilización de GPU", "ocupación del acelerador", "alta incluso con carga sana; no distingue saturación"], ["Profundidad de cola", "demanda insatisfecha", "señal principal: anticipa la degradación"], ["KV cache / TTFT", "presión de memoria y síntoma", "guardrail: llega cuando el usuario ya sufre"]], { y: 1.4, colW: [2.3, 2.6, 4.1], fs: 14, rowH: 0.62 });
    note(s, "Hecho documentado: Amazon EKS — «Autoscale AI inference with HPA and KEDA» usa cola y p95 e2e como disparadores.", 4.95);
  }

  // 30 H V C
  {
    const s = S("Escalamiento horizontal, vertical y de clúster", `[1:34 · 3 min] Horizontal (HPA/KEDA): cambia el número de réplicas; es el mecanismo principal. Límites: cold start y cuota de GPU. Vertical (VPA o ajuste de requests/limits): cambia CPU y memoria por Pod; en inferencia sirve para dimensionar el gateway o el CPU/RAM del servidor, pero NO cambia la VRAM de una GPU física, y normalmente requiere reiniciar el Pod; no combine VPA y HPA sobre la misma métrica de recursos. De clúster/nodos (Cluster Autoscaler, Karpenter, aprovisionamiento automático de nodos): agrega o quita nodos; añade minutos al camino crítico y exige cuota de GPU en la región.
Error frecuente: creer que "escalar verticalmente" una GPU es posible en caliente. Para más VRAM por réplica se cambia a un tipo de nodo/GPU mayor (nueva réplica) o se usan varias GPU con paralelismo.`);
    card(s, { x: 0.5, y: 1.35, w: 2.9, h: 3.55, title: "Horizontal", ic: "FaLayerGroup", color: C.accent1, body: "HPA / KEDA\nCambia el número de réplicas\nPrincipal mecanismo\nLímites: cold start y cuota de GPU" });
    card(s, { x: 3.55, y: 1.35, w: 2.9, h: 3.55, title: "Vertical", ic: "FaTachometerAlt", color: C.accent3, body: "VPA / ajuste de requests\nCambia CPU y RAM por Pod\nNo cambia la VRAM de una GPU\nSuele reiniciar el Pod" });
    card(s, { x: 6.6, y: 1.35, w: 2.9, h: 3.55, title: "De clúster", ic: "FaServer", color: C.accent2, body: "Cluster Autoscaler / Karpenter\nAgrega nodos GPU\nAñade minutos al camino crítico\nExige cuota" });
  }

  // 31 cadena de latencia de escalado
  {
    const s = S("La cadena de latencia del escalado", `[1:37 · 3 min] Cada eslabón suma retraso entre "la demanda sube" y "hay capacidad": (1) intervalo de raspado de la métrica; (2) cálculo y decisión (el HPA sincroniza en un intervalo periódico configurable); (3) programación del Pod y, si no hay nodo, aprovisionamiento del nodo; (4) descarga de imagen; (5) carga de pesos; (6) warm-up y readiness.
Idea fuerza: el escalado reactivo siempre llega tarde a un pico más corto que esta cadena. Por eso se combinan: cola acotada (protege durante el retraso), margen de capacidad, mínimos de réplicas y, si el patrón es predecible (horario de clases), escalado programado (disparador cron en KEDA).
Actividad: pida que estimen, para su proveedor, cada eslabón; la suma es su "tiempo hasta capacidad".`);
    flow(s, ["Métrica\n(raspado)", "Decisión\n(HPA/KEDA)", "Pod\npendiente", "Nodo\n(si falta)", "Imagen y\npesos", "Ready"], { y: 1.6, h: 1.0, gap: 0.2, fills: [C.accent4, C.accent3, C.accent2, C.accent5, C.accent6, C.accent1] });
    s.addText("segundos → minutos", { x: 0.5, y: 2.75, w: 9.0, h: 0.4, fontSize: 14, italic: true, color: C.accent4, align: "center", margin: 0, isTextBox: true });
    bullets(s, ["Mientras escala: la cola acotada y el margen sostienen el servicio", "Picos predecibles (horario de clases): escalado programado", "Nunca confiar solo en el reactivo para picos más cortos que la cadena"], { y: 3.3, h: 1.6, fs: 15 });
  }

  // 32 estabilidad
  {
    const s = S("Estabilidad: evitar el flapping", `[1:40 · 3 min] Flapping = oscilar entre subir y bajar réplicas. En LLM es especialmente costoso porque cada subida paga un cold start y cada bajada descarta capacidad caliente. Técnicas: ventana de estabilización larga al bajar (en nuestro manifiesto: 300 s), políticas asimétricas (subir rápido, bajar despacio), umbral de activación (activationThreshold) para no reaccionar al ruido, histéresis (umbral de bajada menor que el de subida) y cooldown.
Ejemplo de política del repositorio (k8s/50-keda-scaledobject.yaml): subir hasta 2 Pods por minuto sin ventana; bajar 1 Pod cada 2 minutos tras 5 minutos de estabilidad; mínimo 1 y máximo 4. Los umbrales son SUPUESTOS iniciales: se calibran con la prueba de carga.
Pregunta: ¿por qué un máximo de réplicas? Respuesta: cuota de GPU y presupuesto; sin tope, un bug o un ataque de consumo ilimitado escala el costo sin límite.`);
    tbl(s, [["Técnica", "Efecto", "Parámetro del repositorio"], ["Subida rápida", "responde antes a la demanda", "+2 Pods / 60 s, sin ventana"], ["Bajada lenta", "conserva capacidad caliente", "−1 Pod / 120 s, ventana 300 s"], ["Umbral de activación", "ignora ruido", "activationThreshold = 1"], ["Mínimo y máximo", "SLO y presupuesto", "min 1 · max 4"]], { y: 1.4, colW: [2.4, 3.2, 3.4], fs: 14, rowH: 0.65 });
    note(s, "Los umbrales son supuestos iniciales: se calibran con la prueba de carga (loadtest.py).", 4.75);
  }

  // 33 escala a cero
  {
    const s = S("Escalar a cero: ahorro frente a latencia", `[1:43 · 2 min] Escalar a cero réplicas elimina el costo ocioso, ideal para cargas esporádicas, por lotes o de bajo uso. Pero la primera solicitud paga el cold start completo (nodo, imagen, pesos, VRAM): minutos en inferencia con GPU. Para un asistente interactivo de universidad, eso es inaceptable en horario de clases.
Recomendación del caso: minReplicaCount = 1 en horario hábil; evaluar escala a cero fuera de horario con escalado programado. Para evaluación por lotes del modelo: escala a cero con colas y nodos spot/preemptibles.
Pregunta: ¿qué cargas del caso universitario toleran escala a cero? Respuesta esperada: generación de embeddings por lotes, evaluaciones nocturnas; no el chat interactivo.`);
    card(s, { x: 0.5, y: 1.35, w: 4.4, h: 3.5, title: "Ventajas", ic: "FaSnowflake", color: C.accent3, body: "• Sin costo en reposo\n• Ideal para lotes y evaluaciones\n• Combina bien con nodos spot" });
    card(s, { x: 5.1, y: 1.35, w: 4.4, h: 3.5, title: "Costos", ic: "FaClock", color: C.accent5, body: "• Primera solicitud paga el cold start completo\n• Inaceptable para chat interactivo\n• Requiere cola o respuesta asíncrona" });
  }

  // 34 autoscaling nubes
  {
    const s = S("Autoscaling en las tres nubes: dos rutas", `[1:45 · 3 min] Ruta A, Kubernetes administrado (AKS, EKS, GKE): mecanismos de código abierto (HPA, KEDA, Cluster Autoscaler/Karpenter) con control total y portabilidad; usted opera más. Ruta B, plataformas serverless de contenedores o de modelos (Azure Container Apps, Cloud Run, ECS/Fargate, o los endpoints administrados de Foundry/Vertex AI/Bedrock): el proveedor escala por usted con menos control sobre señales y GPU.
Criterio de decisión: control y portabilidad frente a esfuerzo operativo. Para inferencia con modelos propios y GPU, la ruta A suele dar más control; para consumir modelos de proveedor por API, el escalado es del proveedor y su preocupación pasa a cuotas, límites de tasa y resiliencia del cliente.
Advertencia de vigencia: las capacidades de GPU en plataformas serverless y los nombres de servicios cambian con frecuencia; verifique cada afirmación en la documentación vigente antes de comprometer un diseño. En esta sesión no se compara precio.`);
    tbl(s, [["", "Ruta A: Kubernetes administrado", "Ruta B: serverless / endpoints administrados"], ["Azure", "AKS + KEDA / HPA", "Container Apps · Foundry (modelos administrados)"], ["AWS", "EKS + KEDA / Karpenter", "ECS/Fargate · Bedrock (modelos administrados)"], ["GCP", "GKE + HPA / Inference Gateway", "Cloud Run · Vertex AI (modelos administrados)"], ["Control", "alto, portable", "menor; escala el proveedor"], ["Operación", "más trabajo del equipo", "menos trabajo; límites y cuotas del proveedor"]], { y: 1.4, colW: [1.4, 3.7, 3.9], fs: 13, rowH: 0.52 });
    note(s, "Verifique cada servicio y capacidad GPU en la documentación vigente: cambian con frecuencia.", 4.75);
  }

  // =========================================================================
  // BLOQUE 4: GPU
  // =========================================================================
  section("4. GPU scheduling");
  divider("04", "Planificación de GPU", "Device plugin · time-slicing · MIG · MPS · DRA · colocación", `[1:48 · 1 min] Bloque de GPU scheduling (25 min). La GPU es el recurso más caro y escaso del sistema; el planificador de Kubernetes nació para CPU y memoria divisibles, así que necesita extensiones para entender aceleradores.`);

  // 36 por qué especial
  {
    const s = S("Por qué la GPU es un recurso especial", `[1:49 · 3 min] Kubernetes planifica CPU y memoria como cantidades divisibles y sobreasignables. La GPU, por defecto, no: se expone como recurso extendido entero (nvidia.com/gpu: 1), exclusivo, sin sobreasignación. Además: la VRAM no se puede swappear sin consecuencias graves; cada GPU tiene topología (NVLink/PCIe) que importa para paralelismo; los nodos GPU son pocos, caros y con cuota; y las cargas en línea y por lotes compiten por ellos.
Consecuencia: la política de asignación impacta directamente el costo: una GPU entera reservada para un modelo pequeño que usa 10 % de la VRAM es desperdicio; compartirla sin aislamiento puede degradar a todos.`);
    card(s, { x: 0.5, y: 1.35, w: 2.9, h: 3.5, title: "Entera y exclusiva", ic: "FaMicrochip", color: C.accent5, body: "Se pide por unidades enteras; sin sobreasignación por defecto." });
    card(s, { x: 3.55, y: 1.35, w: 2.9, h: 3.5, title: "Topología", ic: "FaNetworkWired", color: C.accent3, body: "NVLink/PCIe importan para paralelismo tensorial." });
    card(s, { x: 6.6, y: 1.35, w: 2.9, h: 3.5, title: "Escasa y cara", ic: "FaDollarSign", color: C.accent2, body: "Pocos nodos, cuota limitada, cargas en competencia." });
  }

  // 37 device plugin
  {
    const s = S("Device plugin: cómo Kubernetes descubre la GPU", `[1:52 · 3 min] Mecanismo clásico: un DaemonSet (el device plugin del fabricante) se registra ante el kubelet por gRPC, lista los dispositivos y el kubelet los anuncia como recurso extendido del nodo. El scheduler solo ve un contador entero; cuando el Pod lo solicita, el kubelet llama a Allocate y el runtime del contenedor inyecta los dispositivos y las bibliotecas necesarias (NVIDIA Container Toolkit).
Qué NO puede expresar: atributos (modelo de GPU, VRAM, topología), compartición fina ni configuración por solicitud. Para eso surgió DRA.
Práctica de aislamiento de pools: los pools GPU se marcan con taints (p. ej. nvidia.com/gpu:NoSchedule) para que solo las cargas con tolerations aterricen ahí; los Pods de aplicación sin GPU no deben ocupar esos nodos.`);
    flow(s, ["Device plugin\n(DaemonSet)", "kubelet\n(registro gRPC)", "Nodo anuncia\nnvidia.com/gpu: N", "Scheduler\nasigna Pod"], { y: 1.5, h: 1.1, gap: 0.35, fills: [C.accent6, C.accent3, C.accent1, C.accent2] });
    bullets(s, ["El scheduler solo ve un contador entero", "Sin atributos (modelo, VRAM), sin compartición fina", "Aislamiento de pools con taints y tolerations"], { y: 3.0, h: 1.9, fs: 16 });
  }

  // 38 compartir
  {
    const s = S("Compartir una GPU: time-slicing, MIG y MPS", `[1:55 · 4 min] Time-slicing: la GPU se reparte por turnos entre varios Pods; mejora la ocupación pero NO hay aislamiento de memoria ni de errores: un proceso puede agotar la VRAM de otro. MIG (Multi-Instance GPU, solo en GPU compatibles): particiona físicamente en instancias con memoria y cómputo dedicados; aislamiento fuerte y tamaños fijos. MPS: permite que varios procesos compartan el cómputo con menor sobrecarga de cambio de contexto; el aislamiento es parcial y requiere configuración.
Criterio: cargas de producción con requisitos de latencia y seguridad por inquilino → GPU entera o MIG. Desarrollo, pruebas o modelos pequeños donde la interferencia es tolerable → time-slicing. Verifique la compatibilidad de GPU y driver antes de planificar.
Pregunta: en un clúster compartido por varios grupos de estudiantes, ¿qué mecanismo elegiría y por qué? Respuesta: MIG si el hardware lo soporta (aislamiento); si no, time-slicing con límites claros y advertencia de interferencia.`);
    tbl(s, [["Mecanismo", "Idea", "Aislamiento", "Cuándo"], ["GPU entera", "un Pod, una GPU", "total", "producción con SLO"], ["Time-slicing", "turnos sobre una GPU", "sin aislamiento de memoria", "desarrollo, modelos pequeños"], ["MIG", "particiones físicas", "fuerte", "multiinquilino; hardware compatible"], ["MPS", "comparte cómputo", "parcial", "muchos procesos pequeños"]], { y: 1.4, colW: [1.8, 2.6, 2.4, 2.2], fs: 13, rowH: 0.62 });
  }

  // 39 DRA
  {
    const s = S("DRA: reclamar dispositivos como almacenamiento", `[1:59 · 4 min] Dynamic Resource Allocation modela dispositivos con objetos análogos a PV/PVC/StorageClass: el administrador define DeviceClass (categoría de dispositivo); el usuario crea un ResourceClaim (o una ResourceClaimTemplate) que describe lo que necesita, incluso con selectores CEL sobre atributos (p. ej. "al menos X GiB de VRAM"); el driver DRA publica los dispositivos disponibles y el scheduler decide con esa información estructurada.
Hecho documentado: las APIs núcleo (resource.k8s.io v1) pasaron a GA en Kubernetes 1.34. En marzo de 2026 NVIDIA donó su driver DRA para GPU a la comunidad de Kubernetes y Google donó el de TPU (KubeCon Europa). Documentación de NVIDIA: usar solo uno de los dos mecanismos (device plugin o DRA) por nodo para evitar sobreadmisión.
Qué gana: selección por atributos, configuración por reclamo, y base para compartición fina. Qué cuesta: mayor complejidad y madurez desigual de drivers: evalúe antes de migrar producción. Nuestro manifiesto de ejemplo (overlays/gpu/dra-example.yaml) es DIDÁCTICO y no fue validado en clúster.`);
    flow(s, ["DeviceClass\n(admin)", "ResourceClaim /\nTemplate", "Driver DRA\n(publica dispositivos)", "Scheduler\nasigna"], { y: 1.45, h: 1.1, gap: 0.35, fills: [C.accent3, C.accent2, C.accent6, C.accent1] });
    card(s, { x: 0.5, y: 2.9, w: 4.4, h: 2.0, title: "Qué aporta", ic: "FaSearch", color: C.accent1, body: "Selección por atributos (modelo, VRAM), configuración por reclamo y base para compartición fina." });
    card(s, { x: 5.1, y: 2.9, w: 4.4, h: 2.0, title: "Estado (hecho)", ic: "FaCheckCircle", color: C.accent6, body: "resource.k8s.io/v1 GA en Kubernetes 1.34; driver NVIDIA donado a la comunidad (mar-2026)." });
  }

  // 40 colocación
  {
    const s = S("Colocación, fragmentación y tipos de carga", `[2:03 · 3 min] Control de colocación: nodeSelector y afinidad para elegir el pool y el tipo de GPU; taints y tolerations para reservar pools; topología para que un modelo repartido en varias GPU quede en el mismo nodo con interconexión rápida. Fragmentación: muchas GPU parcialmente usadas que impiden ubicar un Pod que necesita varias GPU; se mitiga con bin-packing, MIG y planificación consciente de tamaños.
Tipos de carga: en línea (interactiva, SLO estricto) → capacidad dedicada o reservada y sin interrupciones. Por lotes (evaluación, embeddings masivos, ajuste fino) → colas con planificador de trabajos (p. ej. Kueue) y capacidad spot/preemptible, tolerando interrupciones. Mezclarlas sin prioridades degrada el servicio en línea.
Pregunta: ¿qué prioridad de preempción asignaría al chat interactivo frente a una evaluación nocturna? Respuesta: la más alta al chat; el lote se desaloja.`);
    const items = [["FaMicrochip", "Dónde", "nodeSelector, afinidad, taints/tolerations", C.accent1], ["FaLayerGroup", "Topología", "varias GPU del modelo en el mismo nodo/NVLink", C.accent3], ["FaCubes", "Fragmentación", "GPU parciales que bloquean cargas grandes", C.accent5], ["FaTasks", "Tipos de carga", "en línea dedicada; lotes en spot con colas", C.accent2]];
    items.forEach((p, i) => card(s, { x: 0.5 + (i % 2) * 4.6, y: 1.35 + Math.floor(i / 2) * 1.8, w: 4.4, h: 1.65, title: p[1], body: p[2], ic: p[0], color: p[3] }));
  }

  // 41 FinOps
  {
    const s = S("FinOps: el costo por millón de tokens", `[2:06 · 4 min] Fórmula de costo de inferencia autogestionada: costo por millón de tokens = costo de la GPU por hora ÷ (tokens por segundo sostenidos × 3600 × utilización) × 10^6. Lea la fórmula: la utilización multiplica el denominador, así que una GPU mal utilizada encarece cada token.
El repositorio NO incluye precios: cambian con frecuencia y varían por región y modalidad (bajo demanda, reservado, spot). Ejercicio: cada estudiante obtiene el precio vigente de una GPU en su región, mide los tokens por segundo con loadtest.py y calcula su costo por millón de tokens; luego lo compara con la tarifa por token de una API administrada. El resultado depende fuertemente de la utilización y de los requisitos de privacidad (a veces la decisión no es de costo sino de control de datos).
Palancas: aumentar utilización (batching, consolidación), cuantizar, elegir bien el tamaño del modelo, escalar bajo demanda, capacidad reservada para la base y spot para lotes, y apagar lo que no se usa.
Referencia: FinOps Foundation Framework.`);
    formula(s, "USD/1M tokens = USD_GPU_hora ÷ (tok/s × 3600 × utilización) × 10⁶", { y: 1.35, h: 0.8, fs: 18 });
    const l = [["FaTachometerAlt", "Utilización", "la palanca principal: una GPU ociosa cobra igual", C.accent1], ["FaCubes", "Tamaño y cuantización", "modelo suficiente para la tarea", C.accent3], ["FaCloud", "Modalidad de compra", "reservada para la base, spot para lotes", C.accent2]];
    l.forEach((p, i) => card(s, { x: 0.5 + i * 3.05, y: 2.45, w: 2.9, h: 2.3, title: p[1], body: p[2], ic: p[0], color: p[3] }));
    note(s, "Sin precios en el repositorio: use los vigentes de su región y sus propias mediciones.", 4.85);
  }

  // 42 Seguridad checklist
  {
    const s = S("Checklist de seguridad de la sesión", `[2:10 · 3 min] Cierre del contenido teórico con una lista de verificación por dominio. Red: deny-by-default, TLS, servidor de inferencia no expuesto, egress controlado. Almacenamiento: cifrado, versionado, integridad, mínimo privilegio. Autoscaling: máximos para limitar costo y consumo (OWASP LLM10:2025), límites por usuario. GPU: aislamiento adecuado al riesgo (MIG vs time-slicing), pools reservados. Identidad: sin claves estáticas (Entra ID, IAM, ADC).
Advertencia de vigencia: confirme si existe una versión más reciente de OWASP Top 10 for LLM Applications antes de citarla; esta sesión usó la edición 2025.
Marcos: NIST AI RMF 1.0, NIST AI 600-1, ISO/IEC 42001:2023, ISO/IEC 27001:2022.`);
    tbl(s, [["Dominio", "Verificación mínima"], ["Red", "deny-by-default · TLS · inferencia no expuesta · egress mínimo"], ["Almacenamiento", "cifrado · versión fija · checksum · acceso mínimo"], ["Autoscaling", "máximo de réplicas · cola acotada · límites por usuario (OWASP LLM10:2025)"], ["GPU", "aislamiento según riesgo (entera / MIG) · pools reservados"], ["Identidad", "sin claves estáticas · identidad de carga de trabajo"]], { y: 1.4, colW: [2.2, 6.8], fs: 14, rowH: 0.6 });
  }

  // =========================================================================
  // BLOQUE 5: DEMOS
  // =========================================================================
  section("5. Demostraciones");
  divider("05", "Demostraciones en vivo", "Predicciones primero · datos después", `[2:13 · 1 min] Demostraciones (≈ 30 min). Metodología: antes de cada demo, los estudiantes ESCRIBEN su predicción (30 s). Después de la demo se compara. Esto convierte la demo en contraste de hipótesis y no en espectáculo. El código está en el repositorio; aquí se muestran solo resultados y se discute.`);

  // 44 demo 1
  {
    const s = S("Demo 1 — Ollama + gateway: observar la cola", `[2:14 · 12 min] Pasos: (1) docker compose up; (2) verificar /readyz; (3) enviar una solicitud con la interfaz React y observar TTFT, TPOT y latencia; (4) ejecutar loadtest.py con concurrencia 1,2,4,8; (5) en otra terminal observar /metrics (queue_depth, in_flight) y la CPU con htop.
Predicción a registrar antes: ¿la latencia p95 crece linealmente con la concurrencia? Esperado: casi plana hasta max_concurrency (2 en el laboratorio) y luego crece al aparecer la cola. Registre los números reales de SU máquina: no hay valores de referencia en el material porque dependen del hardware.
Si no hay GPU, es normal que sea lento; use max_tokens bajo. Plan B: ejecutar el servidor simulado de las pruebas (pytest) para mostrar el comportamiento de cola sin modelo.`);
    flow(s, ["docker compose\nup", "/readyz\n= listo", "Solicitud en\nla UI React", "loadtest.py\n1·2·4·8"], { y: 1.5, h: 1.0, gap: 0.35, fills: [C.accent1, C.accent6, C.accent3, C.accent2] });
    card(s, { x: 0.5, y: 2.9, w: 4.4, h: 2.0, title: "Predicción (escribirla antes)", ic: "FaQuestionCircle", color: C.accent3, body: "¿Cómo crece la latencia p95 al aumentar la concurrencia?" });
    card(s, { x: 5.1, y: 2.9, w: 4.4, h: 2.0, title: "Qué observar", ic: "FaEye", color: C.accent1, body: "queue_depth, in_flight, TTFT, TPOT y 'codes' del reporte." });
  }

  // 45 demo 2
  {
    const s = S("Demo 2 — Ráfaga: 200, 429 y 503", `[2:26 · 8 min] Con GW_MAX_QUEUE bajo (2) y GW_QUEUE_TIMEOUT_S corto, presione "Ráfaga de 12 solicitudes" en la UI o ejecute loadtest con concurrencia 16. Resultado esperable: algunas respuestas 200, otras 429 inmediatas (cola llena) y, si hay espera larga, algunas 503. Mostrar Retry-After en la respuesta.
Discusión: ¿es mejor un usuario con un error claro y rápido o veinte usuarios con una espera de minutos? Introduzca el concepto de SLO: lo medimos con TTFT p95 y tasa de rechazo.
Si hay un clúster disponible (opcional): aplicar k8s/ y el ScaledObject, repetir la ráfaga y observar con kubectl get pods -w cómo aparece una réplica nueva, y cuánto tarda en pasar de Pending a Ready (¡el cold start medido!). Si no hay clúster, muestre el manifiesto y razone el comportamiento esperado SIN presentarlo como resultado medido.`);
    flow(s, ["Ráfaga\n(12 solicitudes)", "Gateway\n(cola acotada)", "200 · 429 · 503", "queue_depth\n↑"], { y: 1.5, h: 1.0, gap: 0.35, fills: [C.accent4, C.accent1, C.accent5, C.accent2] });
    bullets(s, ["¿Un error rápido y claro o una espera de minutos?", "Con KEDA: queue_depth alto ⇒ nueva réplica ⇒ medir Pending → Ready", "Lo que no se mide en clase no se afirma como resultado"], { y: 3.0, h: 1.9, fs: 16 });
  }

  // 46 labs multicloud
  {
    const s = S("Laboratorios multicloud: un agente, tres nubes", `[2:34 · 5 min] Cada nube tiene dos partes: consola (no-code) y código. Mismo agente de dimensionamiento con una herramienta determinista (estimate_inference_replicas), lo que permite comparar frameworks con la misma tarea. Google: agente en consola de la plataforma y con ADK (despliegue en Cloud Run o Agent Engine). Azure: agente en el portal de Foundry y cuatro frameworks: Microsoft Agent Framework (GA 1.0, abr-2026; recomendado), Semantic Kernel y AutoGen (modo mantenimiento, sucedidos por Agent Framework) y LangGraph. AWS: agente en la consola de Bedrock, Strands Agents SDK y despliegue en Bedrock AgentCore Runtime (GA desde oct-2025).
Estado honesto: el material verificó que los scripts importan y construyen sus objetos; NO se ejecutaron llamadas reales a modelos en las tres nubes. El docente debe ejecutar cada laboratorio una vez antes de clase. Además, los modelos Gemini 2.5 se reportan retirados de Vertex AI en oct-2026: confirmar el ID vigente.
Cuentas: pruebas gratuitas en las tres nubes; los estudiantes no actualizarán a pago por uso; Azure primero en la demostración en vivo.`);
    const cols = [["FaCloud", "Google Cloud", "Consola · ADK · Cloud Run / Agent Engine · Gemini", C.accent3], ["FaServer", "Microsoft Azure", "Portal Foundry · Agent Framework · SK · AutoGen · LangGraph", C.accent1], ["FaCubes", "AWS", "Consola Bedrock · Strands · AgentCore Runtime", C.accent2]];
    cols.forEach((p, i) => card(s, { x: 0.5 + i * 3.05, y: 1.35, w: 2.9, h: 2.75, title: p[1], body: p[2], ic: p[0], color: p[3] }));
    note(s, "Verificado: importaciones y construcción de objetos. NO verificado: llamadas reales a modelos en nube (ejecutar antes de clase).", 4.3);
    note(s, "Modelos y regiones cambian: confirme IDs vigentes (p. ej., Gemini 2.5 retirado en Vertex AI en oct-2026 según fuentes consultadas).", 4.7);
  }

  // =========================================================================
  // CIERRE
  // =========================================================================
  section("6. Cierre");
  // 47 decisiones
  {
    const s = S("Decisiones arquitectónicas del caso (ADR)", `[2:39 · 5 min] Resumen de decisiones con su justificación y su trade-off; cada una está documentada en docs/adr. Pida a los estudiantes que cuestionen una: ¿cambiarían alguna con 10 veces más usuarios? ¿con requisitos de residencia de datos más estrictos?
Recordatorio: una decisión sin alternativa descartada y sin costo declarado no es una decisión de arquitectura, es una preferencia.`);
    tbl(s, [["ADR", "Decisión", "Trade-off principal"], ["001", "Gateway con cola acotada por réplica", "un componente más; límite por réplica"], ["002", "Autoscaling por profundidad de cola (KEDA)", "depende de Prometheus y de calibrar el umbral"], ["003", "StatefulSet con un PVC por réplica", "almacenamiento duplicado; primer arranque lento"], ["004", "NetworkPolicy deny-by-default; inferencia en loopback", "requiere CNI; egress 443 es deuda a eliminar"], ["005", "Identidad sin claves estáticas", "más pasos iniciales de configuración"], ["006", "Ollama en el laboratorio", "no representa el rendimiento de servidores de alto throughput"]], { y: 1.35, colW: [0.8, 4.3, 3.9], fs: 13, rowH: 0.52 });
  }

  // 48 discusión
  {
    const s = S("Discusión guiada", `[2:44 · 8 min] Formato: parejas durante 3 minutos y plenaria de 5. Respuestas esperadas de apoyo para el docente (están ampliadas en la guía docente): (1) Dos réplicas con mismas conexiones pueden diferir en trabajo real; hay que balancear por cola/KV cache. (2) Un 429 es degradación controlada que protege el SLO; una cola infinita transforma un pico en indisponibilidad. (3) Con cold start de minutos, escalar solo reactivamente no cubre picos cortos; se necesita capacidad caliente, cola acotada y escalado programado. (4) Para multiinquilino con requisitos de aislamiento, MIG o GPU entera; time-slicing no aísla memoria.`);
    const q = ["¿Por qué dos réplicas con el mismo número de conexiones pueden estar desigualmente cargadas?", "¿Por qué rechazar tráfico (429) puede mejorar la disponibilidad percibida?", "Con un cold start de minutos, ¿qué combinación de mecanismos protege un pico de 30 s?", "¿Qué mecanismo de compartición de GPU elegiría para un clúster multiusuario y por qué?"];
    q.forEach((t, i) => { badge(s, i + 1, 0.5, 1.4 + i * 0.9, [C.accent1, C.accent3, C.accent2, C.accent6][i]); s.addText(t, { x: 1.1, y: 1.3 + i * 0.9, w: 8.4, h: 0.65, fontSize: 16, color: C.text1, valign: "middle", margin: 0, isTextBox: true }); });
  }

  // 49 síntesis
  {
    const s = S("Síntesis: cinco ideas para recordar", `[2:52 · 3 min] Repase en voz alta. Cierre conectando con el objetivo de desempeño del capítulo: un despliegue contenedorizado de un servidor de inferencia con red, almacenamiento y autoscaling; el repositorio y los laboratorios materializan estas cinco ideas.
Anuncie la actividad de evaluación y la preparación de la Sesión 5: observabilidad y pruebas de carga con SLO sobre este mismo sistema.`);
    const five = ["La capacidad es finita: admitir con cola acotada y rechazar con claridad.", "Balancear trabajo, no conexiones: L7 y, a escala, consciente del modelo.", "Los pesos son datos pesados: el cold start fija la velocidad máxima de escalado.", "Escalar por cola (demanda insatisfecha), con estabilidad, mínimos y máximos.", "La GPU se planifica: entera, MIG, time-slicing o DRA según aislamiento y costo."];
    five.forEach((t, i) => { badge(s, i + 1, 0.5, 1.35 + i * 0.72, [C.accent1, C.accent3, C.accent2, C.accent6, C.accent5][i]); s.addText(t, { x: 1.1, y: 1.3 + i * 0.72, w: 8.4, h: 0.6, fontSize: 16, color: C.text1, valign: "middle", margin: 0, isTextBox: true }); });
  }

  // 50 evaluación
  {
    const s = S("Actividad de evaluación y entregables", `[2:55 · 3 min] La rúbrica detallada está en la guía docente (repositorio privado del docente). Actividad: informe técnico breve (3–5 páginas) con (a) dimensionamiento de capacidad del caso con supuestos explícitos y mediciones propias del laboratorio 0; (b) política de autoscaling con señal, umbral, ventanas, mínimos y máximos justificados; (c) diseño de red y almacenamiento con las decisiones y sus trade-offs; (d) comparación de al menos dos frameworks agénticos a partir de los laboratorios cloud.
Criterios (resumen): exactitud conceptual, calidad de la justificación, uso de evidencia medida frente a supuestos, seguridad, y reproducibilidad.
Autoevaluación: cuestionario de la guía del estudiante.`);
    const d = [["FaFlask", "Laboratorio 0", "Mediciones propias con loadtest.py", C.accent1], ["FaChartLine", "Informe técnico", "Capacidad, autoscaling, red y almacenamiento", C.accent3], ["FaCloud", "Laboratorios 1–3", "Comparación de al menos dos frameworks", C.accent2], ["FaBook", "Autoevaluación", "Cuestionario de la guía del estudiante", C.accent6]];
    d.forEach((p, i) => card(s, { x: 0.5 + (i % 2) * 4.6, y: 1.35 + Math.floor(i / 2) * 1.8, w: 4.4, h: 1.65, title: p[1], body: p[2], ic: p[0], color: p[3] }));
  }

  // 51-52 referencias
  {
    const s = S("Referencias (1/2) — Fundamentos", `[2:58 · 1 min] Las referencias están organizadas en fundamentos académicos y documentación oficial. Fecha de consulta de las fuentes en línea: 3 de noviembre de 2026. Las URL completas están en docs/bibliografia.md del repositorio. Solicite a los estudiantes que NO cite documentación sin verificar su vigencia: los servicios cambian.`);
    bullets(s, [
      "Kwon, W. et al. (2023). Efficient Memory Management for LLM Serving with PagedAttention. SOSP '23.",
      "Yu, G.-I. et al. (2022). Orca: A Distributed Serving System for Transformer-Based Generative Models. OSDI '22.",
      "Zhong, Y. et al. (2024). DistServe: Disaggregating Prefill and Decoding for Goodput-optimized LLM Serving. OSDI '24.",
      "Dean, J. y Barroso, L. A. (2013). The Tail at Scale. Communications of the ACM, 56(2).",
      "Little, J. D. C. (1961). A Proof for the Queuing Formula: L = λW. Operations Research, 9(3).",
      "Beyer, B. et al. (2016). Site Reliability Engineering. O'Reilly.",
    ], { y: 1.35, h: 3.6, fs: 14 });
  }
  {
    const s = S("Referencias (2/2) — Documentación y marcos", `[2:59 · 1 min] Documentación oficial consultada el 2026-11-03. Recuérdeles verificar versiones: Kubernetes (DRA GA en 1.34), KEDA, Agent Framework (GA 1.0 abr-2026), AgentCore (GA oct-2025), modelos de cada proveedor.`);
    bullets(s, [
      "Kubernetes: Dynamic Resource Allocation; Device Plugins; HPA; Network Policies — kubernetes.io/docs.",
      "KEDA — keda.sh/docs (ScaledObject, disparador Prometheus).",
      "Google Cloud: GKE Inference Gateway; blog «DRA: A new era of Kubernetes device management» (25-mar-2026).",
      "AWS: Amazon EKS — Autoscale AI inference with HPA and KEDA; Amazon Bedrock AgentCore (GA 13-oct-2025).",
      "Microsoft: Agent Framework 1.0 (blog Foundry, abr-2026); documentación de Microsoft Foundry.",
      "OWASP Top 10 for LLM Applications 2025 · NIST AI RMF 1.0 y AI 600-1 · ISO/IEC 42001:2023 · ISO/IEC 27001:2022.",
      "FinOps Foundation — FinOps Framework.",
    ], { y: 1.35, h: 3.6, fs: 14 });
  }

  // Cierre
  {
    const s = pres.addSlide({ masterName: "DARK", sectionTitle: sectionOpen });
    s.addText("Preguntas", { placeholder: "title" });
    s.addText("Próxima sesión: observabilidad y pruebas de carga con SLO sobre este mismo sistema.", { placeholder: "body" });
    s.addNotes(`[3:00] Cierre y preguntas. Recuerde publicar el enlace del repositorio y las instrucciones de entrega del informe. Haga la encuesta de 1 minuto: ¿qué fue lo más claro y qué quedó confuso? Úsela para ajustar la próxima sesión.`);
  }

  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("OK", OUT);
})().catch((e) => { console.error(e); process.exit(1); });
