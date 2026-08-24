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
| Altillo (alto del casco) | **350** — la fila corta que va SOBRE los altos, hasta el techo |
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

## Habilidades BLOQUEADAS — no se tocan sin permiso del master

Lo que ya funciona y está en uso NO se cambia por iniciativa propia, ni "de
paso" mientras se arregla otra cosa. Vale para cualquiera que trabaje en este
repo, personas o IAs. **Si crees que hay que cambiar algo de esta lista, pídeselo
al master ANTES y explícale qué se gana y qué se pierde.**

Por qué existe esta lista: el 03/08 se enrutó el botón principal del Estudio 3D
por el render compuesto, y ese camino llamaba directamente a Gemini estándar. El
usuario pulsaba con IA 1 seleccionada, creía seguir en su motor y no lo estaba.
Nadie lo tocó a propósito: se rompió como efecto colateral de otra mejora.

1. **Motor de render del Estudio 3D.** El motor elegido en pantalla manda
   siempre, por cualquier camino (texto, referencia, plano+bocetos):
   `IA 1 → gemini` · `IA 3 → gemini_premium` · `IA 7 → banana_pro`. Todo
   render pasa por `_render_dispatch`; nadie llama directo a un motor.
   - **IA 1 es la de producción y es la única que ve un usuario que no sea
     master.** Las demás son motores de pruebas del master (IA 7 cuesta 3,3x
     por render).
   - **IA 2 (manus) está APAGADA** desde el 18/08, a petición del master: es un
     agente, no un modelo de imagen, y cada render se iba hasta cinco minutos.
     Sigue en el código detrás de `MOTOR_MANUS_ACTIVO`; en pantalla no está.
   - **IA 4 (gemini_flash) está APAGADA** desde el 24/08, a petición del
     master. Nunca fue un motor distinto: forzaba
     `model_override="gemini-2.5-flash-image"`, que es el modelo que la IA 1 ya
     usa por defecto (regla 10). Mismo modelo, mismo encargo, misma imagen,
     mientras la etiqueta decía «Gemini Flash — rápido». La correspondencia
     `ia4 → gemini_flash` se queda en `providerOf()` para que los proyectos ya
     guardados sigan abriendo; lo que se quitó es el botón. Candado:
     `test_calculo_ia4_apagada.py`.
   - **IA 5 no es un motor: es el ENCARGO del 22/07/2026** con el motor de
     siempre (Gemini). Está para comparar los dos caminos con el mismo croquis
     en vez de discutirlo.
   - Esta lista la vigila `test_la_pantalla_ofrece_exactamente_estos_motores`.
     Si se añade o se quita un motor y no se actualiza aquí, el CI se pone
     rojo — que es justo lo que faltó del 18 al 23/08, cuando esta regla estuvo
     cinco días diciendo `IA 2 → manus` con la prueba en verde.
2. **Plano, bocetos, referencia de acabado y descripción se usan A LA VEZ**, cada
   uno mandando en lo suyo. No se vuelve al "o una cosa o la otra".
3. **Tope de 7 imágenes juntas** en render y descripción de proyecto.
4. **Las unidades multiplican**: coste, mano de obra, puertas y el pedido al
   proveedor. Una línea de 4 muebles lleva herraje para 4.
5. **Los descuentos no salen en nada que vea un cliente** (PDF, presupuesto,
   etiqueta comercial). Los mete el master a mano. En la pantalla interna de
   Rentabilidad SÍ se ve el que ha tecleado (04/08, a peticion del master): sin
   verlo no hay forma de saber sobre qué se está calculando el coste.
6. **Lavavajillas = electrodoméstico** (va en hueco, sin casco). Su **puerta de
   integración = material nuestro**. Bajo fregadero y bajo horno son MUEBLES.
7. **Nunca inventar una cota.** Lo que no se sabe va vacío o con "?".
8. **Rentabilidad (Cascos → Alvic/MV) es SOLO del master** (05/08). Ni gerente,
   ni director comercial, ni CONTROLLER: por ahí pasan la tarifa del proveedor,
   el descuento y el margen. Cerrado en pantalla Y en el backend (`_es_master`
   de `routes/cascos.py`); si solo se cierra la pantalla, el cierre es de
   adorno. No confundir con `/api/rentabilidad`, el informe de solo lectura,
   que sí abre el master a CONTROLLER.
