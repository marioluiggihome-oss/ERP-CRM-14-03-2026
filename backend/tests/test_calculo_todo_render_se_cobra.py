# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
TODO LO QUE GENERA UNA IMAGEN SE COBRA, Y CON EL MOTOR ELEGIDO.

Auditoría del Estudio 3D, 06/09/2026, a petición del master.

CUATRO ENDPOINTS GENERAN IMAGEN CON IA y solo DOS cobraban:

    /render          descripción, editar, decorador, HD, 4K…   COBRABA
    /render/orbit    el giro 360º                              COBRABA
    /render/compose  plano + un boceto por pared               NO COBRABA
    /render/params   el formulario de parámetros               NO COBRABA

El de parámetros es el peor de los dos, porque MIENTE: su propio `title` dice
«consume créditos» y encima enseña «Vas a gastar 1 crédito». El servidor no
cobraba ninguno. El contador decía una cosa y la factura del proveedor otra —
que es exactamente lo que la regla 15 de CLAUDE.md existe para impedir.

Y el de plano + bocetos es de los caros: manda el plano y un boceto POR PARED,
o sea varias imágenes de referencia en la misma llamada.

POR QUÉ EL COBRO VIVE AHORA EN UNA SOLA FUNCIÓN. Estaba escrito dentro de
`/render` y COPIADO otra vez dentro de `/render/orbit`; los otros dos no lo
tenían. Con el cobro repartido, cada endpoint nuevo empieza gratis por
omisión y nadie se entera hasta que llega la factura. Con `cobrar_render` en
un sitio, olvidarlo es una línea que falta y esta prueba la ve.

