// Gráficos en SVG, sin librerías. Cada función dibuja dentro de un contenedor con su ancho real
// y se vuelve a llamar cuando cambia el tamaño o el tema (ver `registrar` en app.js).
//
// Reglas (guía de visualización del proyecto): un solo eje Y, líneas de 2 px, barras de 14 px con
// el extremo de datos redondeado, rejilla de 1 px recesiva, leyenda con dos series o más, etiquetas
// selectivas, tooltip también con el teclado, y nunca colores de datos en el texto.

const NS = "http://www.w3.org/2000/svg";

export function svg(tag, atributos = {}, ...hijos) {
  const nodo = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(atributos)) if (v !== undefined && v !== null) nodo.setAttribute(k, v);
  for (const h of hijos) nodo.append(h);
  return nodo;
}

export function color(nombre) {
  return getComputedStyle(document.documentElement).getPropertyValue(`--${nombre}`).trim();
}

// Marcas de eje "redondas": 1, 2 o 5 por potencia de diez
export function marcas(min, max, cantidad = 5) {
  if (min === max) return [min];
  const paso0 = (max - min) / cantidad;
  const potencia = 10 ** Math.floor(Math.log10(paso0));
  const paso = [1, 2, 5, 10].map((m) => m * potencia).find((p) => p >= paso0);
  const desde = Math.floor(min / paso) * paso;
  const hasta = Math.ceil(max / paso) * paso;
  const salida = [];
  for (let v = desde; v <= hasta + paso / 2; v += paso) salida.push(Number(v.toFixed(10)));
  return salida;
}

// ---------------------------------------------------------------------------------------- tooltip
const tip = document.createElement("div");
tip.className = "tooltip";
tip.setAttribute("role", "status");
tip.hidden = true;
document.body.append(tip);

// filas: [{ valor, etiqueta, clave? (color de la línea-clave), nota? }]
export function mostrarTooltip(x, y, titulo, filas) {
  tip.replaceChildren();
  if (titulo) tip.append(Object.assign(document.createElement("div"), { className: "tooltip-titulo", textContent: titulo }));
  for (const f of filas) {
    const fila = document.createElement("div");
    fila.className = "tooltip-fila";
    if (f.clave) {
      const linea = document.createElement("span");
      linea.className = "tooltip-clave";
      linea.style.background = f.clave;
      fila.append(linea);
    }
    fila.append(Object.assign(document.createElement("strong"), { textContent: f.valor }));
    if (f.etiqueta) fila.append(Object.assign(document.createElement("span"), { textContent: f.etiqueta }));
    tip.append(fila);
    if (f.nota) tip.append(Object.assign(document.createElement("div"), { className: "tooltip-nota", textContent: f.nota }));
  }
  tip.hidden = false;
  const { width, height } = tip.getBoundingClientRect();
  const izquierda = Math.min(window.innerWidth - width - 8, Math.max(8, x + 14));
  const arriba = y - height - 14 < 8 ? y + 18 : y - height - 14;
  tip.style.left = `${izquierda}px`;
  tip.style.top = `${arriba}px`;
}

export function ocultarTooltip() {
  tip.hidden = true;
}

function alEnfocar(nodo, contenido) {
  nodo.addEventListener("pointermove", (e) => contenido(e.clientX, e.clientY));
  nodo.addEventListener("pointerleave", ocultarTooltip);
  nodo.addEventListener("focus", () => {
    const r = nodo.getBoundingClientRect();
    contenido(r.left + r.width / 2, r.top);
  });
  nodo.addEventListener("blur", ocultarTooltip);
}

// Barra con el extremo de datos redondeado (4 px) y la base recta
function barra(x0, x1, y, alto, radio = 4) {
  const r = Math.min(radio, Math.abs(x1 - x0), alto / 2);
  if (x1 >= x0) {
    return `M${x0},${y}H${x1 - r}A${r},${r} 0 0 1 ${x1},${y + r}V${y + alto - r}A${r},${r} 0 0 1 ${x1 - r},${y + alto}H${x0}Z`;
  }
  return `M${x0},${y}H${x1 + r}A${r},${r} 0 0 0 ${x1},${y + r}V${y + alto - r}A${r},${r} 0 0 0 ${x1 + r},${y + alto}H${x0}Z`;
}

function columna(x, y0, y1, ancho, radio = 4) {
  const r = Math.min(radio, Math.abs(y0 - y1), ancho / 2);
  return `M${x},${y0}V${y1 + r}A${r},${r} 0 0 1 ${x + r},${y1}H${x + ancho - r}A${r},${r} 0 0 1 ${x + ancho},${y1 + r}V${y0}Z`;
}