8b. **La TARIFA MV (el dinero) es SOLO del master** (24/08). Puntos, PVP, valor
   de punto, la tarifa en crudo y el PDF de las 126 páginas: solo el master. Por
   ahí se lee lo que le cuesta a la casa cada mueble.
   - **El corte va en el PRECIO, no en el CÓDIGO.** Un `B60D` es cómo se llama
     un mueble, no lo que vale. Los códigos, anchos y familias siguen abiertos:
     sin ellos, Cocina Montada 3 y la Relación se quedan muertas para quien
     monta pedidos. `_can_use_mv` = todos (nomenclatura) ·
     `_ve_precios_mv` = master (dinero).
   - Ni `require_admin` ni ninguna lista ancha: por ahí pasan gerente y director
     comercial. Se usa el `_es_master` de `routes/cascos.py`, que es la puerta
     del MV, también desde `routes/products.py`.
   - Candado: `test_calculo_tarifa_mv_solo_master.py`, que LLAMA a los endpoints
     con un usuario que no es master. Comprueba las dos mitades: que no se ve el
     dinero **y** que sí se siguen viendo los códigos.

9. **El candado de Rentabilidad OCULTA IMPORTES, no bloquea la edición**
   (05/08, a petición del master). Echado: se van precios, tarifas, coste,
   mano de obra, margen, precio de venta y €/m². Se quedan códigos,
   descripciones, unidades, medidas y el pedido — y todo eso se sigue pudiendo
   tocar. Sirve para enseñar la pantalla con alguien delante.

10. **El MODELO de imagen de IA 1 no se cambia** (06/08). El candado de motores
   protege QUÉ motor usa cada botón; este protege QUÉ MODELO usa por dentro,
   que es por donde se coló el problema: `gemini-3-pro-image-preview` pasó a
   principal y IA 1 dejó de seguir el boceto —hace imágenes más bonitas pero se
   inventa la distribución—, y IA 3 pasó de `flux-1.1-pro` a `flux-schnell` por
   coste. Ninguno de los dos rompió nada: solo empeoró el resultado, y eso no
   sale en ningún error. **IA 1 es la de producción y su modelo es
   `gemini-2.5-flash-image`.** IA 2/3/4 son motores de pruebas del master: ahí
   puede cambiar, pero dejándolo escrito en
   `backend/tests/test_calculo_modelos_imagen.py`.

El candado no es esta nota: es `backend/tests/test_calculo_motores_render.py` y
el resto de `test_calculo_*.py`. Si alguien cambia una de estas cosas, el CI se
pone en rojo. Ponerlo verde borrando la prueba es exactamente lo que no hay que
hacer.

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

## Propiedad intelectual — qué NO se puede romper

- **Todo fichero propio lleva aviso de copyright.** El CI lo comprueba
  (`herramientas/cabeceras_copyright.py --verificar`). Si añades ficheros,
  ejecuta `python3 herramientas/cabeceras_copyright.py` antes del push.
- **El código de terceros NO se firma como propio.** `frontend/src/components/ui/`
  es shadcn/ui (MIT) y `frontend/src/lib/utils.js` también. Si copias más código
  ajeno al repo, añádelo a `EXCLUIDOS` de esa herramienta Y a `COPIADO_DENTRO`
  de `herramientas/licencias_dependencias.py`. Firmar código ajeno no protege
  nada y es falso.
- **Antes de meter una dependencia nueva, mira su licencia**:
  `python3 herramientas/licencias_dependencias.py`. Una GPL/AGPL en un producto
  que se licencia a clientes es un problema serio, no un detalle.
  **PyMuPDF (`fitz`) esta PROHIBIDO**: es AGPL y obliga a publicar el codigo
  al servir el ERP por red. Se retiro el 05/08. Todo el trato con PDF va por
  `backend/services/pdf_utils.py` (pypdf + pypdfium2); hay una prueba que se
  pone roja si alguien vuelve a importar `fitz`.
- Antes de un depósito notarial o registro:
  `python3 herramientas/inventario_codigo.py` regenera las huellas SHA-256.
