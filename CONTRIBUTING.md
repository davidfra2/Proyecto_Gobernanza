# Cómo trabajamos

Réplica del Cerebro Lima para **München (Múnich), Alemania**.
Taller: https://gobernanzadatos.vercel.app/tallerdatos

## 1. Papeles: cada quien elige el suyo

El taller define cuatro papeles. Somos tres, así que **uno se comparte**.

| Papel | Tramos | Responde por | Revisa a |
|---|---|---|---|
| **Curaduría** | Rastreo, permiso, catálogo | Fuentes, licencias y fichas del catálogo | Interfaz: que cada cifra de las vistas llegue a su ficha |
| **Datos** | Contrato, ingesta, lago, verificación | Que el lago se reconstruya igual con un comando | Curaduría: que lo integrado exista y diga lo que el catálogo dice |
| **Interfaz** | Herramienta, vistas, compuerta (`api/`) | Que abra en un teléfono y se entienda | Datos: que haya comprobaciones de lo que se muestra |
| **Seguridad** | Protección, secretos, datos personales | Atacar el sistema antes que nadie | Todo lo que se publica, incluido el historial del repositorio |

**Regla del taller:** Seguridad la asume alguien que **no** construyó la compuerta.
Si Interfaz construye `api/`, Seguridad se suma a Curaduría o a Datos.

### Cómo elegir

Cada uno escribe su nombre en la tabla de abajo, en el papel o los papeles que quiere, y lo
sube directo a `main`. Si dos eligen lo mismo, lo hablan antes de cambiar la tabla.

| Persona | Usuario GitHub | Papel principal | Papel compartido |
|---|---|---|---|
| Juan Carlos Muñoz | katals | Curaduría | — |
| David Felipe Rios | davidfra2 | Interfaz | — |
| Samuel Molina  | Smuel24 | Datos | — |

La exploración de herramientas no es de un papel: cada papel prueba **al menos dos
herramientas** en sus tramos y las anota en la bitácora del README.

### Qué entrega cada papel

**Curaduría** — sale del tramo cuando:
- [x] Cada fuente tiene su ficha en `catalogo/`, con `probado`, `estado`, `licencia` y `personas`.
- [x] Hay fuentes de al menos **tres familias** distintas (estadística, territorio, ambiente,
      economía, movilidad, lo que se dice…).
- [x] Las fuentes caídas o descartadas también tienen ficha, con el error exacto.
- [x] `catalogo/listas.json` define las listas cerradas de `entidad` y `licencia`.
- [x] El README dice qué **no existe** abierto para München (sección «Huecos»).
- [ ] Al menos dos herramientas de rastreo probadas (p. ej. DuckDB, QGIS, Overture Maps) y
      anotadas en la bitácora de exploración.
- [ ] Más adelante: revisar que cada cifra de las vistas llegue a su ficha.

Por dónde empezar en München (verificar cada enlace antes de catalogarlo):
estadística de la ciudad y de Baviera, portal de datos abiertos de la ciudad, geodatos de
Baviera, meteorología (DWD), transporte (GTFS), OpenStreetMap / Overture Maps, Sentinel-2,
Wikipedia Pageviews y GDELT.

## 2. Flujo con Git

`main` siempre funciona. Antes de empezar: `git pull`.

**Directo a `main`** — cambios pequeños dentro de tu propio tramo:
- Fichas del catálogo, textos del README y de las bitácoras, tu fila en la tabla de papeles.
- Pruebas de herramientas en `explorar/`, que no afectan al sistema.

**Rama y pull request** — lo que afecta a otros o el taller pide que revise otra persona:
- Código de `ingesta/`, `verificacion/`, `web/` y `api/`, y cambios al formato del lago o del catálogo.
- Ramas con nombre corto y vida corta (1–3 días): `ingesta/poblacion`, `vista/mapa`, `fix/verificacion-fechas`.
- Cada PR lo revisa y aprueba **alguien distinto** a quien lo abrió (ver la columna «Revisa a»).

En la duda, pull request. Y siempre: si la verificación falla, se arregla la ingesta,
**nunca** se afloja el verificador.

