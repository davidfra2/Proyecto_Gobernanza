"""Exploración de la herramienta de vistas: los mismos datos de web/ en Streamlit.

No es parte del sistema publicado: sirve para comparar Streamlit con el código propio (web/) con la
misma serie, como pide la bitácora de exploración. Reproduce el mapa por distrito, P1, P2 y la
fuente a un clic.

Uso (en un entorno aparte, porque el sistema no instala nada):
    python3 -m venv .venv-streamlit && .venv-streamlit/bin/pip install streamlit==1.50.0
    .venv-streamlit/bin/streamlit run explorar/vistas_streamlit.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st

RAIZ = Path(__file__).resolve().parent.parent


@st.cache_data
def leer(ruta: str) -> dict:
    return json.loads((RAIZ / ruta).read_text(encoding="utf-8"))


pob = leer("lago/poblacion_stadtbezirke.json")
des = leer("lago/desempleo_stadtbezirke.json")
geo = leer("territorio/stadtbezirke.geojson")
listas = leer("catalogo/listas.json")
fichas = {f["id"]: f for f in (leer(f"catalogo/{p.name}") for p in sorted((RAIZ / "catalogo").glob("F*.json")))}
lago = {d["fuente"]: d for d in (pob, des, geo)}


def fuente(id_fuente: str) -> None:
    """La fuente a un clic: un popover con ID, vigencia, fecha de prueba y licencia."""
    f, d = fichas[id_fuente], lago[id_fuente]
    with st.popover(f"Fuente {id_fuente} · vigente a {d['vigencia']} · probado {d['probado']}", use_container_width=False):
        st.markdown(f"**{f['id']} · {f['nombre']}**")
        st.write(listas["entidades"][f["entidad"]]["nombre"])
        st.write(f"Licencia, tal como aparece: {f['licencia_texto']}")
        st.write(f"Probado: {f['probado']} · {f['respuesta']}")
        st.markdown(f"[URL exacta]({f['url']})")


st.set_page_config(page_title="München · exploración en Streamlit", layout="wide")
st.title("München · exploración en Streamlit")
st.caption("Juan Carlos Muñoz · David Felipe Rios · Samuel Molina — prueba de herramienta, no es el sistema publicado")

df_pob = pd.DataFrame(pob["registros"])
df_des = pd.DataFrame(des["registros"])
nombres = {f["properties"]["sb_codigo"]: f["properties"]["sb_nombre"] for f in geo["features"]}
a0, a1 = df_pob["anio"].min(), df_pob["anio"].max()
ad = df_des["anio"].max()

indicador = st.radio("El mapa muestra", ["Densidad", "Desempleo"], horizontal=True)
ultimo = df_pob[df_pob["anio"] == a1].set_index("sb_codigo")
desempleo = df_des[df_des["anio"] == ad].set_index("sb_codigo")
valores = ultimo["densidad_hab_km2"] if indicador == "Densidad" else desempleo["desempleo_pct"]
distritos = valores.drop("00")
cortes = distritos.quantile([0.2, 0.4, 0.6, 0.8]).tolist()
rampa = [[134, 182, 239], [85, 152, 231], [42, 120, 214], [28, 92, 171], [13, 54, 107]]
for f in geo["features"]:
    v = distritos[f["properties"]["sb_codigo"]]
    f["properties"]["valor"] = float(v)
    f["properties"]["relleno"] = rampa[sum(v > c for c in cortes)]

st.pydeck_chart(pdk.Deck(
    layers=[pdk.Layer("GeoJsonLayer", geo, pickable=True, stroked=True, filled=True,
                      get_fill_color="properties.relleno", get_line_color=[255, 255, 255], line_width_min_pixels=1)],
    initial_view_state=pdk.ViewState(latitude=48.14, longitude=11.55, zoom=9.6),
    tooltip={"text": "{sb_codigo} {sb_nombre}: {valor}"},
    map_style=None,
))
fuente("F01" if indicador == "Densidad" else "F02")
fuente("F03")

st.subheader(f"P1 · Crecimiento de la población, {a0} → {a1}")
base = df_pob[df_pob["anio"] == a0].set_index("sb_codigo")["poblacion"]
crec = ((ultimo["poblacion"] / base - 1) * 100).drop("00").dropna().sort_values()
crec.index = [f"{c} {nombres[c]}" for c in crec.index]
st.bar_chart(crec, horizontal=True)
st.caption("08 Schwanthalerhöhe no aparece: la fuente reserva su población («X»). En web/ se muestra derivada y marcada.")
fuente("F01")

st.subheader(f"P2 · Desempleo por distrito, {ad}")
serie = desempleo["desempleo_pct"].drop("00").sort_values()
serie.index = [f"{c} {nombres[c]}" for c in serie.index]
st.bar_chart(serie, horizontal=True)
fuente("F02")
