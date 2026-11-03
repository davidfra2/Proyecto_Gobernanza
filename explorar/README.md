# Exploraciones · dos herramientas por tramo

Cada script prueba una herramienta sobre **los mismos datos** que usa el sistema y deja el resultado
para la bitácora de exploración del [README](../README.md). Nada de esto lo usa el sistema publicado: la
ingesta y la verificación siguen sin instalar nada.

Cada herramienta se instala **en su propio entorno**, porque se pisan entre sí (dlt trae DuckDB 1.5.6
y el rastreo usa la 2.0.0) y porque así se mide limpio cuánto pide cada una. Desde la raíz del repositorio:

```bash
python3 -m venv /tmp/entorno && /tmp/entorno/bin/pip install <paquete>   # en Windows: entorno\Scripts\pip
```

| Tramo | Script | Paquete (versión probada) | Base contra la que se compara |
|---|---|---|---|
| Rastreo y catálogo | [perfil_stdlib.py](perfil_stdlib.py) | ninguno | — |
| Rastreo y catálogo | [perfil_duckdb.py](perfil_duckdb.py) | `duckdb==2.0.0` | `perfil_stdlib.py` |
| Ingesta | [ingesta_dlt.py](ingesta_dlt.py) | `dlt[duckdb]==1.32.0` | `ingesta/pull_escucha.py` |
| Lago | [lago_ducklake.py](lago_ducklake.py) | `duckdb==2.0.0` (+ `INSTALL ducklake`) | el historial de Git de `lago/` |
| Verificación | [verificar_frictionless.py](verificar_frictionless.py) | `frictionless==5.21.0` | `verificacion/verificar.py` |
| Vistas | [vistas_streamlit.py](vistas_streamlit.py) | `streamlit==1.50.0` (con `pydeck==0.9.3`) | `web/` |

Lo que conviene saber antes de correrlas (detalle en la bitácora):

- **DuckDB descarga extensiones binarias sin avisar** la primera vez que se necesitan: `httpfs`
  (52,7 MB) para leer URL y `ducklake` (48,4 MB), en `~/.duckdb`.
- **dlt envía telemetría por defecto** a `telemetry.scalevector.ai`. Para desactivarla:
  `RUNTIME__DLTHUB_TELEMETRY=false`.
- `ingesta_dlt.py` y `lago_ducklake.py` crean su base en una carpeta temporal, fuera del repositorio;
  se les puede pasar otra carpeta como argumento.
