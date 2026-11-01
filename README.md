# München · sistema de información

Grupo: Juan Carlos Muñoz (Curaduría) · David Felipe Rios (Interfaz) · Samuel Molina (Datos) · Enlace: <url de las vistas> · Repositorio: https://github.com/davidfra2/Proyecto_Gobernanza · Revisado: 2026-11-01

Réplica del Cerebro Lima para Múnich. Cómo trabajamos: [CONTRIBUTING.md](CONTRIBUTING.md) · Gobierno de datos según el DMBOK: [GOBIERNO.md](GOBIERNO.md).

Reconstruir y comprobar el lago (Python 3.9 o superior, sin instalar nada):

```bash
cd ingesta && for s in pull_poblacion pull_desempleo pull_territorio pull_clima pull_escucha; do python3 $s.py; done; cd ..
python3 verificacion/verificar.py
```

## Para quién y qué pregunta
- Usuario: un concejal o un comité de distrito (Bezirksausschuss) de München que necesita comparar los 25 Stadtbezirke con cifras oficiales y fechadas antes de decidir dónde intervenir.
- Preguntas (entre tres y seis), definidas en [catalogo/listas.json](catalogo/listas.json) y citadas por cada campo del diccionario:
  - **P1** · ¿Cuánta gente vive en cada distrito y dónde crece más rápido? (F01, F03)
  - **P2** · ¿En qué distritos pesa más el desempleo y cómo cambió desde 2015? (F02, F03)
  - **P3** · ¿Cómo cambian el calor y la lluvia de la ciudad mes a mes? (F04)
  - **P4** · ¿Cuánto interés despierta München fuera de la ciudad y en qué meses sube? (F05)
- Escala y comparación: los 25 Stadtbezirke y la ciudad (código 00), de 2015 al último año publicado (2025 en población, 2024 en desempleo); el clima y el interés en Wikipedia, por mes y para la ciudad entera.
- Lo que decidimos no mostrar, y por qué: los cortes de desempleo por sexo y nacionalidad (F02), para no facilitar el señalamiento de barrios por nacionalidad; la religión por distrito (F10), que no responde ninguna pregunta; y los crudos de `lago/raw/`, que traen esos cortes.

## La réplica
- Qué replicamos tal cual del ejemplo y qué tuvimos que cambiar para nuestra ciudad: replicamos la anatomía de carpetas del Cerebro Lima (`ingesta/`, `catalogo/`, `lago/` con `raw/` fuera del repositorio, `territorio/`, `verificacion/`, `api/`, `web/`), la ingesta con Python y solo la biblioteca estándar, el lago en JSON y un verificador propio que bloquea la publicación. Cambiamos: las URL de München se piden al catálogo CKAN porque la ciudad renombra los archivos; el cruce territorial va por código de Stadtbezirk porque los nombres no coinciden entre fuentes; las licencias son alemanas (Datenlizenz Deutschland) y el marco de datos personales es el RGPD; y sumamos al catálogo listas cerradas y un diccionario que el verificador contrasta con el lago.
- Fuentes catalogadas · integradas · caídas · descartadas: **11 catalogadas · 5 integradas · 3 candidatas · 0 caídas · 1 inexistente (inventada por la IA) · 2 excluidas**, de cinco familias: estadística (F01, F02, F06, F10, F11), territorio (F03), ambiente (F04, F09), movilidad (F07, F08) y lo que se dice (F05). Una ficha por fuente en [catalogo/](catalogo/), todas probadas de nuevo el 2026-11-01, y un diccionario con los 38 campos del lago en [catalogo/diccionario.json](catalogo/diccionario.json); `verificacion/verificar.py` comprueba que catálogo, diccionario y lago digan lo mismo.
- Huecos: lo que buscamos y no existe abierto para esta ciudad:
  - **Clima por distrito.** En la lista de estaciones del DWD, la 03379 München-Stadt (en Neuhausen-Nymphenburg) es la única activa dentro de la ciudad: el clima se responde para la ciudad entera (F04).
  - **Población y superficie de 08 Schwanthalerhöhe.** F01 las marca con «X» en los 24 años, pero no están ocultas: el total de la ciudad menos los otros 24 distritos da su población (28 684 en 2024, la misma cifra que publica F06), y esa cifra dividida por la densidad publicada da 2,07 km² todos los años, la superficie de 08 en F03. El lago la deja en null porque sería un dato derivado; `verificar.py` comprueba que las tres cifras cuadren, y una vista que la muestre tiene que marcarla como derivada. No sabemos por qué F01 la marca.
  - **Calidad del aire con licencia confirmada.** La API del UBA responde con cinco estaciones en München (F09), pero no encontramos su licencia en el sitio del UBA.
  - **Comparación con otras ciudades alemanas.** GENESIS-Online (F11) es libre y sin registro, pero su API no está probada y Python rechaza su certificado.

