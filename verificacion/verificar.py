"""Verificación del lago: con un solo fallo no se publica. Uso: python3 verificacion/verificar.py

Si algo falla, se arregla la ingesta; nunca se afloja el verificador.
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
VIGENCIA = re.compile(r"^\d{4}-\d{2}(-\d{2})?$")
PROBADO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
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


def cargar(ruta: str) -> dict:
    datos = json.loads((RAIZ / ruta).read_text(encoding="utf-8"))
    for clave in ("fuente", "vigencia", "probado"):
        revisar(bool(datos.get(clave)), f"{ruta}: falta «{clave}»")
    revisar(bool(VIGENCIA.match(str(datos.get("vigencia", "")))), f"{ruta}: vigencia no es AAAA-MM(-DD)")
    probado = str(datos.get("probado", ""))
    if PROBADO.match(probado):
        revisar(probado <= date.today().isoformat(), f"{ruta}: probado ({probado}) es posterior a hoy")
    else:
        revisar(False, f"{ruta}: probado no es AAAA-MM-DD")
    return datos


# F01 · población
pob = cargar("lago/poblacion_stadtbezirke.json")
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
des = cargar("lago/desempleo_stadtbezirke.json")
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

# F03 · territorio, cruzado con F01 por código
geo = cargar("territorio/stadtbezirke.geojson")
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

# F04 · clima
cli = cargar("lago/clima_muenchen_stadt.json")
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
