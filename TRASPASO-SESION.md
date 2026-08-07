# Traspaso de sesión — 06/08/2026

Léeme entero antes de tocar nada. Lo de arriba es lo que está roto; lo de abajo,
lo que ya está hecho y NO hay que rehacer.

---

## 1. LO URGENTE: el render no sigue el boceto

**Síntoma.** El master sube un croquis a mano (cocina en L, dos combis en la
pared izquierda, escobero, despensero, lavavajillas + horno compacto,
desayunador, isla con fregadero) y el Estudio 3D devuelve una cocina **en línea
recta con isla redondeada**: ni la L, ni los combis, ni el escobero, ni el
despensero. No lee el boceto, se inventa una cocina genérica.

**Descartado ya** (comprobado, no lo repitas):
- **NO es el plan de instalaciones ni la geometría del alzado.** `render_3d.py` y
  `ai_engine.py` no importan `kitchen_geometry`, `estudio_cocinas` ni
  `instalaciones_cocina`. Cero referencias. Son tuberías separadas.
- **NO es el reparto de motores.** IA 1 → gemini sigue intacto y con su candado
  (`test_calculo_motores_render.py`).

### RESUELTO el 06/08 — era el detector de croquis, no el modelo

**La causa.** `_is_sketch_reference` (`render_3d.py`) **solo miraba si el fichero
era un PDF**. El master fotografía el croquis con el móvil, así que llegaba un
JPEG, el detector respondía «no es un croquis» y el render se iba por la rama de
**EDITAR UNA FOTO DE UNA COCINA EXISTENTE**, cuyo prompt literal es *«You are
given a reference image of an EXISTING kitchen… your job is to EDIT that exact
image… do NOT redesign, reorganize, add, remove or move anything»*.

Es decir: al modelo se le ordenaba fotorrealizar un dibujo a lápiz **como si ya
fuera una cocina montada**. Con esa orden solo podía hacer una cosa —
inventarse una cocina genérica. De ahí la línea recta y la isla redondeada.

El comentario del código (línea ~556) llevaba meses diciendo que detectaba «PDF
escaneado **o imagen con trazos a mano**». El comentario mentía; el código nunca
hizo lo segundo.

**Arreglado.** El detector mira ahora el CONTENIDO del mapa de bits, que es lo
único que distingue un croquis fotografiado de una foto (el MIME es el mismo en
los dos): un croquis es casi gris (sin color) y casi todo fondo claro de papel.
Es **conservador a propósito** — ante la duda, foto — porque la equivocación
contraria también estropea el render, tirando la referencia real del cliente.
Probado contra el peor caso posible, la foto de una cocina **blanca**: saturación
0,14 frente al 0,10 del umbral, no se cuela.

**Y una segunda causa, encadenada con la primera.** Detectar el croquis no
bastaba: la rama a la que se le enviaba **compartía camino con «diseñar desde
cero»**, que llama a `_expand_brief`. Eso le pide a gemini-2.5-pro que redacte
la distribución y **los módulos de izquierda a derecha a partir del TEXTO y sin
haber visto el dibujo** — o sea, una cocina inventada — y además la mete en un
prompt largo de dirección de arte (`build_render_prompt` + criterios + estilo).
El croquis viajaba, sí, pero compitiendo contra una especificación enorme de
OTRA cocina. El modelo obedecía al texto.

Lo curioso es que esto ya estaba escrito en el propio repo, en el comentario del
render compuesto: *«un texto largo de dirección de arte compite con las imágenes
y el modelo acaba inventando una cocina genérica»*. Estaba aplicado allí y no
aquí. Ahora el croquis tiene rama propia con prompt CORTO centrado en el dibujo:
la geometría sale 100 % del croquis y el texto se queda solo con acabados,
materiales y colores.

**Tercera pieza, en el render compuesto** (el camino del botón principal cuando
subes el plano): el prompt daba por hecho que las referencias eran fotos o
renders. Si el plano va a lápiz ahora se le dice, para que no dibuje el papel y
el trazo, ni «mejore» una distribución que le parece tosca por estar hecha a
mano.