## ¿Se puede usar?
| Fuente | Licencia | Personas | Estado | Condición |
|---|---|---|---|---|
| F01 · Población y densidad por distrito (Statistisches Amt München) | dl-de/by-2-0 | Solo conteos por zona | Integrada | Citar «Landeshauptstadt München, Statistisches Amt · dl-de/by-2-0» con enlace al conjunto |
| F02 · Desempleo por distrito (Statistisches Amt München) | dl-de/by-2-0 | Solo conteos por zona | Integrada | Citar como F01. Solo el total «insgesamt»: sin cortes por sexo ni nacionalidad |
| F03 · Límites de los 25 distritos (GeodatenService München) | dl-de/by-2-0 | No | Integrada | Citar «Landeshauptstadt München, GeodatenService · dl-de/by-2-0» |
| F04 · Clima mensual, estación 03379 (DWD) | CC BY 4.0 | No | Integrada | Citar «Deutscher Wetterdienst · CC BY 4.0». Avisar que los meses recientes pueden corregirse |
| F05 · Vistas de «München» en de.wikipedia (Wikimedia) | CC0 | No | Integrada | Sin condiciones; la citamos igual |
| F06 · Población por distrito al 31-12-2024 (Statistisches Amt München) | dl-de/by-2-0 | Solo conteos por zona | Excluida | Duplica F01 con un solo año y formato irregular |
| F07 · Horarios GTFS de MVG | CC BY 4.0 | No | Candidata | Usable citando a MVG; falta decidir qué pregunta responde |
| F08 · Página de horarios de MVG (URL de la IA) | — | No | No existe | Respondió 404: la URL la inventó la IA |
| F09 · NO₂ por estación (Umweltbundesamt) | No declara | No | Candidata | No se usa hasta leer la licencia en el sitio del UBA |
| F10 · Religión por distrito (Statistisches Amt München) | dl-de/by-2-0 | Solo conteos por zona | Excluida | No responde ninguna pregunta; categoría especial del RGPD (art. 9) |
| F11 · GENESIS-Online (Destatis) | dl-de/by-2-0 | Solo conteos por zona | Candidata | Usable citando a Destatis; falta probar la API con un script |

