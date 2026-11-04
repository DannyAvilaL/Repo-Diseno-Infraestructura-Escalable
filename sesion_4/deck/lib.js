// Utilidades de diseño para la presentación (pptxgenjs). Cada helper crea objetos de opciones NUEVOS
// porque pptxgenjs los muta en sitio.
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");

const THEME = {
  name: "Infraestructura LLM",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "0B1F33", lt1: "FFFFFF", dk2: "163A57", lt2: "EAF1F6",
    accent1: "0E7C86", accent2: "E8871E", accent3: "3B6FB6", accent4: "5B6B7A", accent5: "B83A2E", accent6: "2E8B57",
    hlink: "0E7C86", folHlink: "5B6B7A",
  },
};

async function icon(name, hex = "FFFFFF", px = 256) {
  const Comp = fa[name];
  if (!Comp) throw new Error("icono inexistente: " + name);
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color: "#" + hex, size: px }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

module.exports = { THEME, icon };
