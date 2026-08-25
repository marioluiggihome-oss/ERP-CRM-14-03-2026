#!/usr/bin/env python3
# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
VALIDA LAS MATRICES DE PUERTAS, VITRINAS Y REJILLAS DE LA TARIFA MV.

Estas tablas están transcritas A OJO de un PDF escaneado y torcido: unas 2.300
cifras entre las 21 tarifas. Fiarse de la lectura de nadie no es una opción, así
que cada tabla pasa por dos comprobaciones. No demuestran que un número sea
correcto, pero un renglón corrido rompe casi siempre alguna:

  1. DE IZQUIERDA A DERECHA — una puerta más ancha no puede costar menos.
  2. DE ARRIBA ABAJO — una puerta más alta no puede costar menos.

HUBO UNA TERCERA Y ESTABA MAL, que es justo por lo que se escribe esto y no se
comprueba de memoria: «la misma casilla no puede bajar al subir de tarifa».
Suena razonable y es falso. Lo dice el propio `_meta` del fichero: «cada tarifa
es una LISTA DE PRECIOS INDEPENDIENTE en puntos, NO se calcula con
multiplicador». T1..T21 son modelos y acabados distintos, no escalones de
precio: en PUERTAS 14xP30, T2 vale 11 y T3 vale 4. La regla soltaba 741 avisos
falsos y habría hecho «arreglar» datos que estaban bien. Una comprobación que
salta 741 veces no protege nada: se deja de mirar.

Lo que salta NO se corrige: se lista. Puede ser un error de lectura o puede ser
que la tarifa sea así de verdad (en T1 la vitrina de 147xPV60 vale 118 cuando la
de al lado vale 89 — comprobado con zoom, la tarifa dice 118). Un dato del
proveedor no se «arregla» para que la curva quede bonita.

    python3 herramientas/verificar_matrices_puertas.py
"""
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARIFA = os.path.join(RAIZ, "backend", "data", "mv_tarifas_oficiales.json")

MATRICES = ("PUERTAS", "VITRINA", "VITRINA_INGLESA", "REJILLA_CONFESIONARIO")

# Rarezas COMPROBADAS contra el escaneo a 500-600 dpi: la tarifa impresa dice
# eso, no es un error de lectura. Se listan aparte para que los avisos vivos
# sigan siendo pocos — un informe que siempre saca las mismas dos líneas deja de
# mirarse, y entonces la tercera pasa desapercibida.
#
#   T1/VITRINA 147xPV60 = 118 detrás de un 89 (el resto de la fila va 77..97).
#   T2/PUERTAS col P50  = 67 en el alto 127 y 60 en el 147, o sea más alta y
#                         más barata.
#
# Ninguna se toca. Son datos del proveedor; si están mal, se le pregunta a él.
VERIFICADAS = {
    ("T1", "VITRINA", "147", "PV60"),
    ("T2", "PUERTAS", "147", "P50"),
}

def _orden_tarifas(datos):
    """T1, T2, … T21 en orden numérico, no alfabético (T10 no va tras T1)."""
    return sorted((t for t in datos if t.startswith("T")),
                  key=lambda x: int(x[1:]))


def revisa(datos):
    avisos = []
    for tar in _orden_tarifas(datos):
        for fam in MATRICES:
            f = datos[tar].get(fam)
            if not f or f.get("type") != "matrix":
                continue
            cols = f.get("cols", [])
            filas = f.get("rows", {})

            # 1) de izquierda a derecha
            for h, row in filas.items():
                prev_c, prev_v = None, None
                for c in cols:
                    v = row.get(c)
                    if v is None:
                        continue
                    if prev_v is not None and v < prev_v and (tar, fam, h, c) not in VERIFICADAS:
                        avisos.append(f"{tar}/{fam} fila {h}: {prev_c}={prev_v} "
                                      f"pero {c}={v} (más ancha y más barata)")
                    prev_c, prev_v = c, v

            # 2) de arriba abajo
            alturas = sorted(filas, key=lambda x: float(x))
            for c in cols:
                prev_h, prev_v = None, None
                for h in alturas:
                    v = filas[h].get(c)
                    if v is None:
                        continue
                    if prev_v is not None and v < prev_v and (tar, fam, h, c) not in VERIFICADAS:
                        avisos.append(f"{tar}/{fam} col {c}: alto {prev_h}={prev_v} "
                                      f"pero alto {h}={v} (más alta y más barata)")
                    prev_h, prev_v = h, v

    return avisos


def main():
    with open(TARIFA, "r", encoding="utf-8") as fh:
        datos = json.load(fh)["tariffs"]

    cargadas, casillas = [], 0
    for tar in _orden_tarifas(datos):
        hay = [f for f in MATRICES
               if datos[tar].get(f, {}).get("type") == "matrix"
               and datos[tar][f].get("rows")]
        if hay:
            cargadas.append(tar)
            casillas += sum(len(r) for f in hay
                            for r in datos[tar][f]["rows"].values())

    faltan = [t for t in _orden_tarifas(datos) if t not in cargadas]
    print(f"tarifas con matrices cargadas: {len(cargadas)}/{len(datos)} "
          f"({casillas} casillas)")
    if faltan:
        print(f"  SIN CARGAR todavía: {', '.join(faltan)}")

    print(f"rarezas ya comprobadas contra el escaneo: {len(VERIFICADAS)} "
          "(la tarifa dice eso; no se tocan)")

    avisos = revisa(datos)
    if not avisos:
        print("\n✓ las tres comprobaciones pasan en todo lo cargado")
        return 0
    print(f"\n⚠ {len(avisos)} cosa(s) que mirar (NO se corrigen solas):")
    for a in avisos:
        print("   ·", a)
    return 0        # avisar no es fallar: puede que la tarifa sea así


if __name__ == "__main__":
    sys.exit(main())
