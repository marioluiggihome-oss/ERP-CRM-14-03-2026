# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
QUITARLE LOS COMENTARIOS A UN JSX SIN COMERSE EL CÓDIGO.

Nueve candados de este repo escriben su propio `_sin_comentarios`, y todos
hacen lo mismo: `re.sub(r"/\\*.*?\\*/", " ", cuerpo, flags=re.S)`.

ESO SE COME CÓDIGO, y se descubrió persiguiendo un falso positivo. En
`RentabilidadLineas.jsx` hay esto, que es de lo más corriente en un formulario:

    accept="image/*,application/pdf"

Ese `/*` de dentro de la cadena abre un comentario que no existe, y el
`.*?` lo cierra en el siguiente `*/` de verdad — un comentario JSX DIEZ LÍNEAS
más abajo. Por el camino se traga el código que hay en medio, entre otras cosas
el botón `setShowTotals(s => !s)`. Un candado que busque ese botón dirá que no
está, y otro que busque algo prohibido dirá que no lo hay: MIENTE EN LAS DOS
DIRECCIONES, y sin dar ningún error.

CÓMO SE HACE BIEN, sin escribir un analizador de JavaScript:

1. Se hace una COPIA con todas las cadenas ('...', "...", `...`) rellenas de
   espacios. En esa copia, un `/*` solo puede ser un comentario de verdad.
2. Se localizan los comentarios SOBRE ESA COPIA.
3. Y se recortan del texto ORIGINAL, que es el que devuelve la función: así no
   se pierde ni un `data-testid` ni un rótulo, que es justo lo que buscan los
   candados.

Los comentarios de línea (`//`) se quitan igual, y también sobre la copia: si
no, una URL `https://...` dentro de una cadena se comería el resto de la línea.
"""
import re

_COMILLAS = "'\"`"


def _enmascara_cadenas(cuerpo: str) -> str:
    """La misma longitud, con el contenido de las cadenas puesto a espacios.

    Se conservan los saltos de línea para que los números de línea sigan
    cuadrando con el original, y las propias comillas para no juntar tokens.
    """
    fuera = list(cuerpo)
    i, n = 0, len(cuerpo)
    while i < n:
        c = cuerpo[i]
        if c in _COMILLAS:
            cierre = c
            j = i + 1
            while j < n:
                if cuerpo[j] == "\\":
                    j += 2
                    continue
                if cuerpo[j] == cierre:
                    break
                # Una cadena normal no cruza el salto de línea; la de comilla
                # invertida sí. Sin este corte, una comilla suelta dentro de un
                # texto ("l'aigua") enmascararía medio fichero.
                if cuerpo[j] == "\n" and cierre != "`":
                    break
                fuera[j] = " " if cuerpo[j] != "\n" else "\n"
                j += 1
            i = j + 1
            continue
        i += 1
    return "".join(fuera)


def cortes_de_comentario(cuerpo: str):
    """Los (inicio, fin) de cada comentario. Separado para poder COMPROBARLO:
    su candado exige que todo lo que se recorta empiece por `//` o `/*`, que es
    la propiedad exacta que hay que sostener — «solo se van comentarios»."""
    mascara = _enmascara_cadenas(cuerpo)
    cortes = []
    for m in re.finditer(r"/\*.*?\*/", mascara, re.S):
        cortes.append((m.start(), m.end()))
    for m in re.finditer(r"//[^\n]*", mascara):
        if any(a <= m.start() < b for a, b in cortes):
            continue
        cortes.append((m.start(), m.end()))
    return sorted(cortes)


def sin_comentarios(cuerpo: str) -> str:
    """El JSX sin comentarios y con TODO lo demás intacto."""
    salida, fin = [], 0
    for a, b in cortes_de_comentario(cuerpo):
        if a < fin:
            continue
        salida.append(cuerpo[fin:a])
        # Se dejan los saltos de línea del comentario para no descuadrar las
        # líneas: un candado que informe de «línea 412» tiene que acertar.
        salida.append("\n" * cuerpo[a:b].count("\n"))
        fin = b
    salida.append(cuerpo[fin:])
    return "".join(salida)
