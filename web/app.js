import { cargarTodo } from "./datos.js";
import { barrasH, lineas, columnas, bandaTemperatura, color } from "./graficos.js";

// --------------------------------------------------------------------------------- utilidades
const numero = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 0 });
const decimal1 = new Intl.NumberFormat("es-CO", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const fNum = (v) => numero.format(v);
const fPct = (v) => `${decimal1.format(v)} %`;
const fSigno = (v) => `${v > 0 ? "+" : v < 0 ? "−" : ""}${decimal1.format(Math.abs(v))} %`;
const fGrados = (v) => `${v < 0 ? "−" : ""}${decimal1.format(Math.abs(v))} °C`;
const fMm = (v) => `${numero.format(v)} mm`;
const fCompacto = (v) => (v >= 1000 ? `${decimal1.format(v / 1000).replace(/,0$/, "")} mil` : fNum(v));
const fFecha = (iso) => new Date(`${iso.length === 7 ? `${iso}-01` : iso}T12:00:00`).toLocaleDateString("es-CO",
  iso.length === 7 ? { month: "short", year: "numeric" } : { day: "numeric", month: "short", year: "numeric" }).replace(/ de /g, " ").replace(".", "");
const fMes = (iso) => new Date(`${iso}-01T12:00:00`).toLocaleDateString("es-CO", { month: "short", year: "2-digit" }).replace(/ de /g, " ").replace(".", "");

function el(tag, atributos = {}, ...hijos) {
  const nodo = document.createElement(tag);
  for (const [k, v] of Object.entries(atributos)) {
    if (v === undefined || v === null || v === false) continue;
    if (k === "texto") nodo.textContent = v;
    else if (k.startsWith("on")) nodo.addEventListener(k.slice(2), v);
    else nodo.setAttribute(k, v);
  }
  for (const h of hijos) if (h !== null && h !== undefined) nodo.append(h);
  return nodo;
}

function tabla(cabeceras, filas) {
  return el("table", {},
    el("thead", {}, el("tr", {}, ...cabeceras.map(([t, num]) => el("th", { class: num ? "num" : null, scope: "col", texto: t })))),
    el("tbody", {}, ...filas.map((f) => el("tr", {}, ...f.map((c, i) => el("td", { class: cabeceras[i][1] ? "num" : null, texto: c }))))));
}

// Las vistas se redibujan al cambiar el tamaño, el tema o el distrito elegido
const dibujos = [];
const registrar = (fn) => { dibujos.push(fn); fn(); };
const redibujar = () => dibujos.forEach((fn) => fn());
// Solo el ancho importa: redibujar cambia la altura de la página y no debe volver a disparar el observador
let pendiente = null, anchoAnterior = 0;
new ResizeObserver(([entrada]) => {
  const ancho = Math.round(entrada.contentRect.width);
  if (ancho === anchoAnterior) return;
  anchoAnterior = ancho;
  cancelAnimationFrame(pendiente);
  pendiente = requestAnimationFrame(redibujar);
}).observe(document.body);
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", redibujar);

// ------------------------------------------------------------------------------- fuentes a un clic
let D; // todos los datos cargados

const TIPOS = {
  observada: "observada",
  calculada: "calculada a partir de la fuente",
  derivada: "derivada: no la publica la fuente",
};

// Etiqueta de fuente: ID, vigencia y fecha de prueba (y si la cifra no es observada). El resto, a un clic.
function chip(id, tipo = "observada") {
  const ficha = D.fichas[id];
  const archivo = Object.values(LAGO()).find((a) => a.fuente === id);
  const entidad = D.listas.entidades[ficha.entidad].nombre.split(" (")[0];
  return el("button", { class: "chip", type: "button", onclick: () => abrirFicha(id),
    "aria-label": `Fuente ${id}, ${entidad}. Cifra ${TIPOS[tipo]}. Abrir la ficha` },
    el("strong", { texto: `Fuente ${id}` }),
    archivo ? ` · vigente a ${fFecha(archivo.vigencia)} · probado ${fFecha(archivo.probado)}` : "",
    tipo === "observada" ? "" : ` · ${TIPOS[tipo]}`);
}

function lineaFuentes(contenedor, ...chips) {
  document.getElementById(contenedor).replaceChildren(...chips);
}

function abrirFicha(id) {
  const f = D.fichas[id];
  const licencia = D.listas.licencias[f.licencia];
  const archivo = Object.values(LAGO()).find((a) => a.fuente === id);
  const filas = [
    ["Publica", D.listas.entidades[f.entidad].nombre],
    ["Estado", D.listas.estados[f.estado].excel],
    ["Licencia", licencia.url ? el("a", { href: licencia.url, rel: "noopener", target: "_blank", texto: licencia.nombre }) : licencia.nombre],
    ["Licencia, tal como aparece", f.licencia_texto || "—"],
    ["Dónde la leímos", f.licencia_donde],
    ["Datos de personas", D.listas.personas[f.personas].excel],
    ["Cobertura", f.cobertura || "—"],
    ["Periodo", f.periodo || "—"],
    ["Vigencia en el lago", archivo ? fFecha(archivo.vigencia) : "—"],
    ["Probado", fFecha(f.probado)],
    ["Respuesta", f.respuesta],
    ["URL exacta", el("a", { href: f.url, rel: "noopener", target: "_blank", texto: f.url })],
    ["Script", f.script || "No entra al lago"],
    ["Archivo del lago", f.salida.join(", ") || "—"],
    ["Nota", f.nota],
  ];
  document.getElementById("ficha-contenido").replaceChildren(
    el("h2", { id: "ficha-titulo", texto: `${f.id} · ${f.nombre}` }),
    el("dl", {}, ...filas.flatMap(([t, v]) => [el("dt", { texto: t }), el("dd", {}, v)])),
    el("p", { class: "nota" }, "Ficha completa en el repositorio: ",
      el("a", { href: `https://github.com/davidfra2/Proyecto_Gobernanza/blob/main/catalogo/${D.archivos[f.id]}`, rel: "noopener", target: "_blank", texto: `catalogo/${D.archivos[f.id]}` })),
  );
  document.getElementById("dialogo-ficha").showModal();
}

// ------------------------------------------------------------------------------------- modelo
const LAGO = () => ({ pob: D.pob, des: D.des, geo: D.geo, cli: D.cli, esc: D.esc });
const estado = { distrito: null, indicador: "densidad", tresD: false };

function prepararModelo() {
  const nombres = Object.fromEntries(D.geo.features.map((f) => [f.properties.sb_codigo, f.properties.sb_nombre]));
  const codigos = Object.keys(nombres).sort();
  const pob = {}, des = {};
  for (const r of D.pob.registros) (pob[r.sb_codigo] ??= {})[r.anio] = r;
  for (const r of D.des.registros) (des[r.sb_codigo] ??= {})[r.anio] = r;
  const aniosPob = [...new Set(D.pob.registros.map((r) => r.anio))].sort();
  const aniosDes = [...new Set(D.des.registros.map((r) => r.anio))].sort();
  // 08 Schwanthalerhöhe: la fuente reserva su población («X»). Se deduce restando del total de la
  // ciudad los otros 24 distritos; se muestra siempre marcada como derivada, nunca como observada.
  const deducida = (anio) => {
    const otros = codigos.filter((c) => c !== "08").map((c) => pob[c][anio].poblacion);
    return otros.includes(null) ? null : pob["00"][anio].poblacion - otros.reduce((a, b) => a + b, 0);
  };
  const poblacion = (c, anio) => pob[c][anio].poblacion ?? (c === "08" ? deducida(anio) : null);
  const esDerivada = (c, anio) => pob[c][anio].poblacion === null && c === "08";
  return { nombres, codigos, pob, des, aniosPob, aniosDes, poblacion, esDerivada };
}

// -------------------------------------------------------------------------------------- vistas
function vistaKpis(M) {
  const [a0, a1] = [M.aniosPob[0], M.aniosPob.at(-1)];
  const p1 = M.pob["00"][a1].poblacion, p0 = M.pob["00"][a0].poblacion;
  const aD = M.aniosDes.at(-1);
  const ultimoClima = D.cli.registros.at(-1);
  const ultimaVista = D.esc.registros.at(-1);
  const tarjeta = (etiqueta, valor, detalle, ...chips) =>
    el("div", { class: "kpi" }, el("p", { class: "kpi-etiqueta", texto: etiqueta }), el("p", { class: "kpi-valor", texto: valor }),
      el("p", { class: "kpi-detalle", texto: detalle }), el("div", { class: "fuentes-linea" }, ...chips));
  document.getElementById("kpis").replaceChildren(
    tarjeta(`Habitantes en ${a1}`, fNum(p1), `${fSigno((p1 / p0 - 1) * 100)} desde ${a0}`, chip("F01")),
    tarjeta(`Desempleo en ${aD}`, fPct(M.des["00"][aD].desempleo_pct), `Desempleados sobre la población de 15 a 64 años`, chip("F02")),
    tarjeta(`Temperatura media, ${fFecha(ultimoClima.mes)}`, fGrados(ultimoClima.temp_media_c),
      ultimoClima.nivel_calidad === 10 ? "Dato con control de calidad terminado" : "Provisional: el DWD todavía puede corregirlo", chip("F04")),
    tarjeta(`Vistas en Wikipedia, ${fFecha(ultimaVista.mes)}`, fNum(ultimaVista.vistas), "Artículo «München» en alemán, solo personas", chip("F05")),
  );
}

function vistaSelector(M) {
  const selector = document.getElementById("selector-distrito");
  selector.replaceChildren(el("option", { value: "", texto: "Toda la ciudad" }),
    ...M.codigos.map((c) => el("option", { value: c, texto: `${c} · ${M.nombres[c]}` })));
  selector.addEventListener("change", () => elegir(selector.value || null));
}

const INDICADORES = {
  densidad: { nombre: "Densidad", fuente: "F01", valor: (M, c) => M.pob[c][M.aniosPob.at(-1)].densidad_hab_km2, formato: (v) => `${fNum(v)} hab/km²`, corto: fNum, titulo: (M) => `Habitantes por km², ${M.aniosPob.at(-1)}` },
  poblacion: { nombre: "Habitantes", fuente: "F01", valor: (M, c) => M.pob[c][M.aniosPob.at(-1)].poblacion, formato: fNum, corto: fCompacto, titulo: (M) => `Habitantes, ${M.aniosPob.at(-1)}` },
  desempleo: { nombre: "Desempleo", fuente: "F02", valor: (M, c) => M.des[c][M.aniosDes.at(-1)].desempleo_pct, formato: fPct, corto: fPct, titulo: (M) => `Desempleo, ${M.aniosDes.at(-1)}` },
};

// Clases por cuantiles: cinco grupos de cinco distritos
function clases(valores) {
  const orden = valores.filter((v) => v !== null).sort((a, b) => a - b);
  return [1, 2, 3, 4].map((k) => orden[Math.round((k * orden.length) / 5) - 1]);
}
const claseDe = (v, cortes) => (v === null ? null : cortes.filter((c) => v > c).length);

let mapa = null;
const ALTURA_MAXIMA = 2500; // metros del prisma más alto en la vista 3D (solo escala visual)
function vistaMapa(M) {
  const opciones = document.getElementById("selector-indicador");
  opciones.replaceChildren(...Object.entries(INDICADORES).map(([k, ind]) =>
    el("button", { type: "button", class: "opcion", role: "radio", "aria-checked": String(k === estado.indicador), texto: ind.nombre,
      onclick: () => { estado.indicador = k; redibujar(); } })));
  // Vista 3D: botón aparte del indicador (no es otra cifra, es otra forma de mirar la misma)
  const boton3D = el("button", { type: "button", class: "opcion opcion-3d", "aria-pressed": "false", texto: "Vista 3D",
    onclick: () => { estado.tresD = !estado.tresD; aplicar3D(true); redibujar(); } });
  opciones.after(boton3D);

  const pintar = () => {
    const ind = INDICADORES[estado.indicador];
    for (const b of opciones.children) b.setAttribute("aria-checked", String(b.textContent === ind.nombre));
    boton3D.setAttribute("aria-pressed", String(estado.tresD));
    const valores = Object.fromEntries(M.codigos.map((c) => [c, ind.valor(M, c)]));
    const cortes = clases(Object.values(valores));
    const rampa = [1, 2, 3, 4, 5].map((i) => color(`mapa-${i}`));
    const maximo = Math.max(...Object.values(valores).filter((v) => v !== null));
    const geo = structuredClone(D.geo);
    for (const f of geo.features) {
      const v = valores[f.properties.sb_codigo];
      const k = claseDe(v, cortes);
      f.properties.relleno = k === null ? color("sin-dato") : rampa[k];
      // En 3D la altura repite el mismo valor que el color, en proporción al máximo (sin dato: a ras de suelo)
      f.properties.altura = v === null ? 0 : (v / maximo) * ALTURA_MAXIMA;
    }
    if (mapa?.getSource("distritos")) {
      mapa.getSource("distritos").setData(geo);
      mapa.setFilter("distritos-elegido", ["==", ["get", "sb_codigo"], estado.distrito ?? ""]);
    }
    // leyenda y tabla
    const limites = [Math.min(...Object.values(valores).filter((v) => v !== null)), ...cortes, Math.max(...Object.values(valores).filter((v) => v !== null))];
    const leyenda = document.getElementById("leyenda-mapa");
    // Barra continua de cinco quintiles: los cortes van entre las muestras, la unidad solo en el título
    leyenda.replaceChildren(el("strong", { class: "leyenda-titulo", texto: `${ind.titulo(M)} · cinco grupos de cinco distritos` }),
      el("div", { class: "leyenda-rampa", role: "img", "aria-label": `Cortes: ${limites.map(ind.corto).join(", ")}` },
        ...rampa.map((c) => el("span", { style: `background:${c}` }))),
      el("div", { class: "leyenda-cortes", "aria-hidden": "true" }, ...limites.map((v) => el("span", { texto: ind.corto(v) }))));
    if (Object.values(valores).includes(null)) {
      leyenda.append(el("span", { class: "leyenda-item" }, el("span", { class: "leyenda-muestra", style: `background:${color("sin-dato")}` }), "Sin dato publicado"));
    }
    if (estado.tresD) {
      leyenda.append(el("p", { class: "leyenda-nota", texto:
        `Vista 3D: la altura de cada distrito repite su valor (el más alto, ${ind.corto(maximo)}, mide lo mismo en todos los indicadores). ` +
        "La perspectiva deforma las alturas: para comparar distritos, usa las barras o «Ver tabla». " +
        "Al acercarte aparecen los edificios en 3D, con datos de © OpenStreetMap (ODbL) vía OpenFreeMap: son contexto visual y alturas aproximadas, no cifras de este sistema." }));
    }
    lineaFuentes("fuente-mapa", chip(ind.fuente), chip("F03"));
    document.getElementById("tabla-mapa").replaceChildren(tabla([["Código"], ["Distrito"], [ind.titulo(M), true]],
      M.codigos.map((c) => [c, M.nombres[c], valores[c] === null ? "sin dato publicado" : ind.formato(valores[c])])));
    return geo;
  };

  const geoInicial = pintar();
  registrar(pintar);
  if (!window.maplibregl) {
    document.getElementById("mapa").replaceChildren(el("p", { class: "aviso", texto: "No se pudo cargar la librería del mapa. Los datos siguen en la tabla de abajo." }));
    return;
  }
  // Mapa base sin llave (OpenFreeMap): claro u oscuro según el tema. Si no responde, fondo liso.
  const estilos = {};
  const estiloPara = (oscuro) => (estilos[oscuro] ??= fetch(`https://tiles.openfreemap.org/styles/${oscuro ? "dark" : "positron"}`)
    .then((r) => (r.ok ? r.json() : Promise.reject()))
    .catch(() => ({ version: 8, sources: {}, layers: [{ id: "fondo", type: "background", paint: { "background-color": color("sin-dato") } }] })));
  const etiquetas = { type: "FeatureCollection", features: D.geo.features.map((f) => ({
    type: "Feature", properties: { sb_codigo: f.properties.sb_codigo }, geometry: { type: "Point", coordinates: puntoEtiqueta(f.geometry) } })) };

  // Las capas se vuelven a poner cada vez que cambia el estilo (tema claro ↔ oscuro)
  const agregarCapas = (estilo) => {
    if (mapa.getSource("distritos")) return;
    mapa.addSource("distritos", { type: "geojson", data: geoInicial });
    mapa.addSource("etiquetas", { type: "geojson", data: etiquetas });
    mapa.addLayer({ id: "distritos-relleno", type: "fill", source: "distritos", paint: { "fill-color": ["get", "relleno"], "fill-opacity": 0.86 } });
    // 2 px del color de la superficie entre distritos vecinos: separa sin dibujar una línea más
    mapa.addLayer({ id: "distritos-borde", type: "line", source: "distritos", paint: { "line-color": color("superficie"), "line-width": 1.5 } });
    mapa.addLayer({ id: "distritos-elegido", type: "line", source: "distritos", filter: ["==", ["get", "sb_codigo"], estado.distrito ?? ""], paint: { "line-color": color("texto"), "line-width": 3 } });
    // 3D a escala de ciudad: un prisma por distrito, del mismo color, que se desvanece al acercarse
    mapa.addLayer({ id: "distritos-3d", type: "fill-extrusion", source: "distritos", layout: { visibility: "none" },
      paint: { "fill-extrusion-color": ["get", "relleno"], "fill-extrusion-height": ["get", "altura"], "fill-extrusion-base": 0,
        "fill-extrusion-opacity": ["interpolate", ["linear"], ["zoom"], 11.5, 0.88, 13, 0] } });
    // 3D de cerca: los edificios del mapa base (OpenStreetMap vía OpenFreeMap), con su altura aproximada
    if (estilo.sources?.openmaptiles) {
      mapa.addLayer({ id: "edificios-3d", type: "fill-extrusion", source: "openmaptiles", "source-layer": "building", minzoom: 12.5,
        filter: ["!=", ["get", "hide_3d"], true], layout: { visibility: "none" },
        paint: { "fill-extrusion-color": color("eje"), "fill-extrusion-height": ["coalesce", ["get", "render_height"], 0],
          "fill-extrusion-base": ["coalesce", ["get", "render_min_height"], 0],
          "fill-extrusion-opacity": ["interpolate", ["linear"], ["zoom"], 12.5, 0, 13.5, 0.9] } });
    }
    if (estilo.glyphs) {
      mapa.addLayer({ id: "distritos-codigo", type: "symbol", source: "etiquetas",
        layout: { "text-field": ["get", "sb_codigo"], "text-size": ["interpolate", ["linear"], ["zoom"], 9, 9, 10.5, 11, 12, 13], "text-font": ["Noto Sans Bold"], "text-allow-overlap": true },
        paint: { "text-color": color("texto"), "text-halo-color": color("superficie"), "text-halo-width": 1.6 } });
    }
    pintar();
    aplicar3D(false);
  };

  // Enciende o apaga la vista 3D: cambia qué capas se ven y la inclinación de la cámara
  const aplicar3D = (animar) => {
    if (!mapa?.getLayer("distritos-3d")) return;
    const ver = (capa, visible) => mapa.getLayer(capa) && mapa.setLayoutProperty(capa, "visibility", visible ? "visible" : "none");
    ver("distritos-3d", estado.tresD);
    ver("edificios-3d", estado.tresD);
    ver("distritos-relleno", !estado.tresD);
    ver("building", !estado.tresD); // los edificios planos del mapa base, que en 3D quedarían debajo
    const quieto = !animar || matchMedia("(prefers-reduced-motion: reduce)").matches;
    const camara = estado.tresD ? { pitch: 58, bearing: -18 } : { pitch: 0, bearing: 0 };
    if (mapa.getPitch() !== camara.pitch) quieto ? mapa.jumpTo(camara) : mapa.easeTo({ ...camara, duration: 900 });
  };

  let oscuro = temaOscuro();
  estiloPara(oscuro).then((estilo) => {
    mapa = new maplibregl.Map({ container: "mapa", style: estilo, center: [11.55, 48.14], zoom: 10, attributionControl: { compact: true }, cooperativeGestures: true });
    // Brújula con inclinación: en 3D sirve para ver hacia dónde mira la cámara y volver al norte
    mapa.addControl(new maplibregl.NavigationControl({ showCompass: true, visualizePitch: true }));
    mapa.on("style.load", () => estiloPara(oscuro).then(agregarCapas));
    mapa.once("load", () => {
      const caja = D.geo.features.flatMap((f) => f.geometry.coordinates.flat(2));
      mapa.fitBounds([[Math.min(...caja.map((q) => q[0])), Math.min(...caja.map((q) => q[1]))], [Math.max(...caja.map((q) => q[0])), Math.max(...caja.map((q) => q[1]))]], { padding: 16, duration: 0 });
    });
    for (const capa of ["distritos-relleno", "distritos-3d"]) {
      mapa.on("click", capa, (e) => elegir(e.features[0].properties.sb_codigo));
      mapa.on("mouseenter", capa, () => { mapa.getCanvas().style.cursor = "pointer"; });
      mapa.on("mouseleave", capa, () => { mapa.getCanvas().style.cursor = ""; });
    }
    registrar(() => {
      if (temaOscuro() === oscuro) return;
      oscuro = temaOscuro();
      estiloPara(oscuro).then((nuevo) => mapa.setStyle(nuevo, { diff: false }));
    });
  });
}

function temaOscuro() {
  const tema = document.documentElement.dataset.theme;
  return tema ? tema === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
}

// Un solo punto de etiqueta por distrito: el punto más interior (más lejos del borde) de su parte
// más grande. El 18 y el 19 traen un pedazo mínimo además del principal, y MapLibre pondría una
// etiqueta en cada pedazo; el centroide, en un distrito cóncavo, puede caer en el vecino.
function puntoEtiqueta(geometria) {
  const partes = geometria.type === "Polygon" ? [geometria.coordinates] : geometria.coordinates;
  const area = (anillo) => Math.abs(anillo.reduce((a, [x1, y1], i) => { const [x2, y2] = anillo[(i + 1) % anillo.length]; return a + x1 * y2 - x2 * y1; }, 0)) / 2;
  const parte = partes.reduce((a, b) => (area(b[0]) > area(a[0]) ? b : a));
  const kx = Math.cos((48.14 * Math.PI) / 180); // a esta latitud un grado de longitud mide menos
  const dentro = ([x, y], anillo) => {
    let si = false;
    for (let i = 0, j = anillo.length - 1; i < anillo.length; j = i++) {
      const [xi, yi] = anillo[i], [xj, yj] = anillo[j];
      if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) si = !si;
    }
    return si;
  };
  const distanciaBorde = ([x, y]) => Math.min(...parte.flatMap((anillo) => anillo.slice(1).map(([x2, y2], i) => {
    const [x1, y1] = anillo[i];
    const dx = (x2 - x1) * kx, dy = y2 - y1, px = (x - x1) * kx, py = y - y1;
    const t = Math.max(0, Math.min(1, (px * dx + py * dy) / (dx * dx + dy * dy || 1)));
    return Math.hypot(px - t * dx, py - t * dy);
  })));
  const xs = parte[0].map((q) => q[0]), ys = parte[0].map((q) => q[1]);
  const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
  let mejor = parte[0][0], mejorD = -1;
  const N = 28;
  for (let i = 1; i < N; i++) for (let j = 1; j < N; j++) {
    const q = [x0 + ((x1 - x0) * i) / N, y0 + ((y1 - y0) * j) / N];
    if (!dentro(q, parte[0]) || parte.slice(1).some((hueco) => dentro(q, hueco))) continue;
    const d = distanciaBorde(q);
    if (d > mejorD) { mejorD = d; mejor = q; }
  }
  return mejor;
}

