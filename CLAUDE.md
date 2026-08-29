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

**EL ESCALÓN DE LA TARIFA NO ES LA MEDIDA.** En costados, laterales y regletas,
el «hasta 70 / hasta 90» de la tarifa MV decide lo que CUESTA la pieza; el ancho
y el alto reales son lo que se fabrica, se escriben aparte y viajan con el
pedido (master, 28/08: «aunque pongas hasta 70 o hasta 90, esas medidas las
puedo modificar para que queden grabadas las medidas definitivas»). Escribir la
medida definitiva NO puede tocar el precio: si lo moviera, el presupuesto
cambiaría solo mientras alguien ajusta cotas y nadie lo relacionaría. Si la
pieza se sale del escalón, el escalón se cambia a mano al lado — una decisión,
no un efecto secundario. **Se escriben en CENTÍMETROS y con DECIMALES**
(master, 28/08): un costado se corta a milímetro, así que no se redondea, no se
fija un paso de 0,1 —el navegador rechazaría un 61,55— y se admite la coma,
porque en un teclado español se teclea coma y `Number('61,5')` es `NaN`: la
medida se perdería en silencio. Candado:
`test_pantalla_medidas_definitivas.py`.
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
   porque dos números para lo mismo acaban sin cuadrar. Son **17 € por mueble
   montado** (master, 28/08; antes eran 20) y **cada montador puede tener la
   suya**: manda la de su ficha, si no la de la casa, si no los 17.
   `comisiones.mano_de_obra_de()` lo resuelve en un solo sitio. Un **0 puesto a
   propósito se respeta**: se mira si la cifra ESTÁ, no si es verdadera — las
   rutas lo leían con `float(... or 0)`, y con un `or` ese 0 se cae al escalón
   siguiente y el montador cobra los 17 € cuando el master había decidido que
   no cobra (en un pedido de 40 muebles, 680 € que no se recuperan). Una cifra
   corrupta tampoco cae en el defecto: cae en el escalón siguiente, para que un
   dato roto no invente una nómina. La pantalla de Rentabilidad calcula el
   margen con esta misma cifra y el candado compara las dos, porque si se
   separan la pantalla enseña un margen y la nómina paga otra cosa sin que
   ninguno de los dos números parezca un error
   (`test_calculo_mano_de_obra_montador.py`). Comerciales: cantidad
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
   - **SOLO LOS MUEBLES INCENTIVAN** (master, 25/08). Puertas, vitrinas y
     rejillas (son FRENTES), costados, laterales, regletas, techos, elementos
     lineales y las **líneas manuales de servicios** no llevan compensación de
     ningún tipo. Cambia el dinero por los dos lados: cuenta unidades que no
     existen Y su importe empuja el TRAMO de todos los demás muebles. En un
     pedido corriente eran 990 € contra 420 € — un 136% de más. El corte NO es
     una lista escrita a mano: sale de la categoría `lineal` de
     `nomenclaturas_pdf` y del tipo `matrix` de la tarifa. Ojo: un
     `ALTO_VITRINA` SÍ es mueble (casco con puerta de cristal); por eso se corta
     por `matrix` y no por la palabra «vitrina». Un pedido sin sus líneas no
     paga y se marca `sinDesglose`: pagar de menos se reclama, pagar de más no
     se devuelve. Candado: `test_calculo_solo_muebles_incentivan.py`.
   - **UN PEDIDO ES UN PEDIDO: no se juntan dos para subir de tramo** (master,
     25/08: «eso que falte en cada pedido tiene que ser en ESE pedido»). Dos
     pedidos de 7.000 € pagan 40 €/mueble cada uno —800 € en total—, no los
     60 €/mueble y 1.200 € que daría un pedido de 14.000. Ya se comportaba así;
     se amarró porque «cuánto falta EN TOTAL para el siguiente tramo» es la
     clase de mejora que alguien añade con buena intención, y prometer una
     comisión que no va a llegar es peor que no prometer nada.
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
   - **UNA COMISIÓN PAGADA SE LEE, NO SE CALCULA** (28/08, al poder tener cada
     montador su mano de obra). Al cerrar el mes se guarda en el pedido lo que
     se ha pagado por él (`comisionCongelada`) y desde ahí ese importe no
     depende de la tarifa de hoy: sin esto, cambiarle los 17 € a un montador
     movería hacia atrás las liquidaciones ya pagadas y la nómina de agosto
     dejaría de cuadrar con lo que se pagó en agosto, sin que saltara ningún
     error. Se congela POR ROL: el mismo pedido lo cobran dos personas
     distintas, y leer la del otro es pagarle lo que no es suyo. Una
     congelación corrupta vuelve a calcular en vez de devolver cero — un dato
     roto no puede dejar a nadie sin cobrar en silencio.
   - **UN PEDIDO LO COBRAN DOS PERSONAS, Y CADA UNA SE LIQUIDA POR SU CUENTA**
     (29/08, auditando). La marca de «ya pagado» era UNA sola para el pedido
     (`liquidadoEn`), así que al cerrarle el mes al montador el comercial se
     quedaba sin cobrar PARA SIEMPRE: `POST /liquidar` se lo saltaba y en su
     panel la línea ponía «liquidada». En un pedido de 7.000 € con 10 muebles
     son 400 € que no reclama nadie, porque la pantalla le dice que ya se los
     pagaron. No daba ningún error. Ahora la marca y el importe congelado van
     por rol (`liquidadoEnComercial` / `liquidadoEnMontador` y sus congeladas);
     los pedidos cerrados antes se siguen leyendo por el `rol` que llevan dentro
     del congelado, y si no se puede saber de quién eran cuentan para los dos —
     en la duda no se paga otra vez. `estado_de` PIDE EL ROL: «liquidada» es de
     una persona, nunca del pedido. Candado:
     `test_calculo_liquidar_por_rol.py`.
   - **Y si el `update` no toca nada, NO se ha pagado nada.** La condición de
     idempotencia viaja dentro del `update`, pero el resultado se ignoraba: dos
     pulsaciones a la vez daban el total del mes por duplicado en pantalla
     aunque el segundo no escribiera un euro.
   - **`liquidadoEn` no lo escribía NADIE** hasta el 28/08: se leía en cinco
     sitios y el estado LIQUIDADA no se alcanzaba nunca, así que la misma
     comisión podía entrar en la liquidación de septiembre, la de octubre y la
     de noviembre. Lo escribe `POST /liquidar`, que es IDEMPOTENTE: se salta lo
     ya liquidado y el `update` lleva la condición dentro, para que dos
     pulsaciones a la vez no paguen dos veces.
   - **EL ALBARÁN Y LA FACTURA SON LA FUENTE** (28/08). Nadie escribía
     `servidoAt` ni `cobradoAt`, así que ningún pedido consolidaba jamás — el
     área entera enseñaba una promesa que no se cumplía nunca. El ERP sí lo
     sabe, en Gestión Comercial: el ALBARÁN dice que la mercancía salió y la
     FACTURA `paid` que el dinero entró (`services/enlace_documentos.py`). Se
     ata por `projectId` y `budgetNumber`, las referencias que el gestor ya
     guarda, y por NADA más: dos pedidos del mismo cliente por el mismo importe
     son cosa de todos los días, y confundirlos es pagarle a quien no le toca.
     Un pedido sin referencia se queda sin servir a propósito. Con varias
     entregas manda el ÚLTIMO albarán —hasta entonces la mercancía no está
     fuera del todo—, y con varias facturas hacen falta TODAS pagadas: una
     pagada y otra a medias es un pedido a medio cobrar. Lo que el pedido ya
     traiga escrito manda sobre el documento. Candado:
     `test_calculo_enlace_documentos.py`.
   - **Se leen los nombres que el ERP YA usa**: `deliveredAt` (lo estampa
     `projects.py` al pasar a «entregado») y `paidAt` (`invoices.py` al pasar a
     «paid»), además de `servidoAt`/`cobradoAt`. Sin eso, un pedido entregado y
     cobrado de verdad se quedaba en «en progreso» para siempre esperando a un
     campo que no le pone nadie. No se inventa ningún cruce entre colecciones:
     si el documento trae la fecha, se usa. Candado:
     `test_calculo_congelar_comision.py`.
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

