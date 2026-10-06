"""Verificación del lago: con un solo fallo no se publica. Uso: python3 verificacion/verificar.py

Si algo falla, se arregla la ingesta; nunca se afloja el verificador.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CODIGOS = {f"{i:02d}" for i in range(0, 26)}  # 00 = ciudad, 01–25 = Stadtbezirke
FECHA = re.compile(r"^\d{4}-\d{2}(-\d{2})?$")
fallos: list[str] = []


def revisar(condicion: bool, mensaje: str) -> None:
    if not condicion:
        fallos.append(mensaje)


def cargar(ruta: str) -> dict:
    datos = json.loads((RAIZ / ruta).read_text(encoding="utf-8"))
    for clave in ("fuente", "vigencia", "probado"):
        revisar(bool(datos.get(clave)), f"{ruta}: falta «{clave}»")
    revisar(bool(FECHA.match(str(datos.get("vigencia", "")))), f"{ruta}: vigencia no es AAAA-MM(-DD)")
    revisar(bool(FECHA.match(str(datos.get("probado", "")))), f"{ruta}: probado no es AAAA-MM-DD")
    return datos


# F01 · población
pob = cargar("lago/poblacion_stadtbezirke.json")
for anio in {r["anio"] for r in pob["registros"]}:
    codigos = {r["sb_codigo"] for r in pob["registros"] if r["anio"] == anio}
    revisar(codigos == CODIGOS, f"F01 {anio}: faltan códigos {sorted(CODIGOS - codigos)}")
for r in pob["registros"]:
    clave = f"F01 {r['anio']}/{r['sb_codigo']}"
    revisar(r["densidad_hab_km2"] > 0, f"{clave}: densidad no positiva")
    if r["poblacion"] is None:
        revisar(r["sb_codigo"] == "08", f"{clave}: población vacía en un distrito que no es el 08")
        continue
    # La densidad publicada debe cuadrar con población / superficie (la superficie viene con 1 decimal)
    calculada = r["poblacion"] / r["area_km2"]
    revisar(abs(calculada - r["densidad_hab_km2"]) / r["densidad_hab_km2"] < 0.03, f"{clave}: densidad no cuadra")

# F02 · desempleo
des = cargar("lago/desempleo_stadtbezirke.json")
for r in des["registros"]:
    clave = f"F02 {r['anio']}/{r['sb_codigo']}"
    revisar(r["sb_codigo"] in CODIGOS, f"{clave}: código desconocido")
    revisar(0 <= r["desempleo_pct"] <= 100, f"{clave}: porcentaje fuera de 0–100")
    calculado = 100 * r["desempleados_prom"] / r["poblacion_15_64"]
    revisar(abs(calculado - r["desempleo_pct"]) <= 0.06, f"{clave}: el porcentaje no cuadra con sus bases")
for anio in {r["anio"] for r in des["registros"]}:
    filas = [r for r in des["registros"] if r["anio"] == anio]
    ciudad = next(r for r in filas if r["sb_codigo"] == "00")
    suma = sum(r["desempleados_prom"] for r in filas if r["sb_codigo"] != "00")
    # La ciudad incluye desempleados sin distrito asignado: la suma de distritos no puede pasarla
    revisar(suma <= ciudad["desempleados_prom"] * 1.001, f"F02 {anio}: los distritos suman más que la ciudad")

# F03 · territorio, cruzado con F01 por código
geo = cargar("territorio/stadtbezirke.geojson")
props = {f["properties"]["sb_codigo"]: f["properties"] for f in geo["features"]}
revisar(set(props) == CODIGOS - {"00"}, "F03: no están los 25 distritos")
for f in geo["features"]:
    for poligono in f["geometry"]["coordinates"]:
        for anillo in poligono:
            revisar(anillo[0] == anillo[-1], f"F03 {f['properties']['sb_codigo']}: anillo sin cerrar")
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

# F04 · clima
cli = cargar("lago/clima_muenchen_stadt.json")
for r in cli["registros"]:
    for campo in ("temp_media_c", "temp_max_media_c", "temp_min_media_c"):
        revisar(r[campo] is None or -30 < r[campo] < 45, f"F04 {r['mes']}: {campo} fuera de rango")
    revisar(
        r["temp_min_media_c"] <= r["temp_media_c"] <= r["temp_max_media_c"],
        f"F04 {r['mes']}: mínima/media/máxima desordenadas",
    )
    revisar(r["precipitacion_mm"] is None or r["precipitacion_mm"] >= 0, f"F04 {r['mes']}: lluvia negativa")
    revisar(r["nivel_calidad"] in {1, 2, 3, 5, 7, 8, 9, 10}, f"F04 {r['mes']}: nivel de calidad desconocido")

# F05 · escucha
esc = cargar("lago/escucha.json")
meses = [r["mes"] for r in esc["registros"]]
revisar(meses == sorted(set(meses)), "F05: meses repetidos o desordenados")
revisar(all(r["vistas"] >= 0 for r in esc["registros"]), "F05: vistas negativas")

if fallos:
    print(f"{len(fallos)} comprobaciones fallaron. No se publica.")
    print("\n".join(fallos))
    sys.exit(1)
print("Todas las comprobaciones pasaron.")
