"""F03 · Límites de los 25 Stadtbezirke (GeodatenService München, WFS).

Fuente: https://opendata.muenchen.de/dataset/vablock_stadtbezirke_opendata
Licencia: dl-by-de/2.0 (Datenlizenz Deutschland – Namensnennung – Version 2.0)
Salida:   territorio/stadtbezirke.geojson

Decisiones:
- Se pide al servidor en EPSG:4326 (longitud, latitud), que es lo que lee MapLibre.
- El WFS trae 27 polígonos para 25 distritos (19 y 18 tienen pedazos sueltos): se unen en un
  MultiPolygon por distrito.
- Se redondea a 4 decimales (unos 10 m) y se quitan los puntos repetidos seguidos; el GeoJSON se
  escribe compacto (~200 KB). No se simplifica cada polígono por separado: Douglas-Peucker por
  distrito dejaba huecos y solapes en los bordes compartidos y llegó a reducir un pedazo del 19 a
  un anillo de 3 puntos, sin área. Redondear es igual a ambos lados de un borde, así que los
  vecinos siguen encajando. Sirve para un mapa de distritos, no para medir.
- La superficie se toma del atributo oficial flaeche_qm (no se calcula del polígono redondeado).
"""

from __future__ import annotations

import json

from comun import RAIZ, descargar, escribir, hoy

URL = (
    "https://geoportal.muenchen.de/geoserver/gsm_wfs/ows?service=WFS&version=1.0.0&request=GetFeature"
    "&typeName=gsm_wfs:vablock_stadtbezirk&outputFormat=application/json&srsName=EPSG:4326"
)
DECIMALES = 4


def redondear(anillo: list[list[float]]) -> list[list[float]]:
    """Redondea y quita repetidos seguidos. Un anillo válido necesita al menos 4 posiciones."""
    puntos: list[list[float]] = []
    for x, y in anillo:
        punto = [round(x, DECIMALES), round(y, DECIMALES)]
        if not puntos or puntos[-1] != punto:
            puntos.append(punto)
    if len(puntos) < 4 or puntos[0] != puntos[-1]:
        raise ValueError(f"Anillo inválido tras redondear: {len(puntos)} puntos")
    return puntos


def transformar(wfs: dict) -> list[dict]:
    distritos: dict[str, dict] = {}
    for f in wfs["features"]:
        p = f["properties"]
        if f["geometry"]["type"] != "Polygon":
            raise ValueError(f"Se esperaba Polygon y llegó {f['geometry']['type']} ({p['sb_nummer']})")
        anillos = [redondear(anillo) for anillo in f["geometry"]["coordinates"]]
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
    escribir(RAIZ / "territorio" / "stadtbezirke.geojson", construir(crudo), compacto=True)