20. **El ÁREA del cooperativista: cada uno lo suyo, y nada del dinero de la
   casa** (25/08). `services/area_cooperativista.py` decide QUIÉN mira;
   `routes/cooperativistas.py` son tres rutas y ni una más.
   - **El filtro sale del TOKEN, nunca de la petición.** Si el «de quién son los
     pedidos» viajara en la URL, cualquiera cambiaría el número y vería la
     nómina del compañero. Mismo fallo que tenía el motor de render (regla 11),
     mismo arreglo.
   - **`filtro_de` devuelve `None`, no `{}`,** cuando el usuario no es
     cooperativista. Un `{}` pasado a Mongo son TODOS los pedidos de la casa.
   - **Lista BLANCA de lo que sale** (`CAMPOS_VISIBLES`). Con una lista negra,
     cualquier campo nuevo del pedido —un coste, un margen— saldría solo el día
     que alguien lo añada.
   - **Asignar comercial o montador es del master**: cambiar el comercial de un
     pedido mueve una comisión de un bolsillo a otro.
   - Candado: `test_calculo_area_cooperativista.py`. OJO: la primera versión de
     la prueba del dinero PASABA POR EL MOTIVO EQUIVOCADO —`liquidaciones` no
     produce campos de dinero, así que el recorte no se ejercía nunca y quitarlo
     entero dejaba el CI en verde—. Ahora se fuerza a que la capa de abajo
     devuelva coste y margen para comprobar que el panel los corta de verdad.