// ------------------------------------------------------------------------------ barras horizontales
// filas: [{ clave, etiqueta, valor, derivado? }]; divergente: barras desde cero, rojo < 0 < azul
export function barrasH(contenedor, { filas, formato, divergente = false, resaltado, alSeleccionar, descripcion }) {
  const ancho = contenedor.clientWidth;
  if (ancho < 120) return; // sin ancho todavía (pestaña oculta): se dibuja al aparecer
  const altoFila = 24, grosor = 14;
  const etiquetaAncho = Math.min(210, Math.round(ancho * 0.42));
  const margenDer = 64;
  const alto = filas.length * altoFila + 8;
  const valores = filas.map((f) => f.valor);
  const min = divergente ? Math.min(0, ...valores) : 0;
  const max = Math.max(0, ...valores);
  const x = (v) => etiquetaAncho + ((v - min) / (max - min || 1)) * (ancho - etiquetaAncho - margenDer);
  const raiz = svg("svg", { width: ancho, height: alto, role: "group", "aria-label": descripcion });

  if (divergente) {
    raiz.append(svg("line", { x1: x(0), x2: x(0), y1: 0, y2: alto, stroke: color("eje"), "stroke-width": 1 }));
  }
  filas.forEach((f, i) => {
    const y = i * altoFila + 4;
    const esResaltado = f.clave === resaltado;
    let relleno = divergente ? (f.valor < 0 ? color("negativo") : color("serie-1")) : color("serie-1");
    if (resaltado && !esResaltado && !divergente) relleno = color("atenuado");
    const g = svg("g", { class: "marca", tabindex: 0, role: "button", "aria-label": `${f.etiqueta}: ${formato(f.valor)}${f.derivado ? " (derivado)" : ""}` });
    g.append(svg("rect", { x: 0, y: y - 2, width: ancho, height: altoFila, fill: "transparent" })); // zona de toque
    const texto = svg("text", { x: etiquetaAncho - 8, y: y + grosor - 3, "text-anchor": "end", class: esResaltado ? "etiqueta fuerte" : "etiqueta" });
    // nombres largos: se recortan para que quepan; el nombre completo queda en el tooltip y en aria-label
    const caben = Math.floor((etiquetaAncho - 10) / 6.6);
    texto.textContent = f.etiqueta.length > caben ? `${f.etiqueta.slice(0, caben - 1)}…` : f.etiqueta;
    g.append(texto);
    const forma = svg("path", { d: barra(x(0), x(f.valor), y, grosor), fill: relleno });
    if (f.derivado) forma.setAttribute("fill-opacity", "0.45");
    g.append(forma);
    const derecha = f.valor >= 0;
    const valor = svg("text", { x: x(f.valor) + (derecha ? 6 : -6), y: y + grosor - 3, "text-anchor": derecha ? "start" : "end", class: "valor" });
    valor.textContent = formato(f.valor) + (f.derivado ? "*" : "");
    // si el valor negativo no cabe a la izquierda, se pone a la derecha del cero
    if (!derecha && x(f.valor) - 6 - 40 < etiquetaAncho) {
      valor.setAttribute("x", x(0) + 6);
      valor.setAttribute("text-anchor", "start");
    }
    g.append(valor);
    alEnfocar(g, (cx, cy) => mostrarTooltip(cx, cy, f.etiqueta, [
      { valor: formato(f.valor), nota: f.derivado ? "Derivado: no lo publica la fuente" : undefined },
    ]));
    if (alSeleccionar) {
      g.addEventListener("click", () => alSeleccionar(f.clave));
      g.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); alSeleccionar(f.clave); } });
    }
    raiz.append(g);
  });
  contenedor.replaceChildren(raiz);
}