function vistaPanel(M) {
  registrar(() => {
    const panel = document.getElementById("panel-distrito");
    const c = estado.distrito ?? "00";
    const [a0, a1] = [M.aniosPob[0], M.aniosPob.at(-1)];
    const aD0 = M.aniosDes[0], aD = M.aniosDes.at(-1);
    const r = M.pob[c][a1];
    const titulo = c === "00" ? "Toda la ciudad" : `${c} · ${M.nombres[c]}`;
    const filas = [];
    const p1 = M.poblacion(c, a1), p0 = M.poblacion(c, a0);
    const derivada = M.esDerivada(c, a1);
    filas.push([`Habitantes ${a1}`, p1 === null ? "sin dato" : `${fNum(p1)}${derivada ? "*" : ""}`]);
    filas.push([`Crecimiento ${a0}–${a1}`, p1 && p0 ? `${fSigno((p1 / p0 - 1) * 100)}${derivada ? "*" : ""}` : "sin dato"]);
    filas.push([`Densidad ${a1}`, `${fNum(r.densidad_hab_km2)} hab/km²`]);
    const area = c === "00" ? r.area_km2 : D.geo.features.find((f) => f.properties.sb_codigo === c).properties.area_km2;
    filas.push(["Superficie", `${decimal1.format(area)} km²`]);
    filas.push([`Desempleo ${aD}`, fPct(M.des[c][aD].desempleo_pct)]);
    const cambio = M.des[c][aD].desempleo_pct - M.des[c][aD0].desempleo_pct;
    filas.push([`Cambio desde ${aD0}`, `${cambio > 0 ? "+" : cambio < 0 ? "−" : ""}${decimal1.format(Math.abs(cambio))} puntos`]);
    const lista = el("dl", {}, ...filas.flatMap(([t, v]) => [el("dt", { texto: t }), el("dd", { texto: v })]));
    if (derivada) {
      lista.append(el("p", { class: "derivado", texto: `* Derivado. La fuente reserva la población de este distrito («X»). Se calcula como el total de la ciudad menos los otros 24 distritos; cuadra con su densidad publicada y con su superficie oficial en todos los años. La superficie sale del mapa oficial (F03).` }));
    }
    const chips = [chip("F01", derivada ? "derivada" : "observada"), chip("F02"), ...(c === "00" ? [] : [chip("F03")])];
    panel.replaceChildren(el("h3", { texto: titulo }), lista, el("div", { class: "fuentes-linea" }, ...chips));
  });
}

