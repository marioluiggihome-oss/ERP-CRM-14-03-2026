#!/usr/bin/env python3
# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LA PALETA DEL ERP: LOS MISMOS COLORES, SIN GRITAR.

El master, 25/08/2026: «cambia a diseño con colores que no griten, que queden
bien y que quede todo bastante integrado y moderno».

EL PROBLEMA. El aspecto del ERP no sale de ningún sitio central: son 92
componentes y 78.000 líneas repitiendo clases de Tailwind a mano
(`bg-indigo-600`, `text-amber-700`…). Los tokens de shadcn que existirían para
eso están en su valor de fábrica, sin usar. Repintar a mano es tocar 92 ficheros
y romper cosas.

LA PALANCA. Tailwind resuelve `bg-indigo-600` contra SU tabla de colores, y esa
tabla se puede redefinir en `tailwind.config.js`. Cambiando ahí los valores,
cada clase que ya está escrita renderiza el color nuevo. Un fichero, todo el
ERP, y sin tocar una sola pantalla.

CÓMO SE APAGAN SIN ROMPER NADA. Cada color se pasa a OKLCH —un espacio donde la
L es luminosidad percibida de verdad— y se le baja SOLO la saturación (la C).
La L se deja EXACTA.

Eso último no es un detalle, es lo que hace segura la operación: los contrastes
del ERP (texto blanco sobre `-600`, texto `-900` sobre fondo `-50`…) dependen de
la luminosidad, no de la saturación. Tocando solo la C, un `bg-indigo-600` sigue
siendo igual de oscuro que antes y el blanco encima se sigue leyendo igual. Si
se bajara la L, habría que revisar los 92 componentes uno a uno.

CUÁNTO. Los acentos bajan más que los grises, y los amarillos y naranjas más que
nadie porque son los que más chillan a igualdad de saturación.

    python3 herramientas/paleta_erp.py             # enseña la tabla
    python3 herramientas/paleta_erp.py --escribir  # la mete en tailwind.config.js
    python3 herramientas/paleta_erp.py --contraste # comprueba que se sigue leyendo
