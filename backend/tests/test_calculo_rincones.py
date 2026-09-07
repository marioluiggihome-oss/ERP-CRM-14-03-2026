# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
ESCUADRA, CHAFLÁN Y CIEGO: TRES MUEBLES DE RINCÓN, NO TRES DIBUJOS.

El master, 07/09/2026, enseñando dos fotos: «necesito que el sistema Estudio 3D
distinga entre muebles en escuadra y mueble con chaflán».

POR QUÉ ESTO ES DINERO
──────────────────────
En la tarifa MV los tres existen, con ANCHO PROPIO y PRECIO PROPIO:

    ARC63D/I   chaflán           63 cm   54 pts (alto 70) · 58 (alto 90)
    ARI65D/I   escuadra indep.   65 cm   84 pts          · 90
    BRI95D/I   escuadra bajo     95 cm   88 pts

Con el valor de punto en 2, un alto de rincón a 90 sale a 116 € en chaflán y a
180 € en escuadra: **64 € en un solo mueble**, un 55 % más. Confundirlos no da
ningún error — da un presupuesto plausible y equivocado.

TRES COSAS QUE ESTABAN ROTAS ANTES DE ESTO, Y NINGUNA AVISABA
─────────────────────────────────────────────────────────────
1. `MAPA` de `distribucion_a_mv` NO TENÍA NI UN RINCÓN. Un mueble de esquina
   nunca llegaba a la relación MV: salía en «sin código», o sea que la esquina
   de la cocina no se pedía.
2. 63, 65 y 95 NO ESTÁN entre los anchos estándar de fabricación
   (15…120), así que un rincón que pasara por `snap_ancho` se convertía en un
   60 o en un 90 EN SILENCIO. A partir de ahí ni existe el código ni cuadra la
   pared.
3. EL ENCARGO DEL RENDER NO NOMBRABA LA FORMA. Aunque la distribución llevara
   el chaflán bien detectado, el modelo de imagen pintaba lo que le parecía —
   casi siempre una escuadra.

Y una cuarta que se vio al probarlo: sin `fila`, un ALTO de rincón caía en el
«bajo» por defecto y se tarifaba a 80 cm de alto, una altura que en MV no
existe para los altos (son 70 o 90).