function vistaPoblacion(M) {
  const [a0, a1] = [M.aniosPob[0], M.aniosPob.at(-1)];
  registrar(() => {
    const filas = M.codigos.map((c) => ({
      clave: c, etiqueta: `${c} ${M.nombres[c]}`,
      valor: (M.poblacion(c, a1) / M.poblacion(c, a0) - 1) * 100, derivado: M.esDerivada(c, a1),
    })).sort((a, b) => b.valor - a.valor);
    barrasH(document.getElementById("g-crecimiento"), { filas, formato: fSigno, divergente: true, resaltado: estado.distrito,
      alSeleccionar: elegir, descripcion: `Crecimiento de la población por distrito entre ${a0} y ${a1}` });
    const series = [{ nombre: "Ciudad", valores: M.aniosPob.map((a) => (M.poblacion("00", a) / M.poblacion("00", a0)) * 100), color: color(estado.distrito ? "ciudad" : "serie-1"), enfasis: !estado.distrito }];
    if (estado.distrito) {
      const c = estado.distrito;
      series.push({ nombre: M.nombres[c].split("-")[0], valores: M.aniosPob.map((a) => (M.poblacion(c, a) / M.poblacion(c, a0)) * 100), color: color("serie-1"), enfasis: true });
    }
    document.getElementById("t-indice").textContent = estado.distrito ? `Población de ${M.nombres[estado.distrito]} frente a la ciudad, índice ${a0} = 100` : `Población de la ciudad, índice ${a0} = 100`;
    lineas(document.getElementById("g-indice"), { x: M.aniosPob, series, formatoY: (v) => decimal1.format(v), descripcion: "Población indexada" });
    const derivada = estado.distrito && M.esDerivada(estado.distrito, a1);
    lineaFuentes("fuente-crecimiento", chip("F01", "calculada"));
    lineaFuentes("fuente-indice", chip("F01", derivada ? "derivada" : "calculada"));
    document.getElementById("tabla-poblacion").replaceChildren(tabla([["Código"], ["Distrito"], [`Habitantes ${a0}`, true], [`Habitantes ${a1}`, true], ["Crecimiento", true]],
      ["00", ...M.codigos].map((c) => [c, c === "00" ? "Toda la ciudad" : M.nombres[c],
        `${fNum(M.poblacion(c, a0))}${M.esDerivada(c, a0) ? "*" : ""}`, `${fNum(M.poblacion(c, a1))}${M.esDerivada(c, a1) ? "*" : ""}`,
        fSigno((M.poblacion(c, a1) / M.poblacion(c, a0) - 1) * 100)])));
  });
}

