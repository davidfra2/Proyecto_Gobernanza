"""Funciones comunes de la ingesta. Solo biblioteca estándar de Python 3.12.

Cada archivo del lago tiene la misma envoltura:
    {"fuente": "F01", "vigencia": "AAAA-MM-DD", "probado": "AAAA-MM-DD", "registros": [...]}
- fuente: ID de la fuente en el catálogo (hoja «1. Fuentes» del diccionario).
- vigencia: hasta qué fecha cubren los datos.
- probado: día en que el script descargó la fuente de verdad.
"""

from __future__ import annotations

import json
import os
import urllib.request
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
LAGO = RAIZ / "lago"
RAW = LAGO / "raw"
UA = {"User-Agent": "taller-gobernanza-datos-eafit/1.0 (curso universitario; Proyecto_Gobernanza)"}


def hoy() -> str:
    """Fecha de prueba. PROBADO permite fijarla al reconstruir con crudos ya descargados."""
    return os.environ.get("PROBADO", date.today().isoformat())


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


def escribir(ruta: Path, contenido: dict) -> None:
    """Escribe JSON ordenado y estable: correr dos veces deja el mismo archivo."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(contenido, ensure_ascii=False, indent=1, sort_keys=False)
    ruta.write_text(texto + "\n", encoding="utf-8")
    print(f"{ruta.relative_to(RAIZ)}: {len(contenido.get('registros', contenido.get('features', [])))} registros")
