"""Funciones comunes de la ingesta. Solo biblioteca estándar; corre desde Python 3.9.

Cada archivo del lago tiene la misma envoltura:
    {"fuente": "F01", "vigencia": "AAAA-MM-DD", "probado": "AAAA-MM-DD", "registros": [...]}
- fuente: ID de la fuente en el catálogo (hoja «1. Fuentes» del diccionario).
- vigencia: hasta qué fecha cubren los datos.
- probado: día en que el script descargó la fuente de verdad.
"""

from __future__ import annotations

import json
import urllib.request
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
LAGO = RAIZ / "lago"
RAW = LAGO / "raw"
UA = {"User-Agent": "taller-gobernanza-datos-eafit/1.0 (curso universitario; Proyecto_Gobernanza)"}
CKAN = "https://opendata.muenchen.de/api/3/action/package_show?id="


def hoy() -> str:
    """Fecha de prueba: el día en que el script descargó la fuente. No se puede fijar a mano,
    porque cada script vuelve a descargar y la fecha tiene que ser la de esa descarga."""
    return date.today().isoformat()


def recurso_csv(dataset: str) -> str:
    """URL vigente del CSV de un conjunto de opendata.muenchen.de.

    La ciudad renombra el archivo en cada actualización (…_18_05_26.csv): fijar la URL deja
    al script bajando una versión vieja o un 404. Se pregunta al catálogo CKAN cada vez.
    """
    pedido = urllib.request.Request(CKAN + dataset, headers=UA)
    with urllib.request.urlopen(pedido, timeout=60) as respuesta:
        recursos = json.loads(respuesta.read())["result"]["resources"]
    csvs = [r for r in recursos if r.get("format", "").upper() == "CSV"]
    if not csvs:
        raise RuntimeError(f"El conjunto {dataset} no tiene ningún recurso CSV")
    return max(csvs, key=lambda r: r.get("last_modified") or r.get("created") or "")["url"]


def descargar(url: str, nombre_crudo: str) -> bytes:
    """Baja la URL y guarda el crudo en lago/raw/ (que nunca se sube al repositorio)."""
    pedido = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(pedido, timeout=120) as respuesta:
        datos = respuesta.read()
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / nombre_crudo).write_bytes(datos)
    return datos


def numero(texto: str) -> float | None:
    """'X', '-999', '' y similares son faltantes: se vuelven None, nunca 0."""
    texto = texto.strip().replace(" ", "")
    if texto in {"", "X", "x", "-", ".", "-999"}:
        return None
    return float(texto)


def escribir(ruta: Path, contenido: dict, compacto: bool = False) -> None:
    """Escribe JSON ordenado y estable: correr dos veces deja el mismo archivo, en Windows o en Mac.

    compacto=True escribe una sola línea (para el GeoJSON, que con sangría pesaría el triple).
    """
    ruta.parent.mkdir(parents=True, exist_ok=True)
    if compacto:
        texto = json.dumps(contenido, ensure_ascii=False, separators=(",", ":"))
    else:
        texto = json.dumps(contenido, ensure_ascii=False, indent=1, sort_keys=False)
    # newline="\n": sin esto Windows escribe \r\n y el archivo cambia entero según la máquina
    with open(ruta, "w", encoding="utf-8", newline="\n") as archivo:
        archivo.write(texto + "\n")
    print(f"{ruta.relative_to(RAIZ)}: {len(contenido.get('registros', contenido.get('features', [])))} registros")