function vistaDesempleo(M) {
  const aD = M.aniosDes.at(-1);
  registrar(() => {
    document.getElementById("t-desempleo-barras").textContent = `Desempleo por distrito, ${aD}`;
    const filas = M.codigos.map((c) => ({ clave: c, etiqueta: `${c} ${M.nombres[c]}`, valor: M.des[c][aD].desempleo_pct }))
      .sort((a, b) => b.valor - a.valor);
    barrasH(document.getElementById("g-desempleo"), { filas, formato: fPct, resaltado: estado.distrito, alSeleccionar: elegir,
      descripcion: `Desempleo por distrito en ${aD}` });
    const series = [{ nombre: "Ciudad", valores: M.aniosDes.map((a) => M.des["00"][a].desempleo_pct), color: color(estado.distrito ? "ciudad" : "serie-1"), enfasis: !estado.distrito }];
    if (estado.distrito) {
      series.push({ nombre: M.nombres[estado.distrito].split("-")[0], valores: M.aniosDes.map((a) => M.des[estado.distrito][a].desempleo_pct), color: color("serie-1"), enfasis: true });
    }
    lineas(document.getElementById("g-desempleo-serie"), { x: M.aniosDes, series, formatoY: fPct, descripcion: "Desempleo por año" });
    lineaFuentes("fuente-desempleo", chip("F02"));
    lineaFuentes("fuente-desempleo-serie", chip("F02"));
    document.getElementById("tabla-desempleo").replaceChildren(tabla([["Código"], ["Distrito"], ...M.aniosDes.map((a) => [String(a), true])],
      ["00", ...M.codigos].map((c) => [c, c === "00" ? "Toda la ciudad" : M.nombres[c], ...M.aniosDes.map((a) => fPct(M.des[c][a].desempleo_pct))])));
  });
}

