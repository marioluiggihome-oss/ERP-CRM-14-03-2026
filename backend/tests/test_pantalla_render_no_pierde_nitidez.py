# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO: una edición no puede guardar una imagen AGRANDADA.

24/08/2026, el master: «cada vez que hago una petición o un cambio, que no
pierda intensidad el render».

QUÉ PASABA
----------
Cada edición —Decorador, aplicar cambio, variante de color— hacía esto:

  1. manda al modelo la imagen ACTUAL
  2. el modelo devuelve una imagen MÁS PEQUEÑA
  3. `keepResolution` la AGRANDA hasta el tamaño de la que se envió
  4. esa imagen agrandada se guarda como la buena… y es la que se manda en la
     edición SIGUIENTE

El paso 4 era el problema. Agrandar no inventa detalle: lo emborrona. Y como
el resultado emborronado se convertía en la entrada de la vuelta siguiente, la
pérdida SE ACUMULABA.

MEDIDO sobre un render real, con la varianza del laplaciano (mide detalle
fino), simulando las vueltas:

    partida      137,7   100 %
    1 edición     70,1    51 %   <- la primera ya se lleva la mitad
    2 ediciones   58,7    43 %
    3 ediciones   54,1    39 %
    5 ediciones   50,9    37 %

Y no era el JPEG: `imageToDataUrl` devuelve los bytes tal cual cuando ya es un
data URL, y el agrandado salía en PNG. Era puro reescalado repetido.

POR QUÉ SE PUEDE QUITAR SIN PERDER NADA
---------------------------------------
El <img> del render usa `object-contain` dentro de un contenedor con
`aspectRatio`: el navegador lo escala igual, se guarde del tamaño que se
guarde. Lo único que se ganaba eran píxeles de mentira. Para tener MÁS
resolución de verdad está el botón de HD/4K, que la genera en vez de estirarla.
"""
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ESTUDIO = os.path.join(RAIZ, "frontend", "src", "components", "AIRenderStudio.jsx")


def _codigo():
    """La fuente SIN comentarios: aquí se habla de `keepResolution` a propósito."""
    with open(ESTUDIO, encoding="utf-8") as f:
        return "\n".join(l.split("//")[0] for l in f)


def test_ninguna_edicion_guarda_una_imagen_agrandada():
    codigo = _codigo()
    assert "keepResolution" not in codigo, (
        "ha vuelto `keepResolution` al guardado de las ediciones. Agrandar la "
        "respuesta del modelo hasta el tamaño de la que se envió emborrona la "
        "imagen, y como ESA es la que se manda en la edición siguiente, la "
        "pérdida se acumula: medido, la primera edición se lleva la mitad del "
        "detalle fino")


# Las funciones que guardan un render editado. Se nombran una a una a
# propósito: contar a bulto no dice CUÁL se ha quedado por el camino, y la que
# se queda fuera es justo la que sigue perdiendo nitidez en cada vuelta.
#
# Desde el 07/09/2026 son CUATRO: se añadió «pintar encima del render»
# (`aplicarPintado`), que también devuelve una imagen editada y por tanto tiene
# el mismo problema.
#
# Y desde el 10/09/2026 son CINCO: «Mejorar a acabado PREMIUM»
# (`mejorarAcabadoPremium`), que coge el render aprobado y lo devuelve mejorado.
# Es una edición como las demás y guarda lo que devuelve el modelo.
#
# LA LISTA ESTÁ ESCRITA A MANO Y ESO TIENE UN PRECIO: se queda corta el día que
# alguien añade un botón, y entonces el candado no protege al botón nuevo — que
# es justo el que más falta le hace. Por eso el recuento de abajo compara el
# número de guardados REALES con el de la lista: si aparece uno sin declarar,
# esto se pone rojo y obliga a nombrarlo. Es la red que cazó este quinto.
EDICIONES_QUE_GUARDAN = (
    ("visitaDecorador", "Decorador/a"),
    ("editRender", "Aplicar cambio"),
    ("colorVariant", "Variante de color"),
    ("aplicarPintado", "Pintar encima"),
    ("mejorarAcabadoPremium", "Acabado PREMIUM"),
)


def _funcion(codigo, nombre):
    i = codigo.index(f"const {nombre} = ")
    m = re.search(r"\n  const \w+ = ", codigo[i + 10:])
    return codigo[i:i + 10 + m.start()] if m else codigo[i:]


def test_TODAS_las_ediciones_guardan_lo_que_devuelve_el_modelo():
    """Decorador, aplicar cambio, variante de color y pintar encima."""
    codigo = _codigo()
    sin_guardar = [
        etq for fn, etq in EDICIONES_QUE_GUARDAN
        if "finalImg = await imageToDataUrl(finalImg)" not in _funcion(codigo, fn)]
    assert not sin_guardar, (
        f"estas ediciones NO guardan la imagen nativa del modelo, así que "
        f"siguen perdiendo nitidez en cada vuelta: {sin_guardar}")
    # Y que no aparezca una quinta sin pasar por aquí: una edición nueva que
    # se olvide de esto no da ningún error, solo devuelve la imagen un poco
    # peor cada vez.
    guardados = re.findall(r"finalImg = await imageToDataUrl\(finalImg\)", codigo)
    assert len(guardados) == len(EDICIONES_QUE_GUARDAN), (
        f"hay {len(guardados)} guardados y {len(EDICIONES_QUE_GUARDAN)} "
        f"ediciones declaradas: si has añadido una, nómbrala arriba")


def test_el_render_se_sigue_viendo_escalado_por_el_navegador():
    """Lo que hacía innecesario el agrandado: si esto se pierde, el render
    empezaría a verse del tamaño que venga y habría que replantearlo."""
    with open(ESTUDIO, encoding="utf-8") as f:
        fuente = f.read()
    assert "object-contain" in fuente, (
        "el render ya no se escala solo para verse: sin `object-contain` el "
        "tamaño de la imagen guardada SÍ se notaría en pantalla, y quitar el "
        "agrandado dejaría de ser gratis")
