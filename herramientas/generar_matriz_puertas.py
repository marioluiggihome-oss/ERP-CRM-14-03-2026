#!/usr/bin/env python3
# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
GENERA LA MATRIZ DE PUERTAS DEL FRONTEND A PARTIR DE LA TARIFA OFICIAL.

La pantalla necesita tarifar puertas sin ir al servidor en cada tecla, así que
lleva la matriz dentro. Hasta el 25/08/2026 esa matriz estaba ESCRITA A MANO, y
pasó lo que pasa siempre con las copias a mano:

  · Solo cubría T1..T5. Para T6..T21 había un `|| PUERTAS_MATRIZ_MV.T1`, o sea
    que 16 tarifas cobraban precios de T1 SIN DECIR NADA.
  · En T1 las cuatro filas de abajo (70, 90, 127, 147) coincidían con la tarifa
    en las 26 casillas. Las cuatro de arriba (14, 28, 40, 56) no coincidía
    ninguna, y siempre por encima: una puerta de 14xP60 son 4 puntos y se
    cobraban 10.
  · La columna P25, que en la tarifa solo existe para los altos 70 y 90, estaba
    rellenada también en las de arriba.

Ahora se GENERA. La tarifa manda, la pantalla la copia, y hay un candado
(`test_calculo_puertas_desde_la_tarifa.py`) que vuelve a generarla y la compara
con lo que hay en el JSX: si alguien edita la matriz a mano, el CI se pone rojo.

    python3 herramientas/generar_matriz_puertas.py            # enseña el bloque
    python3 herramientas/generar_matriz_puertas.py --escribir # lo mete en el JSX
"""
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARIFA = os.path.join(RAIZ, "backend", "data", "mv_tarifas_oficiales.json")
JSX = os.path.join(RAIZ, "frontend", "src", "components", "RentabilidadMV.jsx")

# (constante del JSX, familia de la tarifa)
BLOQUES = (
    ("PUERTAS_MATRIZ_MV", "PUERTAS"),
    ("VITRINA_MATRIZ_MV", "VITRINA"),
)
FIN = "\n};"


def bloque_js(constante, familia):
    with open(TARIFA, "r", encoding="utf-8") as f:
        tarifas = json.load(f)["tariffs"]

    orden = sorted((t for t in tarifas if re.match(r"^T\d+$", t)),
                   key=lambda x: int(x[1:]))
    lineas = [f"export const {constante} = {{"]
    for t in orden:
        fam = tarifas[t].get(familia) or {}
        filas = fam.get("rows") or {}
        if not filas:
            continue
        lineas.append(f"  {t}: {{")
        for alto in sorted(filas, key=float):
            cel = ", ".join(f"'{c}': {v}" for c, v in filas[alto].items()
                            if v is not None)
            lineas.append(f"    '{alto}': {{ {cel} }},")
        lineas.append("  },")
    lineas.append("};")
    return "\n".join(lineas)


def main():
    if "--escribir" not in sys.argv:
        for constante, familia in BLOQUES:
            print(bloque_js(constante, familia))
        return 0

    with open(JSX, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    for constante, familia in BLOQUES:
        nuevo = bloque_js(constante, familia)
        marca = f"export const {constante} = {{"
        i = cuerpo.index(marca)
        j = cuerpo.index(FIN, i) + len(FIN)
        cuerpo = cuerpo[:i] + nuevo + cuerpo[j:]
        print(f"✓ {constante} regenerada desde la tarifa ({nuevo.count(chr(10))} líneas)")
    with open(JSX, "w", encoding="utf-8") as f:
        f.write(cuerpo)
    return 0


if __name__ == "__main__":
    sys.exit(main())