21. **TRES PLATAFORMAS EN EL MISMO ERP, Y SOLO UNA REPARTE COMISIONES**
   (27/08). El master: «carpinter.io y Studio3K son solo para vender
   suscripciones a usuarios que pagan... no tienen nada que ver con el negocio
   de los cooperativistas, son plataformas independientes aunque las tengamos
   metidas en la misma gestión del ERP de momento». El campo es
   `plataforma`: `cooperativa` · `carpinter` · `studio3k`
   (`services/plataformas.py`).
   - **La plataforma se comprueba ANTES que el rol.** Las tres comparten la
     colección de usuarios, y ahí está el peligro: «comercial» significa cosas
     distintas en cada negocio. Basta un clic en la pantalla de permisos —marcar
     comercial a un suscriptor de carpinter.io— para que empiece a salir en la
     liquidación cobrando comisiones de la cooperativa. No hace falta mala fe.
     Ser comercial no basta: hay que ser comercial DE LA COOPERATIVA.
   - **SER SOCIO SE MARCA, NO SE DEDUCE DEL ROL** (27/08, corrigiendo la
     primera versión). El master: «no todos son de la cooperativa. Comercial
     cooperativista sí, montador cooperativista también. Los demás son
     independientes. El rol de comisiones solamente es para estos dos». La
     primera versión sacaba el socio de `isMontador` / `isRepresentative`, y ahí
     estaba el dinero: `isRepresentative` es el comercial de toda la vida de la
     casa —hay comerciales sembrados con ese flag en `seed_comerciales.py`— e
     `isMontador` es el de la agenda de montajes. Con aquello entraba en la
     liquidación medio ERP sin que nadie lo hubiera decidido. Ahora hacen falta
     las dos cosas: estar en la cooperativa Y llevar la marca
     (`esCooperativistaComercial` / `esCooperativistaMontador`).
   - **Son DOS marcas y no una casilla «es cooperativista»** porque el rol
     decide CÓMO se paga: el comercial por tramos según la valoración, el
     montador la mano de obra por mueble. Quien lleve las dos entra como
     MONTADOR, que es el rol que no deja deducir el PVP del pedido.
   - **El defecto es `cooperativa`, y eso es una decisión, no un descuido.**
     Todos los usuarios que existen hoy son del negocio de siempre y ninguno
     trae el campo. Con cualquier otro defecto, el día del despliegue los
     cooperativistas de verdad se quedarían sin su área sin que nadie hubiera
     tocado un solo usuario — y el error se vería en la nómina de fin de mes, no
     en el CI. Ojo: el defecto es de PLATAFORMA, no de socio. Nadie cobra por
     defecto; ser de la cooperativa es condición necesaria y no suficiente. Un valor que no se reconozca también cae en `cooperativa`: mejor
     un usuario mal etiquetado en el negocio de siempre, donde alguien lo verá,
     que en un limbo del que no sale en ninguna lista.
   - **El menú es una sugerencia; quien cierra es el servidor.**
     `frontend/src/plataformas.js` es una copia en pantalla para poder decidir
     si se enseña «Mi área» sin llamar a nadie. Copia que no se compara se
     separa, así que el candado EJECUTA en node las funciones del JS y las
     compara con las del backend usuario a usuario. Si se separan, o el
     suscriptor ve un botón que le da 403, o —lo que de verdad importa— el
     cooperativista pierde el suyo y nadie se entera hasta que pregunta.
   - **La pantalla se abre desde el menú Y desde la bienvenida.** Una pantalla
     sin puerta no existe: `AreaCooperativista.jsx` estuvo escrita, con sus
     rutas y sus candados, y sin un solo sitio desde el que abrirla.
   - **EN LA AGENDA DE MONTAJES HAY EXTERNOS Y SOCIOS, MEZCLADOS** (master,
     28/08: «los montadores pueden ser externos o miembros de la cooperativa;
     tenlo muy presente»). Los dos montan cocinas y los dos tienen ficha; solo
     el socio cobra comisión. La agenda NO puede ser la puerta por la que un
     externo entre en la nómina: vincular su ficha con una cuenta no hace socio
     a nadie — eso lo decide la marca `esCooperativistaMontador`, y nada más.
   - **Los socios se dan de alta desde COOP** (master, 28/08). En la pestaña
     Usuarios hay «+ Nuevo socio»: se crea ya marcado con su rol y en la
     plataforma de la cooperativa, que es la única que reparte comisiones. Los
     permisos del ERP se le dan luego a conciencia en el panel Master — un
     montador entra a ver lo suyo, no a presupuestar.
   - **QUIEN GRABA EL PEDIDO SE LO LLEVA, SI ES SOCIO** (master, 28/08:
     «dependiendo del usuario que grabe el pedido, así comisionará, si son
     usuarios cooperativistas»). Le ahorra al master asignar a mano el caso
     normal —el comercial que teclea su propio pedido—, con tres cierres: SOLO
     si `rol_de` dice que es socio (un comercial en nómina o un suscriptor
     graban pedidos igual y no cobran), en SU rol (el montador no puede entrar
     como comercial: cobran distinto) y **sin pisar nunca lo ya asignado**, ni
     al re-guardar el mismo pedido. Para eso el documento anterior se lee CON
     sus asignaciones: leerlo sin ellas haría que la comprobación diera siempre
     vacío y pisara siempre.
   - **LA AGENDA PROPONE, EL MASTER ASIGNA** (28/08). La ficha de montador
     (`montadores.id`, la agenda de montajes) y la cuenta con la que entra eran
     dos mundos: el master repetía a mano quién montó cada pedido cuando el ERP
     ya lo sabía. El puente es `usuario.montadorId`, un campo que existía en el
     modelo y no leía nadie (`services/enlace_montador.py`). Se SUGIERE y no se
     asigna: aplicarlo es un clic suyo, porque ahorrar clics no puede
     convertirse en pagar por deducción. **En la duda se calla**, y son tres
     dudas: ficha sin cuenta, cuenta que no es socio montador (un montador en
     nómina monta cocinas igual y no cobra comisión) y varios montadores
     distintos en el mismo pedido. Tampoco se propone encima de lo ya asignado
     —sería una invitación a deshacer una decisión del master sin querer— ni se
     elige entre dos cuentas que compartan ficha, que es un error de datos y
     resolverlo a dedo sería pagarle a una por sorteo. Candado:
     `test_calculo_enlace_montador.py`.
   - **SOLO CUENTAN COCINA MONTADA 3 Y COCINA DESMONTADA** (master, 28/08:
     «solo lista los pedidos que se hayan realizado desde Cocina Montada 3 o
     Cocina Desmontada»). Lo dijo viendo en pantalla pedidos de la primera
     sección de fábrica. El ERP los guarda en sitios distintos: Desmontada en
     `cascos_orders` (y ahí solo `kind: "pedido"` — un presupuesto no se ha
     vendido y una compra es al proveedor) y las secciones VIEJAS en `orders`.
     La lista es BLANCA (`services/origen_pedidos.py`): se dice qué entra, no
     qué se excluye, porque con una lista negra una sección nueva del ERP se
     colaría sola en la nómina el día que alguien la añada. Y al ESCRIBIR se
     tocan las dos colecciones: escribir siempre en `orders` dejaba sin efecto
     asignar o liquidar un pedido de Desmontada, respondiendo que sí y sin
     cambiar nada. Candado: `test_calculo_origen_pedidos.py`.
   - **EL ROTULO DEL ORIGEN NO PUEDE MENTIR** (29/08, auditando). Desde que
     Cocina Montada 3 crea pedidos, `cascos_orders` ya no es solo Cocina
     Desmontada — y la traducción de esa colección marcaba TODOS los pedidos
     como Desmontada, así que en COOP los de Montada 3 salían con la sección
     equivocada. Contar contaban (las dos están en la lista blanca), pero el
     rótulo es justo lo que hay que mirar el día que se cuele un pedido que no
     toca: si miente, el «solo Montada 3 o Desmontada» que pidió el master no se
     puede comprobar. Y el origen se RESPALDA al guardar: se escribe con un
     `$set` del documento entero, así que sin respaldo un re-guardado que no lo
     trajera lo borraría y el pedido pasaría a contarse como Desmontada solo.
   - **Un pedido sin asignar no da error: no le paga a nadie.** La pantalla
     «Socios» (`SociosCooperativistas.jsx`, dentro del botón **COOP** del menú
     —master, 28/08—, junto con la liquidación del mes) es la que pone quién
     vendió y quién montó cada pedido, y sin ella el área entera enseña ceros.
     Los pedidos sin asignar salen primero y se cuentan, porque un pedido
     servido y cobrado sin dueño no se queja: simplemente no aparece en la
     nómina de nadie. La lista de socios sale por lista BLANCA
     (`CAMPOS_DEL_SOCIO`) —dentro del usuario hay contraseña, descuentos y
     permisos— y ahí no puede aparecer quien no sea socio: si saliera el
     comercial en nómina, asignarle un pedido lo metería en la liquidación por
     la puerta de atrás. La pantalla NO enseña el importe del pedido: el master
     podría verlo, pero para decidir quién montó una cocina no hace falta.
   - Candados: `test_calculo_plataformas.py`, `test_calculo_asignar_socios.py`
     y los tres del enlace en `test_pantalla_area_cooperativista.py`.

