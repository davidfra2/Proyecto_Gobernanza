"""F04 · Clima mensual de la estación DWD 03379 München-Stadt (Deutscher Wetterdienst, CDC).

Fuente: https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/monthly/kl/recent/
Licencia: CC BY 4.0 (condiciones de uso del Climate Data Center del DWD)
Salida:   lago/clima_muenchen_stadt.json

Decisiones:
- Se usa la carpeta «recent» (últimos ~18 meses). La serie larga está en «historical».
- El DWD marca los faltantes con -999: se guardan como null.
- QN_4 es el nivel de calidad del DWD: 1 = solo control formal, 3 = control automático,
  9 = no todos los parámetros corregidos, 10 = control terminado. Los meses recientes todavía
  pueden corregirse; por eso se guarda el nivel junto a cada mes.
- La estación queda en Neuhausen-Nymphenburg (distrito 09): describe la ciudad, no cada distrito.
"""

import csv
import io
import zipfile

from comun import LAGO, descargar, escribir, hoy, numero

URL = (
    "https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/monthly/kl/recent/"
    "monatswerte_KL_03379_akt.zip"
)


def transformar(texto: str) -> list[dict]:
    registros = []
    lector = csv.DictReader(io.StringIO(texto), delimiter=";", skipinitialspace=True)
    for fila in lector:
        fila = {k.strip(): v.strip() for k, v in fila.items() if k}
        inicio = fila["MESS_DATUM_BEGINN"]
        registros.append(
            {
                "mes": f"{inicio[:4]}-{inicio[4:6]}",
                "temp_media_c": numero(fila["MO_TT"]),
                "temp_max_media_c": numero(fila["MO_TX"]),
                "temp_min_media_c": numero(fila["MO_TN"]),
                "precipitacion_mm": numero(fila["MO_RR"]),
                "sol_horas": numero(fila["MO_SD_S"]),
                "nivel_calidad": int(fila["QN_4"]),
            }
        )
    registros.sort(key=lambda r: r["mes"])
    return registros


def construir(texto: str) -> dict:
    registros = transformar(texto)
    return {"fuente": "F04", "vigencia": registros[-1]["mes"], "probado": hoy(), "registros": registros}


if __name__ == "__main__":
    archivo = zipfile.ZipFile(io.BytesIO(descargar(URL, "dwd_monatswerte_KL_03379_akt.zip")))
    producto = next(n for n in archivo.namelist() if n.startswith("produkt_klima_monat"))
    texto = archivo.read(producto).decode("latin-1")  # el DWD publica en Latin-1, no en UTF-8
    escribir(LAGO / "clima_muenchen_stadt.json", construir(texto))
