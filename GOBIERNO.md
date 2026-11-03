# Gobierno de datos · cómo se aplica el DMBOK en este repositorio

El DMBOK (DAMA-DMBOK2) organiza la gestión de datos en áreas de conocimiento con el gobierno en el
centro, más la ética, la madurez y la organización. Esta tabla dice, para cada una, **qué artefacto la
cumple, quién responde y qué control la vigila**. Si un área no tiene control o no aplica, está dicho.

| Área del DMBOK | Dónde está en el repositorio | Responde | Control |
|---|---|---|---|
| **Ética del manejo de datos** (cap. 2) | Lo que decidimos no mostrar aunque sea público y legal: cortes de desempleo por sexo y nacionalidad (F02), religión por distrito (F10), crudos; lo derivado nunca pasa por observado ([README](README.md), «Nuestra posición») | Todo el grupo | `verificar.py`: ningún campo publicado es sensible ni personal, ningún conteo por distrito baja de 100; el glosario obliga a declarar cada cifra como observada, calculada o derivada |
| **Gobierno de datos** (cap. 3) | Papeles, flujo de cambios y revisión: [CONTRIBUTING.md](CONTRIBUTING.md); decisiones e incidencias: más abajo en este archivo | Todo el grupo | Nadie aprueba lo suyo; si la verificación falla, no se publica |
| **Arquitectura** (cap. 4) | Bronce `lago/raw/` (crudo, solo local) → plata `lago/` y `territorio/` (limpio, con fuente y fecha) → oro `web/` (vistas) | Datos | `.gitignore` impide subir el bronce y `.vercelignore` publicarlo; `verificar.py` lo comprueba |
| **Modelado y diseño** (cap. 5) | Envoltura común `{fuente, vigencia, probado, registros}`; llave territorial `sb_codigo` (00 = ciudad, 01–25 = distritos) | Datos | `verificar.py`: estructura contra el diccionario, antes que los valores |
| **Almacenamiento y operaciones** (cap. 6) | JSON en UTF-8 con saltos `\n`; el lago se reconstruye con los seis `ingesta/pull_*.py` (pull_territorio antes que pull_transporte, que usa los límites). Retención: los crudos no se guardan (se vuelven a bajar de la fuente); el historial del lago queda en Git para siempre, y no tiene datos de personas | Datos | Reconstruir y comparar: el lago sale idéntico salvo `probado`. Falta que el despliegue se actualice solo (incidencia I1) |
| **Seguridad** (cap. 7) | Clasificación de cada campo en el diccionario; nivel «abierto, solo agregados»; CSP, huella SRI y cabeceras en [vercel.json](vercel.json); inventario de terceros en [catalogo/dependencias.json](catalogo/dependencias.json) | Seguridad (sin asignar, incidencia I2) | `verificar.py`: todo origen que la CSP deja cargar está en el inventario, con licencia; los crudos no viajan al despliegue. Falta el ataque autorizado de otro grupo |
| **Integración e interoperabilidad** (cap. 8) | Scripts de ingesta; URL resueltas en el catálogo CKAN; cruce entre fuentes solo por código oficial | Datos | `verificar.py`: cuadres F01 ↔ F02 ↔ F03 |
| **Gestión documental** (cap. 9) | No aplica: el sistema no guarda documentos ni contenido no estructurado | — | — |
| **Datos de referencia y maestros** (cap. 10) | [catalogo/listas.json](catalogo/listas.json): único vocabulario (estados, licencias, entidades, tipos de dato y de cifra, preguntas), enlazado a las listas del Excel. F03 es el maestro de los 25 distritos | Curaduría | `verificar.py`: todo valor del catálogo, del diccionario y del glosario sale de las listas |
| **Inteligencia de negocio** (cap. 11) | [web/](web/): vistas que responden P1–P4 y dicen qué no responden; mapa en 2D y 3D; cada cifra con su etiqueta de fuente (vigencia, fecha de prueba, observada, calculada o derivada); glosario y terceros visibles en «Fuentes y método» | Interfaz | `verificar.py`: toda fuente citada en `web/` es una ficha integrada |
| **Metadatos** (cap. 12) | Catálogo de fuentes [catalogo/F*.json](catalogo/), diccionario de campos [catalogo/diccionario.json](catalogo/diccionario.json) y glosario de negocio [catalogo/glosario.json](catalogo/glosario.json). Linaje: fuente → `script` → `salida` (catálogo) → campo (diccionario) → cifra en pantalla (glosario) | Curaduría | `verificar.py`: catálogo ↔ lago ↔ diccionario ↔ glosario; el Excel se genera desde el catálogo con `catalogo/a_excel.py` |
| **Calidad de datos** (cap. 13) | [verificacion/verificar.py](verificacion/verificar.py), por dimensiones: completitud, validez, consistencia, unicidad y actualidad (ningún archivo del lago con más de 60 días sin probar) | Datos | Antes de cada publicación y en cada push y pull request con GitHub Actions ([verificar.yml](.github/workflows/verificar.yml)), en Python 3.9 y 3.13 |
| **Big data y ciencia de datos** (cap. 14) | No aplica: cinco archivos y menos de 300 KB. La exploración con DuckLake y dlt quedó documentada para cuando crezca | — | — |

