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

**Las tres pistas, por orden de solidez:**

1. **`backend/services/luiggi_ai/render_3d.py:1253` fuerza
   `model_override="gemini-2.5-flash-image"`.** Si esa es la ruta de IA 1,
   entonces la lista de modelos de `llm_vision.py` que la otra IA reordenó
   (commit `b79a21a2`) **nunca afectó al render**: el override manda sobre la
   lista. Su arreglo sería correcto pero inocuo, y la causa estaría en otro
   sitio. **Empieza por aquí:** averigua por qué ruta va IA 1 y si el override
   anula la lista.
2. **¿Llega el boceto al modelo?** Sigue la cadena completa
   `generate_render_composed` → `_render_dispatch` → llamada final, y comprueba
   que las imágenes del croquis viajan de verdad y no se pierden ni las recorta
   el tope de 7 (`MAX_IMAGENES_COMPUESTAS`).
3. **El prompt de render se reescribió el 04/08** en cinco commits
   (`6bef32f0`, `f058dce9`, `f5c9a370`, `3bd410ca`, `b31fbbf2`). El de fondo
   cambió el bloque de escala y lo movió a `services/criterios_cocina.py`.
   Compara el prompt de antes del 4/8 con el de ahora, misma cocina y mismo
   motor. Es reversible en un minuto y es la única forma de saber si mejoró o
   empeoró la fidelidad al boceto.

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
