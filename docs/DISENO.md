# El diseño del ERP

Esto es lo que no existía. El 25/08/2026 el master preguntó si había leído «lo
del diseño estético del ERP» y la respuesta honesta fue que no había nada que
leer: el aspecto vivía repartido en 92 componentes y 78.000 líneas de clases
escritas a mano, con los tokens del framework sin usar.

Este documento es corto a propósito. Una guía de diseño que nadie lee no sirve
de nada, y la que se contradice con el código es peor que ninguna.

---

## 1. El color se genera, no se escribe

`frontend/paleta.generada.js` sale de `herramientas/paleta_erp.py`. Son los
colores de Tailwind con la **misma luminosidad y menos saturación**.

```
python3 herramientas/paleta_erp.py --escribir   # regenerar
python3 herramientas/paleta_erp.py --contraste  # comprobar que se lee
```

**La luminosidad no se toca.** Los contrastes de las 92 pantallas dependen de
ella, no de la saturación: bajando solo la saturación, un `bg-accion-600` sigue
siendo igual de oscuro y el blanco encima se sigue leyendo. Tocar la
luminosidad obligaría a revisar las 92 pantallas una a una.

Regla del generador: **apagar un color no puede tumbar un contraste que antes
aprobaba.** Si al apagarse cae por debajo de 4,5, se oscurece lo justo para
volver. Lo que ya venía suspenso del framework se deja como está — arreglar eso
es otra decisión y se toma aparte.

Los colores escritos a pelo en `style={{...}}`, degradados e iconos no pasan por
el framework y se apagan con `herramientas/apagar_hex_sueltos.py`.

---

## 2. El color dice POR QUÉ, no qué tono es

Se escribe `bg-ok-600`, no `bg-emerald-600`. Así la pantalla explica qué
significa ese verde, y el día que el verde no convenza se cambia en un sitio.

| Token | Para qué | Ejemplos de este ERP |
|---|---|---|
| `accion` | Lo que hay que pulsar | Guardar, Añadir mueble, Generar render |
| `ok` | Terminado y correcto | Servido, cobrado, comisión consolidada |
| `aviso` | Pendiente o incompleto | Cota sin dato («?»), pedido sin cobrar, faltan módulos |
| `error` | Roto o destructivo | Borrar, pedido anulado, hueco sin tarifa |
| `master` | Solo lo ve el master | Tarifa MV, rentabilidad, motores de prueba |
| `dato` | Importes, tablas y texto | PVP, base imponible, códigos, medidas |

### El dinero no lleva color de estado

Un importe no es ni bueno ni malo. Pintarlo de ámbar lo convierte en un aviso
permanente, y entonces deja de destacar lo que sí es un aviso. Los importes van
en `dato` y destacan por **tamaño y peso**, como en cualquier pantalla de banco.

Eso libera el ámbar para lo que significa en todas partes: atención.

### Por qué hacía falta decir todo esto

Se midió el uso real del color antes de tocar nada. Las palabras de dinero
aparecían cerca del **46–58% de TODOS los colores** — es un ERP, el dinero está
en todas partes. El único color que significaba algo era el rojo, en el 42% de
los casos junto a «error», «borrar» o «anular». Los demás decoraban.

---

## 3. La letra tiene tres pesos y ya

| Clase | Pesa | Para |
|---|---|---|
| `font-normal` | 400 | Todo el texto corriente |
| `font-bold` | 600 | Lo que destaca dentro de un bloque |
| `font-black` | 700 | El título o la cifra que manda en la pantalla |

Había 2.132 `font-bold` y 1.929 `font-black` contra 29 `font-semibold`: casi
todo en negrita o negrísima. **Si todo grita, nada destaca** — y por eso las
pantallas densas costaban de leer aunque el dato estuviera ahí.

Los pesos son los que Inter descarga de verdad. Antes se pedía 700 sin estar en
el `@import` y el navegador lo falsificaba engordando el 600, de donde salía
parte del aspecto tosco.

---

## 4. Cómo se cambia el aspecto sin romper nada

1. Se toca **la paleta o el config**, nunca los 92 componentes.
2. Se compila (`CI=true npx craco build`) — los avisos son errores.
3. Se **mira con los ojos**: `npx playwright test e2e/capturas-diseno.spec.js`
   saca capturas para comparar antes y después.
4. `pytest backend/tests/test_pantalla_paleta_apagada.py`.

**Ningún otro candado mira cómo se VE.** Todos los demás vigilan lo que se
calcula y lo que la pantalla dice, así que un cambio estético —o su vuelta
atrás— entra entero con el CI en verde. Por eso el paso 3 no se salta.
