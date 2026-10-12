# Gobierno de datos · cómo se aplica el DMBOK en este repositorio

El DMBOK (DAMA-DMBOK2) divide la gestión de datos en once áreas con el gobierno en el centro.
Esta tabla dice, para cada área que toca nuestro sistema, **qué artefacto la cumple, quién
responde y qué control automático la vigila**. Si un área no tiene control, está dicho.

| Área del DMBOK | Dónde está en el repositorio | Responde | Control |
|---|---|---|---|
| **Gobierno de datos** (cap. 3) | Papeles, flujo de cambios y decisiones: [CONTRIBUTING.md](CONTRIBUTING.md) y las cuatro decisiones del [README](README.md) | Todo el grupo | Nadie aprueba lo suyo; si la verificación falla no se publica |
| **Arquitectura** (cap. 4) | Bronce `lago/raw/` (crudo, solo local) → plata `lago/` y `territorio/` (limpio, con fuente y fecha) → oro `web/` (vistas) | Datos | `.gitignore` impide subir el bronce |
| **Modelado y diseño** (cap. 5) | Envoltura común `{fuente, vigencia, probado, registros}`; llave territorial `sb_codigo` (00 = ciudad, 01–25 = distritos) | Datos | `verificar.py`: estructura contra el diccionario |
| **Almacenamiento y operaciones** (cap. 6) | JSON en UTF-8 con saltos `\n`; el lago se reconstruye con los cinco `ingesta/pull_*.py` | Datos | Reconstruir y comparar: el 2026-10-12 el lago salió idéntico |
| **Seguridad** (cap. 7) | Clasificación de cada campo en el diccionario; decisiones de no publicar (cortes de F02 por nacionalidad, F10, crudos) | Seguridad (hoy sin asignar) | Ninguno automático todavía: falta la compuerta y el ataque autorizado |
| **Integración e interoperabilidad** (cap. 8) | Scripts de ingesta; URL resueltas en el catálogo CKAN; cruce entre fuentes solo por código oficial | Datos | `verificar.py`: cuadres F01 ↔ F02 ↔ F03 |
| **Datos de referencia y maestros** (cap. 10) | [catalogo/listas.json](catalogo/listas.json): único vocabulario, enlazado a las listas del Excel. F03 es el maestro de los 25 distritos | Curaduría | `verificar.py`: todo valor del catálogo y del diccionario sale de las listas |
| **Metadatos** (cap. 12) | Catálogo de fuentes [catalogo/F*.json](catalogo/) y diccionario de campos [catalogo/diccionario.json](catalogo/diccionario.json). Linaje: fuente → `script` → `salida` | Curaduría | `verificar.py`: catálogo ↔ lago ↔ diccionario |
| **Calidad de datos** (cap. 13) | [verificacion/verificar.py](verificacion/verificar.py), por dimensiones: completitud, validez, consistencia, unicidad y actualidad | Datos | Se corre antes de cada publicación |
| **Inteligencia de negocio** (cap. 11) | `web/`: vistas que responden P1–P4 | Interfaz | Pendiente: cada cifra debe mostrar fuente, vigencia y fecha de prueba a un clic |

Gestión documental (cap. 9) no aplica: el sistema no guarda documentos ni contenido no estructurado.

## Quién es quién

En el vocabulario del DMBOK:

- **Dueño del dato:** la entidad que lo publica (Statistisches Amt, GeodatenService, DWD, Wikimedia).
  Nosotros no lo cambiamos; si está mal, se anota y se avisa.
- **Custodio de metadatos (data steward):** Curaduría. Responde por el catálogo, el diccionario,
  las licencias y las listas de referencia.
- **Custodio técnico:** Datos. Responde por la ingesta, el lago y las reglas de calidad.
- **Consumidor:** Interfaz, y quien use las vistas.

## Reglas que conectan todo

1. **Un ID por fuente** (F01…F11), el mismo en el Excel, en `catalogo/`, en el campo `fuente` del
   lago y en el diccionario.
2. **Un solo vocabulario.** Estados, licencias, entidades, formatos, frecuencias, tipos de dato,
   clasificaciones y preguntas salen de `listas.json`. Cada valor dice su equivalente en el Excel.
3. **Fechas en ISO 8601.** `probado` y `vigencia` siempre `AAAA-MM-DD`; `mes` es `AAAA-MM` porque
   nombra un período, no un día.
4. **Observado, no derivado.** El lago solo guarda lo que publica la fuente. Lo que se calcula,
   como la población de 08 Schwanthalerhöhe por resta, se documenta y se verifica, pero no se guarda
   como si fuera observado; si una vista lo muestra, lo marca como derivado.
5. **Nada entra sin licencia leída en la propia fuente.** Por eso F09 sigue candidata.
6. **Lo que no sirvió también se documenta**, con el error exacto y la fecha de la prueba.

## Lo que todavía falta

- **Seguridad no tiene responsable.** Somos tres y nadie asumió el papel; tiene que ser alguien que
  no construya la compuerta.
- **Las vistas no existen todavía**, así que la trazabilidad «a un clic» no se puede comprobar.
- **El Excel se mantiene a mano.** La fuente de verdad es el repositorio: `catalogo/` y
  `catalogo/diccionario.json`. Si cambia algo aquí, se cambia también en el Excel antes de entregarlo.
