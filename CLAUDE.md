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
  EXACTAMENTE con el ancho real de esa pared. Pero cuadrarla no vale a cualquier
  precio: un relleno son unos pocos centímetros de tablero, así que por encima de
  `RELLENO_MAXIMO` (60 cm, el ancho de mueble más corriente) la distribución se
  RECHAZA con «faltan módulos» en vez de taparlo. Un «relleno» de 195 cm no es
  una cocina, es una lectura mal hecha.

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
7. **Nunca inventar una cota.** Lo que no se sabe va vacío o con "?". Y ojo con
   taparlo antes de tiempo: `cota_de_ancho` distingue escrita / estimada / sin
   dato, pero hasta el 25/08 la ruta de detectar rellenaba el hueco con un 60
   ANTES de validar, así que el caso "?" no podía darse NUNCA por el camino
   principal y se imprimía "~60" de módulos que no había medido nadie. Un módulo
   sin ancho llega SIN la clave `ancho`: se dibuja para que el alzado cierre y se
   rotula "?". Candado: `test_calculo_cota_sin_dato.py`.
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

11. **El MOTOR de render se comprueba en el SERVIDOR, no solo en la pantalla**
   (25/08, al auditar). La pantalla ya solo le ofrecía los motores de pruebas al
   master, pero el motor viaja en el cuerpo de la petición y la API lo aceptaba
   tal cual: cualquier usuario con sesión podía pedir la IA 7 —3,3x de coste—
   desde fuera. Ahora pasa por `motor_permitido()` de `routes/ai_engine.py`, con
   la misma puerta que el MV (`_es_master`), y el coste en créditos depende del
   motor. Candado: `test_calculo_motor_solo_master.py`.

12. **Un proyecto guardado se abre con las medidas con las que se cerró**
   (25/08). No se guardaban: vivían solo en la sesión del navegador, y al
   reabrir el proyecto la pared se quedaba sin anclar y todas las cotas pasaban
   de escritas a estimadas solas. Van al servidor `medidas`, `distribucion` y
   `tipo3d`, y se recuperan al abrir. OJO: se guarda con `$set` del documento
   entero, así que un guardado que no las traiga NO puede borrarlas — de ahí que
   se parta de lo que ya había y que estén en la proyección del `find_one`.
   Candado: `test_calculo_proyecto_guarda_medidas.py`.

13. **La ALTURA de un mueble MV la elige el master, y manda en el precio**
   (25/08). La pantalla no mandaba `alto_altos` ni `alto_columnas` y el backend
   cogía 70 y 200 en silencio: TODA relación salía tarifada a 70/200 aunque la
   cocina llevara otra cosa. Un alto de 60 vale 156,51 € a 70 y 169,83 € a 90.
   Propuestas del master: **altos 90, bajos 80, columnas 220**; los bajos no se
   eligen (esta fábrica solo los hace a 80). Se pueden cambiar antes de sacar la
   relación Y en el presupuesto ya hecho, antes de pasar a pedido. Candado:
   `test_calculo_alturas_mv.py`.

14. **Un proyecto guarda las DECISIONES de la relación MV, nunca los PRECIOS**
   (25/08). La mano D/I y el «dos puertas» los decide el master y se perdían al
   cerrar. Se guardan; el precio NO, y se vuelve a pedir al catálogo al abrir.
   Si se guardara, el proyecto llevaría la tarifa MV dentro y cualquiera que lo
   abriera vería el dinero sin pasar por el candado del servidor (regla 8b): un
   candado que se rodea guardando un fichero no es un candado. Candado:
   `test_calculo_proyecto_guarda_medidas.py`.

15. **El aviso de coste del render NUNCA dice qué IA se usa** (25/08, a petición
   del master). Se dice el número de créditos y ya está: IA 1 es la única que ve
   un usuario que no sea master (regla 1), así que poner el motor en pantalla
   enseña por dónde va la casa. La tabla de costes está en la pantalla y en el
   servidor, y el candado compara las dos: si se separan, el aviso diría una
   cosa y la factura otra. Candado: `test_pantalla_aviso_de_coste.py`.