## Bitácora de exploración
| Tramo | Herramienta | Qué pidió para empezar | Licencia | Dónde quedan los datos | ¿Se rehace con un comando? | Estado del proyecto | Qué resolvió | Qué no pudo | ¿Quedó? ¿Por qué? |
|---|---|---|---|---|---|---|---|---|---|
| Rastreo y catálogo | Python 3.11, solo biblioteca estándar ([explorar/perfil_stdlib.py](explorar/perfil_stdlib.py)) | Nada: Python ya estaba instalado | PSF (OSI), sin cambios | En memoria; no deja archivos | Sí: `python3 explorar/perfil_stdlib.py` | Python 3.11.9; el código corre desde 3.9 | Perfil de F01 y F02 antes de catalogarlas (2026-11-01): 624 y 3 250 filas, años 2002–2025 y 2000–2024, 26 zonas, los 5 cortes de F02 (incluida la nacionalidad) y las 24 «X» de F01, todas en el distrito 08. 4,4 s | Cada pregunta nueva exige escribir un bucle; no sirve para explorar al vuelo | **Sí**, para la ingesta y el perfil de cada ficha: da el mismo resultado sin añadir ninguna dependencia |
| Rastreo y catálogo | DuckDB 2.0.0 ([explorar/perfil_duckdb.py](explorar/perfil_duckdb.py)) | `pip install duckdb==2.0.0`; la primera lectura de una URL descarga sin avisar la extensión `httpfs` (52,7 MB) en `~/.duckdb` | MIT (OSI), sin cambios | En memoria (tabla temporal); la extensión queda en `~/.duckdb`, fuera del repositorio | Sí: `python3 explorar/perfil_duckdb.py` | 2.0.0, publicada el 2026-10-21 | El mismo perfil, idéntico campo por campo, con SQL directamente sobre el CSV remoto. 4,3 s | Si adivina los tipos, convierte en texto, sin avisar, las columnas que tienen «X» (hubo que leerlo todo como texto). Con una vista en vez de una tabla volvía a descargar el CSV en cada consulta: 22 s la primera vez, 15 s la segunda | **No para la ingesta**: suma una dependencia y una descarga binaria sin ganar nada. **Sí** para consultar fuentes nuevas durante el rastreo, donde escribir SQL es más rápido que un bucle |

## Protección
- Nivel: abierto · solo agregados · compuerta · no se publica
- Qué protegemos, y de quién:
- Pruebas de terminal o de ventana privada:
- Revisión de secretos en el historial:

## Herramienta elegida para las vistas
- Qué necesitábamos mostrar:
- Qué teníamos que proteger:
- Por qué esta herramienta cumple las dos cosas, y cuál descartamos por poco:

## Nuestra posición
- Una reflexión de gestión y gobierno de datos, y nuestra respuesta con evidencia de nuestro sistema:
- Una reflexión de ciberseguridad, y nuestra respuesta con evidencia de nuestro sistema:

