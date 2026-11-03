"""Vuelca el catálogo del repositorio al Excel «Diccionario de datos» que pide el taller.

La fuente de verdad es el repositorio (catalogo/F*.json y catalogo/diccionario.json). El Excel se
mantenía a mano y se separó del repositorio: fechas de prueba viejas, licencias resumidas en vez de
copiadas y una nota del 08 que ya no era cierta. Este script reescribe las hojas «1. Fuentes» y
«2. Diccionario» desde los JSON, borra la fila gris de ejemplo de Medellín (traía un campo que no
está en nuestro lago) y deja intactos el formato, las listas desplegables, la «3. Bitácora IA» y las
fórmulas del «Resumen».

Es el único script del repositorio que necesita algo fuera de la biblioteca estándar (openpyxl, ver
requirements-excel.txt); la ingesta y la verificación siguen sin instalar nada.

Uso: python3 catalogo/a_excel.py [plantilla.xlsx] [salida.xlsx]
     (por omisión lee y reescribe catalogo/Diccionario_de_datos_Muenchen.xlsx)
"""

from __future__ import annotations

import json
import re
import sys
from copy import copy
from pathlib import Path

import openpyxl
from openpyxl.worksheet.cell_range import MultiCellRange

RAIZ = Path(__file__).resolve().parent.parent
EXCEL = RAIZ / "catalogo" / "Diccionario_de_datos_Muenchen.xlsx"
PRIMERA, ULTIMA = 5, 44  # filas amarillas de la plantilla
# Hoja «Instrucciones»: datos del grupo y de esta entrega (lo demás es la plantilla del taller y no se toca)
INSTRUCCIONES = {
    "B1": "Taller de datos · Entrega 2 · El sistema: diccionario actualizado del lago",
    "B4": "Datos del grupo: Grupo Munich",
    "B6": "Grupo Munich · Integrantes: Juan Carlos Muñoz (Curaduría) · David Felipe Rios (Interfaz) · Samuel Molina (Datos)",
    "B7": "Repositorio: https://github.com/davidfra2/Proyecto_Gobernanza (carpetas lago/ y territorio/) · "
          "Sistema publicado: https://proyecto-gobernanza-muenchen.vercel.app",
}
EJEMPLO = 4  # fila gris de ejemplo (Medellín): se borra para que el Excel diga solo lo que hay en nuestro lago


def leer(ruta: Path) -> dict:
    return json.loads(ruta.read_text(encoding="utf-8"))


def escribir_filas(hoja, filas: list[list]) -> int:
    """Escribe las filas desde PRIMERA. Si no caben en las 40 de la plantilla, la extiende: copia el formato
    de la fila amarilla 44 y alarga las listas desplegables. Devuelve la última fila que usa la hoja.

    El script lee el Excel que él mismo generó la vez anterior, que puede venir ya extendido (o más largo
    de lo que hace falta ahora): por eso los rangos se reescriben desde cualquier última fila, no solo la 44."""
    ultima = max(ULTIMA, PRIMERA + len(filas) - 1)
    for n in range(ULTIMA + 1, ultima + 1):
        hoja.row_dimensions[n].height = hoja.row_dimensions[ULTIMA].height
        for col in range(1, hoja.max_column + 1):
            hoja.cell(n, col)._style = copy(hoja.cell(ULTIMA, col)._style)
    for validacion in hoja.data_validations.dataValidation:
        validacion.sqref = MultiCellRange(" ".join(
            re.sub(rf"^([A-Z]+){PRIMERA}:([A-Z]+)\d+$", rf"\g<1>{PRIMERA}:\g<2>{ultima}", str(rango)) for rango in validacion.sqref.ranges))
    for n in range(PRIMERA, max(ultima, hoja.max_row) + 1):  # también vacía lo que sobre de una vez anterior
        for col in range(1, hoja.max_column + 1):
            hoja.cell(n, col).value = None
    for n, fila in enumerate(filas, start=PRIMERA):
        for col, valor in enumerate(fila, start=1):
            hoja.cell(n, col).value = valor
    return ultima