## Quién es quién (cap. 16)

- **Dueño del dato:** la entidad que lo publica (Statistisches Amt, GeodatenService, DWD, Wikimedia).
  Nosotros no lo cambiamos; si está mal, se anota y se avisa.
- **Custodio de metadatos (data steward):** Curaduría. Responde por el catálogo, el diccionario, el
  glosario, las licencias y las listas de referencia.
- **Custodio técnico:** Datos. Responde por la ingesta, el lago y las reglas de calidad.
- **Consumidor:** Interfaz, y quien use las vistas.
- **Seguridad:** sin asignar (incidencia I2).

## Reglas que conectan todo

1. **Un ID por fuente** (F01…F11), el mismo en el Excel, en `catalogo/`, en el campo `fuente` del
   lago, en el diccionario, en el glosario y en las etiquetas de las vistas.
2. **Un solo vocabulario.** Todo valor cerrado sale de `listas.json`, y cada uno dice su equivalente
   en el Excel.
3. **Fechas en ISO 8601.** `probado` y `vigencia` siempre `AAAA-MM-DD`; `mes` es `AAAA-MM` porque
   nombra un período, no un día.
4. **Observado, no derivado.** El lago solo guarda lo que publica la fuente. Lo que se calcula se
   define en el glosario con su fórmula; lo derivado (la población del 08) se marca siempre como tal.
5. **Nada entra sin licencia leída en la propia fuente.** Por eso F09 sigue candidata.
6. **Nada ajeno se carga sin estar inventariado.** La CSP de las vistas y `dependencias.json` dicen lo
   mismo, y el verificador lo comprueba.
7. **Lo que no sirvió también se documenta**, con el error exacto y la fecha de la prueba.

## Registro de decisiones

| Fecha | Decisión | Por qué | Dónde queda |
|---|---|---|---|
| 2026-09-27 | Los crudos (`lago/raw/`) no se suben ni se publican | Traen cortes que decidimos no mostrar, y se pueden volver a bajar de la fuente | `.gitignore`, `.vercelignore` |
| 2026-10-06 | Integrar F01–F05; F06 y F10 excluidas; F07, F09 y F11 candidatas; F08 no existe | Duplicado (F06), dato sensible sin pregunta (F10), licencia sin leer (F09), API sin probar (F11), URL inventada por la IA (F08) | `catalogo/` |
| 2026-10-06 | De F02 solo el total «insgesamt» | No facilitar el señalamiento de barrios por nacionalidad | `ingesta/pull_desempleo.py` |
| 2026-10-12 | El lago no guarda derivados: la población del 08 queda en `null` | Una cifra deducida no puede pasar por observada | `glosario.json` (`poblacion_08`) |
| 2026-10-12 | Redondear la geometría en lugar de simplificar cada distrito | La simplificación dejaba un polígono de 3 puntos y huecos entre vecinos | `ingesta/pull_territorio.py` |
| 2026-11-02 | Protección «abierto, solo agregados», sin compuerta; mínimo de 100 personas por celda | Todo lo integrado se puede republicar y ninguna fila es una persona | README, «Protección»; `verificar.py` |
| 2026-11-02 | Vistas con código propio; Streamlit descartada por poco | Control de lo que viaja al despliegue y un solo paquete ajeno en el navegador | README, «Herramienta elegida» |
| 2026-11-03 | dlt, DuckLake y Frictionless probadas y no adoptadas | Repiten lo que ya hacemos con más dependencias, o no ven los cuadres entre fuentes | README, bitácora de exploración |
| 2026-11-03 | Vista 3D como escala visual; los edificios de OpenStreetMap, solo como contexto | La altura repite el valor del color; los edificios no son cifras del sistema | `glosario.json` (`altura_3d`), `dependencias.json` |
| 2026-11-03 | Segundo rastreo por familias: 31 fichas nuevas (F12–F42) del portal de la ciudad y de fuera de él | El primero solo buscó lo que respondía las cuatro preguntas: 11 fuentes de 337 conjuntos del portal | `catalogo/`, README |
| 2026-11-03 | Integrar el GTFS de toda la red MVV (F26) y responder P5 | Trae la S-Bahn que le falta a F07; el lago guarda cada parada y las vistas cuentan por distrito | `ingesta/pull_transporte.py`, `glosario.json` |
| 2026-11-03 | Excluir los datos de adelantamiento a bicicletas (F29) | Traen `user_id` con GPS y hora exacta: datos personales seudonimizados, aunque la licencia lo permita | `catalogo/F29_adelantamientos_bici.json` |
| 2026-11-03 | No saltarse el bloqueo de la estadística de Baviera (F41) | Respondió 403 a nuestro script; hacerse pasar por un navegador sería burlar una decisión del publicador | `catalogo/F41_estadistica_baviera.json` |
| 2026-11-03 | La hoja «3. Bitácora IA» del Excel se genera desde `catalogo/bitacora_ia.json` (cierra la incidencia I6) | Tenía solo los 12 encargos de la primera entrega; copiarla a mano se habría vuelto a atrasar. `verificar.py` exige una fila por cada fila de la bitácora del README | `catalogo/bitacora_ia.json`, `a_excel.py` |
| 2026-11-03 | Un lago con más de 60 días sin probar no se publica | Las fuentes cambian: el DWD corrigió tres meses en tres semanas | `verificar.py` |

