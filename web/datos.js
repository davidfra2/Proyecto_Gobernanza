// Capa de datos de las vistas: el ÚNICO lugar que sabe de dónde salen los datos.
//
// Hoy lee los archivos del lago directamente (lago/, territorio/, catalogo/), servidos junto a web/.
// Cuando exista la compuerta (api/), solo cambia `leer()`: el resto de las vistas no se toca.

const RAIZ = new URL("../", import.meta.url); // raíz del repositorio

async function leer(ruta) {
  const respuesta = await fetch(new URL(ruta, RAIZ), { cache: "no-cache" });
  if (!respuesta.ok) throw new Error(`${ruta}: HTTP ${respuesta.status}`);
  return respuesta.json();
}

export async function cargarTodo() {
  const [pob, des, geo, cli, esc, listas, indice] = await Promise.all([
    leer("lago/poblacion_stadtbezirke.json"),
    leer("lago/desempleo_stadtbezirke.json"),
    leer("territorio/stadtbezirke.geojson"),
    leer("lago/clima_muenchen_stadt.json"),
    leer("lago/escucha.json"),
    leer("catalogo/listas.json"),
    leer("catalogo/indice.json"),
  ]);
  const lista = await Promise.all(indice.fichas.map((f) => leer(`catalogo/${f}`)));
  const fichas = Object.fromEntries(lista.map((f) => [f.id, f]));
  const archivos = Object.fromEntries(lista.map((f, i) => [f.id, indice.fichas[i]])); // F01 → F01_….json
  return { pob, des, geo, cli, esc, listas, fichas, archivos };
}
