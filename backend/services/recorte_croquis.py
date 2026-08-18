# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""Recorta EL DIBUJO de dentro de la página.

EL PROBLEMA
-----------
El master no sube un croquis suelto: sube el PANTALLAZO DEL MÓVIL de una página
de presupuesto. En esa imagen hay la barra de estado del teléfono, el título
«Presupuesto estimado», el nombre («Cocina lineal»), un recuadro de marca, el
dibujo de la cocina, tres líneas con precios, el total y la barra de navegación
de Android.

El dibujo ocupa **un tercio de la altura**. Todo lo demás es envoltorio.

Eso hace daño dos veces:

· A quien LEE el croquis: el modelo de visión reparte su atención entre el
  dibujo y un montón de texto que no son muebles.
· A quien RENDERIZA: la referencia que recibe tiene la cocina pequeña y en una
  esquina, así que el detalle fino —los altos partidos en dos filas, el nicho
  de la campana, las divisiones de los frentes— sencillamente no se ve.

Se le pueden dar todas las órdenes del mundo; si en la imagen no se ve, no se
ve. Por eso esto NO es otra regla de prompt: es darle la cocina a pantalla
completa.

CÓMO SE DECIDE
--------------
El dibujo es, con diferencia, la MANCHA DE TINTA MÁS GRANDE Y CONEXA de la
página: sus líneas se tocan todas entre sí. El texto, en cambio, cae en
manchas pequeñas y sueltas —una por línea—. Así que:

  1. se pasa a gris y se marca la tinta (lo que no es fondo),
  2. se engorda un poco para que los trazos vecinos se toquen,
  3. se buscan las manchas conexas,
  4. se elige la de mayor área de recuadro,
  5. se recorta con margen.