SEGUNDA MITAD: EL MOTOR. `generate_render_from_params` era el ÚNICO de los
once sitios que llaman a `_render_dispatch` que no le pasaba el motor, así que
el botón de parámetros renderizaba SIEMPRE con el de por defecto aunque en
pantalla hubiera otro elegido. No daba ningún error: devolvía una imagen, solo
que de otro motor — y de otro precio. Es la regla 1 de CLAUDE.md: «el motor
elegido en pantalla manda siempre, POR CUALQUIER CAMINO».
"""
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RUTAS = os.path.join(RAIZ, "backend", "routes", "ai_engine.py")
MOTOR = os.path.join(RAIZ, "backend", "services", "luiggi_ai", "render_3d.py")
PANTALLA = os.path.join(RAIZ, "frontend", "src", "components", "AIRenderStudio.jsx")

# Los cuatro que producen una imagen con IA. `/render/upscale-4k` NO está: es
# un reescalado determinista con Pillow, sin IA y sin coste de proveedor, y
# tiene su propio permiso (`canUse4K`).
GENERAN_IMAGEN = ("/render", "/render/compose", "/render/orbit", "/render/params")


def _lee(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def _endpoints(cuerpo):
    marcas = [(m.group(2), m.start())
              for m in re.finditer(r'@ai_engine_router\.(post|get)\("([^"]+)"\)', cuerpo)]
    out = {}
    for i, (ruta, ini) in enumerate(marcas):
        fin = marcas[i + 1][1] if i + 1 < len(marcas) else len(cuerpo)
        out[ruta] = cuerpo[ini:fin]
    return out


def test_LOS_CUATRO_QUE_GENERAN_IMAGEN_COBRAN():
    """Uno que no cobra no da ningún error: da renders gratis hasta que llega
    la factura del proveedor."""
    eps = _endpoints(_lee(RUTAS))
    sin_cobrar = []
    for ruta in GENERAN_IMAGEN:
        assert ruta in eps, f"ha desaparecido el endpoint {ruta}"
        if "cobrar_render(" not in eps[ruta]:
            sin_cobrar.append(ruta)
    assert not sin_cobrar, (
        f"estos endpoints generan una imagen con IA y NO descuentan créditos: "
        f"{sin_cobrar}")


def test_EL_COBRO_VIVE_EN_UN_SOLO_SITIO():
    """Repartido, cada endpoint nuevo empieza gratis por omisión. Y si hubiera
    dos copias, una se arreglaría y la otra no — que es como llegamos aquí."""
    cuerpo = _lee(RUTAS)
    assert "async def cobrar_render(" in cuerpo, (
        "no existe la función única de cobro")
    # `consume_credits` solo se llama DESDE ella; ningún endpoint lo hace por
    # su cuenta, que es como se acaba teniendo dos versiones distintas.
    # Se quita la propia `cobrar_render` antes de mirar: vive entre dos
    # endpoints, asi que el troceo por decoradores se la lleva dentro del
    # anterior y se acusaria a si misma.
    i0 = cuerpo.index("async def cobrar_render(")
    sin_helper = cuerpo[:i0] + cuerpo[cuerpo.index("\n@ai_engine_router", i0):]
    fuera = [n for n, b in _endpoints(sin_helper).items() if "consume_credits(" in b]
    assert not fuera, (
        f"estos endpoints cobran por su cuenta en vez de usar `cobrar_render`: "
        f"{fuera}. Dos copias del cobro acaban siendo dos cobros distintos")


def test_SE_COBRA_POR_EL_MOTOR_QUE_SE_VA_A_USAR():
    """`motor_permitido` ya rebaja a IA 1 a quien no sea master: cobrarle el
    3,3x de un motor que no va a llegar a tocar sería cobrarle de más."""
    cuerpo = _lee(RUTAS)
    i = cuerpo.index("async def cobrar_render(")
    bloque = cuerpo[i:cuerpo.index("\n@ai_engine_router", i)]
    assert "motor_permitido(user, provider)" in bloque, (
        "el cobro no pasa por `motor_permitido`: se cobraría por el motor "
        "PEDIDO y no por el que de verdad se va a usar")
    assert "402" in bloque and "mensaje_sin_creditos" in bloque, (
        "sin créditos tiene que dar 402 con su explicación, no un error seco")
    # UN FALLO DEL CONTADOR NO PUEDE DEJAR A NADIE SIN TRABAJAR. Es la misma
    # decisión que ya tomaba `/render`: solo se bloquea cuando de verdad no
    # quedan créditos.
    assert "except Exception:" in bloque and "return veces" in bloque, (
        "un error interno leyendo el saldo estaría bloqueando la generación")


def test_EL_MOTOR_ELEGIDO_LLEGA_POR_LOS_ONCE_CAMINOS():
    """CLAUDE.md, regla 1: «el motor elegido en pantalla manda siempre, por
    cualquier camino». `generate_render_from_params` era el único que no se lo
    pasaba al despachador."""
    cuerpo = _lee(MOTOR)
    sin_motor = []
    for m in re.finditer(r"_render_dispatch\((.{0,400}?)\)\n", cuerpo, re.S):
        if "def _render_dispatch" in cuerpo[max(0, m.start() - 40):m.start()]:
            continue
        if "provider" not in m.group(1):
            fn = [f.group(1) for f in
                  re.finditer(r"async def (\w+)", cuerpo[:m.start()])][-1]
            sin_motor.append(fn)
    assert not sin_motor, (
        f"estas funciones renderizan sin pasarle el motor elegido, así que usan "
        f"el de por defecto sin decirlo: {sin_motor}")
    # Y la ruta tiene que aceptarlo y filtrarlo por quién puede pedirlo.
    rutas = _lee(RUTAS)
    params = _endpoints(rutas)["/render/params"]
    assert "motor_permitido(user, request.provider)" in params, (
        "`/render/params` no filtra el motor: cualquiera podría pedir por API "
        "el motor caro (CLAUDE.md, regla 11)")
    assert "provider: Optional[str] = None" in rutas[
        rutas.index("class RenderParamsRequest"):rutas.index("class AnalyzeRequest")], (
        "`RenderParamsRequest` no acepta el motor, así que la pantalla no puede "
        "mandarlo")
    # Y lo mismo en los otros tres: quién puede pedir cada motor se decide en el
    # SERVIDOR (regla 11), porque el motor viaja en el cuerpo de la petición y
    # cualquiera con sesión podría pedir el caro desde fuera de la pantalla.
    eps = _endpoints(rutas)
    for ruta in ("/render", "/render/compose", "/render/orbit", "/render/params"):
        assert "motor_permitido(" in eps[ruta], (
            f"«{ruta}» acepta el motor tal cual: cualquier usuario con sesión "
            f"podría pedir por API el motor caro (CLAUDE.md, regla 11)")


def test_LA_PANTALLA_MANDA_EL_MOTOR_Y_AVISA_DE_LO_QUE_SE_VA_A_COBRAR():
    """El aviso tiene que decir lo que se cobra de VERDAD. Con plano o bocetos
    se genera UNA imagen aunque haya varias variantes pedidas; si el aviso
    dijera 3 y se cobrara 1, el contador y el aviso volverían a contar cosas
    distintas (regla 15)."""
    cuerpo = _lee(PANTALLA)
    i = cuerpo.index("const handleGenerateParams")
    bloque = cuerpo[i:cuerpo.index("\n  const ", i + 10)]
    assert "provider: providerOf()" in bloque, (
        "el botón de parámetros no manda el motor elegido")
    assert "<AvisoDeCoste n={(floorPlan || wallSketches.length > 0) ? 1 : variantCount} />" in cuerpo, (
        "el aviso de coste sigue prometiendo una variante por cada pedida "
        "cuando con plano o bocetos solo se genera —y se cobra— una")
