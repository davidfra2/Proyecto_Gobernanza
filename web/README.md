# Vistas · `web/`

Primera versión de las vistas: la **réplica mínima** del Cerebro Lima (HTML y JavaScript sin
framework, MapLibre GL para el mapa). Responde P1–P4 y cada cifra lleva su etiqueta de fuente, que
abre la ficha del catálogo con un clic.

## Cómo verla

Los navegadores no dejan leer archivos locales con `fetch`, así que hay que servir la **raíz del
repositorio** (no la carpeta `web/`, porque las vistas leen `lago/`, `territorio/` y `catalogo/`):

```bash
python3 -m http.server 8000
```

y abrir http://localhost:8000/web/

## Archivos

| Archivo | Qué hace |
|---|---|
| `index.html` | Estructura de la página: panorama, mapa, P1–P4, fuentes y método |
| `estilos.css` | Tokens de color (modo claro y oscuro) y diseño adaptable al teléfono |
| `datos.js` | **El único punto que sabe de dónde salen los datos.** Hoy lee el lago directamente; con la compuerta, solo cambia `leer()` |
| `graficos.js` | Gráficos en SVG hechos a mano: barras, líneas, columnas y la franja de temperatura, con tooltip también por teclado |
| `app.js` | Lógica: carga, distrito elegido (sincronizado entre mapa, selector y barras), etiquetas de fuente y ficha |

## Decisiones ya tomadas (y por qué)

- **Fuente a un clic.** Cada cifra tiene una etiqueta «Fuente F0x · vigente a … · probado …». Al
  tocarla se abre la ficha: licencia, dónde se leyó, URL exacta, script y nota. Si la cifra no es
  observada, la etiqueta lo dice: *calculada a partir de la fuente* (crecimiento, índice) o *derivada*.
- **Observado frente a derivado.** La población del 08 Schwanthalerhöhe no la publica la fuente
  («X»). Se muestra deducida (ciudad − otros 24 distritos) pero siempre marcada con * y explicada en
  el panel; en las barras va más clara.
- **Un solo eje Y.** La población del distrito y la de la ciudad se comparan como índice
  (2015 = 100), porque sus escalas no caben en el mismo eje.
- **Colores validados** con el validador de paleta de la guía de visualización: pareja azul/rojo de
  las barras divergentes (pasa en claro y oscuro, también para daltonismo) y rampa de 5 azules del
  mapa (pasos 250–700, contraste ≥ 2:1 en el más claro).
- **Accesible.** Toda barra y gráfico de líneas se puede recorrer con el teclado; cada gráfico tiene
  su «Ver tabla»; el distrito también se elige con un selector, no solo tocando el mapa.
- **Seguridad básica.** MapLibre con versión fija y huella SRI (el navegador la rechaza si alguien
  la altera), una política CSP que solo permite este sitio, jsdelivr y OpenFreeMap, y ningún dato
  insertado con `innerHTML`.
- **Dependencias externas, todas sin llave ni registro:** MapLibre GL JS 5.24.0 (BSD-3, desde
  cdn.jsdelivr.net) y el mapa base de OpenFreeMap (datos © OpenStreetMap, ODbL). Si el mapa base no
  responde, el mapa sigue con un fondo liso.

## Lo que falta (David)

- [ ] **Publicar el enlace** (por ejemplo, Vercel sirviendo la raíz del repositorio, con `/` → `/web/`).
- [ ] **Decidir la protección** con quien asuma Seguridad: abierto, solo agregados o compuerta.
      Si hay compuerta (`api/`), cambiar solo `leer()` en `datos.js` y probarla desde la terminal.
- [ ] **Explorar una segunda herramienta** para las vistas sobre los mismos datos (por ejemplo,
      Observable Plot, Leaflet, Evidence o Streamlit) y anotar las dos en la bitácora del README.
- [ ] Llenar «Herramienta elegida para las vistas» en el README con esa comparación.
- [ ] Revisar textos y orden de las secciones con el grupo.
- [ ] Opcional: modo oscuro para el mapa base (OpenFreeMap tiene un estilo `dark`).
