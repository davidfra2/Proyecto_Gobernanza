"""F03 · Límites de los 25 Stadtbezirke (GeodatenService München, WFS).

Fuente: https://opendata.muenchen.de/dataset/vablock_stadtbezirke_opendata
Licencia: dl-by-de/2.0 (Datenlizenz Deutschland – Namensnennung – Version 2.0)
Salida:   territorio/stadtbezirke.geojson

Decisiones:
- Se pide al servidor en EPSG:4326 (longitud, latitud), que es lo que lee MapLibre.
- El WFS trae 27 polígonos para 25 distritos (19 y 18 tienen pedazos sueltos): se unen en un
  MultiPolygon por distrito.
- Se simplifica con Douglas-Peucker (tolerancia 0.0005°, unos 40 m) y se redondea a 4 decimales
  (unos 10 m): el archivo pasa de ~500 KB a ~20 KB. Sirve para un mapa de distritos, no para medir.
- La superficie se toma del atributo oficial flaeche_qm (no se calcula del polígono simplificado).
"""

import json
import math

from comun import RAIZ, descargar, escribir, hoy

URL = (
    "https://geoportal.muenchen.de/geoserver/gsm_wfs/ows?service=WFS&version=1.0.0&request=GetFeature"
    "&typeName=gsm_wfs:vablock_stadtbezirk&outputFormat=application/json&srsName=EPSG:4326"
)
TOLERANCIA = 0.0005
DECIMALES = 4


def simplificar(puntos: list[list[float]], tol: float = TOLERANCIA) -> list[list[float]]:
    """Douglas-Peucker. Es la misma versión que se usó en el navegador para la primera carga."""
    if len(puntos) < 3:
        return puntos
    (x1, y1), (x2, y2) = puntos[0], puntos[-1]
    dx, dy = x2 - x1, y2 - y1
    largo = math.hypot(dx, dy)
    dmax, indice = 0.0, 0
    for i in range(1, len(puntos) - 1):
        x, y = puntos[i]
        d = math.hypot(x - x1, y - y1) if largo == 0 else abs(dy * x - dx * y + x2 * y1 - y2 * x1) / largo
        if d > dmax:
            dmax, indice = d, i
    if dmax > tol:
        izquierda = simplificar(puntos[: indice + 1], tol)
        derecha = simplificar(puntos[indice:], tol)
        return izquierda[:-1] + derecha
    return [puntos[0], puntos[-1]]


def transformar(wfs: dict) -> list[dict]:
    distritos: dict[str, dict] = {}
    for f in wfs["features"]:
        p = f["properties"]
        anillos = [
            [[round(x, DECIMALES), round(y, DECIMALES)] for x, y in simplificar(anillo)]
            for anillo in f["geometry"]["coordinates"]
        ]
        d = distritos.setdefault(
            p["sb_nummer"],
            {"nombre": p["sb_name"], "area_km2": round(p["flaeche_qm"] / 1_000_000, 2), "poligonos": []},
        )
        d["poligonos"].append(anillos)
    return [
        {
            "type": "Feature",
            "properties": {"sb_codigo": codigo, "sb_nombre": d["nombre"], "area_km2": d["area_km2"]},
            "geometry": {"type": "MultiPolygon", "coordinates": d["poligonos"]},
        }
        for codigo, d in sorted(distritos.items())
    ]


def construir(wfs: dict) -> dict:
    return {
        "type": "FeatureCollection",
        "fuente": "F03",
        "vigencia": hoy(),
        "probado": hoy(),
        "features": transformar(wfs),
    }


if __name__ == "__main__":
    crudo = json.loads(descargar(URL, "stadtbezirke_wfs.geojson"))
    escribir(RAIZ / "territorio" / "stadtbezirke.geojson", construir(crudo))