// ------------------------------------------------------------------------------------------ líneas
// series: [{ nombre, valores (null = sin dato), color, enfasis }]
export function lineas(contenedor, { x, series, formatoY, formatoX = (v) => v, descripcion, alto = 260 }) {
  const ancho = contenedor.clientWidth;
  if (ancho < 120) return; // sin ancho todavía (pestaña oculta): se dibuja al aparecer
  const m = { arriba: 16, derecha: 110, abajo: 28, izquierda: 52 };
  const todos = series.flatMap((s) => s.valores).filter((v) => v !== null);
  const ticks = marcas(Math.min(...todos), Math.max(...todos), 4);
  const [y0, y1] = [ticks[0], ticks[ticks.length - 1]];
  const px = (i) => m.izquierda + (i / Math.max(1, x.length - 1)) * (ancho - m.izquierda - m.derecha);
  const py = (v) => alto - m.abajo - ((v - y0) / (y1 - y0 || 1)) * (alto - m.arriba - m.abajo);
  const raiz = svg("svg", { width: ancho, height: alto, role: "img", "aria-label": descripcion });

  for (const t of ticks) {
    raiz.append(svg("line", { x1: m.izquierda, x2: ancho - m.derecha, y1: py(t), y2: py(t), stroke: color("rejilla"), "stroke-width": 1 }));
    const et = svg("text", { x: m.izquierda - 8, y: py(t) + 4, "text-anchor": "end", class: "eje" });
    et.textContent = formatoY(t);
    raiz.append(et);
  }
  const salto = Math.ceil(x.length / Math.max(2, Math.floor((ancho - m.izquierda - m.derecha) / 56)));
  x.forEach((etiqueta, i) => {
    if (i % salto !== 0 && i !== x.length - 1) return;
    const et = svg("text", { x: px(i), y: alto - 8, "text-anchor": "middle", class: "eje" });
    et.textContent = formatoX(etiqueta);
    raiz.append(et);
  });

  for (const s of [...series].sort((a, b) => (a.enfasis ? 1 : 0) - (b.enfasis ? 1 : 0))) {
    let d = "";
    s.valores.forEach((v, i) => { if (v !== null) d += `${d && s.valores[i - 1] !== null ? "L" : "M"}${px(i)},${py(v)}`; });
    raiz.append(svg("path", { d, fill: "none", stroke: s.color, "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round" }));
    const ultimo = s.valores.length - 1 - [...s.valores].reverse().findIndex((v) => v !== null);
    raiz.append(svg("circle", { cx: px(ultimo), cy: py(s.valores[ultimo]), r: 4, fill: s.color, stroke: color("superficie"), "stroke-width": 2 }));
  }
  // etiquetas al final de cada línea; si se tocan, se separan lo justo
  const finales = series.map((s) => {
    const i = s.valores.length - 1 - [...s.valores].reverse().findIndex((v) => v !== null);
    return { s, y: py(s.valores[i]), v: s.valores[i] };
  }).sort((a, b) => a.y - b.y);
  for (let i = 1; i < finales.length; i++) if (finales[i].y - finales[i - 1].y < 14) finales[i].y = finales[i - 1].y + 14;
  for (const f of finales) {
    const et = svg("text", { x: ancho - m.derecha + 10, y: f.y + 4, class: f.s.enfasis ? "etiqueta fuerte" : "etiqueta" });
    et.textContent = `${formatoY(f.v)} ${f.s.nombre}`;
    raiz.append(et);
  }

  // retícula que sigue al puntero y salta al año / mes más cercano
  const cruz = svg("line", { y1: m.arriba, y2: alto - m.abajo, stroke: color("eje"), "stroke-width": 1, visibility: "hidden" });
  raiz.append(cruz);
  const zona = svg("rect", { x: m.izquierda, y: 0, width: ancho - m.izquierda - m.derecha, height: alto, fill: "transparent", tabindex: 0, "aria-label": `${descripcion}. Usa las flechas para recorrer los valores` });
  let actual = x.length - 1;
  const mostrar = (i, cx, cy) => {
    actual = i;
    cruz.setAttribute("x1", px(i)); cruz.setAttribute("x2", px(i)); cruz.setAttribute("visibility", "visible");
    mostrarTooltip(cx, cy, formatoX(x[i]), series.map((s) => ({
      valor: s.valores[i] === null ? "sin dato" : formatoY(s.valores[i]), etiqueta: s.nombre, clave: s.color,
    })));
  };
  zona.addEventListener("pointermove", (e) => {
    const caja = raiz.getBoundingClientRect();
    const rel = (e.clientX - caja.left - m.izquierda) / (ancho - m.izquierda - m.derecha);
    mostrar(Math.max(0, Math.min(x.length - 1, Math.round(rel * (x.length - 1)))), e.clientX, e.clientY);
  });
  const esconder = () => { cruz.setAttribute("visibility", "hidden"); ocultarTooltip(); };
  zona.addEventListener("pointerleave", esconder);
  zona.addEventListener("blur", esconder);
  const conTeclado = () => { const c = raiz.getBoundingClientRect(); mostrar(actual, c.left + px(actual), c.top + m.arriba); };
  zona.addEventListener("focus", conTeclado);
  zona.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft") { actual = Math.max(0, actual - 1); conTeclado(); e.preventDefault(); }
    if (e.key === "ArrowRight") { actual = Math.min(x.length - 1, actual + 1); conTeclado(); e.preventDefault(); }
  });
  raiz.append(zona);
  contenedor.replaceChildren(raiz);
}

