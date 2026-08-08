# Traspaso de sesión — 07-08/08/2026

Léeme entero antes de tocar nada.

---

## 1. LO PRIMERO, ANTES DE CUALQUIER FUNCIÓN NUEVA

**Que el render siga el boceto SIGUE SIN VERIFICARSE con las imágenes reales del
master.**

Se arregló en la PR #20 (dos causas: el detector de croquis solo miraba PDF, y
el croquis competía contra una cocina inventada por un LLM). Está demostrado
**en el código y con imágenes sintéticas**. Eso NO es lo mismo que ver el render
bien.

Se le pidió varias veces el croquis y el render juntos. Lo que mandó fueron
capturas de pantalla del Estudio 3D y de la conversación. **Hasta que no se
comparen croquis ↔ render ↔ alzado con sus imágenes, no se puede decir que esté
confirmado.** Pídeselo otra vez.

---

## 2. HECHO EN ESTA SESIÓN — no rehacer

Todo en la PR #21 (rama `claude/render-boceto-mismatch-205rv6`), 14 commits,
310 pruebas / 0 skipped.

| Qué | Dónde |
|---|---|
| Dictado por voz: se repetían las palabras | `frontend/src/hooks/useSpeechRecognition.js` |
| Incidencias con CAUSA | `backend/routes/postventa.py` |
| Control de cambios de proyecto | `backend/services/cambios_proyecto.py` |
| Bloqueo de fabricación (409) | `backend/routes/orders.py` |
| Comparador presupuesto ↔ fabricación | `backend/services/comparador_fabricacion.py` |
| Almacén (motor de cálculo) | `backend/services/almacen.py` |
| Expediente de validación | `backend/services/validacion_fabricacion.py` |
| Expediente único + filtro de importes | `backend/services/expediente.py` |
| Boceto de alzado a mano alzada | flag `boceto` en `estudio_cocinas.py` |
| Motor de perspectiva 3D | `backend/services/perspectiva.py` |

Cada uno tiene su `test_calculo_*.py`. **No los borres para poner el CI en
verde**: son el candado.

### El dictado, por si vuelve

Se repetía («cuandocuandocuando») porque se sumaban trozos dando por hecho que
cada resultado final del navegador llega **una sola vez**. Chrome de Android los
reentrega. Ahora el cálculo es **idempotente**: se rehace el texto entero en
cada evento. Estaba copiado en CUATRO pantallas; ahora hay un solo hook.

---

## 3. A MEDIO CAMINO

- **Boceto en PERSPECTIVA.** El motor 3D está hecho y probado
  (`perspectiva.py`). **Falta dibujarlo**: el trazo de lápiz encima y elegir el
  punto de vista bueno para una cocina. El master enseñó sus referencias —
  bocetos de dormitorio a lápiz, con profundidad y punto de fuga — y confirmó
  que quiere eso, no el alzado plano.
- **Botón del boceto de alzado.** El backend ya acepta el flag; falta el
  interruptor al lado de «Alzado + planta + medidas».
- **Almacén.** Falta la parte de datos: campos de existencias en materiales,
  reservas por proyecto y enganche con el despiece.
- **Pantalla del expediente.** Los datos están; falta el React para tablet de 8".

---

## 4. DECISIONES DEL MASTER, SIN RESPUESTA

- Icono de la app instalada (se dejó sin icono: producto marca blanca).
- PDF de croquis multipágina: `max_pages=1` pierde las demás hojas **en
  silencio**.
- Respaldo silencioso de modelo en `llm_vision.py` (>90 s baja al modelo
  «creativo»).
- **Respaldo silencioso de IA 2**: si falta `MANUS_API_KEY`, `_render_dispatch`
  cae a Gemini —o sea IA 1— **sin avisar**. En pantalla no se distingue. Es la
  «opción 1» que NO pidió.
- Vercel está conectado al repo **desde fuera** (app de GitHub), con
  `rootDirectory: null` y publicando una URL pública en cada push.
- `KitchenDesigner3D.jsx:1225` dice «Usará Motor IA 2» cuando el motor efectivo
  es `gemini`, **que es IA 1**. Se contradice con su propia línea 1230.
- Si el bloqueo de fabricación resulta agresivo, se ablanda en una línea.
- El temblor del trazo del boceto se ajusta con un número.

---

## 5. IDEAS QUE SÍ MERECEN CONSTRUIRSE

El master está pasando propuestas de ChatGPT. Buena parte ya está hecha —
conviene cribarlas antes de ponerse. Lo que salió **nuevo y bueno**:

1. **Medición en obra con tres niveles**: introducida / tomada / confirmada.
   Encaja exactamente con la regla de oro y no existe.
2. **Comparación entre mediciones**: «3.245 vs 3.238 → diferencia de 7 mm», y
   **no decidir cuál es correcta**, solo obligar a revisar.
3. **Medidas críticas**: marcar cuáles bloquean. Engancha con
   `validacion_fabricacion.py`.
4. **Origen de fabricación** (casco / tablero / banda / comprado). Es real: en
   esta casa se fabrica desde casco y a veces desde banda, y cada origen sigue
   una ruta distinta. Un flujo único «despiece → corte → canteado» sería falso.
5. **Sustituciones registradas**: nunca sustituir un componente o un material
   en silencio.
6. **Recepción parcial** de pedidos (llegan 60 de 100).
7. **Coste por origen del error** — es el pago del campo `causa` de las
   incidencias, ya construido.

---

## 6. LA LECCIÓN QUE SE REPITIÓ CUATRO VECES

Cuatro fallos distintos de esta sesión tenían **la misma forma**: *avisar por lo
bajo y seguir*.

- El respaldo de IA 2 cae a Gemini y no lo dice.
- `cambiar()` en postventa no miraba el resultado de la petición.
- La normalización de imagen fallaba, dejaba un aviso en el log y llamaba a
  Gemini igualmente → el master veía un error de Google sin sentido.
- El PDF de croquis pierde páginas sin avisar.

Un fallo que se registra pero no detiene nada **reaparece disfrazado de otra
cosa mucho más lejos**, y ahí ya no se puede diagnosticar. Si te encuentras
escribiendo `logger.warning(...)` y a continuación siguiendo como si nada,
párate.

Y la otra, que va por tres: **cuando algo está copiado, no basta con arreglar
donde se ha visto el fallo**. Barre el repo entero ANTES de decir cuántos son.
Pasó con el texto blanco, con la cabecera del proveedor y con el dictado — en
este último se dijo «dos sitios» y eran cuatro.
