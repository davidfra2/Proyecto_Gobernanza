"""F02 · Proporción de desempleados por Stadtbezirk (Indikatorenatlas, Statistisches Amt München).

Fuente: https://opendata.muenchen.de/dataset/indikatorenatlas-2014-arbeitsmarkt-arbeitslosendichte-83r65mct
Licencia: dl-by-de/2.0 (Datenlizenz Deutschland – Namensnennung – Version 2.0)
Salida:   lago/desempleo_stadtbezirke.json

Decisiones:
- Solo la Ausprägung «insgesamt» (la fuente también separa por sexo y nacionalidad; no las usamos)
  y los años desde DESDE.
- Los desempleados y la población de 15 a 64 años son promedios anuales: traen decimales.
"""

from __future__ import annotations

import csv
import io

from comun import LAGO, descargar, escribir, hoy, numero
from pull_poblacion import codigo

URL = (
    "https://opendata.muenchen.de/dataset/0771b22f-b1e7-4480-8fe5-d641c2586f3e/resource/"
    "55a1adb0-6c06-403b-ab7f-7e6c41d18e32/download/"
    "indikat_2605arbeitsmarkt_arbeitslose_-_anteil_18_05_26.csv"
)
DESDE = 2015


def transformar(texto: str) -> list[dict]:
    registros = []
    for fila in csv.DictReader(io.StringIO(texto)):
        if fila["Ausprägung"] != "insgesamt" or int(fila["Jahr"]) < DESDE:
            continue
        registros.append(
            {
                "sb_codigo": codigo(fila["Raumbezug"]),
                "anio": int(fila["Jahr"]),
                "desempleo_pct": numero(fila["Indikatorwert"]),
                "desempleados_prom": numero(fila["Basiswert 1"]),
                "poblacion_15_64": numero(fila["Basiswert 2"]),
            }
        )
    registros.sort(key=lambda r: (r["anio"], r["sb_codigo"]))
    return registros


def construir(texto: str) -> dict:
    registros = transformar(texto)
    ultimo = max(r["anio"] for r in registros)
    return {"fuente": "F02", "vigencia": f"{ultimo}-12-31", "probado": hoy(), "registros": registros}


if __name__ == "__main__":
    crudo = descargar(URL, "desempleo_arbeitslose_anteil.csv").decode("utf-8-sig")
    escribir(LAGO / "desempleo_stadtbezirke.json", construir(crudo))
