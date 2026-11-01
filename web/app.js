import { cargarTodo } from "./datos.js";
import { barrasH, lineas, columnas, bandaTemperatura, color } from "./graficos.js";

// --------------------------------------------------------------------------------- utilidades
const numero = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 0 });
const decimal1 = new Intl.NumberFormat("es-CO", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const fNum = (v) => numero.format(v);
const fPct = (v) => `${decimal1.format(v)} %`;
const fSigno = (v) => `${v > 0 ? "+" : v < 0 ? "−" : ""}${decimal1.format(Math.abs(v))} %`;
const fGrados = (v) => `${decimal1.format(v)} °C`;
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
const estado = { distrito: null, indicador: "densidad" };

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
  densidad: { nombre: "Densidad", fuente: "F01", valor: (M, c) => M.pob[c][M.aniosPob.at(-1)].densidad_hab_km2, formato: (v) => `${fNum(v)} hab/km²`, titulo: (M) => `Habitantes por km², ${M.aniosPob.at(-1)}` },
  poblacion: { nombre: "Habitantes", fuente: "F01", valor: (M, c) => M.pob[c][M.aniosPob.at(-1)].poblacion, formato: fNum, titulo: (M) => `Habitantes, ${M.aniosPob.at(-1)}` },
  desempleo: { nombre: "Desempleo", fuente: "F02", valor: (M, c) => M.des[c][M.aniosDes.at(-1)].desempleo_pct, formato: fPct, titulo: (M) => `Desempleo, ${M.aniosDes.at(-1)}` },
};

// Clases por cuantiles: cinco grupos de cinco distritos
function clases(valores) {
  const orden = valores.filter((v) => v !== null).sort((a, b) => a - b);
  return [1, 2, 3, 4].map((k) => orden[Math.round((k * orden.length) / 5) - 1]);
}
const claseDe = (v, cortes) => (v === null ? null : cortes.filter((c) => v > c).length);

let mapa = null;
function vistaMapa(M) {
  const opciones = document.getElementById("selector-indicador");
  opciones.replaceChildren(...Object.entries(INDICADORES).map(([k, ind]) =>
    el("button", { type: "button", class: "opcion", role: "radio", "aria-checked": String(k === estado.indicador), texto: ind.nombre,
      onclick: () => { estado.indicador = k; redibujar(); } })));

  const pintar = () => {
    const ind = INDICADORES[estado.indicador];
    for (const b of opciones.children) b.setAttribute("aria-checked", String(b.textContent === ind.nombre));
    const valores = Object.fromEntries(M.codigos.map((c) => [c, ind.valor(M, c)]));
    const cortes = clases(Object.values(valores));
    const rampa = [1, 2, 3, 4, 5].map((i) => color(`mapa-${i}`));
    const geo = structuredClone(D.geo);
    for (const f of geo.features) {
      const k = claseDe(valores[f.properties.sb_codigo], cortes);
      f.properties.relleno = k === null ? color("sin-dato") : rampa[k];
    }
    if (mapa?.getSource("distritos")) {
      mapa.getSource("distritos").setData(geo);
      mapa.setFilter("distritos-elegido", ["==", ["get", "sb_codigo"], estado.distrito ?? ""]);
    }
    // leyenda y tabla
    const limites = [Math.min(...Object.values(valores).filter((v) => v !== null)), ...cortes, Math.max(...Object.values(valores).filter((v) => v !== null))];
    const leyenda = document.getElementById("leyenda-mapa");
    leyenda.replaceChildren(el("strong", { texto: ind.titulo(M) }), ...rampa.map((c, i) => el("span", { class: "leyenda-item" },
      el("span", { class: "leyenda-muestra", style: `background:${c}` }), `${ind.formato(limites[i])} – ${ind.formato(limites[i + 1])}`)));
    if (Object.values(valores).includes(null)) {
      leyenda.append(el("span", { class: "leyenda-item" }, el("span", { class: "leyenda-muestra", style: `background:${color("sin-dato")}` }), "Sin dato publicado"));
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
  // Mapa base sin llave (OpenFreeMap). Si no responde, el mapa sigue con un fondo liso.
  const estiloBase = fetch("https://tiles.openfreemap.org/styles/positron").then((r) => (r.ok ? r.json() : Promise.reject()))
    .catch(() => ({ version: 8, sources: {}, layers: [{ id: "fondo", type: "background", paint: { "background-color": "#efeee9" } }] }));
  estiloBase.then((estilo) => {
    mapa = new maplibregl.Map({ container: "mapa", style: estilo, center: [11.55, 48.14], zoom: 10, attributionControl: { compact: true }, cooperativeGestures: true });
    mapa.addControl(new maplibregl.NavigationControl({ showCompass: false }));
    mapa.on("load", () => {
      mapa.addSource("distritos", { type: "geojson", data: geoInicial });
      mapa.addLayer({ id: "distritos-relleno", type: "fill", source: "distritos", paint: { "fill-color": ["get", "relleno"], "fill-opacity": 0.82 } });
      mapa.addLayer({ id: "distritos-borde", type: "line", source: "distritos", paint: { "line-color": "#ffffff", "line-width": 1.2 } });
      mapa.addLayer({ id: "distritos-elegido", type: "line", source: "distritos", filter: ["==", ["get", "sb_codigo"], estado.distrito ?? ""], paint: { "line-color": "#0b0b0b", "line-width": 3 } });
      if (estilo.glyphs) {
        mapa.addLayer({ id: "distritos-codigo", type: "symbol", source: "distritos",
          layout: { "text-field": ["get", "sb_codigo"], "text-size": 12, "text-font": ["Noto Sans Regular"] },
          paint: { "text-color": "#0b0b0b", "text-halo-color": "#ffffff", "text-halo-width": 1.5 } });
      }
      const caja = D.geo.features.flatMap((f) => f.geometry.coordinates.flat(2));
      mapa.fitBounds([[Math.min(...caja.map((p) => p[0])), Math.min(...caja.map((p) => p[1]))], [Math.max(...caja.map((p) => p[0])), Math.max(...caja.map((p) => p[1]))]], { padding: 16, duration: 0 });
      pintar();
    });
    mapa.on("click", "distritos-relleno", (e) => elegir(e.features[0].properties.sb_codigo));
    mapa.on("mouseenter", "distritos-relleno", () => { mapa.getCanvas().style.cursor = "pointer"; });
    mapa.on("mouseleave", "distritos-relleno", () => { mapa.getCanvas().style.cursor = ""; });
  });
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
  document.getElementById("lista-fuentes").replaceChildren(...fichas.map((f) => el("article", { class: "ficha" },
    el("h3", { texto: `${f.id} · ${f.nombre}` }),
    el("span", { class: "estado", texto: D.listas.estados[f.estado].excel }),
    el("p", { texto: D.listas.entidades[f.entidad].nombre }),
    el("p", { texto: `Licencia: ${D.listas.licencias[f.licencia].nombre}` }),
    el("p", { texto: `Probado: ${fFecha(f.probado)} · ${f.respuesta}` }),
    el("button", { class: "chip", type: "button", onclick: () => abrirFicha(f.id), texto: "Ver la ficha completa" }))));
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
  vistaMapa(M);
  vistaPanel(M);
  vistaPoblacion(M);
  vistaDesempleo(M);
  vistaClima();
  vistaInteres();
  vistaFuentes();
}

iniciar();
