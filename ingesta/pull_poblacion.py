"""F01 · Población, superficie y densidad por Stadtbezirk (Indikatorenatlas, Statistisches Amt München).

Fuente: https://opendata.muenchen.de/dataset/indikatorenatlas-bevoelkerung-bevoelkerungsdichte-83r65mct
Licencia: dl-by-de/2.0 (Datenlizenz Deutschland – Namensnennung – Version 2.0)
Salida:   lago/poblacion_stadtbezirke.json

Decisiones:
- Solo la Ausprägung «insgesamt» y los años desde DESDE (los últimos diez y uno más).
- «Stadt München» se guarda con el código 00; los distritos con su código oficial 01–25.
- La fuente publica «X» (dato reservado) en la población y la superficie de 08 Schwanthalerhöhe:
  se guarda como null, no como 0. La densidad de 08 sí viene publicada.
"""

from __future__ import annotations

import csv
import io

from comun import LAGO, descargar, escribir, hoy, numero, recurso_csv

DATASET = "0be6dc92-9ca5-4ae9-8a08-ba4039f2a225"  # la URL del CSV se resuelve en el catálogo
DESDE = 2015


def entero(texto: str) -> int | None:
    valor = numero(texto)
    return int(valor) if valor is not None else None


def codigo(raumbezug: str) -> str:
    """'Stadt München' -> '00'; '09 Neuhausen - Nymphenburg' -> '09'. Se cruza por código, nunca por nombre."""
    return "00" if raumbezug.startswith("Stadt") else raumbezug[:2]


def transformar(texto: str) -> list[dict]:
    registros = []
    for fila in csv.DictReader(io.StringIO(texto)):
        if fila["Ausprägung"] != "insgesamt" or int(fila["Jahr"]) < DESDE:
            continue
        registros.append(
            {
                "sb_codigo": codigo(fila["Raumbezug"]),
                "anio": int(fila["Jahr"]),
                "poblacion": entero(fila["Basiswert 1"]),
                "area_km2": numero(fila["Basiswert 2"]),
                # Si algún día la densidad también viene reservada, queda null y lo marca verificar.py
                "densidad_hab_km2": entero(fila["Indikatorwert"]),
            }
        )
    registros.sort(key=lambda r: (r["anio"], r["sb_codigo"]))
    return registros


def construir(texto: str) -> dict:
    registros = transformar(texto)
    ultimo = max(r["anio"] for r in registros)
    return {"fuente": "F01", "vigencia": f"{ultimo}-12-31", "probado": hoy(), "registros": registros}


if __name__ == "__main__":
    crudo = descargar(recurso_csv(DATASET), "poblacion_bevoelkerungsdichte.csv").decode("utf-8-sig")
    escribir(LAGO / "poblacion_stadtbezirke.json", construir(crudo))
