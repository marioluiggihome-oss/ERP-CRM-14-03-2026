#!/usr/bin/env python3
# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""REGENERA EL CLON DEL ESTUDIO 3D DESDE EL ORIGINAL.

`Estudio3DLab.jsx` es una copia de `AIRenderStudio.jsx` con UNA cosa más: el
botón IA PREMIUM (CLAUDE.md, regla 33). Existe para comparar MOTORES con todo
lo demás igual.

EL PROBLEMA QUE RESUELVE ESTA HERRAMIENTA. Cada vez que alguien mejora el
original —y el 10/09 pasó al día siguiente de crear el clon—, los dos ficheros
se separan y el clon deja de medir el motor: pasa a medir también las
diferencias que se hayan quedado por el camino. Copiar los cambios a mano es
garantizar que un día se copien a medias.

Aquí se REGENERA: se parte del original y se le vuelven a aplicar las DOS
únicas diferencias que el clon puede tener. Si el original cambia de una forma
que rompa esos anclajes, esto FALLA EN VOZ ALTA en vez de dejar un clon a
medias — que es lo que hay que hacer cuando ya no se puede garantizar que los
dos sean comparables.

    python3 herramientas/sincronizar_clon_estudio3d.py            # regenera
    python3 herramientas/sincronizar_clon_estudio3d.py --verificar # solo mira

Lo vigila `test_pantalla_clon_estudio3d.py`, que mide la distancia entre los
dos y exige que el clon conserve las piezas que deciden el render.
"""
import argparse
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL = os.path.join(RAIZ, "frontend", "src", "components", "AIRenderStudio.jsx")
CLON = os.path.join(RAIZ, "frontend", "src", "components", "Estudio3DLab.jsx")

CABECERA = '''

/**
 * ESTUDIO 3D — LABORATORIO. El clon donde se prueban motores nuevos.
 *
 * ESTE FICHERO SE GENERA. No se edita a mano:
 *     python3 herramientas/sincronizar_clon_estudio3d.py
 * Sale de `AIRenderStudio.jsx` con UNA cosa más, el botón IA PREMIUM. Tocarlo
 * aquí es separarlo del original, y entonces comparar los dos renders deja de
 * medir el MOTOR y pasa a medir lo que alguien haya metido por el camino.
 *
 * POR QUÉ ES UNA COPIA Y NO UNA BANDERA DENTRO DE LA PANTALLA BUENA:
 * el Estudio 3D de producción está CONGELADO desde el 04/09/2026 («eso no se
 * toca ya, para nada»). Meterle un `if modoLab` por dentro sería tocarlo en
 * cada prueba que se quiera hacer, que es justo lo que la congelación impide.
 *
 * LO ÚNICO QUE CAMBIA RESPECTO AL ORIGINAL:
 *   · el botón IA PREMIUM (motor `chatgpt`), que aquí existe y allí no;
 *   · el nombre del componente.
 * Todo lo demás es idéntico A PROPÓSITO.
 */'''

# Las DOS diferencias, con su ancla. Si un ancla ya no aparece exactamente una
# vez, la regeneración se para: mejor sin clon que con un clon que miente.
CAMBIOS = [
    (
        "el botón IA PREMIUM en la botonera",
        "                        ['ia7', 'IA7', 'Configuración mejorada de prueba'],\n",
        "                        ['ia7', 'IA7', 'Configuración mejorada de prueba'],\n"
        "                        ['premium', 'IA PREMIUM', 'Configuración premium en pruebas'],\n",
    ),
    (
        "la traducción de 'premium' a su motor",
        "    if (motor === 'ia7') return 'julio11_plus';\n",
        "    if (motor === 'ia7') return 'julio11_plus';\n"
        "    // IA PREMIUM — SOLO EXISTE EN ESTE CLON. El Estudio 3D de producción no\n"
        "    // ofrece este botón ni sabe traducirlo, y el servidor solo se lo acepta a\n"
        "    // quien tenga la casilla `canUseIAPremium` (regla 33). Es el motor más\n"
        "    // caro: 7 créditos por render contra 1.\n"
        "    if (motor === 'premium') return 'chatgpt';\n",
    ),
]


def generar():
    with open(ORIGINAL, encoding="utf-8") as f:
        src = f.read()

    if "AIRenderStudio" not in src:
        raise SystemExit("✗ el original ya no se llama AIRenderStudio: revisa a mano")
    src = src.replace("AIRenderStudio", "Estudio3DLab")

    i = src.index("*/") + 2
    src = src[:i] + CABECERA + src[i:]

    for que, viejo, nuevo in CAMBIOS:
        n = src.count(viejo)
        if n != 1:
            raise SystemExit(
                f"✗ no se puede regenerar el clon: el ancla de «{que}» aparece {n} "
                f"veces en el original y tiene que aparecer 1.\n"
                f"  El original ha cambiado de forma. Mira qué ha pasado y ajusta "
                f"esta herramienta A PROPÓSITO — no dejes el clon a medias.")
        src = src.replace(viejo, nuevo)
    return src


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verificar", action="store_true",
                    help="no escribe: dice si el clon está al día")
    args = ap.parse_args()

    nuevo = generar()
    actual = ""
    if os.path.exists(CLON):
        with open(CLON, encoding="utf-8") as f:
            actual = f.read()

    if actual == nuevo:
        print("✓ el clon del Estudio 3D está al día con el original")
        return 0

    if args.verificar:
        import difflib
        d = list(difflib.unified_diff(actual.splitlines(), nuevo.splitlines(),
                                      "Estudio3DLab.jsx (ahora)",
                                      "Estudio3DLab.jsx (regenerado)", lineterm="", n=0))
        cambios = sum(1 for l in d if l[:1] in "+-" and not l.startswith(("+++", "---")))
        print(f"✗ el clon se ha separado del original en {cambios} líneas.")
        print("  Ejecuta: python3 herramientas/sincronizar_clon_estudio3d.py")
        return 1

    with open(CLON, "w", encoding="utf-8") as f:
        f.write(nuevo)
    print(f"✓ clon regenerado desde el original ({len(nuevo.splitlines())} líneas)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