LO QUE MV NO FABRICA SE DICE, NO SE SUSTITUYE. No hay BAJO rincón chaflán en su
tarifa. Cambiarlo por un escuadra a escondidas son 64 € y otro ancho, y en el
pedido no lo vería nadie.
"""
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKEND = os.path.join(RAIZ, "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)
os.environ.setdefault("JWT_SECRET", "test-secret-para-los-candados")

ESTUDIO = os.path.join(BACKEND, "routes", "estudio_cocinas.py")
RENDER = os.path.join(BACKEND, "services", "luiggi_ai", "render_3d.py")
JSX = os.path.join(RAIZ, "frontend", "src", "components", "AIRenderStudio.jsx")


def _texto(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


# ─── LOS TRES SON TRES ───────────────────────────────────────────────────────

def test_escuadra_y_chaflan_son_FORMAS_distintas():
    """Es lo que pidió el master, y lo que hay que poder dibujar."""
    from services import rincones as R
    assert R.forma_de("alto_rincon_escuadra") == "escuadra"
    assert R.forma_de("alto_rincon_escuadra_unidas") == "escuadra"
    assert R.forma_de("alto_rincon_chaflan") == "chaflan"
    assert R.forma_de("alto_rincon_chaflan_vitrina") == "chaflan"
    assert R.forma_de("alto_rincon_ciego") == "ciego"
    assert R.forma_de("bajo_rincon_escuadra") == "escuadra"
    assert R.forma_de("mueble") is None
    assert R.es_rincon("alto_rincon_chaflan") and not R.es_rincon("placa")


def test_la_fila_sale_del_TIPO_y_no_de_las_palabras():
    """«bajo_rincon_escuadra» y «alto_rincon_chaflan» llevan los dos la palabra
    «rincón»: adivinar la fila por el texto es jugársela."""
    from services import rincones as R
    assert R.fila_de("alto_rincon_chaflan") == "alto"
    assert R.fila_de("bajo_rincon_escuadra") == "bajo"
    assert R.fila_de("bajo_rincon_ciego") == "bajo"


def test_la_fila_DECLARADA_y_la_ADIVINADA_dicen_lo_mismo_HOY():
    """El aviso para el que añada un rincón nuevo.

    Con los ocho ids de hoy, adivinar la fila por el texto (`es_alto`) da la
    misma respuesta que la tabla, porque todos empiezan por «alto_» o «bajo_».
    Eso hace que quitar la tabla no rompa nada… hasta que alguien añada un id
    que no empiece así —«rincon_chaflan_superior», o uno con la etiqueta
    puesta al revés— y entonces la fila se elija por una palabra. Esta prueba
    es la que se pondrá roja ese día: o el id nuevo se deja deducir, o la
    tabla es la que manda y el resto del código tiene que preguntarle a ella.
    """
    from services import rincones as R
    from services.kitchen_geometry import es_alto
    for eid, t in R.TIPOS.items():
        adivinada = "alto" if es_alto(eid, t["label"]) else "bajo"
        assert adivinada == t["fila"], (
            f"«{eid}»: la tabla dice «{t['fila']}» y por el texto se deduce "
            f"«{adivinada}». A partir de aquí la fila TIENE que salir de "
            "`rincones.fila_de`, nunca de `es_alto`.")


def test_los_anchos_se_LEEN_DE_LA_TARIFA_y_no_de_una_lista_a_mano():
    """Una lista copiada se separa del catálogo el día que MV mueva una medida,
    y entonces diría que un mueble no existe cuando sí (o al revés, y entraría
    en un pedido un código que el proveedor no sirve)."""
    from services import rincones as R
    assert R.anchos_de("alto_rincon_chaflan") == [63]
    assert R.anchos_de("alto_rincon_escuadra") == [65]
    assert R.anchos_de("bajo_rincon_escuadra") == [95]
    assert R.ancho_fijo_de("alto_rincon_chaflan") == 63
    # Los ciegos se hacen en varias medidas: ahí NO se elige por el diseñador.
    assert len(R.anchos_de("bajo_rincon_ciego")) > 1
    assert R.ancho_fijo_de("bajo_rincon_ciego") is None
    assert R.anchos_de("no_existe") == []


def test_el_prefijo_AR_no_se_traga_los_ARC_ni_los_ARI():
    """«AR» es el ciego y «ARC» el chaflán. Buscar por «AR» a secas se llevaría
    los ARC, los ARCV, los ARI y los ARU, y el ciego saldría fabricándose en
    seis medidas que no son suyas."""
    from services import rincones as R
    ciego = set(R.anchos_de("alto_rincon_ciego"))
    assert 63 not in ciego, "se ha colado el chaflán (ARC63) en el ciego"
    assert ciego and ciego <= {60, 65}


# ─── EL ANCHO DE UN RINCÓN NO SE AJUSTA AL ESTÁNDAR ──────────────────────────

def test_63_65_y_95_NO_son_anchos_estandar():
    """Si algún día lo fueran, media prueba de aquí dejaría de significar
    nada."""
    from services.kitchen_geometry import ANCHOS_STD
    for a in (63, 65, 95):
        assert a not in ANCHOS_STD


def test_un_rincon_CONSERVA_su_ancho_de_catalogo():
    """`snap_ancho` los dejaría en 60, 60 y 90 sin decir una palabra, y a partir
    de ahí ni existe el código MV ni cuadra la pared."""
    from services.kitchen_geometry import validar_distribucion
    d = {"tipo": "l", "paredes": [{"ancho": 223}], "elementos": [
        {"id": "alto_rincon_chaflan", "label": "Chaflán", "pared_idx": 0,
         "posicion_cm": 0, "ancho": 63},
        {"id": "alto_rincon_escuadra", "label": "Escuadra", "pared_idx": 0,
         "posicion_cm": 63, "ancho": 65},
        {"id": "bajo_rincon_escuadra", "label": "Bajo", "pared_idx": 0,
         "posicion_cm": 128, "ancho": 95}]}
    anchos = {e["id"]: e.get("ancho") for e in validar_distribucion(d)["elementos"]}
    assert anchos["alto_rincon_chaflan"] == 63
    assert anchos["alto_rincon_escuadra"] == 65
    assert anchos["bajo_rincon_escuadra"] == 95


def test_un_rincon_mal_medido_se_AVISA_no_se_corrige_a_la_brava():
    """Un rincón que se ajusta solo acaba en el pedido siendo otro mueble."""
    from services.kitchen_geometry import validar_distribucion
    d = {"tipo": "l", "paredes": [{"ancho": 60}], "elementos": [
        {"id": "alto_rincon_chaflan", "label": "Chaflán", "pared_idx": 0,
         "posicion_cm": 0, "ancho": 60}]}
    r = validar_distribucion(d)
    assert r["elementos"][0]["ancho"] == 60, "se ha ajustado en silencio"
    assert any("63" in a for a in r["avisos"]), (
        "no se avisa de que MV lo hace de 63 cm")


def test_la_fila_del_rincon_llega_al_alzado():
    from services.kitchen_geometry import validar_distribucion
    d = {"tipo": "l", "paredes": [{"ancho": 158}], "elementos": [
        {"id": "alto_rincon_chaflan", "label": "Chaflán", "pared_idx": 0,
         "posicion_cm": 0, "ancho": 63},
        {"id": "bajo_rincon_escuadra", "label": "Bajo", "pared_idx": 0,
         "posicion_cm": 63, "ancho": 95}]}
    filas = {e["id"]: e.get("fila") for e in validar_distribucion(d)["elementos"]}
    assert filas["alto_rincon_chaflan"] == "alto"
    assert filas["bajo_rincon_escuadra"] == "bajo"


# ─── EL RINCÓN LLEGA A LA RELACIÓN MV ────────────────────────────────────────

def _relacion(elementos, ancho_pared=400):
    from services.distribucion_a_mv import distribucion_a_relacion
    return distribucion_a_relacion(
        {"tipo": "l", "paredes": [{"ancho": ancho_pared}], "elementos": elementos})


def test_cada_rincon_sale_con_SU_codigo_MV():
    """Antes de esto, `MAPA` no tenía ni un rincón: la esquina de la cocina no
    se pedía."""
    r = _relacion([
        {"id": "alto_rincon_chaflan", "label": "Chaflán", "pared_idx": 0, "ancho": 63},
        {"id": "alto_rincon_chaflan_vitrina", "label": "Vitrina", "pared_idx": 0, "ancho": 63},
        {"id": "alto_rincon_escuadra", "label": "Escuadra", "pared_idx": 0, "ancho": 65},
        {"id": "bajo_rincon_escuadra", "label": "Bajo", "pared_idx": 0, "ancho": 95}])
    codigos = [re.sub(r"[DI]$", "", ln["codigo"]) for ln in r["lineas"]]
    assert codigos == ["ARC63", "ARCV63", "ARI65", "BRI95"], codigos
    assert not r["sin_codigo"]


def test_un_ALTO_de_rincon_no_se_tarifa_a_la_altura_de_un_BAJO():
    """Sin `fila`, el alto caía en el «bajo» por defecto y salía a 80 cm — una
    altura que en MV no existe para los altos (son 70 o 90). Otro precio, sin
    ningún error."""
    r = _relacion([{"id": "alto_rincon_chaflan", "label": "Chaflán",
                    "pared_idx": 0, "ancho": 63}])
    assert r["lineas"][0]["alto"] in (70, 90)
    r2 = _relacion([{"id": "bajo_rincon_escuadra", "label": "Bajo",
                     "pared_idx": 0, "ancho": 95}])
    assert r2["lineas"][0]["alto"] == 80


def test_el_BAJO_CHAFLAN_se_DICE_que_no_existe_y_no_se_cambia_por_otro():
    """MV no lo fabrica. Sustituirlo por un escuadra son 64 € y otro ancho, y
    en el pedido no lo vería nadie."""
    r = _relacion([{"id": "bajo_rincon_chaflan", "label": "Bajo chaflán",
                    "pared_idx": 0, "ancho": 95}])
    assert not r["lineas"], "ha entrado un mueble que el proveedor no sirve"
    assert len(r["sin_codigo"]) == 1
    motivo = r["sin_codigo"][0]["motivo"]
    assert "chaflán" in motivo.lower() and "BRI" in motivo, motivo


def test_un_rincon_de_una_medida_que_MV_no_hace_no_se_inventa():
    r = _relacion([{"id": "alto_rincon_chaflan", "label": "Chaflán",
                    "pared_idx": 0, "ancho": 60}])
    assert not r["lineas"]
    assert "63" in r["sin_codigo"][0]["motivo"]


def test_chaflan_y_escuadra_NO_cuestan_lo_mismo():
    """Si costaran igual, todo esto sería estética. Son 64 € por mueble a
    altura 90 con el valor de punto en 2."""
    import json
    ruta = os.path.join(BACKEND, "data", "mv_tarifas_oficiales.json")
    with open(ruta, "r", encoding="utf-8") as f:
        t1 = json.load(f)["tariffs"]["T1"]
    def _pts(cod):
        for fam in t1.values():
            it = (fam.get("items") or {}).get(cod)
            if it is not None:
                return it
        raise AssertionError(f"{cod} no está en la tarifa T1")
    chaflan, escuadra = _pts("ARC63D/I"), _pts("ARI65D/I")
    assert chaflan != escuadra, (
        "el chaflán y la escuadra valen lo mismo: revisa la tarifa, porque toda "
        "esta distinción se hizo porque NO valen lo mismo")


# ─── LA IA TIENE QUE SABER DISTINGUIRLOS ─────────────────────────────────────

def test_el_encargo_de_DETECTAR_nombra_las_tres_formas():
    src = _texto(ESTUDIO)
    i = src.index("EL MUEBLE DEL RINCÓN")
    bloque = src[i:i + 1600]
    for palabra in ("ESCUADRA", "CHAFLÁN", "CIEGO", "45"):
        assert palabra in bloque, palabra
    for eid in ("alto_rincon_escuadra", "alto_rincon_chaflan",
                "alto_rincon_chaflan_vitrina", "bajo_rincon_escuadra"):
        assert eid in src, f"el id «{eid}» no se le ofrece al detector"


def test_el_detector_tiene_PROHIBIDO_adivinar_la_forma():
    """Elegir mal cambia el mueble y el precio. Sin esta frase, un modelo de
    lenguaje siempre elige: es lo que hacen."""
    src = _texto(ESTUDIO)
    i = src.index("EL MUEBLE DEL RINCÓN")
    bloque = src[i:i + 1600]
    assert "NO adivines" in bloque, (
        "falta el «si no se ve, no adivines»: el detector rellenará el hueco")


def test_el_encargo_del_RENDER_distingue_chaflan_de_escuadra():
    """Aunque la distribución lo detecte bien, el modelo de imagen pinta lo que
    le parezca si el encargo no lo nombra."""
    src = _texto(RENDER)
    i = src.index("CORNER CABINET SHAPE")
    bloque = src[i:i + 1200]
    assert "DIAGONALLY" in bloque and "45" in bloque
    assert "90-degree" in bloque and "BOTH fronts" in bloque
    assert "BLIND" in bloque or "CIEGO" in bloque
    assert "NEVER swap one for another" in bloque


def test_la_pantalla_MANDA_el_rincon_en_el_encargo():
    """Una frase escrita que no viaja en el prompt no existe."""
    src = _texto(JSX)
    assert "const rinconTexto = ()" in src
    i = src.index("const conMedidas = (desc)")
    cuerpo = src[i:i + 400]
    assert "rinconTexto()" in cuerpo, (
        "`rinconTexto` está escrita pero no entra en el encargo del render")


def test_la_pantalla_y_el_backend_LEEN_IGUAL_la_forma_del_rincon():
    """La pantalla saca la forma del id con `formaDeRincon` y el backend con
    `forma_de`. Si se separan, la pantalla le pide al render un chaflán y la
    relación pide una escuadra — y el cliente ve una cocina que no es la que se
    le fabrica."""
    from services import rincones as R
    src = _texto(JSX)
    i = src.index("const formaDeRincon = (id) =>")
    js = src[i:src.index("const rinconTexto", i)]
    for eid, forma in ((k, v["forma"]) for k, v in R.TIPOS.items()):
        # Se reproduce el mismo orden de comprobación que hace el JS.
        t = eid.lower()
        esperado = None
        if "rincon" in t:
            if "chaflan" in t:
                esperado = "chaflan"
            elif "escuadra" in t:
                esperado = "escuadra"
            elif "ciego" in t:
                esperado = "ciego"
        assert esperado == forma, (
            f"«{eid}»: el backend dice «{forma}» y el id no lo deja deducir; "
            "la pantalla leería otra cosa")
    assert "chaflan" in js and "escuadra" in js and "ciego" in js