22. **EL PRESUPUESTADOR: DOS PANTALLAS, UNA PUERTA** (28/08). Cocina Montada 3
   y Cocina Desmontada viven bajo una sección llamada «Presupuestador», en
   pestañas. **Se junta la CARCASA, no los motores**: cada pestaña pinta la
   pantalla que ya existía, sin tocarla por dentro, y cada una sigue guardando
   donde guardaba —Montada por tarifa MV, Desmontada en `cascos_orders` con su
   expediente y su compra al proveedor—. Unificar el almacenamiento rompería lo
   que hace que COOP distinga el origen de cada pedido (regla 21).
   - **LOS PERMISOS NO CAMBIAN**, y eso es lo importante:
     `canUsePresupuestador3` para Montada (donde «no estar desactivado» ya era
     el criterio) y `canUseCascos` explícito para Desmontada, nunca para una
     tienda. Mover pantallas de sitio no puede cambiar quién entra: si de paso
     se movieran los permisos, nadie sabría si un usuario dejó de ver algo por
     el rediseño o porque se lo quitamos. `frontend/src/presupuestador.js` los
     resuelve en un solo sitio y el candado los compara usuario a usuario.
   - **LOS CAMINOS VIEJOS SIGUEN VIVOS.** `cocinaMontada3` y `cascos` abren su
     pestaña dentro de la sección. Una pantalla a la que se llegaba y ya no se
     llega es una pantalla perdida, y hay enlaces y estado de navegador con esos
     nombres.
   - **La pestaña que no se ve NO se desmonta**, se oculta: si se desmontara,
     cambiar de pestaña vaciaría una relación a medio hacer — y en Cocina
     Montada 3 eso puede ser una cocina entera tecleada a mano.
   - El corte por permiso está SOLO en pantalla, a propósito y de momento: la
     regla 8 pide cerrarlo también en el servidor, pero eso es apretar un
     candado y el 28/08 apretar uno dejó al master sin sus propios precios (ver
     `services/master.py`). Se hará con el orden correcto: primero comprobar a
     quién afecta, después cerrar.
   - Candado: `test_pantalla_presupuestador.py`.