def extender_resumen(libro, ultimas: dict[str, int]) -> None:
    """Las fórmulas del «Resumen» cuentan las filas 5 a 44 de cada hoja; cada rango se ajusta a la última fila
    de su hoja, venga de la plantilla original o de una generación anterior."""
    def ajustar(m: re.Match) -> str:
        hoja = m.group(1)
        return f"'{hoja}'!{m.group(2)}{PRIMERA}:{m.group(3)}{ultimas.get(hoja, ULTIMA)}"
    for fila in libro["Resumen"].iter_rows():
        for celda in fila:
            if isinstance(celda.value, str) and celda.value.startswith("="):
                celda.value = re.sub(rf"'([^']+)'!([A-Z]+){PRIMERA}:([A-Z]+)\d+", ajustar, celda.value)


def main() -> None:
    plantilla = Path(sys.argv[1]) if len(sys.argv) > 1 else EXCEL
    salida = Path(sys.argv[2]) if len(sys.argv) > 2 else EXCEL
    listas = leer(RAIZ / "catalogo" / "listas.json")
    fichas = [leer(p) for p in sorted((RAIZ / "catalogo").glob("F*.json"))]
    campos = leer(RAIZ / "catalogo" / "diccionario.json")["campos"]
    libro = openpyxl.load_workbook(plantilla)

    # 1. Fuentes: todas las fichas, también las que no entraron (explican las decisiones)
    fuentes = []
    for f in fichas:
        entidad = listas["entidades"][f["entidad"]]
        formato = listas["formatos"][f["formato"]]["excel"]
        frecuencia = listas["frecuencias"][f["frecuencia"]]["excel"]
        fuentes.append([
            f["id"], f["nombre"], entidad["nombre"], listas["tipos_publicador"][entidad["tipo"]]["excel"], f["url"],
            formato, listas["accesos"][f["acceso"]]["excel"],
            # La licencia se copia tal como aparece; si la fuente no la dice, «no declara» (instrucciones del Excel)
            f["licencia_texto"] or "no declara",
            listas["personas"][f["personas"]]["excel"], f.get("cobertura"), f.get("periodo"),
            frecuencia, f["probado"], listas["estados"][f["estado"]]["excel"], f["como_se_encontro"],
            " ".join(t for t in (
                f"Formato: {f['formato_detalle']}." if f.get("formato_detalle") else "",
                f"Frecuencia: {f['frecuencia_detalle']}." if f.get("frecuencia_detalle") else "",
                f"Licencia leída en: {f['licencia_donde']}." if f.get("licencia_donde") else "",
                f"Respuesta el {f['probado']}: {f['respuesta']}.",
                f["nota"] or "",
            ) if t),
        ])
    ultima_fuentes = escribir_filas(libro["1. Fuentes"], fuentes)

    # 2. Diccionario: solo los campos que están en el lago (verificar.py comprueba que coincidan)
    preguntas = listas["preguntas"]
    diccionario = [[
        c["fuente"], c["archivo"], c["campo"], c["nombre_original"], c["significado"],
        listas["tipos_dato"][c["tipo"]]["excel"], c["unidad"] or "—", str(c["ejemplo"]),
        "Sí" if c["puede_vacio"] else "No", c["valores_permitidos"],
        listas["clasificaciones"][c["clasificacion"]]["excel"], c["transformacion"],
        " | ".join(f"{'Todas' if p == 'TODAS' else p}: {preguntas[p]}" for p in c["preguntas"]),
    ] for c in campos]
    ultima_diccionario = escribir_filas(libro["2. Diccionario"], diccionario)
    extender_resumen(libro, {"1. Fuentes": ultima_fuentes, "2. Diccionario": ultima_diccionario})

    for nombre in ("1. Fuentes", "2. Diccionario", "3. Bitácora IA"):
        hoja = libro[nombre]
        for col in range(1, hoja.max_column + 1):
            hoja.cell(EJEMPLO, col).value = None

    for celda, texto in INSTRUCCIONES.items():
        libro["Instrucciones"][celda].value = texto

    libro.save(salida)
    print(f"{salida.relative_to(RAIZ) if salida.is_relative_to(RAIZ) else salida}: {len(fuentes)} fuentes, {len(diccionario)} campos")


if __name__ == "__main__":
    main()
