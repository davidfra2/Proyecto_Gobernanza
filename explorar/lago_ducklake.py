"""Exploración · tramo Lago · herramienta B: DuckLake (la A es el lago en JSON con su historial en Git).

Pregunta: el DWD corrige meses provisionales (F04). ¿Qué valor tenía marzo de 2026 antes de la
corrección, y desde qué descarga cambió? Con JSON + Git la respuesta está en `git log -p`; aquí se
cargan las mismas tres versiones del lago (las de los commits de abajo) en un DuckLake, que guarda una
instantánea por carga y deja consultar la tabla como estaba en cada una.

Uso (desde la raíz del repositorio):
    python3 -m pip install duckdb==2.0.0
    python3 explorar/lago_ducklake.py [carpeta para el DuckLake, fuera del repositorio]
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parent.parent
ARCHIVO = "lago/clima_muenchen_stadt.json"
# Las tres descargas del clima que están en el historial del repositorio
VERSIONES = {"2026-10-12": "86af63d", "2026-11-01": "2de163c", "2026-11-03": "3495b05"}
DESTINO = Path(sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp(prefix="ducklake_muenchen_"))


def lago_en(commit: str) -> dict:
    texto = subprocess.run(["git", "show", f"{commit}:{ARCHIVO}"], cwd=RAIZ, capture_output=True, check=True).stdout
    return json.loads(texto.decode("utf-8"))


if __name__ == "__main__":
    con = duckdb.connect()
    con.execute("INSTALL ducklake; LOAD ducklake")
    con.execute(f"ATTACH 'ducklake:{(DESTINO / 'catalogo.ducklake').as_posix()}' AS lago (DATA_PATH '{(DESTINO / 'datos').as_posix()}/')")
    con.execute("""CREATE TABLE IF NOT EXISTS lago.clima (mes VARCHAR, temp_media_c DOUBLE, temp_max_media_c DOUBLE,
                   temp_min_media_c DOUBLE, precipitacion_mm DOUBLE, sol_horas DOUBLE, nivel_calidad INTEGER, probado VARCHAR)""")
    for probado, commit in VERSIONES.items():
        datos = lago_en(commit)
        assert datos["probado"] == probado, (commit, datos["probado"])
        filas = [tuple(r[c] for c in ("mes", "temp_media_c", "temp_max_media_c", "temp_min_media_c", "precipitacion_mm",
                                       "sol_horas", "nivel_calidad")) + (probado,) for r in datos["registros"]]
        con.execute("BEGIN")
        con.execute("DELETE FROM lago.clima")
        con.executemany("INSERT INTO lago.clima VALUES (?, ?, ?, ?, ?, ?, ?, ?)", filas)
        con.execute("COMMIT")
        print(f"carga del {probado} ({commit}): {len(filas)} meses")
    instantaneas = con.execute("SELECT snapshot_id FROM ducklake_snapshots('lago') ORDER BY snapshot_id").fetchall()
    print("instantáneas:", [s[0] for s in instantaneas])
    ultimas = [s[0] for s in instantaneas][-3:]  # una por carga
    for mes in ("2026-03", "2026-07"):
        fila = [con.execute(f"SELECT sol_horas, nivel_calidad FROM lago.clima AT (VERSION => {v}) WHERE mes = '{mes}'").fetchone() for v in ultimas]
        print(f"{mes} (sol_horas, nivel_calidad) en cada carga:", fila)
    print("meses en cada carga:", [con.execute(f"SELECT min(mes) || ' – ' || max(mes) FROM lago.clima AT (VERSION => {v})").fetchone()[0] for v in ultimas])
    cambios = con.execute(f"SELECT change_type, mes, sol_horas, nivel_calidad FROM ducklake_table_changes('lago', 'main', 'clima', {ultimas[0] + 1}, {ultimas[-1]}) "
                          "WHERE change_type <> 'delete' ORDER BY mes LIMIT 3").fetchall()
    # Con una recarga completa (DELETE + INSERT), el registro de cambios marca todas las filas como nuevas:
    # no aísla las correcciones. Para eso habría que cargar con MERGE por mes.
    print("ducklake_table_changes con recarga completa (todo sale como insert):", cambios)
    tamano = sum(p.stat().st_size for p in DESTINO.rglob("*") if p.is_file())
    print(f"DuckLake: {tamano / 1e3:.0f} kB en {DESTINO} (catálogo + {len(list((DESTINO / 'datos').rglob('*.parquet')))} archivos Parquet)")
