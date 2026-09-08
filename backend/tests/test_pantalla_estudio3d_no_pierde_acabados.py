# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
EL ESTUDIO 3D NO PUEDE PERDER LOS ACABADOS QUE YA SE HAN PEDIDO.

El master, 06/09/2026: «cuando le doy al botón de visita decorador cambia los
colores que he ido cambiando después de las puertas, y eso no debería pasar;
debería guardar todo lo que yo le voy pidiendo».

QUÉ PASABA, Y POR QUÉ NO ERA COSA DEL DECORADOR. El servidor tiene un detector
de croquis: si la imagen de referencia parece un dibujo a mano, no la EDITA
—la INTERPRETA— y reconstruye la cocina desde cero. Una cocina clara (paredes,
muebles y encimera claros) tiene poco color y mucho brillo, que es justo la
firma del papel, así que se la tomaba por un croquis. De ahí que volviera otra
cocina, con los acabados de partida.

Eso YA SE SABÍA: el campo `editingRender` existe precisamente para decir «esta
imagen es un render nuestro, no lo adivines», y su comentario en el código
cuenta el fallo con detalle. Lo que pasa es que se le puso A UNA SOLA de las
llamadas —la línea de «aplicar cambios»— y quedaron SEIS botones más editando
la misma imagen sin decirlo: decorador, HD, 4K, variante de color, ficha
técnica y el 360º.

UN ARREGLO QUE SE APLICA A UN SITIO Y NO A LOS OTROS SEIS NO ES UN ARREGLO, y
esto es lo que este candado vigila: TODA llamada al render que mande la imagen
actual como referencia tiene que declarar su procedencia. Si mañana se añade un
botón nuevo y se olvida, se pone rojo aquí y no en la pantalla del master.

Y LA SEGUNDA MITAD: LA MEMORIA. La imagen sola no basta — al modelo hay que
DECIRLE lo que debe conservar, porque si no lee la escena y la reinterpreta. La
línea de «aplicar cambios» ya arrastraba la lista de lo aplicado de una vuelta
a la siguiente; los botones que NO deben tocar el diseño no la llevaban, así
que cada uno era una vuelta sin memoria.

OJO: `colorVariant` y la ficha técnica NO la llevan, y es a propósito. El
primero está cambiando el color aposta —la lista traería el anterior y pelearía
con el nuevo— y la segunda no es una foto, es un plano.