function vistaClima() {
  const r = D.cli.registros;
  const x = r.map((m) => m.mes);
  const provisionales = r.map((m) => m.nivel_calidad === 1 || m.nivel_calidad === 3);
  registrar(() => {
    bandaTemperatura(document.getElementById("g-temperatura"), {
      x, minimas: r.map((m) => m.temp_min_media_c), medias: r.map((m) => m.temp_media_c), maximas: r.map((m) => m.temp_max_media_c),
      provisionales, formato: (v) => `${decimal1.format(v)}°`, formatoX: fMes, descripcion: "Temperatura mensual en München",
    });
    const lluvia = r.map((m) => m.precipitacion_mm);
    const maxIdx = lluvia.indexOf(Math.max(...lluvia.filter((v) => v !== null)));
    columnas(document.getElementById("g-lluvia"), {
      x, valores: lluvia, formato: fMm, formatoX: fMes, etiquetar: [maxIdx], marcados: provisionales.flatMap((p, i) => (p ? [i] : [])),
      notaMarcado: "provisional", descripcion: "Lluvia mensual en München",
    });
  });
  const calidad = { 1: "Solo control formal (provisional)", 3: "Control automático (provisional)", 9: "No todos los parámetros corregidos", 10: "Control terminado" };
  lineaFuentes("fuente-clima", chip("F04"));
  document.getElementById("tabla-clima").replaceChildren(tabla([["Mes"], ["Mínima media", true], ["Media", true], ["Máxima media", true], ["Lluvia", true], ["Sol", true], ["Calidad"]],
    r.map((m) => [fFecha(m.mes), ...[m.temp_min_media_c, m.temp_media_c, m.temp_max_media_c].map((v) => (v === null ? "sin dato" : fGrados(v))),
      m.precipitacion_mm === null ? "sin dato" : fMm(m.precipitacion_mm), m.sol_horas === null ? "sin dato" : `${fNum(m.sol_horas)} h`, calidad[m.nivel_calidad] ?? String(m.nivel_calidad)])));
}