## Incidencias abiertas

| # | Desde | Qué pasa | Qué hace falta | Quién |
|---|---|---|---|---|
| I1 | 2026-11-03 | El sitio publicado no se actualiza solo: dos pushes a `main` pasaron `verificar.py` en GitHub Actions, pero el sitio siguió con el lago del 2026-11-01. El despliegue en Vercel se hace aparte | Volver a desplegar antes de cada entrega y comprobar en el sitio la fecha `probado`; mejor, conectar Vercel al repositorio para que despliegue `main` cuando la comprobación pase | Interfaz |
| I2 | 2026-10-06 | Nadie asumió Seguridad | Asignarla a alguien que no construyó lo que se publica | Todo el grupo |
| I3 | 2026-10-12 | F11 (Destatis) falla desde Python: certificado el 2026-10-12, tiempo agotado el 2026-11-01 y el 2026-11-03; con curl responde | Resolver la conexión sin desactivar la verificación del certificado antes de integrarla | Curaduría |
| I4 | 2026-10-06 | F09 (calidad del aire) sin licencia leída en el sitio del UBA | Encontrar sus condiciones de uso y copiarlas en la ficha | Curaduría |
| I5 | 2026-10-12 | F01 marca con «X» la población del 08 aunque se deduce y F06 la publica | Preguntar al Statistisches Amt por qué | Curaduría |
| I7 | 2026-11-02 | Faltan la auditoría de tres cifras y el ataque autorizado de otro grupo | Se hacen en clase sobre el enlace publicado | Todo el grupo |
| I8 | 2026-11-03 | El GTFS de MVV (F26) marca la S-Bahn (S1–S8, S20) con `route_type 0`, que en GTFS es tranvía | El script la reconoce por el nombre y `verificar.py` vigila que no desaparezca; avisar a MVV del error | Datos |
| I9 | 2026-11-03 | Sentinel-2 (F37) enlaza unas condiciones de uso de la ESA cuyo dominio no resuelve | Encontrar las condiciones de Copernicus en una página que funcione | Curaduría |
| I10 | 2026-11-03 | La API Overpass de OpenStreetMap (F38) no respondió dos veces | Volver a probar, o usar Overture (F39) para los mismos datos | Curaduría |

## Autoevaluación de madurez (cap. 15)

Escala del DMBOK: 0 sin capacidad · 1 inicial (depende de personas) · 2 repetible · 3 definido (escrito
y seguido) · 4 gestionado (medido y controlado automáticamente) · 5 optimizado. Hecha el 2026-11-03,
con la evidencia de este repositorio.

| Área | Nivel | Por qué no es más |
|---|---|---|
| Metadatos | 4 | Catálogo, diccionario y glosario verificados en cada push. No 5: el Excel se genera entero desde el repositorio, pero hay que correr `a_excel.py` a mano antes de cada entrega |
| Calidad de datos | 4 | Reglas por dimensión, en cada push, que bloquean la publicación. No 5: no se mide la calidad a lo largo del tiempo |
| Datos de referencia | 4 | Un vocabulario único verificado. No 5: los cambios a las listas no tienen un proceso propio |
| Ética | 3 | Decisiones escritas y con control automático. No 4: no hay revisión externa todavía (I7) |
| Gobierno | 3 | Papeles, reglas y revisión por pares escritos y seguidos. No 4: Seguridad sin asignar (I2) |
| Arquitectura, modelado, integración | 3 | Definidas y verificadas. No 4: la ingesta se corre a mano |
| Inteligencia de negocio | 3 | Vistas con trazabilidad a un clic. No 4: sin auditoría externa de cifras (I7) |
| Seguridad | 2 | Controles técnicos (CSP, SRI, inventario, crudos fuera) que se repiten. No 3: sin responsable ni ataque autorizado (I2, I7) |
| Almacenamiento y operaciones | 2 | El lago se reconstruye igual. No 3: el despliegue no sigue al repositorio (I1) |

## Gestión del cambio (cap. 17)

Todo cambio entra por Git: pequeños cambios del propio tramo directo a `main`, código que afecta a
otros por pull request revisado por otra persona ([CONTRIBUTING.md](CONTRIBUTING.md)). Cada push corre
`verificar.py`; una decisión nueva va al registro de arriba y un problema abierto, a las incidencias.
