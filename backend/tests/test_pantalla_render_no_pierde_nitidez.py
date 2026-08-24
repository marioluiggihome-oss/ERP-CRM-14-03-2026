# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
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


def test_las_tres_ediciones_guardan_lo_que_devuelve_el_modelo():
    """Decorador, aplicar cambio y variante de color: las tres."""
    codigo = _codigo()
    guardados = re.findall(r"finalImg = await imageToDataUrl\(finalImg\)", codigo)
    assert len(guardados) == 3, (
        f"hay {len(guardados)} ediciones guardando la imagen nativa y deberían "
        f"ser 3 (Decorador, aplicar cambio y variante de color). Si una se ha "
        f"quedado por el camino, esa sigue perdiendo nitidez en cada vuelta")


def test_el_render_se_sigue_viendo_escalado_por_el_navegador():
    """Lo que hacía innecesario el agrandado: si esto se pierde, el render
    empezaría a verse del tamaño que venga y habría que replantearlo."""
    with open(ESTUDIO, encoding="utf-8") as f:
        fuente = f.read()
    assert "object-contain" in fuente, (
        "el render ya no se escala solo para verse: sin `object-contain` el "
        "tamaño de la imagen guardada SÍ se notaría en pantalla, y quitar el "
        "agrandado dejaría de ser gratis")