23. **NINGÚN HOOK POR DEBAJO DE UN `return`: eso deja el ERP EN NEGRO** (29/08).
   El master: «cuando entro en máster sale este error», con la pantalla
   completamente negra en el móvil. En `SettingsModal.jsx` —el panel Master— se
   había colado un `useEffect` debajo del `if (!isOpen) return null` que ese
   componente tiene a media altura: cerrado, React ejecutaba 87 hooks; abierto,
   88. Eso es «Rendered more hooks than during the previous render», y React no
   tira esa pantalla: tira el árbol ENTERO. El ERP completo se va a negro y solo
   vuelve recargando.
   - **No lo avisa nada.** El build pasa, ESLint con esta configuración no lo
     ve, y ningún otro candado mira si una pantalla se llega a PINTAR: todos
     vigilan lo que el ERP calcula.
   - La regla es la de React de siempre: los hooks van TODOS antes del primer
     `return` del componente. Lo que se condiciona es lo que hacen dentro
     (`useEffect(() => { if (!isOpen) return; … }, [isOpen])`).
   - Candado: `test_pantalla_hooks_antes_del_return.py`, que barre las 92
     pantallas. Y comprueba que su propio reconocedor SÍ encuentra el fallo
     cuando se le da: un detector que no detecta nada da cero y el CI en verde.

