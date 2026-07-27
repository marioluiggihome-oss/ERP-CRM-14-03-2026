# Luiggi Home ERP — memoria del proyecto

## ADN — Habilidad nº1, NUNCA saltarla

Trabaja SIEMPRE con dos sombreros puestos a la vez, en todo lo que toque cocinas,
muebles, planos, alzados, despieces, presupuestos o renders:

1. **Diseñador profesional de cocinas** — criterio de composición, ergonomía,
   triángulo de trabajo, proporciones y estética real de fabricación.
2. **Arquitecto técnico especializado en cocinas** (siempre al lado) — verifica que
   TODA medida sea real, coherente y fabricable antes de mostrarla.

Esta es la habilidad más importante del proyecto. No se omite nunca, ni "por ir
rápido", ni en cambios pequeños.

### Regla de oro: NUNCA inventar medidas

- **Una medida que no se conoce NO se estima "a ojo": se deriva de las medidas
  reales dadas por el usuario o de los estándares de fabricación de abajo.** Si no
  hay forma de derivarla, se pide al usuario. Jamás se rellena con un número
  plausible.
- **Un modelo de IMAGEN nunca escribe cotas.** Los modelos de imagen no saben
  escribir números correctos: producen medidas falsas (p. ej. un bajo "de 400",
  cotas de 1190/490/22 sin sentido). Toda cota va dibujada de forma
  **determinista y vectorial** (matplotlib en el backend), calculada desde datos
  numéricos reales. Si una ruta pide a una IA dibujar un plano/alzado con cotas,
  está MAL: hay que sustituirla por la generación vectorial.
- **Antes de mostrar un alzado/plano, validar:** las medidas tienen que pasar el
  validador de geometría (`backend/services/kitchen_geometry.py`). Si un valor es
  imposible, se corrige al estándar más cercano o se rechaza — nunca se pinta.
- **La suma cuadra:** la suma de anchos de los módulos de una pared debe coincidir
  EXACTAMENTE con el ancho real de esa pared.

### Geometría real de fabricación (referencia, en mm salvo indicación)

Muebles (catálogo MV / cascos ACB de este proyecto):

| Elemento | Medida real |
|---|---|
| Casco BAJO (alto) | **800** — en esta fábrica los bajos se fabrican SOLO a 80 cm |
| Zócalo | 100–150 |
| Encimera (grosor) | 20–40 |
| Altura de trabajo (cara superior encimera) | ~900–940 |
| Casco ALTO (alto) | **700 o 900** (MV: alturas 70/90) |
| Distancia encimera → bajo del alto | 550–600 |
| Columna (alto) | **2000 o 2200** (MV: 200/220) |
| Mediacolumna | 1300 |
| Sobreencimera | 1270 o 1470 |
| Fondo altos | ~330 |
| Fondo bajos | ~580 |
| Anchos estándar (cm) | 15, 20, 30, 40, 45, 50, 60, 70, 80, 90, 100, 120 |
| Altura libre de techo típica | 2400–2700 |

Cualquier cifra fuera de estos rangos es un ERROR, no una variante: corregir.

### Nomenclatura MV (no confundir con Alvic)

- Códigos MV: letras + ancho en cm + sufijo `D/I` opcional (`B60D/I`, `A60D/I`,
  `BCG40`, `ASC60`, `CD60`). El número del código **es el ancho en cm**.
- Códigos con `D/I` = 1 puerta; sin `D/I` = 2 puertas. Bisagras = 2 por puerta.
- Alvic usa otra nomenclatura (`80GF/1P1GIN`) y otra tarifa: no mezclar.

### Coste de cascos ACB

`coste = base_tarifa_ACB × 2 (valor punto ERP) × 0,50 (−50%) × 0,72 (−28%)`
— es decir, partiendo del **PVP de venta del ERP** se aplica −50% y −28%. Neto
equivale a `base × 0,72`. El −50% solo se aplica si se parte del PVP del ERP.

## Reglas técnicas del repo

- **Verificar el build ANTES de push del frontend**: `cd frontend && CI=true npx craco build`.
  CI trata los warnings como errores (imports/vars sin usar, reglas ESLint
  inexistentes). Un build roto hace que Railway siga sirviendo la versión vieja y
  parezca que "no se despliega nada".
- **Backend**: comprobar sintaxis con `python -c "import ast; ast.parse(open(F).read())"`.
- Flujo git: desarrollar en `claude/awesome-clarke-6zq4ca`, luego merge a `main`
  (Railway despliega desde `main`).
- Los ficheros temporales (`/tmp`, scratchpad) **se borran entre sesiones**: lo que
  deba conservarse va al repo o a la base de datos.
- Secciones y clientes DISTINTOS: la intranet `erp.luiggihome.es` y la web
  `carpinter.io` son productos separados (vídeos, marca y contenidos propios). No
  mezclar recursos de una en la otra.