"""
import json
import math
import os
import re
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONT = os.path.join(RAIZ, "frontend")
CONFIG = os.path.join(FRONT, "tailwind.config.js")
DESTINO = os.path.join(FRONT, "paleta.generada.js")

# Cuánta saturación se queda cada familia (1.0 = igual que Tailwind).
FACTOR = {
    # Amarillos y naranjas: los que más chillan. Se quedan en la mitad justa.
    "amber": 0.48, "yellow": 0.46, "orange": 0.50, "lime": 0.48,
    # Acentos principales del ERP.
    "indigo": 0.58, "violet": 0.58, "purple": 0.56, "fuchsia": 0.52,
    "blue": 0.58, "sky": 0.56, "cyan": 0.54,
    "emerald": 0.56, "green": 0.54, "teal": 0.56,
    # El rojo baja menos: es el único color que TIENE que dar un respingo.
    "red": 0.70, "rose": 0.60, "pink": 0.56,
    # Grises: casi no llevan saturación, así que apenas se tocan. Un pelín, para
    # que el fondo no tire a azulado al lado de los acentos ya apagados.
    "slate": 0.75, "gray": 0.80, "zinc": 0.85, "neutral": 1.0, "stone": 0.85,
}


# ── sRGB <-> OKLCH ───────────────────────────────────────────────────────────
def _a_lineal(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _a_srgb(c):
    return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055


def hex_a_oklch(h):
    h = h.lstrip("#")
    r, g, b = (_a_lineal(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4))
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s_ = (v ** (1 / 3) if v > 0 else -((-v) ** (1 / 3)) for v in (l, m, s))
    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    A = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    B = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    return L, math.hypot(A, B), math.atan2(B, A)


def oklch_a_hex(L, C, H):
    A, B = C * math.cos(H), C * math.sin(H)
    l_ = L + 0.3963377774 * A + 0.2158037573 * B
    m_ = L - 0.1055613458 * A - 0.0638541728 * B
    s_ = L - 0.0894841775 * A - 1.2914855480 * B
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    b = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    out = []
    for v in (r, g, b):
        v = _a_srgb(max(0.0, min(1.0, v)))
        out.append(max(0, min(255, round(v * 255))))
    return "#{:02x}{:02x}{:02x}".format(*out)


def apaga(hexcol, factor):
    """Misma luminosidad, menos saturación. El truco entero está aquí."""
    L, C, H = hex_a_oklch(hexcol)
    return oklch_a_hex(L, C * factor, H)


# ── Contraste WCAG, para poder afirmar que se sigue leyendo ─────────────────
def _luminancia(h):
    h = h.lstrip("#")
    r, g, b = (_a_lineal(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(h1, h2):
    a, b = sorted((_luminancia(h1), _luminancia(h2)), reverse=True)
    return (a + 0.05) / (b + 0.05)


# ── Paleta ───────────────────────────────────────────────────────────────────
def tailwind_por_defecto():
    guion = ("const c=require('tailwindcss/colors');"
             "const f=%s;const o={};"
             "for(const k of f) if(c[k]&&typeof c[k]==='object') o[k]=c[k];"
             "console.log(JSON.stringify(o));" % json.dumps(sorted(FACTOR)))
    r = subprocess.run(["node", "-e", guion], capture_output=True, text=True,
                       cwd=FRONT, timeout=120)
    if r.returncode != 0:
        raise SystemExit(f"no se pudo leer la paleta de Tailwind: {r.stderr}")
    return json.loads(r.stdout)


# Pares que el ERP usa de verdad y que hay que vigilar. Texto blanco sobre el
# botón, y texto oscuro sobre la pastilla clara.
PARES = (("600", None), ("700", None), ("100", "900"), ("50", "900"))
AA = 4.5


def _rescata(hex_nuevo, hex_texto, minimo=AA):
    """Oscurece un color lo justo para volver a pasar el contraste.

    Regla que se impone este generador: **apagar los colores no puede tumbar un
    contraste que antes aprobaba**. Bajar la saturación cambia poco la
    luminancia, pero lo suficiente para que un par que iba justo (4,7) se caiga
    por debajo de 4,5. Cuando pasa, se baja la L —y solo entonces— hasta
    recuperarlo. Es la única vez que este módulo toca la luminosidad, y se hace
    a propósito y medido, no a ojo.
    """
    L, C, H = hex_a_oklch(hex_nuevo)
    for _ in range(60):
        if contraste(oklch_a_hex(L, C, H), hex_texto) >= minimo:
            break
        L -= 0.005
        if L <= 0:
            break
    return oklch_a_hex(max(L, 0.0), C, H)


def paleta():
    base = tailwind_por_defecto()
    nueva, rescatados = {}, []
    for fam, tonos in sorted(base.items()):
        f = FACTOR[fam]
        nueva[fam] = {t: apaga(v, f) for t, v in tonos.items()
                      if re.match(r"^\d+$", t)}

    for fam in nueva:
        for tono, clave_texto in PARES:
            if tono not in nueva[fam]:
                continue
            t_a = base[fam][clave_texto] if clave_texto else "#ffffff"
            t_n = nueva[fam][clave_texto] if clave_texto else "#ffffff"
            antes = contraste(base[fam][tono], t_a)
            ahora = contraste(nueva[fam][tono], t_n)
            # Solo se rescata lo que ANTES aprobaba. Lo que ya venía suspenso de
            # Tailwind se deja como está: arreglarlo aquí sería cambiar el
            # aspecto del ERP por la puerta de atrás, y eso se decide aparte.
            if antes >= AA > ahora:
                nueva[fam][tono] = _rescata(nueva[fam][tono], t_n)
                rescatados.append(f"{fam}-{tono} ({antes:.2f} -> {ahora:.2f} -> "
                                  f"{contraste(nueva[fam][tono], t_n):.2f})")
    return base, nueva, rescatados


def modulo_js(nueva, rescatados):
    """La paleta como módulo aparte.

    Aparte y no dentro de `tailwind.config.js` por una razón que costó un rato
    entender: el config YA tenía una clave `colors` (la de shadcn), y al meter
    otra quedaban DOS claves iguales en el mismo objeto. En JavaScript eso no da
    error: gana la última y la otra se descarta en silencio. La paleta estaba
    escrita, el build pasaba en verde, y en pantalla no cambiaba nada.

    Con un módulo aparte hay UNA sola clave `colors` en el config, que hace
    `...paleta` y añade encima las variables de shadcn.
    """
    lineas = [
        "/*",
        " * PALETA DEL ERP — GENERADA. NO SE EDITA A MANO.",
        " *",
        " *   python3 herramientas/paleta_erp.py --escribir",
        " *",
        " * Son los colores de Tailwind con la MISMA luminosidad y menos",
        " * saturación, para que no griten sin mover los contrastes. El porqué de",
        " * cada número está en `herramientas/paleta_erp.py`.",
        " */",
        "module.exports = {",
    ]
    for fam, tonos in nueva.items():
        pares = ", ".join(f"'{t}': '{v}'" for t, v in tonos.items())
        lineas.append(f"  {fam}: {{ {pares} }},")
    lineas.append("};")
    if rescatados:
        lineas.insert(9, "// Oscurecidos lo justo para no bajar de 4.5 de contraste: "
                         + ", ".join(r.split(" ")[0] for r in rescatados))
    return "\n".join(lineas) + "\n"


def main():
    base, nueva, rescatados = paleta()
    if rescatados:
        print(f"# rescatados para no bajar de {AA}: " + ", ".join(rescatados),
              file=sys.stderr)

    if "--contraste" in sys.argv:
        print("Pares que usa el ERP. WCAG AA pide 4.5 para texto normal.\n")
        print(f"{'par':38} {'antes':>7} {'ahora':>7}   ")
        peor = 99
        for fam in sorted(nueva):
            for fondo, texto in (("600", "#ffffff"), ("700", "#ffffff"),
                                 ("100", None), ("50", None)):
                t_a = texto or base[fam]["900"]
                t_n = texto or nueva[fam]["900"]
                ca = contraste(base[fam][fondo], t_a)
                cn = contraste(nueva[fam][fondo], t_n)
                peor = min(peor, cn)
                aviso = "  <-- por debajo de 4.5" if cn < 4.5 else ""
                if aviso or abs(ca - cn) > 0.35:
                    et = "blanco" if texto else "texto-900"
                    print(f"{fam+'-'+fondo+' + '+et:38} {ca:7.2f} {cn:7.2f}{aviso}")
        print(f"\npeor contraste de todos los pares mirados: {peor:.2f}")
        return 0

    if "--escribir" not in sys.argv:
        print(f"{'color':16} {'antes':>9} {'ahora':>9}")
        for fam in sorted(nueva):
            for t in ("500", "600"):
                print(f"{fam+'-'+t:16} {base[fam][t]:>9} {nueva[fam][t]:>9}")
        return 0

    with open(DESTINO, "w", encoding="utf-8") as f:
        f.write(modulo_js(nueva, rescatados))
    print(f"✓ paleta escrita en {os.path.relpath(DESTINO, RAIZ)} "
          f"({len(nueva)} familias, {sum(len(v) for v in nueva.values())} tonos)")

    with open(CONFIG, "r", encoding="utf-8") as f:
        cfg = f.read()
    if "paleta.generada" not in cfg:
        print("  OJO: tailwind.config.js todavía no la usa. Tiene que hacer "
              "`const paleta = require('./paleta.generada.js')` y `...paleta` "
              "DENTRO de su única clave `colors`.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
