# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
UN BOTÓN OFRECÍA SUBIR VÍDEOS Y ESCANEOS LiDAR, Y NO HABÍA NADA QUE LOS LEYERA.

El master, 15/09/2026, señalando el botón «📱 Escaneo LiDAR / Vídeo»: «¿para
qué servía este botón?».

Para nada. Aceptaba `video/*,.usdz,.ply,.e57` y se los pasaba a
`handleReferenceUpload`, que es EL MISMO manejador de las fotos. En el servidor
no hay nada que lea vídeo ni nubes de puntos — ni `ffmpeg`, ni `.usdz`, ni
`.ply`, ni `.e57`.

Y FALLABA DE LA PEOR MANERA POSIBLE, que es la razón por la que esto merece un
candado y no solo un borrado. `downscaleImage` intenta decodificar el fichero
como imagen y, cuando no puede, hace:

    img.onerror = () => resolve(original);   // no es imagen (PDF u otro)

NO da error: devuelve el fichero tal cual. Así que el vídeo entraba en la lista
como «foto de referencia», ocupaba uno de los SIETE huecos del tope (regla 3) y
DESPLAZABA a un croquis que sí habría servido. El render salía peor y no había
forma de saber por qué. Es el patrón de siempre en este repo: no un error, un
resultado peor en silencio.

LO QUE ESTE CANDADO VIGILA, y no es «que no vuelva la palabra LiDAR»:

    NO SE OFRECE SUBIR UN FORMATO QUE EL MANEJADOR NO SEPA LEER.

Escrito así aguanta el caso siguiente. Si mañana alguien añade un botón de
`.dwg`, o de `.obj`, o de vídeo otra vez, se pone rojo igual — aunque no se
llame LiDAR. Y si algún día SE IMPLEMENTA de verdad la lectura de vídeo, esta
prueba se actualiza a conciencia, que es distinto de que nadie se entere.

Las DOS pantallas: el Estudio 3D y su clon (regla 1).
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jsx_limpio import sin_comentarios  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COMPONENTES = os.path.join(RAIZ, "frontend", "src", "components")
PANTALLAS = ("AIRenderStudio.jsx", "Estudio3DLab.jsx")

# Lo ÚNICO que `downscaleImage` sabe convertir, o que el lector de planos sabe
# mirar. Cualquier otra cosa se cuela entera y ocupa un hueco de referencia.
FORMATOS_QUE_SABEMOS_LEER = {"image/*", "application/pdf"}


def _limpio(nombre):
    with open(os.path.join(COMPONENTES, nombre), "r", encoding="utf-8") as f:
        cuerpo = sin_comentarios(f.read())
    # El recorte de comentarios no puede habernos dejado sin código: este
    # fichero EXPLICA el fallo citando los formatos que se quitaron, así que
    # sin quitarlos el candado se creería su propia nota (reglas 24, 34, 35).
    assert "handleReferenceUpload" in cuerpo, "%s: el recorte se comió el código" % nombre
    return cuerpo


def _accepts(cuerpo):
    """Todos los `accept=` de los `<input type="file">` de la pantalla."""
    return re.findall(r'<input\s+type="file"\s+accept="([^"]+)"', cuerpo)


def test_NO_SE_OFRECE_SUBIR_NADA_QUE_NO_SEPAMOS_LEER():
    """El candado de verdad: lo que se ofrece y lo que se sabe leer, iguales."""
    for pantalla in PANTALLAS:
        cuerpo = _limpio(pantalla)
        listas = _accepts(cuerpo)
        assert listas, "%s ya no tiene ningún campo de subida" % pantalla
        for lista in listas:
            sobran = [t.strip() for t in lista.split(",")
                      if t.strip() and t.strip() not in FORMATOS_QUE_SABEMOS_LEER]
            assert not sobran, (
                "%s ofrece subir %s y no hay nada que lo lea: el fichero no da "
                "error, se cuela como «foto de referencia», ocupa uno de los 7 "
                "huecos y desplaza a un croquis que sí servía"
                % (pantalla, sobran))


def test_EL_VIDEO_Y_EL_LiDAR_NO_VUELVEN_POR_LA_PUERTA_DE_ATRAS():
    """El caso concreto que vio el master, por su nombre.

    Vale que sea explícito además de la regla general: son las extensiones que
    estuvieron ofrecidas de verdad, y volver a ponerlas es exactamente el fallo
    que costó esta conversación.
    """
    for pantalla in PANTALLAS:
        cuerpo = _limpio(pantalla)
        todo = " ".join(_accepts(cuerpo))
        for formato in ("video/", ".usdz", ".ply", ".e57"):
            assert formato not in todo, (
                "%s vuelve a ofrecer subir %s sin que nadie lo lea" % (pantalla, formato))


def test_EL_BOTON_QUE_QUEDA_DICE_QUE_TAMBIEN_TRAGA_PDF():
    """El plano acotado de las apps de medir sale en PDF, y es lo que de verdad
    sirve. Si el botón solo dice «croquis/foto», nadie prueba a subirlo — y la
    función existe desde siempre."""
    for pantalla in PANTALLAS:
        cuerpo = _limpio(pantalla)
        assert "application/pdf" in " ".join(_accepts(cuerpo)), (
            "%s ha dejado de aceptar PDF: por ahí entra el plano acotado" % pantalla)
        assert re.search(r"Subir croquis[^<]*PDF", cuerpo), (
            "%s no dice que acepta un plano en PDF, así que nadie lo va a "
            "intentar" % pantalla)


def test_EL_MANEJADOR_SIGUE_SIN_DAR_ERROR_CON_LO_QUE_NO_ES_IMAGEN():
    """Por qué el corte va en el `accept` y no en el manejador.

    `downscaleImage` resuelve con el fichero ORIGINAL cuando no lo puede
    decodificar —y tiene que seguir haciéndolo, porque así es como pasan los
    PDF—. Eso significa que el manejador NUNCA va a rechazar nada: el único
    sitio donde se puede cerrar la puerta es el `accept`. Si alguien quita este
    comportamiento creyendo que «así se validaría», los PDF dejan de entrar.
    """
    for pantalla in PANTALLAS:
        cuerpo = _limpio(pantalla)
        assert "img.onerror = () => resolve(original)" in cuerpo, (
            "%s ha cambiado cómo trata un fichero que no es imagen: si ahora "
            "rechaza, los PDF dejan de entrar; si sigue colando, el corte tiene "
            "que seguir estando en el `accept`" % pantalla)
