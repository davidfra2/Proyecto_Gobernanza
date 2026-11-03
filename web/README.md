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
  responde, el mapa sigue con un fondo liso. Están inventariadas en
  [catalogo/dependencias.json](../catalogo/dependencias.json), y `verificar.py` falla si la CSP deja
  cargar un origen que no esté ahí.
- **Vista 3D (botón «Vista 3D» del mapa).** A escala de ciudad, cada distrito se eleva en proporción
  al indicador elegido: la altura repite el valor del color, no es una cifra nueva, y la leyenda avisa
  que la perspectiva la deforma. Al acercarse (zoom 13 o más), los prismas se desvanecen y aparecen
  los edificios del mapa base con su altura aproximada (`render_height` de OpenStreetMap): contexto
  visual, no cifras del sistema. Respeta «reducir movimiento» del sistema operativo (sin animación).
- **Glosario y terceros a la vista.** «Fuentes y método» muestra el glosario
  ([catalogo/glosario.json](../catalogo/glosario.json)): cada cifra, si es observada, calculada o
  derivada, cómo se obtiene y de qué campos sale; y el inventario de terceros, con lo que reciben de
  quien visita la página.

## Publicación

Vercel sirve la raíz del repositorio sin build: [vercel.json](../vercel.json) redirige `/` a `/web/`
y añade cabeceras de seguridad; [.vercelignore](../.vercelignore) deja fuera `lago/raw/`, los scripts,
el Excel y la documentación. Nivel de protección: abierto, solo agregados (README, «Protección»).

## Lo que falta

- [x] Publicado en https://proyecto-gobernanza-muenchen.vercel.app (2026-11-02).
- [x] Pruebas de terminal contra el enlace (resultados en el README, «Protección»).
- [ ] Conectar el repositorio en Vercel para que cada push a `main` se publique solo (hoy se publica con `npx vercel deploy --prod`).
- [ ] Revisión cruzada: tres cifras auditadas y el ataque de otro grupo.
- [x] Modo oscuro del mapa base (estilo `dark` de OpenFreeMap).
- [x] Vista 3D del mapa (2026-11-03).
