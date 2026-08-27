#!/usr/bin/env python3
# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
APAGA TAMBIÉN LOS COLORES ESCRITOS A MANO EN HEXADECIMAL.

Redefinir la paleta de Tailwind arregla todo lo que va por clases
(`bg-indigo-600`), que es la mayoría. Pero en los componentes hay además 436
colores escritos a pelo —`style={{ background: '#10b981' }}`, degradados,
iconos, SVG— que NO pasan por Tailwind y se quedaban chillando al lado de los ya
apagados. Peor que antes: antes al menos gritaban todos a la vez.

QUÉ HACE. Recorre los `.jsx` y sustituye cada hexadecimal por su versión
apagada, con exactamente el mismo criterio que `paleta_erp.py`: misma
luminosidad, menos saturación. Los que ya son un tono de Tailwind se cambian por
el color EXACTO de la paleta nueva, para que un `#10b981` a mano y un
`bg-emerald-500` acaben siendo el mismo color y no dos verdes parecidos.

QUÉ NO TOCA:
  · Los grises y negros puros (saturación casi nula): no gritan.
  · El blanco y el negro.
  · `frontend/src/components/ui/` — es shadcn, código de terceros (CLAUDE.md).

    python3 herramientas/apagar_hex_sueltos.py           # solo enseña
    python3 herramientas/apagar_hex_sueltos.py --escribir
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paleta_erp import FACTOR, apaga, hex_a_oklch, paleta  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(RAIZ, "frontend", "src")
EXCLUIDOS = (os.path.join("components", "ui") + os.sep,)

HEX = re.compile(r"#[0-9a-fA-F]{6}\b")
# Por debajo de esta saturación un color es un gris: no grita y no se toca.
GRIS = 0.02
# Factor para un color suelto que no está en la paleta de Tailwind. Se usa el de
# los acentos corrientes, no el de los amarillos: no se sabe qué es.
FACTOR_SUELTO = 0.58


def _mapa_tailwind():
    """hex original de Tailwind -> hex ya apagado de la paleta nueva."""
    base, nueva, _ = paleta()
    m = {}
    for fam in base:
        for tono, val in base[fam].items():
            if re.match(r"^\d+$", tono) and tono in nueva[fam]:
                m[val.lower()] = nueva[fam][tono]
    return m


def convierte(hexcol, mapa):
    h = hexcol.lower()
    if h in mapa:
        return mapa[h]
    _, C, _ = hex_a_oklch(h)
    if C < GRIS:
        return None                      # es un gris: se queda
    return apaga(h, FACTOR_SUELTO)


def ficheros():
    for base, _, nombres in os.walk(SRC):
        for n in nombres:
            if not n.endswith((".jsx", ".js", ".css")):
                continue
            ruta = os.path.join(base, n)
            rel = os.path.relpath(ruta, SRC)
            if any(x in rel for x in EXCLUIDOS):
                continue
            yield ruta


def main():
    mapa = _mapa_tailwind()
    escribir = "--escribir" in sys.argv
    tocados = cambios = grises = 0
    for ruta in ficheros():
        with open(ruta, "r", encoding="utf-8") as f:
            cuerpo = f.read()
        n_local = 0

        def rep(m):
            nonlocal n_local, grises
            nuevo = convierte(m.group(0), mapa)
            if nuevo is None:
                grises += 1
                return m.group(0)
            if nuevo.lower() == m.group(0).lower():
                return m.group(0)
            n_local += 1
            return nuevo

        nuevo_cuerpo = HEX.sub(rep, cuerpo)
        if n_local:
            tocados += 1
            cambios += n_local
            if escribir:
                with open(ruta, "w", encoding="utf-8") as f:
                    f.write(nuevo_cuerpo)

    print(f"{'apagados' if escribir else 'se apagarían'}: {cambios} colores "
          f"en {tocados} ficheros")
    print(f"grises respetados (no gritan): {grises}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