// ---------------------------------------------------------------------------------------- columnas
// valores: números; huecos: índices sin dato; marcados: índices con una marca (p. ej. dato provisional)
export function columnas(contenedor, { x, valores, formato, formatoX = (v) => v, etiquetar = [], marcados = [], notaMarcado, descripcion, alto = 220 }) {
  const ancho = contenedor.clientWidth;
  if (ancho < 120) return; // sin ancho todavía (pestaña oculta): se dibuja al aparecer
  const m = { arriba: 22, derecha: 12, abajo: 28, izquierda: 52 };
  const presentes = valores.filter((v) => v !== null);
  const ticks = marcas(0, Math.max(...presentes), 4);
  const tope = ticks[ticks.length - 1];
  const banda = (ancho - m.izquierda - m.derecha) / x.length;
  const grosor = Math.min(24, Math.max(4, banda - 2)); // 2 px de aire entre columnas vecinas
  const py = (v) => alto - m.abajo - (v / tope) * (alto - m.arriba - m.abajo);
  const raiz = svg("svg", { width: ancho, height: alto, role: "group", "aria-label": descripcion });
  for (const t of ticks) {
    raiz.append(svg("line", { x1: m.izquierda, x2: ancho - m.derecha, y1: py(t), y2: py(t), stroke: color(t === 0 ? "eje" : "rejilla"), "stroke-width": 1 }));
    const et = svg("text", { x: m.izquierda - 8, y: py(t) + 4, "text-anchor": "end", class: "eje" });
    et.textContent = formato(t);
    raiz.append(et);
  }
  const salto = Math.ceil(x.length / Math.max(2, Math.floor((ancho - m.izquierda - m.derecha) / 56)));
  valores.forEach((v, i) => {
    const cx = m.izquierda + i * banda + (banda - grosor) / 2;
    if (i % salto === 0 || i === x.length - 1) {
      const et = svg("text", { x: cx + grosor / 2, y: alto - 8, "text-anchor": "middle", class: "eje" });
      et.textContent = formatoX(x[i]);
      raiz.append(et);
    }
    if (v === null) return;
    const marcado = marcados.includes(i);
    const g = svg("g", { class: "marca", tabindex: 0, "aria-label": `${formatoX(x[i])}: ${formato(v)}${marcado ? ` (${notaMarcado})` : ""}` });
    g.append(svg("rect", { x: m.izquierda + i * banda, y: m.arriba, width: banda, height: alto - m.arriba - m.abajo, fill: "transparent" }));
    const forma = svg("path", { d: columna(cx, py(0), py(v), grosor), fill: color("serie-1") });
    if (marcado) forma.setAttribute("fill-opacity", "0.5");
    g.append(forma);
    if (etiquetar.includes(i)) {
      const et = svg("text", { x: cx + grosor / 2, y: py(v) - 6, "text-anchor": "middle", class: "valor" });
      et.textContent = formato(v);
      g.append(et);
    }
    alEnfocar(g, (px, py2) => mostrarTooltip(px, py2, formatoX(x[i]), [{ valor: formato(v), nota: marcado ? notaMarcado : undefined }]));
    raiz.append(g);
  });
  contenedor.replaceChildren(raiz);
}

