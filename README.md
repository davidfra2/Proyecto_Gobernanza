# München · sistema de información

Grupo: Juan Carlos Muñoz (Curaduría) · David Felipe Rios (Interfaz) · Samuel Molina (Datos) · Enlace: <url de las vistas> · Repositorio: https://github.com/davidfra2/Proyecto_Gobernanza · Revisado: 2026-10-12

Réplica del Cerebro Lima para Múnich. Cómo trabajamos: [CONTRIBUTING.md](CONTRIBUTING.md).

## Para quién y qué pregunta
- Usuario:
- Preguntas (entre tres y seis):
- Escala y comparación:
- Lo que decidimos no mostrar, y por qué:

## La réplica
- Qué replicamos tal cual del ejemplo y qué tuvimos que cambiar para nuestra ciudad:
- Fuentes catalogadas · integradas · caídas · descartadas: **11 catalogadas · 5 integradas · 3 candidatas · 0 caídas · 1 inexistente (inventada por la IA) · 2 excluidas**, de cinco familias: estadística (F01, F02, F06, F10, F11), territorio (F03), ambiente (F04, F09), movilidad (F07, F08) y lo que se dice (F05). Una ficha por fuente en [catalogo/](catalogo/), todas probadas el 2026-10-12; `verificacion/verificar.py` comprueba que el catálogo y el lago digan lo mismo.
- Huecos: lo que buscamos y no existe abierto para esta ciudad:
  - **Clima por distrito.** En la lista de estaciones del DWD, la 03379 München-Stadt (en Neuhausen-Nymphenburg) es la única activa dentro de la ciudad: el clima se responde para la ciudad entera (F04).
  - **Población y superficie de 08 Schwanthalerhöhe.** F01 las reserva con «X» en todos los años; solo publica su densidad. F06 sí trae la población de 2024 (28 684): falta preguntar al Statistisches Amt por qué la reserva en F01 antes de usarla.
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

## Revisión cruzada
- Tres cifras auditadas por el grupo <X>: resultado y correcciones
- Ataque del grupo <Y>: qué intentó, qué consiguió, qué cambiamos
- Vueltas atrás en la ruta: de qué tramo a cuál, y por qué
