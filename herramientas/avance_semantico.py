#!/usr/bin/env python3
# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
CUÁNTO COLOR DEL ERP YA DICE POR QUÉ, Y CUÁNTO SIGUE DECORANDO.

El color del ERP ya no grita (`paleta_erp.py`), pero apagarlo no lo hace
informar. Se escribe `bg-emerald-600` y la pantalla no dice si ese verde
significa «terminado», «correcto» o simplemente que quedaba bonito ahí.

Los alias semánticos de `tailwind.config.js` (`accion`, `ok`, `aviso`, `error`,
`master`, `dato`) le ponen nombre al uso. Migrar los 92 componentes es un
trabajo largo y a mano —hay que saber QUÉ significa cada color en cada sitio, y
eso no lo puede adivinar un script sin equivocarse—, así que esto no migra nada:
solo mide, para que el avance se vea y no se haga a ciegas.

    python3 herramientas/avance_semantico.py           # el resumen
    python3 herramientas/avance_semantico.py --detalle # pantalla por pantalla
"""
import collections
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMP = os.path.join(RAIZ, "frontend", "src", "components")

SEMANTICOS = ("accion", "ok", "aviso", "error", "master", "dato")
# Los que se usan como acento y deberían acabar teniendo un porqué.
DECORATIVOS = ("indigo", "emerald", "amber", "orange", "purple", "red", "blue",
               "violet", "teal", "rose", "cyan", "sky", "green", "fuchsia",
               "pink", "lime", "yellow")

RE_SEM = re.compile(r"\b(?:bg|text|border|from|to|ring|divide|outline)-(%s)-\d{2,3}"
                    % "|".join(SEMANTICOS))
RE_DEC = re.compile(r"\b(?:bg|text|border|from|to|ring|divide|outline)-(%s)-\d{2,3}"
                    % "|".join(DECORATIVOS))


def main():
    por_fichero = {}
    for base, _, nombres in os.walk(COMP):
        if os.path.join("components", "ui") in base:
            continue                     # shadcn: código de terceros
        for n in sorted(nombres):
            if not n.endswith(".jsx"):
                continue
            with open(os.path.join(base, n), "r", encoding="utf-8") as f:
                cuerpo = f.read()
            sem = len(RE_SEM.findall(cuerpo))
            dec = len(RE_DEC.findall(cuerpo))
            if sem or dec:
                por_fichero[n] = (sem, dec)

    sem = sum(v[0] for v in por_fichero.values())
    dec = sum(v[1] for v in por_fichero.values())
    tot = sem + dec
    hechos = [n for n, (s, d) in por_fichero.items() if s and not d]

    print(f"clases de color de acento: {tot}")
    print(f"  con significado  : {sem:5}  ({sem * 100 // tot if tot else 0}%)")
    print(f"  aún decorativas  : {dec:5}  ({dec * 100 // tot if tot else 0}%)")
    print(f"pantallas del todo migradas: {len(hechos)} de {len(por_fichero)}")

    if "--detalle" in sys.argv:
        print("\nlas que más color decorativo tienen (por dónde empezar):")
        for n, (s, d) in sorted(por_fichero.items(), key=lambda x: -x[1][1])[:15]:
            print(f"  {n:42} decorativas {d:4}  semánticas {s:3}")
    else:
        peor = sorted(por_fichero.items(), key=lambda x: -x[1][1])[:3]
        print("\npor dónde seguir: " + ", ".join(f"{n} ({d})" for n, (_, d) in peor))
    return 0


if __name__ == "__main__":
    sys.exit(main())
