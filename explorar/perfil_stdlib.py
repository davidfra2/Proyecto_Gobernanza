"""Exploración · tramo Rastreo y catálogo (Curaduría) · herramienta A: Python, solo biblioteca estándar.

Pregunta: antes de catalogar una fuente, ¿qué trae? Filas, columnas, años, zonas, cortes y valores
reservados («X»). Es lo que hay que saber para llenar su ficha. La misma pregunta, sobre los mismos
CSV, se responde con DuckDB en perfil_duckdb.py.

Uso (desde la raíz del repositorio): python3 explorar/perfil_stdlib.py
"""

from __future__ import annotations

import csv
import io
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ingesta"))
from comun import UA, recurso_csv  # noqa: E402

import urllib.request  # noqa: E402

FUENTES = {"F01": "0be6dc92-9ca5-4ae9-8a08-ba4039f2a225", "F02": "0771b22f-b1e7-4480-8fe5-d641c2586f3e"}


def perfil(url: str) -> dict:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        filas = list(csv.DictReader(io.StringIO(r.read().decode("utf-8-sig"))))
    anios = sorted({int(f["Jahr"]) for f in filas})
    return {
        "filas": len(filas),
        "columnas": list(filas[0]),
        "anios": [anios[0], anios[-1]],
        "zonas": len({f["Raumbezug"] for f in filas}),
        "cortes": sorted({f["Ausprägung"] for f in filas}),
        "reservados_X": {c: sum(f[c].strip() == "X" for f in filas) for c in ("Indikatorwert", "Basiswert 1", "Basiswert 2")},
        "zonas_con_X": sorted({f["Raumbezug"] for f in filas if "X" in (f["Basiswert 1"].strip(), f["Basiswert 2"].strip())}),
    }


if __name__ == "__main__":
    inicio = time.perf_counter()
    resultado = {fid: perfil(recurso_csv(ds)) for fid, ds in FUENTES.items()}
    resultado["segundos"] = round(time.perf_counter() - inicio, 2)
    print(json.dumps(resultado, ensure_ascii=False, indent=1))