function vistaInteres() {
  const r = D.esc.registros;
  registrar(() => {
    const valores = r.map((m) => m.vistas);
    const maxIdx = valores.indexOf(Math.max(...valores));
    columnas(document.getElementById("g-vistas"), { x: r.map((m) => m.mes), valores, formato: fCompacto, formatoX: fMes,
      etiquetar: [maxIdx, valores.length - 1], descripcion: "Vistas mensuales del artículo München en Wikipedia" });
  });
  lineaFuentes("fuente-vistas", chip("F05"));
  document.getElementById("tabla-vistas").replaceChildren(tabla([["Mes"], ["Vistas", true]], r.map((m) => [fFecha(m.mes), fNum(m.vistas)])));
}

function vistaFuentes() {
  const fichas = Object.values(D.fichas).sort((a, b) => a.id.localeCompare(b.id));
  document.getElementById("n-fuentes").textContent = fichas.length;
  document.getElementById("n-integradas").textContent = fichas.filter((f) => f.estado === "integrado").length;
  const probado = Object.values(LAGO()).map((d) => d.probado).sort()[0];
  document.getElementById("meta-sistema").textContent =
    `${fichas.filter((f) => f.estado === "integrado").length} de ${fichas.length} fuentes integradas · lago probado el ${fFecha(probado)} · protección: abierto, solo agregados`;
  document.getElementById("lista-fuentes").replaceChildren(...fichas.map((f) => el("article", { class: "ficha" },
    el("h3", { texto: `${f.id} · ${f.nombre}` }),
    el("span", { class: "estado", texto: D.listas.estados[f.estado].excel }),
    el("p", { texto: D.listas.entidades[f.entidad].nombre }),
    el("p", { texto: `Licencia: ${D.listas.licencias[f.licencia].nombre}` }),
    el("p", { texto: `Probado: ${fFecha(f.probado)} · ${f.respuesta}` }),
    el("button", { class: "chip", type: "button", onclick: () => abrirFicha(f.id), texto: "Ver la ficha completa" }))));
  document.getElementById("glosario").replaceChildren(tabla([["Término"], ["Tipo"], ["Qué es"], ["Cómo se obtiene"], ["Campos del lago"], ["Fuentes"]],
    D.glosario.map((t) => [t.termino, t.tipo.replace("_", " "), t.definicion, t.formula ?? "La publica la fuente",
      t.campos.map((c) => c.split(":")[1]).filter((c, i, a) => a.indexOf(c) === i).join(", "), t.fuentes.join(", ")])));
  document.getElementById("dependencias").replaceChildren(tabla([["Servicio"], ["Para qué"], ["Licencia"], ["Qué recibe de quien visita"], ["Si falla"]],
    D.dependencias.map((d) => [`${d.nombre}${d.version ? ` (${d.version})` : ""}`, d.uso, d.licencia, d.recibe, d.si_falla])));
}