16. **Las COMISIONES de los cooperativistas son NÓMINA: los números los dicta
   el master** (25/08). Montadores: su comisión ES la mano de obra por mueble
   que ya se teclea en Rentabilidad MV — no tiene fórmula propia a propósito,
   porque dos números para lo mismo acaban sin cuadrar. Comerciales: cantidad
   FIJA por mueble según la valoración del pedido: **20 € por debajo de
   2.500 €, 30 € hasta 6.000 €, 40 € hasta 9.000 €, 50 € hasta 12.000 €, 60 €
   hasta 15.000 € y 70 € por encima**, con un tope de 70 € por mueble (el tope
   sube SIEMPRE con el tramo más alto: ver abajo). El cálculo vive en
   `services/comisiones.py` y la
   pantalla tiene su propia tabla: el candado compara las dos —los números Y el
   nombre del tramo—, porque si se separan alguien cobra de menos, o cobra bien
   con una explicación que miente. Van dentro del candado de importes de
   Rentabilidad (regla 9). Candado: `test_calculo_comisiones.py`.
   - El tramo lo marca la **BASE IMPONIBLE**: el PVP DESPUÉS del descuento y
     SIN IVA. Costó dos correcciones del master: primero se hizo sobre el coste
     («importes de costo»), lo corrigió a PVP, y después zanjó lo del descuento
     con «siempre va sobre la base imponible, no sobre el total con IVA». Ni el
     coste ni el total con IVA pueden entrar: con el IVA, 5.500 € de base pasan
     a 6.655 € y saltan de tramo sin valer un euro más para la casa.
   - En el borde EXACTO se paga el tramo de arriba, en todos: 2.500 → 30 €,
     6.000 → 40 €, 9.000 → 50 €, 12.000 → 60 €, 15.000 → 70 €. Confirmado por
     el master el 25/08 («en 6.000 euros exactos, 40 euros»).
   - **EL TOPE SUBE CON EL TRAMO MÁS ALTO, SIEMPRE.** La escala creció en tres
     tandas el 25/08 (9.000 → 50 €, «el bloque de 12000 y 60 euros de prima»,
     «el último bloque de 15000 euros y 70 euros de prima») y el tope pasó de
     50 a 70 con ella. Si se quedara por detrás, `min(euros, TOPE)` recortaría
     los tramos altos EN SILENCIO —sin error, sin aviso— y el comercial cobraría
     de menos. Si se queda por delante, es letra muerta. Un tramo nuevo obliga a
     mirar el tope A LA VEZ, preguntando antes al master. Hay candado para eso.
     Se le preguntó si quería un techo por encima de la escala y dijo que no:
     «70 tope de momento» (25/08). Que hoy no recorte nada es la decisión, no un
     cabo suelto.
   - El **rótulo** del tramo se DERIVA de la tabla, no se escribe a mano, en las
     dos puntas. Escrito a mano ya se rompió: al añadir el tramo de 9.000 € el
     importe pasó a 50 € y la etiqueta se quedó en «más de 6.000 €» — el número
     bien y la explicación mintiendo, que es peor, porque quien lo lee se fía.
     El candado `test_la_pantalla_PAGA_Y_ROTULA_igual_que_el_calculo` EJECUTA en
     node las funciones del JSX y las compara con las del backend valor a valor.

17. **CUÁNDO cobra un cooperativista: los tres estados del dinero** (25/08).
   `comisiones.py` dice CUÁNTO; `services/liquidaciones.py` dice CUÁNDO, que es
   donde se paga dos veces o se paga de más. **En progreso** = pedido aceptado:
   lo VE en euros (es el plan de estimulación) pero no es suyo y se cae con el
   pedido. **Consolidada** = servido del todo Y cobrado del todo. **Liquidada** =
   ya pagada, no vuelve a entrar nunca. Se liquida **una vez al mes**.
   - **El mes es el de la ENTREGA**, no el del cobro: «si se sirven en agosto se
     liquidan en agosto» (master). El cobro decide SI se libera, no CUÁNDO.
   - **Las dos condiciones son una «Y».** Servido sin cobrar es pagar con dinero
     que no ha entrado; cobrado sin servir es un anticipo.
   - **«Cobrado» es cobrado del TODO.** Este ERP lleva cobros a cuenta
     (`pendienteCobro`): al 90% no libera. Media céntimo de tolerancia, que es
     redondeo — sin ella, un descuadre de un céntimo congelaría una comisión
     para siempre.
   - «Todos los pedidos antes de salir del almacén tienen que estar cobrados»
     (master). Eso es una NORMA DE LA CASA, no una ley de la física: la cumplen
     personas y el dato lo teclean personas. **No se da por hecha.** Si un pedido
     sale con pendiente, no se paga Y se marca (`es_anomalia`) en vez de quedarse
     callado entre los normales. Un candado que se apoya en que nadie se
     equivoque no es un candado.
   - Un pedido anulado o sin aceptar devuelve `None`, no cero euros: una línea a
     cero en el panel del comercial es recordarle lo que no va a cobrar. Y el
     panel NO da un total que sume los tres montones — son promesas de distinto
     valor. Candado: `test_calculo_liquidaciones.py`.