Candado: `backend/tests/test_calculo_croquis_render.py` (11 pruebas).

**Sobre las tres pistas de esta sección — la nº 1 estaba del revés:**

1. **`render_3d.py:1253` NO es la ruta de IA 1.** Ese `model_override` está
   dentro de la rama `provider == "gemini_flash"`, que es **IA 4**. IA 1 cae al
   `return` final, sin override. Conclusión contraria a la que suponía este
   documento: el arreglo de la otra IA (`b79a21a2`) **sí llegó a IA 1** — era
   correcto y además útil, no inocuo. Pero no era la causa del síntoma.
2. **El boceto SÍ llega al modelo.** Cadena comprobada de punta a punta: las
   imágenes se decodifican y viajan como `Part.from_bytes` antes del prompt, y
   el tope de 7 no recortaba nada en este caso. Hay candado nuevo para que siga
   llegando (`test_el_croquis_viaja_de_verdad_hasta_el_modelo`).
3. **El prompt del 04/08 queda sin tocar.** No hacía falta: el problema no era
   qué decía el prompt, era **qué prompt se elegía**. Sigue disponible como
   experimento si el master quiere comparar fidelidad.

### Lo que queda abierto de este punto

- **Un croquis en PDF de VARIAS páginas pierde todas menos la primera.**
  `_prepare_reference` convierte con `max_pages=1`, en silencio. Si el master
  escanea planta + alzados en un solo PDF, el modelo solo ve la hoja 1. No lo
  he tocado porque subir el número de páginas gasta del tope de 7 imágenes, que
  es habilidad bloqueada (regla 3): **decide el master cómo repartir ese cupo.**
- **Decisión del master: el respaldo silencioso de modelo.** Si
  `gemini-2.5-flash-image` falla o tarda más de 90 s, la cascada de
  `llm_vision.py` baja sola a `gemini-3-pro-image-preview` — justo el modelo que
  «se inventa la distribución». El render sale, parece bueno, y nadie se entera.
  La regla 10 dice que el modelo de IA 1 es fijo, así que **no he cambiado el
  comportamiento sin permiso**: de momento queda un `logger.error` bien visible.
  Si el master quiere que IA 1 **falle** en vez de renderizar con el modelo
  creativo, es un cambio de una línea.

---

## 2. El alzado alámbrico: lo que SIGUE mal

Caso real: croquis con MALL. NEGRO 60 + lavadora 60 + cajonera 60 +
lavavajillas PBI-60 + mueble 80 + columna frigo 60 = **380 cm**.
El ERP dibujó **440 cm**.

**Causa: la placa se cuenta como un mueble más.** Mete una «Placa 60×80» entre
la cajonera y el lavavajillas, dibujada como armario con puerta. Pero una placa
va **encastrada en la encimera**, encima de la cajonera: no es un mueble ni
ocupa ancho de pared. Al tratarla como módulo, la pared se alarga 60 cm y todas
las cotas se desplazan.

**Qué hacer (pendiente de hacer, con cuidado — toca `kitchen_geometry.py`, que
es el corazón por donde pasan alzado, planta e instalaciones):**

1. **La placa deja de ocupar ancho propio.** Se dibuja como marca sobre la
   encimera en su posición. **Ojo:** si debajo no hay ningún mueble, entonces sí
   hay que insertar un «bajo placa» de ese ancho — si no, se pierden 60 cm en
   las cocinas donde la IA solo devuelve la placa.
2. **Misma regla para el fregadero**, que es el mismo caso.
3. **Altura de columna configurable** (200/220/238,5). Ahora está fija a 220 y
   el croquis decía 238,5 (249 hasta el techo).
4. **Faltan altos.** El croquis tiene cuatro (80+60+60+80 = 280 cm) y el dibujo
   pinta dos (60+80). Que el prompt insista en devolver TODOS los altos con su
   ancho.
5. Menor: la cajonera sigue con el rótulo encabalgado sobre las cotas de los
   frentes; el frigorífico se pinta con aspas de hueco en vez de columna cerrada.

