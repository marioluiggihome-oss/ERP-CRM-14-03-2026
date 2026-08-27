#!/usr/bin/env python3
# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LE PONE NOMBRE AL COLOR DE UNA PANTALLA, MIRANDO PARA QUÉ SE USA.

`bg-emerald-600` no dice nada; `bg-ok-600` dice que ahí hay algo terminado. Pero
el cambio NO puede hacerse a ciegas familia por familia: hay verdes que son «ok»
y verdes que estaban ahí porque quedaban bien. Renombrar los segundos sería
peor que no hacer nada — el código afirmaría un significado que no existe.

Así que esto lee el CONTEXTO de cada clase —la etiqueta que la envuelve, el
icono, el texto del botón, el título— y solo cambia lo que reconoce. Lo que no
reconoce se queda como está y se CUENTA, para que se vea lo que falta en vez de
darlo por hecho.

    python3 herramientas/semantizar_pantalla.py Fichero.jsx            # propone
    python3 herramientas/semantizar_pantalla.py Fichero.jsx --escribir
"""
import os
import re
import sys
from collections import Counter

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMP = os.path.join(RAIZ, "frontend", "src", "components")

FAMILIAS = ("indigo", "emerald", "amber", "orange", "purple", "red", "blue",
            "violet", "teal", "rose", "cyan", "sky", "green", "fuchsia",
            "pink", "lime", "yellow")
CLASE = re.compile(r"\b((?:bg|text|border|from|to|ring|divide)-)(%s)(-\d{2,3})"
                   % "|".join(FAMILIAS))

# En orden: gana la primera que reconoce. `error` va antes que `accion` porque un
# botón de borrar es las dos cosas y lo que importa es que es destructivo.
REGLAS = (
    # OJO con el idioma: la pantalla está en español pero los identificadores
    # están en inglés (`deleteOrder`, `removeLine`). Mirando solo el español,
    # cuatro botones de BORRAR de Cocina Desmontada salían clasificados como
    # «acción» — un botón rojo de borrar marcado como acción corriente es
    # exactamente el error que hace que el color deje de avisar.
    ("error", r"trash|borrar|elimin|error|anul|rechaz|peligro|no se pudo|"
              r"fall[oa]|sin tarifa|inv[aá]lid|cancelar|xcircle|alertcircle|"
              r"destructiv|quitar|cerrar sesi|"
              r"\bdelete|\bremove|\bdestroy|\bdiscard|\bclear[A-Z_]|\bwipe"),
    ("ok", r"check|correcto|listo|guardad|confirmad|completad|servid|cobrad|"
           r"v[aá]lid|[eé]xito|aceptad|encontrad|disponible|activo|hecho|"
           r"badgecheck|circlecheck"),
    ("aviso", r"aviso|atenci[oó]n|revisar|pendiente|falta[nr]?\b|incomplet|"
              r"cuidado|alerttriangle|triangle|sin dato|estimad|aprox|"
              r"ojo\b|no medid|dudos"),
    ("master", r"\bmaster\b|solo el master|privad|candado|\block\b|restringid|"
               r"solo t[uú]|no lo ve"),
    ("accion", r"onclick|<button|generar|guardar|a[ñn]adir|detectar|aplicar|"
               r"buscar|enviar|subir|descargar|copiar|crear|siguiente|"
               r"continuar|abrir|seleccionar|elegir|calcular|pegar|deshacer"),
    ("dato", r"€|eur\(|\bpvp\b|precio|importe|total|base imponible|"
             r"\bmm\b|\bcm\b|medida|ancho|alto|fondo|c[oó]digo"),
)


def _contexto(cuerpo, pos):
    """SOLO la etiqueta que lleva la clase, y el texto que hay justo detrás.

    La primera versión miraba 900 caracteres hacia atrás y se contagiaba del
    elemento de al lado: un `<div>` cualquiera pegado a un botón de «Borrar»
    salía clasificado como `error`. Salían cosas imposibles —`sky -> error`,
    `emerald -> master`— y un nombre semántico equivocado es PEOR que ninguno,
    porque el código afirma un significado que no existe y el siguiente que
    llegue se fía.

    Ahora el contexto es la etiqueta propia (ahí están el icono, el `onClick` y
    el `title`) más su primer texto visible. Nada más.
    """
    ini = cuerpo.rfind("<", max(0, pos - 1200), pos)
    if ini == -1:
        return ""
    fin_tag = cuerpo.find(">", pos)
    if fin_tag == -1:
        return ""
    etiqueta = cuerpo[ini:fin_tag + 1]
    # El texto que el usuario lee justo dentro de esa etiqueta.
    resto = cuerpo[fin_tag + 1:fin_tag + 160]
    texto = resto.split("<")[0]
    return (etiqueta + " " + texto).lower()


# Un color no puede significar cualquier cosa. Si el contexto dice «error» pero
# la clase es `sky`, casi seguro que el contexto se ha contagiado: un azul cielo
# no es un error en ninguna pantalla de este ERP. Cuando familia y significado
# no pegan, se deja como está y se cuenta — mejor un hueco visible que una
# etiqueta que miente.
COHERENTE = {
    "error": ("red", "rose", "orange", "amber"),
    "ok": ("emerald", "green", "teal", "lime", "cyan", "sky", "blue"),
    "aviso": ("amber", "yellow", "orange", "rose", "red"),
    "master": ("purple", "violet", "fuchsia", "indigo"),
    # `accion` y `dato` los puede llevar cualquier color: hoy los botones del
    # ERP están de todos los colores, y eso es justo lo que se viene a arreglar.
}


# Un icono suelto de adorno: `<List size={16} className="text-indigo-600" />`.
ICONO = re.compile(r"^<[a-z][a-z0-9]*\s[^>]*\bsize=\{")


def clasifica(ctx, familia):
    for token, patron in REGLAS:
        if re.search(patron, ctx):
            permitidas = COHERENTE.get(token)
            if permitidas and familia not in permitidas:
                return None
            return token

    # Iconos de adorno -> NEUTRO. En Cocina Montada 3 había cuatro iconos
    # seguidos de la misma lista en cuatro colores distintos (indigo, ámbar,
    # cian, esmeralda) sin que ninguno significara nada. Eso es el ruido: cuatro
    # colores compitiendo por la atención al lado del único que sí importa, que
    # es el del botón. Un icono que no dice nada no lleva color.
    #
    # Va el ÚLTIMO a propósito: si el icono tuviera significado (una papelera
    # roja) ya lo habría cogido una regla de arriba.
    if ICONO.match(ctx):
        return "dato"
    return None


def procesa(ruta, escribir=False):
    with open(ruta, "r", encoding="utf-8") as f:
        cuerpo = f.read()

    cambios, sin_clasificar = Counter(), Counter()
    piezas, ultimo = [], 0
    for m in CLASE.finditer(cuerpo):
        token = clasifica(_contexto(cuerpo, m.start()), m.group(2))
        piezas.append(cuerpo[ultimo:m.start()])
        if token:
            piezas.append(f"{m.group(1)}{token}{m.group(3)}")
            cambios[f"{m.group(2)} -> {token}"] += 1
        else:
            piezas.append(m.group(0))
            sin_clasificar[m.group(2)] += 1
        ultimo = m.end()
    piezas.append(cuerpo[ultimo:])

    if escribir:
        with open(ruta, "w", encoding="utf-8") as f:
            f.write("".join(piezas))
    return cambios, sin_clasificar


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    escribir = "--escribir" in sys.argv
    total_c = total_s = 0
    for nombre in [a for a in sys.argv[1:] if not a.startswith("--")]:
        ruta = nombre if os.path.isabs(nombre) else os.path.join(COMP, nombre)
        cambios, sin_c = procesa(ruta, escribir)
        c, s = sum(cambios.values()), sum(sin_c.values())
        total_c += c
        total_s += s
        print(f"\n{os.path.basename(ruta)}: {c} con significado, {s} sin clasificar")
        for k, v in cambios.most_common():
            print(f"    {k:24} {v}")
        if sin_c:
            print("    sin reconocer: "
                  + ", ".join(f"{k} {v}" for k, v in sin_c.most_common(6)))
    print(f"\nTOTAL: {total_c} clasificadas, {total_s} sin clasificar "
          f"({total_c * 100 // max(1, total_c + total_s)}% reconocido)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