### Mensajes de commit

Formato [Conventional Commits](https://www.conventionalcommits.org/es/), en español e imperativo:

```
<tipo>(<tramo>): <qué hace>

feat(ingesta): descargar población por Stadtbezirk desde opendata.muenchen.de
fix(verificacion): rechazar cifras sin fecha de prueba
docs(catalogo): marcar <fuente> como caída (<error exacto> el <AAAA-MM-DD>)
```

Tipos: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `explore` (pruebas de herramientas).
Tramos: `catalogo`, `ingesta`, `lago`, `verificacion`, `vistas`, `api`, `seguridad`, `bitacora`.

## 3. Convenciones de código y datos

**Python (ingesta y verificación)**
- Python 3.9 o superior (el que trae macOS), solo biblioteca estándar. Un script por tema: `ingesta/pull_<tema>.py`.
- Nombres en `snake_case`; formato y lint con `ruff format` y `ruff check`.
- Cada script es **idempotente**: se puede correr dos veces y deja el mismo resultado.
- Nada de llaves de pago. Si una API pide llave gratuita, va en `.env` (nunca en el código).
- Dependencias en `requirements.txt` con versión fijada.

**Catálogo** (`catalogo/<ID>_<tema>.json`, una ficha por fuente, **incluidas las caídas y descartadas**)

El ID (F01, F02…) es el mismo del Excel «Diccionario de datos» y del campo `fuente` del lago.
Ejemplo completo: [catalogo/F01_poblacion_densidad.json](catalogo/F01_poblacion_densidad.json).

| Campo | Qué lleva |
|---|---|
| `id`, `nombre` | ID del Excel y nombre del conjunto tal como lo publica la fuente |
| `entidad`, `licencia`, `estado`, `personas`, `acceso` | Un valor de las **listas cerradas** de `catalogo/listas.json` |
| `licencia_texto`, `licencia_donde` | La licencia copiada tal como aparece, y dónde la leímos |
| `url`, `pagina` | URL exacta que se probó, y página del conjunto en su portal |
| `probado`, `respuesta` | Día de la prueba y lo que respondió (código HTTP, tipo, tamaño o error exacto) |
| `script`, `salida` | Script de ingesta y archivos del lago que produce (vacío si no está integrada) |
| `cobertura`, `periodo`, `frecuencia`, `formato` | Qué territorio y qué años cubre, cada cuánto se actualiza |
| `como_se_encontro`, `nota` | Si vino de la IA o de una búsqueda, y todo lo que hay que saber para usarla |

- `estado`: `integrado`, `candidato`, `caido`, `no_existe` (URL inventada por la IA), `declarado`, `excluido`.
- Las listas cerradas existen porque el catálogo de Lima escribió la licencia de 34 maneras
  distintas. Para añadir una entidad o licencia nueva, se añade primero a `listas.json`.
- `verificar.py` comprueba el catálogo: campos completos, valores de las listas, que lo integrado
  tenga licencia, script y salida, y que cada archivo del lago apunte a una ficha integrada.
- Cruzar territorio por **código oficial** (AGS / código de Stadtbezirk), nunca por nombre.

**Lago**
- `lago/raw/` guarda los crudos (bronce) y **nunca se sube** al repositorio (está en `.gitignore`).
- `lago/` guarda el dato limpio (plata); cada cifra lleva `fuente`, `vigencia` y `probado`.
- Fechas en ISO 8601 (`AAAA-MM-DD`). Codificación UTF-8.

**Secretos y datos personales**
- Claves y contraseñas solo en `.env` local o en variables de entorno de Vercel.
- Nunca en el JavaScript de `web/`. Seguridad revisa el historial antes de cada entrega.
- Alemania aplica el RGPD (DSGVO): si una fuente trae datos de personas, se marca en
  `personas` y se decide su protección antes de integrarla.

## 4. Uso de IA

Toda ayuda de IA se registra en la **Bitácora de IA** del README: qué se le pidió, qué entregó
y **qué se le corrigió**. Ninguna fuente entra al catálogo hasta que alguien del grupo abre el
enlace o un script lo descarga.