// --------------------------------------------------------------------- banda mínima–media–máxima
export function bandaTemperatura(contenedor, { x, minimas, medias, maximas, provisionales, formato, formatoX, descripcion, alto = 260 }) {
  const ancho = contenedor.clientWidth;
  if (ancho < 120) return; // sin ancho todavía (pestaña oculta): se dibuja al aparecer
  const m = { arriba: 16, derecha: 16, abajo: 28, izquierda: 52 };
  const todos = [...minimas, ...maximas].filter((v) => v !== null);
  const ticks = marcas(Math.min(...todos), Math.max(...todos), 4);
  const [y0, y1] = [ticks[0], ticks[ticks.length - 1]];
  const px = (i) => m.izquierda + (i / Math.max(1, x.length - 1)) * (ancho - m.izquierda - m.derecha);
  const py = (v) => alto - m.abajo - ((v - y0) / (y1 - y0 || 1)) * (alto - m.arriba - m.abajo);
  const raiz = svg("svg", { width: ancho, height: alto, role: "img", "aria-label": descripcion });
  for (const t of ticks) {
    raiz.append(svg("line", { x1: m.izquierda, x2: ancho - m.derecha, y1: py(t), y2: py(t), stroke: color(t === 0 ? "eje" : "rejilla"), "stroke-width": 1 }));
    const et = svg("text", { x: m.izquierda - 8, y: py(t) + 4, "text-anchor": "end", class: "eje" });
    et.textContent = formato(t);
    raiz.append(et);
  }
  const salto = Math.ceil(x.length / Math.max(2, Math.floor((ancho - m.izquierda - m.derecha) / 56)));
  x.forEach((etiqueta, i) => {
    if (i % salto !== 0 && i !== x.length - 1) return;
    const et = svg("text", { x: px(i), y: alto - 8, "text-anchor": "middle", class: "eje" });
    et.textContent = formatoX(etiqueta);
    raiz.append(et);
  });
  const idx = x.map((_, i) => i).filter((i) => minimas[i] !== null && maximas[i] !== null);
  const area = idx.map((i, k) => `${k ? "L" : "M"}${px(i)},${py(maximas[i])}`).join("") +
    [...idx].reverse().map((i) => `L${px(i)},${py(minimas[i])}`).join("") + "Z";
  raiz.append(svg("path", { d: area, fill: color("serie-1"), "fill-opacity": 0.12 }));
  let d = "";
  medias.forEach((v, i) => { if (v !== null) d += `${d && medias[i - 1] !== null ? "L" : "M"}${px(i)},${py(v)}`; });
  raiz.append(svg("path", { d, fill: "none", stroke: color("serie-1"), "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round" }));
  // los meses provisionales se dibujan con el marcador hueco
  medias.forEach((v, i) => {
    if (v === null) return;
    const hueco = provisionales[i];
    raiz.append(svg("circle", { cx: px(i), cy: py(v), r: 4, fill: hueco ? color("superficie") : color("serie-1"), stroke: hueco ? color("serie-1") : color("superficie"), "stroke-width": 2 }));
  });
  const cruz = svg("line", { y1: m.arriba, y2: alto - m.abajo, stroke: color("eje"), "stroke-width": 1, visibility: "hidden" });
  raiz.append(cruz);
  const zona = svg("rect", { x: m.izquierda, y: 0, width: ancho - m.izquierda - m.derecha, height: alto, fill: "transparent", tabindex: 0, "aria-label": `${descripcion}. Usa las flechas para recorrer los meses` });
  let actual = x.length - 1;
  const mostrar = (i, cx, cy) => {
    actual = i;
    cruz.setAttribute("x1", px(i)); cruz.setAttribute("x2", px(i)); cruz.setAttribute("visibility", "visible");
    const f = (v) => (v === null ? "sin dato" : formato(v));
    mostrarTooltip(cx, cy, formatoX(x[i]), [
      { valor: f(maximas[i]), etiqueta: "máxima media" },
      { valor: f(medias[i]), etiqueta: "media", clave: color("serie-1") },
      { valor: f(minimas[i]), etiqueta: "mínima media", nota: provisionales[i] ? "Provisional: el DWD todavía puede corregirlo" : undefined },
    ]);
  };
  zona.addEventListener("pointermove", (e) => {
    const caja = raiz.getBoundingClientRect();
    const rel = (e.clientX - caja.left - m.izquierda) / (ancho - m.izquierda - m.derecha);
    mostrar(Math.max(0, Math.min(x.length - 1, Math.round(rel * (x.length - 1)))), e.clientX, e.clientY);
  });
  const esconder = () => { cruz.setAttribute("visibility", "hidden"); ocultarTooltip(); };
  zona.addEventListener("pointerleave", esconder);
  zona.addEventListener("blur", esconder);
  const conTeclado = () => { const c = raiz.getBoundingClientRect(); mostrar(actual, c.left + px(actual), c.top + m.arriba); };
  zona.addEventListener("focus", conTeclado);
  zona.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft") { actual = Math.max(0, actual - 1); conTeclado(); e.preventDefault(); }
    if (e.key === "ArrowRight") { actual = Math.min(x.length - 1, actual + 1); conTeclado(); e.preventDefault(); }
  });
  raiz.append(zona);
  contenedor.replaceChildren(raiz);
}
