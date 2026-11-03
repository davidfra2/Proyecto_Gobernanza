"""Exploración · tramo Verificación · herramienta B: Frictionless (la A es verificacion/verificar.py).

Genera un Table Schema por archivo del lago a partir de catalogo/diccionario.json (tipos, campos
obligatorios y llave primaria) y valida los registros contra él. Después rompe una copia del lago a
propósito y compara qué atrapa Frictionless y qué atrapa verificar.py.

Uso (desde la raíz del repositorio):
    python3 -m pip install frictionless
    python3 explorar/verificar_frictionless.py
"""

from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from frictionless import Resource, Schema

RAIZ = Path(__file__).resolve().parent.parent
DICCIONARIO = json.loads((RAIZ / "catalogo/diccionario.json").read_text(encoding="utf-8"))["campos"]
LLAVES = {"lago/poblacion_stadtbezirke.json": ["anio", "sb_codigo"], "lago/desempleo_stadtbezirke.json": ["anio", "sb_codigo"],
          "lago/clima_muenchen_stadt.json": ["mes"], "lago/escucha.json": ["mes"]}
TIPO = {"entero": "integer", "decimal": "number", "texto": "string", "fecha": "date"}


def esquema(ruta: str, ejemplo: dict) -> Schema:
    campos = []
    for c in DICCIONARIO:
        if c["archivo"] != ruta or c["campo"] in ("fuente", "vigencia", "probado"):
            continue
        tipo = TIPO.get(c["tipo"], "string")
        if c["tipo"] == "fecha" and c["campo"] == "mes":
            tipo = "yearmonth"
        if c["tipo"] == "codigo":  # «código» puede ser texto (sb_codigo) o entero (nivel_calidad), según venga
            tipo = "integer" if isinstance(ejemplo.get(c["campo"]), int) else "string"
        campos.append({"name": c["campo"], "type": tipo, "constraints": {"required": not c["puede_vacio"]}})
    return Schema.from_descriptor({"fields": campos, "primaryKey": LLAVES[ruta]})


def validar(raiz: Path) -> dict[str, list[str]]:
    errores = {}
    for ruta in LLAVES:
        registros = json.loads((raiz / ruta).read_text(encoding="utf-8"))["registros"]
        nombres = [f.name for f in esquema(ruta, registros[0]).fields]
        filas = [nombres] + [[r.get(n) for n in nombres] for r in registros]
        informe = Resource(data=filas, schema=esquema(ruta, registros[0])).validate()
        errores[ruta] = [f"{e.type}: {e.note}"[:110] for t in informe.tasks for e in t.errors]
    return errores


if __name__ == "__main__":
    print("== lago real")
    for ruta, errores in validar(RAIZ).items():
        print(f"{ruta}: {len(errores)} errores")
    # Dos copias rotas a propósito. verificar.py para en la estructura si un tipo está mal, así que el error de
    # estructura y los de valor van en copias distintas para que las dos herramientas vean lo mismo.
    def romper_estructura(copia: Path) -> None:  # un tipo equivocado
        esc = json.loads((copia / "lago/escucha.json").read_text(encoding="utf-8"))
        esc["registros"][3]["vistas"] = "muchas"
        (copia / "lago/escucha.json").write_text(json.dumps(esc, ensure_ascii=False), encoding="utf-8")

    def romper_valores(copia: Path) -> None:  # un registro repetido y una densidad que no cuadra con población / superficie
        pob = json.loads((copia / "lago/poblacion_stadtbezirke.json").read_text(encoding="utf-8"))
        pob["registros"].append(copy.deepcopy(pob["registros"][5]))
        pob["registros"][30]["densidad_hab_km2"] *= 2
        (copia / "lago/poblacion_stadtbezirke.json").write_text(json.dumps(pob, ensure_ascii=False), encoding="utf-8")

    for nombre, romper in (("tipo equivocado", romper_estructura), ("repetido + densidad que no cuadra", romper_valores)):
        copia = Path(tempfile.mkdtemp(prefix="lago_roto_"))
        for carpeta in ("lago", "territorio", "catalogo", "verificacion", "ingesta", "web"):
            shutil.copytree(RAIZ / carpeta, copia / carpeta, ignore=shutil.ignore_patterns("raw"))
        shutil.copy(RAIZ / ".vercelignore", copia / ".vercelignore")
        romper(copia)
        print(f"== copia rota ({nombre}): Frictionless")
        for ruta, errores in validar(copia).items():
            for e in errores:
                print(f"  {ruta}: {e}")
        print(f"== copia rota ({nombre}): verificar.py")
        salida = subprocess.run([sys.executable, "-X", "utf8", str(copia / "verificacion/verificar.py")],
                                capture_output=True, text=True, encoding="utf-8")
        print("  " + salida.stdout.strip().replace("\n", "\n  "))
        shutil.rmtree(copia)
