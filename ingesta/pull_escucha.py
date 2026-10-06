"""F05 · Vistas mensuales del artículo «München» en la Wikipedia en alemán (Wikimedia REST API).

Fuente: https://wikimedia.org/api/rest_v1/metrics/pageviews/
Licencia: CC0 («All Analytics datasets are available under the Creative Commons CC0 dedication»)
Salida:   lago/escucha.json

Decisiones:
- agent=user: cuenta personas, no bots ni arañas.
- Solo de.wikipedia: es la edición con más lectores del artículo y la que lee la gente de la región.
- Desde enero de 2025 hasta el último mes completo.
"""

import json
from datetime import date, timedelta

from comun import LAGO, descargar, escribir, hoy

ARTICULO = "M%C3%BCnchen"
DESDE = "20250101"


def url() -> str:
    hasta = (date.today().replace(day=1) - timedelta(days=1)).strftime("%Y%m%d")  # último mes completo
    return (
        "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/de.wikipedia/all-access/user/"
        f"{ARTICULO}/monthly/{DESDE}/{hasta}"
    )


def transformar(items: list[dict]) -> list[dict]:
    registros = [{"mes": f"{i['timestamp'][:4]}-{i['timestamp'][4:6]}", "vistas": int(i["views"])} for i in items]
    registros.sort(key=lambda r: r["mes"])
    return registros


def construir(items: list[dict]) -> dict:
    registros = transformar(items)
    return {"fuente": "F05", "vigencia": registros[-1]["mes"], "probado": hoy(), "registros": registros}


if __name__ == "__main__":
    respuesta = json.loads(descargar(url(), "wikipedia_pageviews_muenchen.json"))
    escribir(LAGO / "escucha.json", construir(respuesta["items"]))
