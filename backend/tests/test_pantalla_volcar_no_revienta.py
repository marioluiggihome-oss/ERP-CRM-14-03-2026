# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO: volcar al presupuesto no puede tumbar la pantalla.

15/08/2026, el master: «en cocina 3d, cuando le doy a volcar al presupuesto este
es el error que sale» — y manda el pantallazo del «⚠️ Algo ha fallado», que es
el error boundary de React. O sea una excepcion de JavaScript, no un fallo del
servidor.

DE DONDE SALE
-------------
Los muebles del IA Lab vienen de un JSON que escribe un MODELO. El codigo hacia
`furniture.subtipo.replace(...)`, `matchedCode.toUpperCase()` y
`productCode.toUpperCase()` dando por hecho que eran cadenas. Si el modelo
devuelve un NUMERO donde se espera texto —`subtipo: 2`, o un codigo sin letras—
esos metodos no existen, salta un TypeError y se cae la pantalla ENTERA. El
usuario ve «Algo ha fallado» y pierde lo que tuviera a medias.

Un dato raro de la IA tiene que dar una linea rara, no tumbar el ERP.

Y ADEMAS, QUE EL ERROR DIGA DONDE
---------------------------------
El detalle tecnico solo pintaba `error.message`. Por eso esto se reporto como
«da fallo» y hubo que ir a buscarlo a mano. Ahora lleva la pila de componentes
—que dice en QUE componente ha reventado— y un boton para copiarlo.
"""
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
APP = os.path.join(RAIZ, "frontend", "src", "App.js")
INDEX = os.path.join(RAIZ, "frontend", "src", "index.js")


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def _volcado():
    src = _leer(APP)
    i = src.index("const handleAddFromVisualizer")
    return src[i:src.index("\n  };", i)]


def test_lo_que_viene_de_la_IA_se_trata_como_texto():
    """CANDADO PRINCIPAL. `2.toUpperCase()` no existe: TypeError y pantalla en
    blanco."""
    cuerpo = _volcado()
    # Se mira el CODIGO, no los comentarios.
    codigo = "\n".join(l.split("//")[0] for l in cuerpo.splitlines())
    malas = []
    for m in re.finditer(r"(\w[\w.]*)\.(toUpperCase|toLowerCase|replace|trim|split|startsWith|endsWith)\(",
                         codigo):
        var = m.group(1)
        if var in ("tipo", "subtipo"):      # ya vienen normalizadas con String()
            continue
        antes = codigo[max(0, m.start() - 14):m.start()]
        if "String(" not in antes:
            malas.append(f"{var}.{m.group(2)}()")
    assert not malas, (
        "vuelve a llamarse a un metodo de texto sobre un dato de la IA sin "
        "asegurar que sea texto: si el modelo devuelve un numero, se cae la "
        "pantalla entera al volcar. Sitios: " + ", ".join(malas))


def test_el_tipo_y_el_subtipo_se_normalizan_a_texto():
    cuerpo = _volcado()
    assert "String(furniture.tipo" in cuerpo, "`tipo` vuelve a darse por texto"
    assert "String(furniture.subtipo)" in cuerpo, "`subtipo` vuelve a darse por texto"


# ─── El error tiene que decir DONDE ─────────────────────────────────────────

def test_el_detalle_tecnico_dice_en_que_componente_ha_fallado():
    """Sin esto, un fallo se reporta como «da fallo» y hay que adivinarlo."""
    src = _leer(INDEX)
    assert "componentStack" in src, (
        "el error boundary vuelve a enseniar solo el mensaje: un fallo no dira "
        "en que pantalla ha sido y habra que buscarlo a mano")


def test_el_detalle_se_puede_copiar():
    """Se reporta desde el movil: transcribir una traza a mano no lo hace nadie."""
    src = _leer(INDEX)
    assert "clipboard.writeText" in src, \
        "ya no se puede copiar el detalle del error para mandarlo"