EL ESTUDIO 3D ESTÁ CONGELADO (CLAUDE.md, regla 1) desde el 04/09/2026. Esto se
toca porque lo pidió el master, que es quien puso el candado, y se toca SOLO
esto.
"""
import os
import re

from jsx_limpio import sin_comentarios

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PANTALLA = os.path.join(RAIZ, "frontend", "src", "components", "AIRenderStudio.jsx")

# Los que NO pueden rediseñar: lo suyo es mejorar la foto, no la cocina.
SIN_REDISENAR = ("visitaDecorador", "mejorarResolucion", "generar4K")
# Estos dos cambian el diseño a propósito, así que NO llevan la memoria.
CAMBIAN_A_PROPOSITO = ("colorVariant", "generarFichaTecnica")


def _lee():
    with open(PANTALLA, "r", encoding="utf-8") as f:
        return f.read()


def _funciones(cuerpo):
    """Trocea el fichero por funciones `const X = async (…) => {…}`.

    Se corta en el arranque de la SIGUIENTE, que es un ancla estable: contar
    llaves aquí no vale, porque dentro hay plantillas con `${…}` y objetos.
    """
    arranques = [(m.group(1), m.start())
                 for m in re.finditer(r"\n  const (\w+) = async", cuerpo)]
    out = {}
    for i, (nombre, ini) in enumerate(arranques):
        fin = arranques[i + 1][1] if i + 1 < len(arranques) else len(cuerpo)
        out[nombre] = cuerpo[ini:fin]
    return out


def _envian_la_imagen_actual(cuerpo):
    """Las funciones que mandan la imagen ACTUAL al render como referencia.

    Son las que editan nuestro propio render, y por tanto las que tienen que
    declararlo. Se detectan por lo que HACEN, no por una lista escrita a mano:
    una lista se queda corta el día que alguien añada un botón, que es
    exactamente lo que pasó.
    """
    return {n: b for n, b in _funciones(cuerpo).items()
            if "/api/ai-engine/render`" in b
            and ("referenceImage: dataUrl" in b or "referenceImage: img" in b)}


def _cuerpo_de_la_peticion(fn):
    """El objeto que va DENTRO de `JSON.stringify(...)`, y solo ese.

    Hace falta un emparejador de llaves de verdad —saltándose las cadenas y
    las plantillas `${…}`— porque el fallo que esto vigila es de UN NIVEL de
    anidamiento: la palabra está en la función, pero fuera del cuerpo. Buscar
    por texto no distingue las dos cosas.
    """
    i = fn.find("JSON.stringify(")
    if i < 0:
        return ""
    j = i + len("JSON.stringify(")
    prof, comilla, salida = 1, "", []
    while j < len(fn) and prof > 0:
        c = fn[j]
        if comilla:
            if c == "\\":
                salida.append(fn[j:j + 2]); j += 2; continue
            if c == comilla:
                comilla = ""
        elif c in "\"'`":
            comilla = c
        elif c in "({[":
            prof += 1
        elif c in ")}]":
            prof -= 1
            if prof == 0:
                break
        salida.append(c)
        j += 1
    return "".join(salida)


def test_TODO_BOTON_QUE_EDITA_NUESTRO_RENDER_LO_DECLARA():
    """Sin `editingRender`, el servidor le pasa el render al detector de
    croquis y una cocina clara se toma por un dibujo a mano: en vez de aplicar
    el cambio, REHACE la cocina — y ahí es donde se pierden los acabados.

    No da ningún error: devuelve una cocina preciosa que no es la suya."""
    cuerpo = sin_comentarios(_lee())
    editores = _envian_la_imagen_actual(cuerpo)
    # La edición principal usa deliberadamente `referenceImage: img`, que es
    # el último diseño aprobado; los demás flujos convierten la referencia a
    # dataURL antes de enviarla.
    assert len(editores) >= 6, (
        f"el reconocedor solo encuentra {len(editores)} botones que editen el "
        f"render; algo ha cambiado de forma y esta prueba dejaría de mirar lo "
        f"que tiene que mirar: {sorted(editores)}")
    # NO BASTA CON QUE LA PALABRA ESTÉ EN LA FUNCIÓN: TIENE QUE IR DENTRO DEL
    # CUERPO DE LA PETICIÓN. Se comprobó el 07/09/2026 y estaba mal en CUATRO
    # de los seis botones:
    #
    #     body: JSON.stringify({ description: desc, ... }),
    #     editingRender: true,          ← hermano de `method` y `headers`
    #
    # Ahí `editingRender` es una opción de `fetch`, que `fetch` ignora sin
    # decir nada: al servidor no le llega el campo. O sea que el arreglo del
    # 06/09 estaba escrito y no surtía efecto — el decorador seguía perdiendo
    # los acabados, que es justo lo que el master había pedido que dejara de
    # pasar. Y esta prueba pasaba en verde, porque buscaba el texto en la
    # función entera.
    sin_declarar = [n for n, b in editores.items()
                    if "editingRender: true" not in _cuerpo_de_la_peticion(b)]
    assert not sin_declarar, (
        f"estos botones mandan nuestro propio render y NO lo declaran DENTRO "
        f"del cuerpo de la petición, así que el campo no sale del navegador y "
        f"el servidor puede tomarlo por un croquis y rehacer la cocina "
        f"entera: {sorted(sin_declarar)}")


def test_LOS_QUE_NO_DEBEN_REDISENAR_ARRASTRAN_LO_YA_PEDIDO():
    """La imagen de referencia sola no basta: al modelo hay que DECIRLE lo que
    tiene que conservar. Si no, lee la escena y la reinterpreta — que es cómo
    volvían los acabados de partida."""
    cuerpo = sin_comentarios(_lee())
    funcs = _funciones(cuerpo)
    for nombre in SIN_REDISENAR:
        assert nombre in funcs, f"ha desaparecido {nombre}"
        assert "memoriaDeCambios()" in funcs[nombre], (
            f"«{nombre}» no arrastra los acabados ya aplicados: cada pulsación "
            f"es una vuelta sin memoria y el modelo vuelve a los originales")


def test_LOS_QUE_CAMBIAN_A_PROPOSITO_NO_LA_ARRASTRAN():
    """Y es a propósito, no un olvido. `colorVariant` está cambiando el color:
    darle la lista de lo ya aplicado le metería el color ANTERIOR peleando con
    el nuevo. La ficha técnica no es una foto, es un plano.

    Se comprueba para que nadie «complete» el arreglo de arriba extendiéndolo a
    estos dos y rompa justo lo que sí funciona."""
    cuerpo = sin_comentarios(_lee())
    funcs = _funciones(cuerpo)
    for nombre in CAMBIAN_A_PROPOSITO:
        assert nombre in funcs, f"ha desaparecido {nombre}"
        assert "memoriaDeCambios()" not in funcs[nombre], (
            f"«{nombre}» arrastra los cambios ya aplicados, y no debe: está "
            f"cambiando el diseño a propósito y la lista le mete lo anterior")


def test_LA_MEMORIA_SALE_DE_LO_QUE_SE_HA_APLICADO_DE_VERDAD():
    """`memoriaDeCambios` lee `editAppliedChanges`, que es la lista que la
    línea de «aplicar cambios» va llenando. Si se armara con otra cosa, diría
    que hay que conservar algo que el master no pidió."""
    cuerpo = sin_comentarios(_lee())
    i = cuerpo.index("const memoriaDeCambios = ()")
    bloque = cuerpo[i:cuerpo.index("\n  );", i)]
    assert "editAppliedChanges" in bloque, (
        "la memoria no sale de los cambios realmente aplicados")
    assert "CONSERVAR" in bloque.upper(), (
        "el encargo no le dice al modelo que los conserve: una lista de "
        "cambios sin decir para qué es, un modelo la lee como cosas que hacer")
    # Y sin cambios aplicados no se manda un encabezado vacío, que sería una
    # instrucción sin contenido detrás.
    assert "editAppliedChanges.length" in bloque, (
        "sin cambios aplicados se manda igualmente el encabezado, y una lista "
        "vacía en un encargo es ruido que compite con lo que sí se pide")


def test_LA_ORBITA_NO_LE_CUELA_UN_CAMPO_QUE_SU_RUTA_NO_TIENE():
    """El 360º va por `/render/orbit`, cuyo cuerpo no declara `editingRender`.
    Mandárselo no arreglaría nada y ensuciaría la petición — y esa ruta no pasa
    por el detector de croquis, así que no tiene el problema."""
    cuerpo = sin_comentarios(_lee())
    orb = _funciones(cuerpo).get("generarOrbita", "")
    assert "/render/orbit" in orb
    assert "editingRender" not in orb, (
        "se le está mandando `editingRender` a una ruta que no lo declara")


def test_LA_EDICION_LOCALIZADA_BLOQUEA_LO_NO_SOLICITADO():
    """Una orden de tiradores en bajos debe viajar con zona, propiedad e
    invariantes explícitas; el prompt genérico por sí solo ya demostró que no
    basta: añadió repisas y alteró los muebles altos."""
    cuerpo = sin_comentarios(_lee())
    assert "const contratoEdicion = (lineas)" in cuerpo
    assert "editContract: contratoEdicion(allLines)" in cuerpo
    for texto in ("muebles altos", "lavavajillas", "integrable", "repisas", "módulos bajos"):
        assert texto in cuerpo, f"falta el bloqueo explícito de {texto}"


def test_EL_EDITOR_MOVIL_RESERVA_EL_ESPACIO_DEL_TECLADO():
    """En una tableta vertical la última línea no puede quedar detrás del
    teclado virtual; el panel debe medir el viewport visual y desplazar el
    campo enfocado con relleno inferior."""
    cuerpo = sin_comentarios(_lee())
    for texto in ("visualViewport", "keyboardInset", "scrollPaddingBottom", "enfocarCampoEdicion"):
        assert texto in cuerpo, f"falta la protección móvil {texto}"
    assert "onFocus={e => enfocarCampoEdicion(e.currentTarget)}" in cuerpo


def test_EL_BACKEND_APLICA_EL_CONTRATO_LOCALIZADO():
    ruta = os.path.join(RAIZ, "backend", "services", "luiggi_ai", "render_3d.py")
    with open(ruta, encoding="utf-8") as f:
        servicio = f.read()
    assert "edit_contract: Optional[dict]" in servicio
    for texto in ("CONTRATO DE EDICIÓN LOCALIZADA", "INMUTABLE", "semi-integrable", "repisas"):
        assert texto in servicio, f"falta la regla backend {texto}"


def test_LA_RUTA_ACEPTA_Y_PROPAGA_EL_CONTRATO():
    ruta = os.path.join(RAIZ, "backend", "routes", "ai_engine.py")
    with open(ruta, encoding="utf-8") as f:
        router = f.read()
    assert "editContract: Optional[dict]" in router
    assert "edit_contract=request.editContract" in router
