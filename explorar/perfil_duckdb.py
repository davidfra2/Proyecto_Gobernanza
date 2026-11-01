"""Exploración · tramo Rastreo y catálogo (Curaduría) · herramienta B: DuckDB.

La misma pregunta que perfil_stdlib.py, sobre los mismos CSV: filas, columnas, años, zonas, cortes y
valores reservados («X»). DuckDB lee el CSV directamente desde la URL y lo consulta con SQL, sin
guardarlo antes en disco.

Uso (desde la raíz del repositorio):
    python3 -m pip install duckdb==2.0.0
    python3 explorar/perfil_duckdb.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ingesta"))
from comun import recurso_csv  # noqa: E402

FUENTES = {"F01": "0be6dc92-9ca5-4ae9-8a08-ba4039f2a225", "F02": "0771b22f-b1e7-4480-8fe5-d641c2586f3e"}


def perfil(con: duckdb.DuckDBPyConnection, url: str) -> dict:
    # all_varchar: que DuckDB no adivine tipos, para poder contar las «X» tal como vienen (si los adivina,
    # «Basiswert 1» y «Basiswert 2» pasan enteras a texto sin avisar). Tabla y no vista: una vista volvería
    # a descargar el CSV en cada consulta.
    con.execute(f"CREATE OR REPLACE TEMP TABLE f AS SELECT * FROM read_csv('{url}', all_varchar = true)")
    filas, anio0, anio1, zonas = con.execute(
        "SELECT count(*), min(CAST(Jahr AS INT)), max(CAST(Jahr AS INT)), count(DISTINCT Raumbezug) FROM f").fetchone()
    reservados = con.execute("""
        SELECT count(*) FILTER (WHERE trim(Indikatorwert) = 'X'),
               count(*) FILTER (WHERE trim("Basiswert 1") = 'X'),
               count(*) FILTER (WHERE trim("Basiswert 2") = 'X')
        FROM f""").fetchone()
    return {
        "filas": filas,
        "columnas": [c[0] for c in con.execute("DESCRIBE f").fetchall()],
        "anios": [anio0, anio1],
        "zonas": zonas,
        "cortes": [r[0] for r in con.execute('SELECT DISTINCT "Ausprägung" FROM f ORDER BY 1').fetchall()],
        "reservados_X": dict(zip(("Indikatorwert", "Basiswert 1", "Basiswert 2"), reservados)),
        "zonas_con_X": [r[0] for r in con.execute(
            "SELECT DISTINCT Raumbezug FROM f WHERE trim(\"Basiswert 1\") = 'X' OR trim(\"Basiswert 2\") = 'X' ORDER BY 1").fetchall()],
    }


if __name__ == "__main__":
    inicio = time.perf_counter()
    con = duckdb.connect()  # en memoria: no deja ningún archivo
    resultado = {fid: perfil(con, recurso_csv(ds)) for fid, ds in FUENTES.items()}
    resultado["segundos"] = round(time.perf_counter() - inicio, 2)
    print(json.dumps(resultado, ensure_ascii=False, indent=1))