// ------------------------------------------------------------------- respuestas escritas
// Ninguna cifra de estas frases está escrita a mano: todas se calculan desde el lago al cargar,
// para que un lago nuevo no deje la prosa diciendo otra cosa que los gráficos.
function respuesta(id, ...partes) {
  const chips = partes.filter((p) => p instanceof HTMLElement && p.classList.contains("chip"));
  const textos = partes.filter((p) => !chips.includes(p));
  document.getElementById(id).replaceChildren(...textos.map((t) => el("p", { texto: t })), el("div", { class: "fuentes-linea" }, ...chips));
}

function vistaRespuestas(M) {
  const [a0, a1] = [M.aniosPob[0], M.aniosPob.at(-1)];
  const crec = M.codigos.map((c) => ({ c, v: (M.poblacion(c, a1) / M.poblacion(c, a0) - 1) * 100, d: M.esDerivada(c, a1) }))
    .sort((a, b) => b.v - a.v);
  const mayor = M.codigos.filter((c) => !M.esDerivada(c, a1)).sort((a, b) => M.poblacion(b, a1) - M.poblacion(a, a1))[0];
  const pierden = crec.filter((x) => x.v < 0);
  const nombre = (c) => `${c} ${M.nombres[c]}`;
  respuesta("r-p1",
    `En ${a1} vivían ${fNum(M.poblacion("00", a1))} personas en München, ${fSigno((M.poblacion("00", a1) / M.poblacion("00", a0) - 1) * 100)} que en ${a0}. El distrito más poblado es ${nombre(mayor)} (${fNum(M.poblacion(mayor, a1))}).`,
    `El que más creció fue ${nombre(crec[0].c)} (${fSigno(crec[0].v)}${crec[0].d ? "*" : ""}), seguido de ${nombre(crec[1].c)} (${fSigno(crec[1].v)}${crec[1].d ? "*" : ""}). ` +
      (pierden.length ? `${pierden.length === 1 ? "Un distrito perdió" : `${pierden.length} distritos perdieron`} población: ${pierden.map((x) => `${nombre(x.c)} (${fSigno(x.v)}${x.d ? "*" : ""})`).join(", ")}.` : "Ningún distrito perdió población."),
    ...(crec.some((x) => x.d) ? ["* 08 Schwanthalerhöhe: población derivada (total de la ciudad menos los otros 24 distritos), porque la fuente la reserva con «X»."] : []),
    chip("F01"), chip("F01", "calculada"), chip("F01", "derivada"));

  const aD0 = M.aniosDes[0], aD = M.aniosDes.at(-1);
  const des = M.codigos.map((c) => ({ c, v: M.des[c][aD].desempleo_pct })).sort((a, b) => b.v - a.v);
  const ciudad0 = M.des["00"][aD0].desempleo_pct, ciudad1 = M.des["00"][aD].desempleo_pct;
  const subieron = M.codigos.filter((c) => M.des[c][aD].desempleo_pct > M.des[c][aD0].desempleo_pct).length;
  respuesta("r-p2",
    `En ${aD} el desempleo pesa más en ${nombre(des[0].c)} (${fPct(des[0].v)}) y en ${nombre(des[1].c)} (${fPct(des[1].v)}), y menos en ${nombre(des.at(-1).c)} (${fPct(des.at(-1).v)}). En toda la ciudad fue de ${fPct(ciudad1)}.`,
    `Desde ${aD0} la ciudad pasó de ${fPct(ciudad0)} a ${fPct(ciudad1)}, y ${subieron} de los 25 distritos terminaron ${aD} más arriba que en ${aD0}.`,
    chip("F02"));

  const r = D.cli.registros.filter((m) => m.temp_media_c !== null);
  const calido = r.reduce((a, b) => (b.temp_media_c > a.temp_media_c ? b : a));
  const frio = r.reduce((a, b) => (b.temp_media_c < a.temp_media_c ? b : a));
  const ll = D.cli.registros.filter((m) => m.precipitacion_mm !== null);
  const lluvioso = ll.reduce((a, b) => (b.precipitacion_mm > a.precipitacion_mm ? b : a));
  const seco = ll.reduce((a, b) => (b.precipitacion_mm < a.precipitacion_mm ? b : a));
  const prov = D.cli.registros.filter((m) => m.nivel_calidad === 1 || m.nivel_calidad === 3).length;
  respuesta("r-p3",
    `Entre ${fFecha(D.cli.registros[0].mes)} y ${fFecha(D.cli.registros.at(-1).mes)} el mes más cálido fue ${fFecha(calido.mes)} (media de ${fGrados(calido.temp_media_c)}) y el más frío ${fFecha(frio.mes)} (${fGrados(frio.temp_media_c)}). El más lluvioso fue ${fFecha(lluvioso.mes)} (${fMm(lluvioso.precipitacion_mm)}) y el más seco ${fFecha(seco.mes)} (${fMm(seco.precipitacion_mm)}).`,
    `Respuesta parcial: es una sola estación para toda la ciudad, y ${prov} de los ${D.cli.registros.length} meses todavía son provisionales.`,
    chip("F04"));

  const v = D.esc.registros;
  const pico = v.reduce((a, b) => (b.vistas > a.vistas ? b : a));
  const valle = v.reduce((a, b) => (b.vistas < a.vistas ? b : a));
  respuesta("r-p4",
    `El artículo «München» de la Wikipedia en alemán tuvo su mes más leído en ${fFecha(pico.mes)} (${fNum(pico.vistas)} vistas) y el menos leído en ${fFecha(valle.mes)} (${fNum(valle.vistas)}).`,
    "Respuesta parcial: las vistas no dicen desde dónde se lee, así que no separan el interés de fuera del de quienes viven en la ciudad, y solo se integró la edición en alemán.",
    chip("F05"));

  const estados = [
    ["P1", "Respondida", "poblacion", ["F01", "F03"], "Población, densidad y crecimiento de los 25 distritos, 2015–2025. El 08 lleva su población derivada, marcada."],
    ["P2", "Respondida", "desempleo", ["F02", "F03"], "Desempleo de los 25 distritos, 2015–2024. Solo el total: sin cortes por sexo ni nacionalidad."],
    ["P3", "Parcial", "clima", ["F04"], "Mes a mes para la ciudad entera. No hay clima por distrito, y la carpeta reciente del DWD cubre unos 18 meses."],
    ["P4", "Parcial", "interes", ["F05"], "Vistas mensuales en de.wikipedia. No distingue de dónde viene quien lee."],
  ];
  document.getElementById("lista-preguntas").replaceChildren(...estados.map(([id, est, ancla, fuentes, texto]) =>
    el("article", { class: "pregunta" },
      el("span", { class: `estado${est === "Parcial" ? " parcial" : ""}`, texto: est }),
      el("h3", {}, el("a", { href: `#${ancla}`, texto: `${id} · ${D.listas.preguntas[id]}` })),
      el("p", { texto }),
      el("div", { class: "fuentes-linea" }, ...fuentes.map((f) => chip(f))))));
}

// ---------------------------------------------------------------------------------- arranque
function elegir(codigo) {
  estado.distrito = codigo && codigo !== "00" ? codigo : null;
  document.getElementById("selector-distrito").value = estado.distrito ?? "";
  redibujar();
}

async function iniciar() {
  const aviso = document.getElementById("estado-carga");
  try {
    D = await cargarTodo();
  } catch (error) {
    aviso.textContent = `No se pudo cargar el lago (${error.message}). Si abriste el archivo directamente, sírvelo con un servidor web: ver web/README.md.`;
    aviso.classList.add("error");
    return;
  }
  aviso.remove();
  const M = prepararModelo();
  vistaSelector(M);
  vistaKpis(M);
  vistaRespuestas(M);
  vistaMapa(M);
  vistaPanel(M);
  vistaPoblacion(M);
  vistaDesempleo(M);
  vistaClima();
  vistaInteres();
  vistaFuentes();
}

iniciar();
