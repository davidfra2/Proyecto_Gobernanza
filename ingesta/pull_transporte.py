"""F26 · Paradas del transporte público en München (horarios GTFS de toda la red MVV).

Fuente: https://opendata.muenchen.de/dataset/soll-fahrplandaten-mvv-gesamtnetz-gtfs
Licencia: CC BY 4.0 (Münchner Verkehrs- und Tarifverbund GmbH)
Salida:   lago/transporte_paradas.json

Decisiones:
- Una fila por parada física (las plataformas de una misma estación se agrupan en su «parent_station»),
  solo las que caen dentro de uno de los 25 Stadtbezirke (punto en polígono contra territorio/, F03).
- Para cada parada se guarda qué medios la sirven (S-Bahn, U-Bahn, tranvía, autobús, tren regional),
  según las rutas que paran en ella en stop_times.txt. No se guardan horarios ni frecuencias.
- El lago guarda las paradas, que son lo observado; los conteos por distrito se calculan en las vistas
  (ver catalogo/glosario.json).
- El servidor de MVV es lento (unos 30 KB/s): la descarga de ~19 MB tarda varios minutos.
"""

from __future__ import annotations

import csv
import io
import json
import zipfile
from datetime import date

from comun import LAGO, RAIZ, descargar, escribir, hoy, recurso

DATASET = "soll-fahrplandaten-mvv-gesamtnetz-gtfs"  # la URL del ZIP se resuelve en el catálogo
DECIMALES = 5


def leer(zip_: zipfile.ZipFile, nombre: str):
    return csv.DictReader(io.TextIOWrapper(zip_.open(nombre), encoding="utf-8-sig"))


def modo(ruta: dict) -> str | None:
    """Clasifica una ruta GTFS (tipos básicos y extendidos) en uno de los cinco medios del lago."""
    nombre, tipo = ruta.get("route_short_name", "").strip(), int(ruta["route_type"])
    if nombre[:1] == "S" and nombre[1:2].isdigit():
        return "s_bahn"
    if tipo in (1, 400, 401, 402, 403, 404) or (nombre[:1] == "U" and nombre[1:2].isdigit()):
        return "u_bahn"
    if tipo == 0 or 900 <= tipo <= 906:
        return "tranvia"
    if tipo == 3 or 700 <= tipo <= 716 or 200 <= tipo <= 209:
        return "bus"
    if tipo == 2 or 100 <= tipo <= 117:
        return "tren_regional"
    return None


def dentro(x: float, y: float, anillo: list) -> bool:
    adentro, j = False, len(anillo) - 1
    for i in range(len(anillo)):
        xi, yi = anillo[i]
        xj, yj = anillo[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            adentro = not adentro
        j = i
    return adentro


def distrito(x: float, y: float, distritos: list) -> str | None:
    for codigo, poligonos in distritos:
        for poligono in poligonos:
            if dentro(x, y, poligono[0]) and not any(dentro(x, y, hueco) for hueco in poligono[1:]):
                return codigo
    return None


def transformar(zip_: zipfile.ZipFile, distritos: list) -> tuple[list[dict], str]:
    rutas = {r["route_id"]: modo(r) for r in leer(zip_, "routes.txt")}
    viajes = {t["trip_id"]: rutas.get(t["route_id"]) for t in leer(zip_, "trips.txt")}
    paradas = {p["stop_id"]: p for p in leer(zip_, "stops.txt")}
    raiz = lambda sid: paradas[sid].get("parent_station") or sid  # noqa: E731  (andén → estación)
    medios: dict[str, set] = {}
    for st in leer(zip_, "stop_times.txt"):
        m = viajes.get(st["trip_id"])
        if m and st["stop_id"] in paradas:
            medios.setdefault(raiz(st["stop_id"]), set()).add(m)
    registros = []
    for sid, servida in medios.items():
        p = paradas.get(sid)
        if p is None or not p.get("stop_lat"):
            continue
        lon, lat = round(float(p["stop_lon"]), DECIMALES), round(float(p["stop_lat"]), DECIMALES)
        codigo = distrito(lon, lat, distritos)
        if codigo is None:
            continue  # fuera de la ciudad: la red MVV llega a toda la región
        registros.append({"parada_id": sid, "nombre": p["stop_name"].strip(), "lon": lon, "lat": lat, "sb_codigo": codigo,
                          **{m: m in servida for m in ("s_bahn", "u_bahn", "tranvia", "bus", "tren_regional")}})
    registros.sort(key=lambda r: (r["sb_codigo"], r["nombre"], r["parada_id"]))
    # vigencia: último día de servicio del calendario, o el día de la descarga si no lo dice
    fin = None
    if "feed_info.txt" in zip_.namelist():
        fin = next(leer(zip_, "feed_info.txt"), {}).get("feed_end_date")
    if not fin and "calendar.txt" in zip_.namelist():
        fin = max((c["end_date"] for c in leer(zip_, "calendar.txt")), default=None)
    vigencia = date(int(fin[:4]), int(fin[4:6]), int(fin[6:8])).isoformat() if fin else hoy()
    return registros, vigencia


def construir(zip_: zipfile.ZipFile) -> dict:
    geo = json.loads((RAIZ / "territorio" / "stadtbezirke.geojson").read_text(encoding="utf-8"))
    distritos = [(f["properties"]["sb_codigo"], f["geometry"]["coordinates"]) for f in geo["features"]]
    registros, vigencia = transformar(zip_, distritos)
    return {"fuente": "F26", "vigencia": vigencia, "probado": hoy(), "registros": registros}


if __name__ == "__main__":
    crudo = descargar(recurso(DATASET, "ZIP"), "mvv_gtfs_gesamtnetz.zip")
    escribir(LAGO / "transporte_paradas.json", construir(zipfile.ZipFile(io.BytesIO(crudo))))