**Verifica siempre contra los tres documentos del master a la vez:** el croquis
a mano, el render y el alzado generado. Si las tres cifras no coinciden, está mal.

---

## 3. Decisión pendiente del master (NO decidir por él)

**¿«INC 25 %» es margen sobre coste o sobre venta?**

Hoy el digitalizador multiplica por 1,25 → es un **markup del 25 % sobre el
coste**, que sobre el precio de venta es un **20 %**. Con sus números:
coste 5.042,30 → venta 6.302,88 → gana 1.260,58 = 20,0 % de lo facturado.
Si quisiera ganar el 25 % **de la venta**, sería dividir entre 0,75 → 6.723,07 €.
**420 € de diferencia en un solo presupuesto.** No se toca sin que él lo diga.

Aparte, hay un fallo real ahí: **la casilla INC% de cada línea NO es editable**
(es un `<span>` que repite el global, pintado igual que la de Dto%, que sí lo es).
Si él cambia el 25 de una línea suelta, no pasa nada y no se le avisa.

---

## 4. LO QUE YA ESTÁ HECHO HOY — no lo rehagas

| Qué | Estado |
|---|---|
| **Guardado del digitalizador** | 9 peticiones iban SIN token (401) y el fallo se ignoraba en silencio: decía «guardado» y no guardaba. Arreglado + candado. |
| **Plan de instalaciones** | Reescrito. Sale de la cocina real, con cota de replanteo por punto. Corregidos: potencia sumando amperios, placa «trifásica», RITE para fontanería, circuitos sin nomenclatura ITC-BT-25. |
| **Medidas escritas > estimación IA** | Orden de verdad: usuario > cota escrita > suma de módulos escritos > estimación. Antes aplastaba un croquis de 407 cm contra una pared «de 280» inventada. |
| **Geometría del alzado** | Altos y bajos en filas independientes; la suma cuadra o no se dibuja; anchos de catálogo; rellenos recalculados. |
| **Planta (`/plano-2d`)** | Ya no se inventa una pared de 400×240 en silencio. |
| **Errores 4xx disfrazados de 500** | Barrido con `ast` de todo `estudio_cocinas.py`. |
| **PyMuPDF (AGPL) fuera** | Sustituido por pypdf + pypdfium2. Sin copyleft fuerte en el producto. |
| **Propiedad intelectual** | Cabeceras de copyright (287 ficheros), inventario SHA-256, auditoría de licencias, aviso legal y condiciones de uso. |
| **Candado del modelo de imagen** | IA 1 fijada a `gemini-2.5-flash-image`; IA 3 devuelta a `flux-1.1-pro` (estaba en `flux-schnell` por coste desde el 01/08). |

**174 pruebas en verde.** Todo desplegado en `main`.

---

## 5. Reglas que NO se rompen

Están en `CLAUDE.md`, sección «Habilidades BLOQUEADAS». Las dos que más se han
saltado, por si acaso:

- **Nunca inventar una medida.** Ni una pared por defecto, ni un ancho «plausible».
  Lo que no se sabe se pide. Y si la suma no cuadra, **no se dibuja**: un plano
  que miente es peor que no tener plano, porque parece bueno y va al taller.
- **El modelo de imagen de IA 1 no se cambia** (regla 10). IA 1 es la de
  producción; IA 2/3/4 son motores de pruebas del master. Un cambio de modelo
  **no da ningún error**, solo empeora el resultado — por eso hay candado.
- **Qué modelo hay detrás es secreto industrial.** No sale en ninguna pantalla
  que vea un cliente. El master lo ve en Ajustes → Consumo de IA.

---

## 6. Lo que NO se ha auditado

Dicho para que no se dé por revisado lo que no lo está:

- Ficha técnica, presentación y dossier del Estudio de Cocinas.
- El presupuesto que sale del Estudio 3D.
- El comportamiento real en producción: todo se verificó en local con datos
  reales del master, pero sin abrir el ERP y pulsar los botones.