## Bitácora de IA
| Tramo | Herramienta | Qué le encargamos | Qué entregó | Qué le corregimos |
|---|---|---|---|---|
| Rastreo | Claude | Una fuente abierta de población por distrito, con serie de varios años | El Indikatorenatlas (F01) y además la tabla «Bevölkerung in den Stadtbezirken» (F06) | Nada en la propuesta; la elección entre las dos tablas la hicimos nosotros (encargo 2) |
| Catálogo | Claude | Comparar las dos tablas de población y decir cuál integrar | Integrar F01 (serie 2002–2025) y descartar F06 | Correcto; lo confirmamos abriendo F06: «101 901» con espacio, el total como distrito «26» y densidad en hab/ha |
| Rastreo | Claude | Desempleo por distrito | El Indikatorenatlas de desempleo (F02), con cortes por sexo y nacionalidad | Correcto; `verificar.py` comprueba el porcentaje contra sus bases en los 260 registros |
| Rastreo | Claude | Los límites oficiales de los distritos | El WFS del GeodatenService (F03) | Venían 27 polígonos para 25 distritos y en EPSG:25832: lo pedimos en EPSG:4326 y unimos los pedazos por código |
| Rastreo | Claude | Clima mensual de la ciudad | La estación 03379 München-Stadt del DWD (F04) | Correcto; la licencia la leímos en Terms_of_use.pdf y los -999 se guardan como null |
| Rastreo | Claude | Replicar la escucha del taller (vistas de Wikipedia) | La URL de de.wikipedia y sumar es y en (F05) | es y en fallaron por CORS desde el navegador: solo se integró de.wikipedia |
| Rastreo | Claude | La dirección de descarga del GTFS de MVG | Una URL de mvg.de que da 404 (F08) | **Inventada.** La real (F07) apareció buscando «GTFS» en el catálogo CKAN |
| Rastreo | Claude | Datos abiertos de calidad del aire | La API del UBA y una página de documentación con la licencia (F09) | La página dio 404 y la licencia no apareció: queda candidata |
| Catálogo | Claude | Qué tablas del Indikatorenatlas no deberían entrar | La religión por distrito (F10), categoría especial del RGPD | Correcto; confirmamos que no responde ninguna pregunta |
| Rastreo | Claude | Una fuente para comparar München con otras ciudades | GENESIS-Online de Destatis (F11), «sin registro» | Solo se leyó la página; la API sigue sin probar |
| Ingesta | Claude | Los scripts de ingesta | Cinco scripts con sintaxis de Python 3.10 o superior | El Mac de David tiene Python 3.9.6: se añadió `from __future__ import annotations` |
| Lago | Claude | Construir el lago con los datos bajados desde el navegador | Los archivos del lago armados a mano | Al correr el script, la geometría salió distinta (+18 puntos): se subió la versión del script |
| Entrega 1 | Claude (Claude Code) | Responder el Word «Por qué estos datos» a partir del Excel | Las seis respuestas | Al revisarlas contra las fuentes: eran 5 estaciones de aire y no 2; «el 08 queda sin densidad» era falso; la densidad se comprueba en 275 registros y no en 286; la licencia del UBA no se pudo leer, no «no existe» |
| Ingesta y verificación | Claude (Claude Code) | Revisar el PR #1 y corregir lo que encontrara | 10 hallazgos (un anillo de 3 puntos en el distrito 19, un verificador que se caía con vacíos, `PROBADO`, URL fijas, saltos de línea) y sus correcciones | Al probar sus propias correcciones, el verificador nuevo se caía con un tipo equivocado: se reordenó para revisar primero la estructura y después los valores |
| Catálogo | Claude (Claude Code) | Las fichas de las 11 fuentes | 11 fichas, listas cerradas y su control en `verificar.py` | Afirmó que el GTFS de MVG no incluye la S-Bahn sin haberlo comprobado; se verificó en `routes.txt` antes de publicarlo (243 rutas, ninguna de S-Bahn) |
| Gobierno | Claude (Claude Code) | Revisar que Excel, catálogo y lago no se contradigan, siguiendo el DMBOK | Diccionario en el repositorio, vocabulario único y `GOBIERNO.md` | La auditoría mostró que su propia respuesta del Word sobre el 08 era falsa (la población se deduce por resta): se corrigieron el Word y el Excel |
| Vistas | Claude (Claude Code) | La primera versión de `web/` | Mapa, P1–P4 y la fuente de cada cifra a un clic | El validador de paleta rechazó la rampa del mapa (contraste 1,5:1) y los gráficos se dibujaban con ancho 0 en una pestaña oculta: se corrigieron antes de subirla |
| Lago | Claude (Claude Code) | Actualizar el lago (2026-11-01) | Lago y fichas al día | `verificar.py` bloqueó la publicación hasta volver a probar las fuentes; F11 fallaba por otra causa que la anotada y se registró la nueva |
| Rastreo y catálogo | Claude (Claude Code) | Probar dos herramientas para perfilar fuentes | `explorar/perfil_stdlib.py` y `explorar/perfil_duckdb.py` | Con una vista, DuckDB descargaba el CSV en cada consulta (se cambió a tabla); con tipos automáticos convertía en texto las columnas con «X» |

## Revisión cruzada
- Tres cifras auditadas por el grupo <X>: resultado y correcciones
- Ataque del grupo <Y>: qué intentó, qué consiguió, qué cambiamos
- Vueltas atrás en la ruta: de qué tramo a cuál, y por qué