24. **EL ERP ES ESPAÑOL Y NADIE LO TRADUCE** (29/08). `index.html` decía
   `<html lang="en">` con todo escrito en castellano. Un Chrome de móvil en
   español, con «traducir siempre las páginas en inglés» puesto, se cree la
   etiqueta y TRADUCE el ERP solo, sin preguntar: para traducir mete cada texto
   dentro de un `<font>`, o sea que le cambia el DOM a React por debajo. La
   siguiente vez que React va a mover algo, el nodo ya no está donde lo dejó —
   `NotFoundError: insertBefore` — y eso no rompe una pantalla, **tumba la
   aplicación entera**. En el portátil no pasaba porque ahí Chrome pregunta
   antes.
   - Y aunque no tumbara nada: por estas pantallas pasan `B60D/I`, `CMCB`,
     medidas y euros. **«BAJO» no es una palabra que traducir, es una familia de
     la tarifa MV.**
   - Van las TRES marcas, que se refuerzan: `lang="es"` (que además es lo que
     leen los lectores de pantalla, así que estaba mal por dos motivos),
     `translate="no"` en el `<html>` y `<meta name="google" content="notranslate">`,
     que es la que de verdad respeta Chrome.
   - Candado: `test_pantalla_no_traducir.py`. Su reconocedor **ignora los
     comentarios**, porque el propio fichero explica el fallo citando un
     `lang="en"` de ejemplo que si no lo engañaría.

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