SI HAY DUDA, NO SE TOCA
-----------------------
Un recorte mal hecho es MUCHO peor que no recortar: se llevaría por delante
media cocina y nadie se enteraría, porque el render seguiría saliendo bonito.
Por eso el recorte solo se aplica cuando queda claramente por debajo de la
página entera y claramente por encima de un trozo suelto. Fuera de esa
horquilla —una foto de cocina, un croquis que ya llena el papel, una imagen
rara— se devuelve la original tal cual.
"""
from __future__ import annotations

import base64
import io
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Ancho al que se analiza. No hace falta más para localizar una mancha, y con
# esto el recorrido de las manchas tarda milisegundos en vez de segundos.
ANCHO_ANALISIS = 420

# Un píxel es TINTA si es más oscuro que esto (0 = negro, 255 = blanco). El
# fondo de la página del master es blanco o gris muy claro (≈245).
UMBRAL_TINTA = 225

# Cuánto se engorda la tinta para que los trazos sueltos de un mismo dibujo se
# toquen. En la imagen de análisis, no en la original.
ENGORDE = 3

# El recorte tiene que quedar DENTRO de esta horquilla respecto al área de la
# página. Por debajo sería quedarse con un trozo suelto (un icono, una línea de
# precio); por encima no merece la pena y además delata que la mancha grande se
# ha comido la página entera.
AREA_MIN = 0.06
AREA_MAX = 0.80

# Margen que se deja alrededor del dibujo, en tanto por uno del lado recortado.
MARGEN = 0.04


def _manchas(tinta, ancho: int, alto: int):
    """Recorre las manchas conexas (4-vecinos) y devuelve sus recuadros.

    Se hace con una pila propia en vez de recursión: una mancha puede ocupar
    media imagen y Python se queda sin pila mucho antes.
    """
    visto = bytearray(ancho * alto)
    cajas = []
    for inicio in range(ancho * alto):
        if not tinta[inicio] or visto[inicio]:
            continue
        visto[inicio] = 1
        pila = [inicio]
        x0 = x1 = inicio % ancho
        y0 = y1 = inicio // ancho
        peso = 0
        while pila:
            p = pila.pop()
            peso += 1
            x, y = p % ancho, p // ancho
            if x < x0:
                x0 = x
            if x > x1:
                x1 = x
            if y < y0:
                y0 = y
            if y > y1:
                y1 = y
            if x > 0 and tinta[p - 1] and not visto[p - 1]:
                visto[p - 1] = 1
                pila.append(p - 1)
            if x < ancho - 1 and tinta[p + 1] and not visto[p + 1]:
                visto[p + 1] = 1
                pila.append(p + 1)
            if y > 0 and tinta[p - ancho] and not visto[p - ancho]:
                visto[p - ancho] = 1
                pila.append(p - ancho)
            if y < alto - 1 and tinta[p + ancho] and not visto[p + ancho]:
                visto[p + ancho] = 1
                pila.append(p + ancho)
        cajas.append((x0, y0, x1, y1, peso))
    return cajas


def recuadro_del_dibujo(imagen) -> Optional[Tuple[int, int, int, int]]:
    """Devuelve (izq, arr, der, aba) del dibujo dentro de la página, o None.

    None significa «no lo tengo claro»: quien llama se queda con la original.
    """
    try:
        from PIL import Image, ImageFilter
    except Exception:
        return None
    try:
        ancho_o, alto_o = imagen.size
        if ancho_o < 200 or alto_o < 200:
            return None
        escala = ANCHO_ANALISIS / float(ancho_o)
        ancho = ANCHO_ANALISIS
        alto = max(1, int(round(alto_o * escala)))
        gris = imagen.convert("L").resize((ancho, alto))
        # MinFilter sobre el gris = engordar lo OSCURO, que es la tinta.
        gris = gris.filter(ImageFilter.MinFilter(ENGORDE if ENGORDE % 2 else ENGORDE + 1))
        # `tobytes()` y no `getdata()`: en modo "L" es un byte por píxel, es lo
        # mismo, y `getdata()` está marcado para desaparecer en Pillow 14.
        tinta = bytearray(1 if v < UMBRAL_TINTA else 0 for v in gris.tobytes())
        if not any(tinta):
            return None

        cajas = _manchas(tinta, ancho, alto)
        if not cajas:
            return None
        # La mayor POR ÁREA DE RECUADRO: el dibujo es lo que más sitio ocupa.
        # (Por peso de tinta ganaría a veces un bloque de texto muy tupido.)
        x0, y0, x1, y1, _peso = max(cajas, key=lambda c: (c[2] - c[0] + 1) * (c[3] - c[1] + 1))

        # Vuelta a las coordenadas de la imagen original, con margen.
        izq, arr = x0 / escala, y0 / escala
        der, aba = (x1 + 1) / escala, (y1 + 1) / escala
        mx, my = (der - izq) * MARGEN, (aba - arr) * MARGEN
        izq, arr = max(0, int(izq - mx)), max(0, int(arr - my))
        der, aba = min(ancho_o, int(der + mx)), min(alto_o, int(aba + my))
        if der - izq < 80 or aba - arr < 80:
            return None

        proporcion = ((der - izq) * (aba - arr)) / float(ancho_o * alto_o)
        if not (AREA_MIN <= proporcion <= AREA_MAX):
            # O es un trozo suelto, o es la página entera: en ambos casos, no
            # se toca. Mejor una referencia pequeña que media cocina cortada.
            return None
        return izq, arr, der, aba
    except Exception as e:
        logger.warning(f"No se pudo localizar el dibujo dentro de la página: {e}")
        return None


def recortar_dibujo_base64(raw_b64: str, mime: str = "image/png") -> Tuple[str, bool]:
    """Recorta el dibujo de un base64 y lo devuelve como PNG base64.

    Devuelve (base64, recortado). Si no hay nada claro que recortar, devuelve
    el original y False — nunca lanza.
    """
    if not raw_b64:
        return raw_b64, False
    try:
        from PIL import Image
        crudo = raw_b64.split(",", 1)[-1] if "," in raw_b64 else raw_b64
        imagen = Image.open(io.BytesIO(base64.b64decode(crudo)))
        imagen.load()
        caja = recuadro_del_dibujo(imagen)
        if not caja:
            return raw_b64, False
        recorte = imagen.convert("RGB").crop(caja)
        buf = io.BytesIO()
        recorte.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("ascii"), True
    except Exception as e:
        logger.warning(f"No se pudo recortar el dibujo: {e}")
        return raw_b64, False
