"""Exploración · tramo Ingesta · herramienta B: dlt (la A es ingesta/pull_escucha.py).

La misma fuente que el script base (F05, vistas de «München» en de.wikipedia, misma URL), cargada con
dlt en una base DuckDB. Se corre dos veces con «replace» y una con «append» para ver qué hace dlt con
las cargas repetidas, y al final se compara con lago/escucha.json.

Uso (desde la raíz del repositorio):
    python3 -m pip install "dlt[duckdb]"
    python3 explorar/ingesta_dlt.py [carpeta para la base de dlt, fuera del repositorio]
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import dlt
import duckdb
from dlt.sources.helpers import requests

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "ingesta"))
from comun import UA  # noqa: E402
from pull_escucha import url  # noqa: E402  (la misma URL que usa el script base)

DESTINO = Path(sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp(prefix="dlt_muenchen_"))


def vistas(disposicion: str):
    @dlt.resource(name="vistas_wikipedia", write_disposition=disposicion)
    def recurso():
        respuesta = requests.get(url(), headers=UA)
        respuesta.raise_for_status()
        yield respuesta.json()["items"]
    return recurso


def correr(disposicion: str) -> None:
    pipeline = dlt.pipeline(pipeline_name="muenchen", pipelines_dir=str(DESTINO / "estado"),
                            destination=dlt.destinations.duckdb(str(DESTINO / "muenchen.duckdb")), dataset_name="escucha")
    info = pipeline.run(vistas(disposicion)())
    print(f"{disposicion}: {len(info.loads_ids)} carga(s)")


if __name__ == "__main__":
    for disposicion in ("replace", "replace", "append"):
        correr(disposicion)
    con = duckdb.connect(str(DESTINO / "muenchen.duckdb"), read_only=True)
    print("tablas:", sorted(t[0] for t in con.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'escucha'").fetchall()))
    print("columnas de vistas_wikipedia:", [c[0] for c in con.execute("DESCRIBE escucha.vistas_wikipedia").fetchall()])
    filas, distintas = con.execute("SELECT count(*), count(DISTINCT timestamp) FROM escucha.vistas_wikipedia").fetchone()
    print(f"filas tras replace, replace, append: {filas} ({distintas} meses distintos)")
    print("registro de cargas (_dlt_loads):", con.execute("SELECT count(*) FROM escucha._dlt_loads").fetchone()[0])
    # ¿Dice lo mismo que el lago del script base?
    dlt_vistas = dict(con.execute("SELECT left(timestamp, 6), views FROM escucha.vistas_wikipedia "
                                  "QUALIFY row_number() OVER (PARTITION BY timestamp ORDER BY _dlt_load_id DESC) = 1").fetchall())
    lago = {r["mes"].replace("-", ""): r["vistas"] for r in json.loads((RAIZ / "lago/escucha.json").read_text(encoding="utf-8"))["registros"]}
    print("mismas cifras que lago/escucha.json:", dlt_vistas == lago, f"({len(lago)} meses)")
    tamano = sum(p.stat().st_size for p in DESTINO.rglob("*") if p.is_file())
    print(f"dlt dejó {tamano / 1e6:.1f} MB en {DESTINO}")