18. **El COLOR del ERP se genera, no se escribe a mano** (25/08). El master:
   «colores que no griten, que queden bien y que quede todo bastante integrado
   y moderno». El aspecto no salía de ningún sitio central — 92 componentes y
   78.000 líneas repitiendo clases de Tailwind, con los tokens de shadcn sin
   usar. Ahora la paleta vive en `frontend/paleta.generada.js`, que sale de
   `herramientas/paleta_erp.py`: los colores de Tailwind con la **misma
   luminosidad y menos saturación**.
   - **La L no se toca.** Los contrastes de las 92 pantallas dependen de la
     luminosidad, no de la saturación: bajando solo la C, un `bg-indigo-600`
     sigue siendo igual de oscuro y el blanco encima se sigue leyendo. Única
     excepción: tres colores (fuchsia, pink, rose en el tono 600) que al
     apagarse cruzaban por debajo de 4,5 de contraste y se oscurecieron lo
     justo. Regla: **apagar no puede tumbar un contraste que antes aprobaba**;
     lo que ya venía suspenso de Tailwind se deja como está.
   - **UNA sola clave `colors` en `tailwind.config.js`.** La primera versión
     metió una segunda y en JavaScript gana la última: la paleta entera se
     descartó EN SILENCIO — fichero escrito, build en verde, pantalla igual.
   - Los **1.279 hexadecimales sueltos** de los componentes (estilos en línea,
     degradados, iconos) se apagan con `herramientas/apagar_hex_sueltos.py`:
     no pasan por Tailwind, y apagar solo las clases habría dejado media
     pantalla gritando al lado de la otra media.
   - **Pesos de letra:** `font-bold` pesa 600 y `font-black` 700 (eran 700 y
     900). Había 2.132 y 1.929 usos contra 29 `font-semibold`: si todo va en
     negrísima no hay jerarquía y nada destaca. Y ahora son pesos que Inter
     descarga de verdad — antes se pedía 700 sin estar en el `@import` y el
     navegador lo falsificaba.
   - Candado: `test_pantalla_paleta_apagada.py`. Hace falta porque **ningún
     otro candado mira cómo se VE**: todos vigilan el cálculo y lo que la
     pantalla dice, así que un cambio estético entra entero con el CI en verde.

19. **El color dice POR QUÉ, no qué tono es** (25/08). Se escribe `bg-ok-600`,
   no `bg-emerald-600`. Seis tokens en `tailwind.config.js`, todos apuntando a
   la paleta apagada: `accion` · `ok` · `aviso` · `error` · `master` · `dato`.
   La guía es `docs/DISENO.md`.
   - Se midió antes de decidir: las palabras de dinero salían cerca del **46-58%
     de TODOS los colores** (es un ERP, el dinero está en todas partes). El
     único que significaba algo era el rojo, en el 42% junto a «error»,
     «borrar» o «anular». O sea que esto no sustituye un sistema: monta el
     primero que hay.
   - **El dinero NO lleva color de estado.** Un importe no es ni bueno ni malo;
     pintarlo de ámbar lo vuelve un aviso permanente y entonces deja de
     destacar lo que sí lo es. Va en `dato` y destaca por tamaño y peso. Eso
     libera el ámbar para lo que significa en todas partes: atención.
   - La migración de los 92 componentes es a mano y larga —un script no puede
     adivinar qué significa cada color sin equivocarse—, así que va por
     pantallas. `herramientas/avance_semantico.py` mide cuánto queda; un plan
     sin forma de medirlo se abandona a la mitad sin que nadie lo note.
   - Candado: `test_pantalla_colores_con_significado.py`. Comprueba que los
     tokens RESUELVEN de verdad (un alias mal escrito daría `undefined` y la
     clase no pintaría nada con el CI en verde) y que el dinero sigue en gris.

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
