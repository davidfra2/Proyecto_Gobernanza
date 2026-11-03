"""Verificación del lago: con un solo fallo no se publica. Uso: python3 verificacion/verificar.py

Si algo falla, se arregla la ingesta; nunca se afloja el verificador.

Cada comprobación cubre una dimensión de calidad del DMBOK (cap. 13):
- completitud: no faltan distritos, años, campos ni fichas;
- validez: rangos, formatos de fecha y valores de las listas cerradas;
- consistencia: las cifras cuadran entre sí y entre fuentes (F01 ↔ F03, catálogo ↔ lago);
- unicidad: no hay registros repetidos;
- actualidad: «probado» es una fecha real, no posterior a hoy y de hace 60 días como mucho.
Además comprueba los metadatos: el lago coincide con catalogo/diccionario.json, cada archivo del
lago apunta a una ficha integrada de catalogo/, cada cifra del glosario sale de campos del diccionario,
y todo tercero que la CSP de las vistas deja cargar está en catalogo/dependencias.json.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CODIGOS = {f"{i:02d}" for i in range(0, 26)}  # 00 = ciudad, 01–25 = Stadtbezirke
FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MES = re.compile(r"^\d{4}-\d{2}$")
HOY = date.today().isoformat()
fallos: list[str] = []


def revisar(condicion: bool, mensaje: str) -> None:
    if not condicion:
        fallos.append(mensaje)


def presentes(r: dict, clave: str, campos: tuple[str, ...]) -> bool:
    """Un campo vacío es un fallo que se informa, no un error de Python que tumba la verificación."""
    vacios = [c for c in campos if r.get(c) is None]
    revisar(not vacios, f"{clave}: vacío en {', '.join(vacios)}")
    return not vacios


def sin_repetidos(registros: list[dict], campos: tuple[str, ...], etiqueta: str) -> None:
    repetidos = [k for k, n in Counter(tuple(r[c] for c in campos) for r in registros).items() if n > 1]
    revisar(not repetidos, f"{etiqueta}: registros repetidos {repetidos[:5]}")


def leer(ruta: str) -> dict:
    return json.loads((RAIZ / ruta).read_text(encoding="utf-8"))


def cargar(ruta: str) -> dict:
    datos = leer(ruta)
    for clave in ("fuente", "vigencia", "probado"):
        revisar(bool(datos.get(clave)), f"{ruta}: falta «{clave}»")
    revisar(bool(FECHA.match(str(datos.get("vigencia", "")))), f"{ruta}: vigencia no es AAAA-MM-DD")
    probado = str(datos.get("probado", ""))
    if FECHA.match(probado):
        revisar(probado <= HOY, f"{ruta}: probado ({probado}) es posterior a hoy")
    else:
        revisar(False, f"{ruta}: probado no es AAAA-MM-DD")
    return datos


# Estructura primero: el lago tiene exactamente los campos del diccionario, con su tipo y sus vacíos.
# Si la estructura falla, no tiene sentido comprobar rangos sobre tipos equivocados: se para aquí.
LAGO = {ruta: cargar(ruta) for ruta in (
    "lago/poblacion_stadtbezirke.json",
    "lago/desempleo_stadtbezirke.json",
    "territorio/stadtbezirke.geojson",
    "lago/clima_muenchen_stadt.json",
    "lago/escucha.json",
    "lago/transporte_paradas.json",
)}
pob, des, geo, cli, esc, tra = LAGO.values()
huerfanos = {
    str(p.relative_to(RAIZ)).replace("\\", "/")
    for p in [*(RAIZ / "lago").glob("*.json"), *(RAIZ / "territorio").glob("*.geojson")]
} - set(LAGO)
revisar(not huerfanos, f"lago: archivos que nadie verifica ni documenta {sorted(huerfanos)}")

listas = leer("catalogo/listas.json")
diccionario = leer("catalogo/diccionario.json")["campos"]
TIPOS = {"str": str, "int": int, "float": float, "bool": bool, "dict": dict}
ENVOLTURA = ("fuente", "vigencia", "probado")
for ruta, datos in LAGO.items():
    documentados = {c["campo"]: c for c in diccionario if c["archivo"] == ruta}
    if "features" in datos:
        filas = [dict(f["properties"], geometry=f["geometry"]) for f in datos["features"]]
    else:
        filas = datos["registros"]
    reales = set(ENVOLTURA) | {k for fila in filas for k in fila}
    revisar(not reales - set(documentados), f"{ruta}: campos sin documentar {sorted(reales - set(documentados))}")
    revisar(not set(documentados) - reales, f"{ruta}: documentados que no existen {sorted(set(documentados) - reales)}")
    for campo, doc in documentados.items():
        tipo = listas["tipos_dato"].get(doc["tipo"])
        revisar(tipo is not None, f"diccionario {ruta}:{campo}: tipo «{doc['tipo']}» no está en listas.json")
        revisar(doc["clasificacion"] in listas["clasificaciones"],
                f"diccionario {ruta}:{campo}: clasificación «{doc['clasificacion']}» no está en listas.json")
        revisar(bool(doc["preguntas"]) and set(doc["preguntas"]) <= set(listas["preguntas"]),
                f"diccionario {ruta}:{campo}: sin pregunta del sistema, o con una que no existe")
        revisar(doc["fuente"] == datos.get("fuente"), f"diccionario {ruta}:{campo}: dice fuente {doc['fuente']}")
        if tipo is None:
            continue
        valores = [datos[campo]] if campo in ENVOLTURA else [fila.get(campo) for fila in filas]
        permitidos = tuple(TIPOS[t] for t in tipo["json"])
        for valor in valores:
            if valor is None:
                revisar(doc["puede_vacio"], f"{ruta}:{campo}: vacío, y el diccionario dice que no puede")
                continue
            # bool es subclase de int en Python: un True no debe pasar por entero
            valido = isinstance(valor, permitidos) and not (isinstance(valor, bool) and bool not in permitidos)
            if valido and doc["tipo"] == "fecha":
                valido = bool((MES if campo == "mes" else FECHA).match(valor))
            if not valido:
                revisar(False, f"{ruta}:{campo}: «{valor}» no es {doc['tipo']}")
                break

if fallos:
    print(f"{len(fallos)} comprobaciones de estructura fallaron. No se publica (los valores no se revisan).")
    print("\n".join(fallos))
    sys.exit(1)

# F01 · población
sin_repetidos(pob["registros"], ("anio", "sb_codigo"), "F01")
for anio in {r["anio"] for r in pob["registros"]}:
    codigos = {r["sb_codigo"] for r in pob["registros"] if r["anio"] == anio}
    revisar(codigos == CODIGOS, f"F01 {anio}: faltan códigos {sorted(CODIGOS - codigos)}")
for r in pob["registros"]:
    clave = f"F01 {r['anio']}/{r['sb_codigo']}"
    if not presentes(r, clave, ("densidad_hab_km2",)):
        continue
    revisar(r["densidad_hab_km2"] > 0, f"{clave}: densidad no positiva")
    if r["poblacion"] is None or r["area_km2"] is None:
        # Solo 08 Schwanthalerhöhe tiene población y superficie reservadas («X») en la fuente
        revisar(r["sb_codigo"] == "08", f"{clave}: población o superficie vacía en un distrito que no es el 08")
        continue
    revisar(r["area_km2"] > 0, f"{clave}: superficie no positiva")
    if r["area_km2"] > 0:
        # La densidad publicada debe cuadrar con población / superficie (la superficie viene con 1 decimal)
        calculada = r["poblacion"] / r["area_km2"]
        revisar(abs(calculada - r["densidad_hab_km2"]) / r["densidad_hab_km2"] < 0.03, f"{clave}: densidad no cuadra")

# F02 · desempleo
sin_repetidos(des["registros"], ("anio", "sb_codigo"), "F02")
CAMPOS_F02 = ("desempleo_pct", "desempleados_prom", "poblacion_15_64")
for r in des["registros"]:
    clave = f"F02 {r['anio']}/{r['sb_codigo']}"
    revisar(r["sb_codigo"] in CODIGOS, f"{clave}: código desconocido")
    if not presentes(r, clave, CAMPOS_F02):
        continue
    revisar(0 <= r["desempleo_pct"] <= 100, f"{clave}: porcentaje fuera de 0–100")
    revisar(r["poblacion_15_64"] > 0, f"{clave}: población de 15 a 64 no positiva")
    if r["poblacion_15_64"] > 0:
        calculado = 100 * r["desempleados_prom"] / r["poblacion_15_64"]
        revisar(abs(calculado - r["desempleo_pct"]) <= 0.06, f"{clave}: el porcentaje no cuadra con sus bases")
for anio in {r["anio"] for r in des["registros"]}:
    filas = [r for r in des["registros"] if r["anio"] == anio and r["desempleados_prom"] is not None]
    ciudad = next((r for r in filas if r["sb_codigo"] == "00"), None)
    if ciudad is None:
        revisar(False, f"F02 {anio}: falta el total de la ciudad")
        continue
    suma = sum(r["desempleados_prom"] for r in filas if r["sb_codigo"] != "00")
    # La ciudad incluye desempleados sin distrito asignado: la suma de distritos no puede pasarla
    revisar(suma <= ciudad["desempleados_prom"] * 1.001, f"F02 {anio}: los distritos suman más que la ciudad")
# F01 ↔ F02: la población de 15 a 64 años es una parte de la población total del mismo distrito y año
pob_por_clave = {(r["anio"], r["sb_codigo"]): r for r in pob["registros"]}
for r in des["registros"]:
    total = pob_por_clave.get((r["anio"], r["sb_codigo"]), {}).get("poblacion")
    if total and r["poblacion_15_64"] is not None:
        revisar(0.5 < r["poblacion_15_64"] / total < 0.9,
                f"F01/F02 {r['anio']}/{r['sb_codigo']}: la población de 15 a 64 no es una parte creíble del total")

# F03 · territorio, cruzado con F01 por código
props = {f["properties"]["sb_codigo"]: f["properties"] for f in geo["features"]}
revisar(set(props) == CODIGOS - {"00"}, "F03: no están los 25 distritos")
for f in geo["features"]:
    for poligono in f["geometry"]["coordinates"]:
        for anillo in poligono:
            revisar(anillo[0] == anillo[-1], f"F03 {f['properties']['sb_codigo']}: anillo sin cerrar")
            # GeoJSON (RFC 7946): un anillo necesita 4 posiciones o más; con 3 no tiene área
            revisar(len(anillo) >= 4, f"F03 {f['properties']['sb_codigo']}: anillo de {len(anillo)} puntos")
            for lon, lat in anillo:
                revisar(
                    11.3 < lon < 11.8 and 48.0 < lat < 48.3,
                    f"F03 {f['properties']['sb_codigo']}: punto fuera de München",
                )
ultimo = max(r["anio"] for r in pob["registros"])
for r in pob["registros"]:
    if r["anio"] == ultimo and r["sb_codigo"] in props and r["area_km2"] is not None:
        revisar(
            abs(props[r["sb_codigo"]]["area_km2"] - r["area_km2"]) <= 0.1,
            f"F01/F03 {r['sb_codigo']}: superficies distintas",
        )
revisar(abs(sum(p["area_km2"] for p in props.values()) - pob_por_clave[(ultimo, "00")]["area_km2"]) <= 0.5,
        "F01/F03: la suma de los 25 distritos no da la superficie de la ciudad")
# 08 Schwanthalerhöhe: F01 reserva su población, pero ciudad − otros 24 distritos, dividido por la
# densidad publicada, tiene que dar la superficie oficial de F03. Si no, alguna de las tres cifras está mal.
if "08" in props:
    for anio in sorted({r["anio"] for r in pob["registros"]}):
        filas = {r["sb_codigo"]: r for r in pob["registros"] if r["anio"] == anio}
        otros = [filas[c]["poblacion"] for c in CODIGOS - {"00", "08"} if c in filas]
        if None in otros or "00" not in filas or "08" not in filas or not filas["08"]["densidad_hab_km2"]:
            continue
        deducida = filas["00"]["poblacion"] - sum(otros)
        area = deducida / filas["08"]["densidad_hab_km2"]
        revisar(abs(area - props["08"]["area_km2"]) / props["08"]["area_km2"] < 0.02,
                f"F01/F03 {anio}/08: población deducida ({deducida}) / densidad no da la superficie de F03")

# F04 · clima
sin_repetidos(cli["registros"], ("mes",), "F04")
for r in cli["registros"]:
    temperaturas = ("temp_min_media_c", "temp_media_c", "temp_max_media_c")
    for campo in temperaturas:
        revisar(r[campo] is None or -30 < r[campo] < 45, f"F04 {r['mes']}: {campo} fuera de rango")
    # El DWD puede dejar un mes sin dato (-999 → null): el orden solo se compara si están las tres
    if all(r[campo] is not None for campo in temperaturas):
        revisar(
            r["temp_min_media_c"] <= r["temp_media_c"] <= r["temp_max_media_c"],
            f"F04 {r['mes']}: mínima/media/máxima desordenadas",
        )
    revisar(r["precipitacion_mm"] is None or r["precipitacion_mm"] >= 0, f"F04 {r['mes']}: lluvia negativa")
    revisar(r["nivel_calidad"] in {1, 2, 3, 5, 7, 8, 9, 10}, f"F04 {r['mes']}: nivel de calidad desconocido")
revisar(cli["vigencia"][:7] == max(r["mes"] for r in cli["registros"]), "F04: la vigencia no es el último mes")

# F05 · escucha
meses = [r["mes"] for r in esc["registros"]]
revisar(meses == sorted(set(meses)), "F05: meses repetidos o desordenados")
revisar(all(r["vistas"] >= 0 for r in esc["registros"]), "F05: vistas negativas")
revisar(esc["vigencia"][:7] == meses[-1], "F05: la vigencia no es el último mes")

# F26 · transporte: una fila por parada física dentro de la ciudad, con los medios que la sirven
MEDIOS = ("s_bahn", "u_bahn", "tranvia", "bus", "tren_regional")
sin_repetidos(tra["registros"], ("parada_id",), "F26")
for r in tra["registros"]:
    clave = f"F26 {r['parada_id']}"
    revisar(r["sb_codigo"] in CODIGOS - {"00"}, f"{clave}: distrito «{r['sb_codigo']}» desconocido")
    revisar(11.3 < r["lon"] < 11.8 and 48.0 < r["lat"] < 48.3, f"{clave}: coordenadas fuera de München")
    revisar(any(r[m] for m in MEDIOS), f"{clave}: ningún medio para en ella")
revisar({r["sb_codigo"] for r in tra["registros"]} == CODIGOS - {"00"}, "F26: hay distritos sin ninguna parada")
# La fuente marca la S-Bahn con route_type 0 (tranvía en GTFS); el script la reconoce por el nombre de la línea.
# Si eso dejara de funcionar, la S-Bahn desaparecería en silencio: München tiene más de 30 estaciones de cada red rápida.
for medio, minimo in (("s_bahn", 30), ("u_bahn", 80)):
    n = sum(r[medio] for r in tra["registros"])
    revisar(n >= minimo, f"F26: solo {n} paradas con {medio} (se esperan al menos {minimo}); revisen la clasificación de rutas")

# Catálogo · cada ficha bien formada, con valores de las listas cerradas, y unida al lago
CAMPOS_FICHA = (
    "id", "nombre", "entidad", "url", "formato", "acceso", "licencia", "licencia_texto", "licencia_donde",
    "personas", "frecuencia", "estado", "probado", "respuesta", "script", "salida", "como_se_encontro", "nota",
)
VOCABULARIO = (
    ("estado", "estados"), ("entidad", "entidades"), ("licencia", "licencias"), ("personas", "personas"),
    ("acceso", "accesos"), ("formato", "formatos"), ("frecuencia", "frecuencias"),
)
for clave, entidad in listas["entidades"].items():
    revisar(entidad["tipo"] in listas["tipos_publicador"], f"listas.json: {clave} tiene un tipo de publicador desconocido")
fichas: dict[str, dict] = {}
for archivo in sorted((RAIZ / "catalogo").glob("F*.json")):
    ficha = json.loads(archivo.read_text(encoding="utf-8"))
    nombre = f"catalogo/{archivo.name}"
    faltan = [c for c in CAMPOS_FICHA if c not in ficha]
    revisar(not faltan, f"{nombre}: faltan campos {faltan}")
    if faltan:
        continue
    revisar(archivo.name.startswith(ficha["id"] + "_"), f"{nombre}: el nombre no empieza por su id {ficha['id']}")
    revisar(ficha["id"] not in fichas, f"{nombre}: id {ficha['id']} repetido")
    fichas[ficha["id"]] = ficha
    for campo, lista in VOCABULARIO:
        revisar(ficha[campo] in listas[lista], f"{nombre}: {campo} «{ficha[campo]}» no está en listas.json")
    probado = str(ficha["probado"])
    revisar(bool(FECHA.match(probado)) and probado <= HOY, f"{nombre}: probado «{probado}» no es AAAA-MM-DD o es posterior a hoy")
    if ficha["estado"] == "integrado":
        licencia = listas["licencias"].get(ficha["licencia"], {})
        revisar(licencia.get("permite_integrar", False), f"{nombre}: integrada con una licencia que no lo permite")
        revisar(bool(ficha["licencia_texto"]), f"{nombre}: integrada sin el texto de la licencia tal como aparece")
        revisar(bool(ficha["salida"]), f"{nombre}: integrada sin archivo de salida")
        revisar(bool(ficha["script"]) and (RAIZ / str(ficha["script"])).exists(),
                f"{nombre}: integrada sin script de ingesta que exista")
        for salida in ficha["salida"]:
            datos = LAGO.get(salida)
            revisar(datos is not None, f"{nombre}: su salida {salida} no está en el lago verificado")
            if datos is not None:
                revisar(datos.get("fuente") == ficha["id"], f"{nombre}: {salida} dice fuente «{datos.get('fuente')}»")
                revisar(datos.get("probado") <= probado,
                        f"{nombre}: el lago se descargó ({datos.get('probado')}) después de la última prueba de la ficha")
    else:
        revisar(not ficha["salida"], f"{nombre}: tiene salida pero su estado es «{ficha['estado']}»")
# El índice que leen las vistas lista exactamente las fichas que existen, en orden
indice = leer("catalogo/indice.json")["fichas"]
reales = sorted(p.name for p in (RAIZ / "catalogo").glob("F*.json"))
revisar(indice == reales, f"catalogo/indice.json no coincide con las fichas: sobran {sorted(set(indice) - set(reales))}, faltan {sorted(set(reales) - set(indice))}")
# Lo que está en el lago tiene que estar en el catálogo como integrado
for ruta, datos in LAGO.items():
    ficha = fichas.get(datos.get("fuente"))
    revisar(ficha is not None and ficha["estado"] == "integrado" and ruta in ficha["salida"],
            f"{ruta}: su fuente {datos.get('fuente')} no está integrada en el catálogo con esta salida")
for c in diccionario:
    revisar(c["fuente"] in fichas and fichas[c["fuente"]]["estado"] == "integrado",
            f"diccionario {c['archivo']}:{c['campo']}: su fuente {c['fuente']} no está integrada")

# Vistas · toda fuente que cita web/ es una ficha integrada (Curaduría revisa a Interfaz): una etiqueta
# «Fuente F09» en pantalla sería mostrar una cifra de una fuente sin licencia leída.
citadas = set()
for archivo in sorted((RAIZ / "web").glob("*.js")):
    citadas |= set(re.findall(r'"(F\d{2})"', archivo.read_text(encoding="utf-8")))
revisar(bool(citadas), "web/: las vistas no citan ninguna fuente")
for id_fuente in sorted(citadas):
    revisar(id_fuente in fichas and fichas[id_fuente]["estado"] == "integrado",
            f"web/: las vistas citan {id_fuente}, que no es una ficha integrada")

# Protección · nivel «abierto, solo agregados»: lo que se publica no tiene datos de personas, y los
# crudos (que traen los cortes por sexo y nacionalidad) no viajan al despliegue.
for c in diccionario:
    revisar(c["clasificacion"] not in ("sensible", "dato_personal"),
            f"diccionario {c['archivo']}:{c['campo']}: clasificado «{c['clasificacion']}» en un lago que se publica abierto")
# Conteo mínimo por celda: ningún conteo de personas por distrito por debajo de 100. Es una decisión del
# grupo, no una norma (README, «Nuestra posición»); si una fuente nueva baja de ahí, no se publica.
MINIMO_CELDA = 100
for r in pob["registros"]:
    revisar(r["poblacion"] is None or r["poblacion"] >= MINIMO_CELDA,
            f"F01 {r['anio']}/{r['sb_codigo']}: {r['poblacion']} habitantes, menos de {MINIMO_CELDA}")
for r in des["registros"]:
    for campo in ("desempleados_prom", "poblacion_15_64"):
        revisar(r[campo] is None or r[campo] >= MINIMO_CELDA,
                f"F02 {r['anio']}/{r['sb_codigo']}: {campo} = {r[campo]}, menos de {MINIMO_CELDA}")
ignorados = (RAIZ / ".vercelignore").read_text(encoding="utf-8").split() if (RAIZ / ".vercelignore").exists() else []
revisar("lago/raw" in ignorados, ".vercelignore: falta «lago/raw»; los crudos llegarían al despliegue")

# Actualidad · un lago viejo no se publica: cada archivo tiene que haberse probado en los últimos 60 días
MAXIMO_DIAS = 60
for ruta, datos in LAGO.items():
    edad = (date.today() - date.fromisoformat(datos["probado"])).days
    revisar(edad <= MAXIMO_DIAS, f"{ruta}: probado hace {edad} días (máximo {MAXIMO_DIAS}); corran la ingesta y vuelvan a probar las fichas")

# Glosario · cada cifra que muestran las vistas tiene definición y sale de campos que existen en el diccionario
glosario = leer("catalogo/glosario.json")["terminos"]
documentados_todos = {f"{c['archivo']}:{c['campo']}" for c in diccionario}
ids_glosario = [t["id"] for t in glosario]
revisar(len(ids_glosario) == len(set(ids_glosario)), "glosario: términos repetidos")
for t in glosario:
    nombre = f"glosario {t['id']}"
    revisar(t["tipo"] in listas["tipos_cifra"], f"{nombre}: tipo «{t['tipo']}» no está en listas.json")
    revisar(bool(t["definicion"]) and bool(t["campos"]) and bool(t["fuentes"]), f"{nombre}: falta definición, campos o fuentes")
    revisar(t["tipo"] not in ("calculada", "derivada", "escala_visual") or bool(t["formula"]), f"{nombre}: es {t['tipo']} y no dice cómo se obtiene")
    for campo in t["campos"]:
        revisar(campo in documentados_todos, f"{nombre}: el campo {campo} no está en el diccionario")
    for id_fuente in t["fuentes"]:
        revisar(id_fuente in fichas and fichas[id_fuente]["estado"] == "integrado", f"{nombre}: la fuente {id_fuente} no está integrada")

# Bitácora de IA · la hoja del Excel sale de este archivo: vocabulario cerrado, fuentes que existen y una fila
# por cada fila de la bitácora del README, para que las dos no se separen
bitacora = leer("catalogo/bitacora_ia.json")["filas"]
for n, b in enumerate(bitacora, start=1):
    nombre = f"bitacora_ia fila {n}"
    revisar(all(b.get(c) for c in ("herramienta", "encargo", "respuesta", "comprobacion", "aprendizaje")),
            f"{nombre}: falta herramienta, encargo, respuesta, comprobación o aprendizaje")
    revisar(b.get("resultado") in listas["resultados_ia"], f"{nombre}: resultado «{b.get('resultado')}» no está en listas.json")
    for id_fuente in b.get("fuentes", []):
        revisar(id_fuente in fichas, f"{nombre}: la fuente {id_fuente} no tiene ficha")
readme = (RAIZ / "README.md").read_text(encoding="utf-8")
seccion = readme.split("## Bitácora de IA", 1)[-1].split("\n## ", 1)[0]
filas_readme = [l for l in seccion.splitlines() if l.startswith("| ") and not l.startswith("| Tramo ")]
revisar(len(filas_readme) == len(bitacora),
        f"bitacora_ia.json tiene {len(bitacora)} filas y la bitácora de IA del README {len(filas_readme)}: añadan la que falta")

# Terceros · todo origen externo que la política CSP de las vistas deja cargar está registrado, con licencia
dependencias = leer("catalogo/dependencias.json")["dependencias"]
registrados = {d["origen"] for d in dependencias}
html = (RAIZ / "web" / "index.html").read_text(encoding="utf-8")
csp = re.search(r'Content-Security-Policy" content="([^"]+)"', html)
revisar(csp is not None, "web/index.html: no tiene política CSP")
for origen in sorted(set(re.findall(r"https://[a-z0-9.-]+", csp.group(1) if csp else ""))):
    revisar(origen in registrados, f"web/index.html: la CSP deja cargar {origen}, que no está en catalogo/dependencias.json")
for d in dependencias:
    revisar(bool(d.get("licencia")) and bool(d.get("si_falla")) and bool(d.get("recibe")),
            f"dependencias {d['id']}: falta licencia, qué recibe o qué pasa si falla")

if fallos:
    print(f"{len(fallos)} comprobaciones fallaron. No se publica.")
    print("\n".join(fallos))
    sys.exit(1)
print("Todas las comprobaciones pasaron.")
