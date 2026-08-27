# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LOS CUATRO CABOS SUELTOS DE LA AUDITORÍA DEL 25/08/2026.

Cada uno era pequeño por separado, y por eso llevaban tiempo ahí.

  04. El router del Estudio 3D se quedaba SIN AUTENTICAR si fallaba un import.
  05. Un «relleno» de 195 cm pasaba por fabricable.
  06. `_sanea_distribucion`: código muerto que se inventaba medidas.
  08. El docstring de `_render_dispatch` seguía diciendo que el motor por
      defecto era Manus, apagado desde el 18/08.

El 08 parece cosmético y no lo es: el lío del 03/08 —el botón principal del
Estudio 3D saliéndose del motor elegido— empezó porque alguien se creyó lo que
ponía en un comentario. Una frase que miente es una trampa con retardo.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ESTUDIO = os.path.join(RAIZ, "routes", "estudio_cocinas.py")
RENDER3D = os.path.join(RAIZ, "services", "luiggi_ai", "render_3d.py")


def _lee(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


# ── 04 ───────────────────────────────────────────────────────────────────────
def test_el_estudio_3d_no_puede_arrancar_sin_autenticacion():
    """Si `require_auth` no se puede importar, el ERP NO ARRANCA. A propósito.

    Antes eso se tragaba con un `except` y el router se quedaba con
    `dependencies=[]`: todos los endpoints del Estudio 3D abiertos —render,
    planos, relación MV, volcado— sin una línea en el registro.
    """
    cuerpo = _lee(ESTUDIO)
    cabecera = cuerpo[:cuerpo.index("router = APIRouter(")]
    # Solo las líneas de CÓDIGO: el comentario que explica por qué se quitó el
    # respaldo cita el `_DEPS = []` que ya no debe existir, y sin esto la prueba
    # se cazaría a sí misma.
    codigo = "\n".join(l for l in cabecera.splitlines() if not l.lstrip().startswith("#"))
    assert "_DEPS = []" not in codigo, (
        "ha vuelto el respaldo que deja el router SIN AUTENTICAR. Un ERP que no "
        "arranca se arregla en cinco minutos; uno que arranca con la puerta "
        "abierta no se nota hasta que es tarde.")
    assert "from services.jwt_service import require_auth" in cabecera, (
        "el import de `require_auth` ya no es obligatorio")
    assert "dependencies=_DEPS" in cuerpo
    # Y que de verdad haya UNA dependencia, no una lista vacía.
    from routes import estudio_cocinas
    assert len(estudio_cocinas._DEPS) == 1, (
        f"el router va con {len(estudio_cocinas._DEPS)} dependencias de auth")


# ── 05 ───────────────────────────────────────────────────────────────────────
def _pared_con_hueco(ancho_pared, anchos_modulos):
    from services.kitchen_geometry import validar_distribucion
    elementos = []
    x = 0
    for i, w in enumerate(anchos_modulos):
        elementos.append({"id": f"bajo{i}", "ancho": w, "pared_idx": 0,
                          "posicion_cm": x, "medida_escrita": True})
        x += w
    return validar_distribucion({
        "paredes": [{"nombre": "P1", "ancho": ancho_pared, "alto": 240,
                     "ancho_escrito": True}],
        "elementos": elementos})


def test_un_relleno_de_casi_dos_metros_ya_no_pasa_por_bueno():
    """Si falta un mueble entero, se dice; no se tapa con «un relleno»."""
    r = _pared_con_hueco(300, [90, 15])   # faltan 195 cm
    assert r["ok"] is False, (
        "una pared con 195 cm sin muebles ha salido como válida. Un relleno es "
        "una tira de tablero de unos pocos centímetros; ahí cabe un mueble "
        "entero, y ese «relleno» puede acabar volcado al presupuesto como una "
        "línea de material.")
    texto = " ".join(r["avisos"])
    assert "195" in texto and ("falta" in texto.lower() or "sin ningún mueble" in texto), (
        f"no se explica qué pasa. Avisos: {r['avisos']}")


def test_el_relleno_de_verdad_SIGUE_funcionando():
    """La otra mitad: poner un tope no puede cargarse el caso legítimo.

    367 cm con tres muebles de 120 dejan 7 cm. Eso SÍ es un relleno, y es
    exactamente lo que se hace en obra.
    """
    r = _pared_con_hueco(367, [120, 120, 120])
    assert r["ok"] is True, f"un hueco de 7 cm debería cuadrarse solo: {r.get('motivo')}"
    rellenos = [e for e in r["elementos"] if e["id"] == "relleno"]
    assert len(rellenos) == 1 and rellenos[0]["ancho"] == 7, (
        f"se esperaba un relleno de 7 cm y hay {rellenos}")


@pytest.mark.parametrize("hueco", [10, 30, 60])
def test_los_huecos_razonables_se_siguen_rellenando(hueco):
    r = _pared_con_hueco(240 + hueco, [120, 120])
    assert r["ok"] is True, f"un hueco de {hueco} cm debería seguir siendo un relleno"


def test_el_tope_del_relleno_esta_escrito_y_no_a_ojo():
    from services.kitchen_geometry import RELLENO_MAXIMO
    assert RELLENO_MAXIMO == 60, (
        "el tope del relleno ha cambiado. 60 cm es el ancho de mueble más "
        "corriente: si en el hueco cabe un mueble entero, es que falta el mueble.")


# ── 06 ───────────────────────────────────────────────────────────────────────
def test_no_vuelve_la_funcion_que_se_inventaba_medidas():
    cuerpo = _lee(ESTUDIO)
    assert "def _sanea_distribucion" not in cuerpo, (
        "ha vuelto `_sanea_distribucion`. Ejecutándola salen un bajo de 180 cm y "
        "otro de 127 cm —ninguno existe— y una pared de 400 cm inventada, y se "
        "salta el validador entero. Para sanear está `validar_distribucion`.")


def test_toda_distribucion_que_sale_del_estudio_pasa_por_el_validador():
    """Las tres rutas que devuelven una distribución la validan antes."""
    cuerpo = _lee(ESTUDIO)
    for ruta in ("/detect-distribucion", "/validar-distribucion", "/distribucion-desde-texto"):
        i = cuerpo.index(f'@router.post("{ruta}")')
        # Hasta la SIGUIENTE ruta, no una ventana de tantos caracteres: la de
        # detectar lleva dentro un prompt larguísimo y una ventana fija se
        # quedaba corta, dando por bueno que no validaba cuando sí lo hace.
        siguiente = cuerpo.find("@router.", i + 10)
        trozo = cuerpo[i:siguiente if siguiente > 0 else len(cuerpo)]
        assert "validar_distribucion" in trozo, (
            f"la ruta {ruta} devuelve una distribución SIN validarla. Por ahí se "
            "cuela una medida imposible hasta un plano de taller.")


# ── 08 ───────────────────────────────────────────────────────────────────────
def test_el_docstring_del_reparto_de_motores_no_miente():
    cuerpo = _lee(RENDER3D)
    i = cuerpo.index("async def _render_dispatch")
    doc = cuerpo[i:i + 2500]
    assert "Por defecto MANUS" not in doc, (
        "el docstring vuelve a decir que el motor por defecto es Manus. La IA 2 "
        "está apagada desde el 18/08 y el defecto es Gemini. Así empezó el lío "
        "del 03/08: alguien se creyó un comentario.")
    assert "GEMINI" in doc.upper(), "el docstring ya no dice cuál es el motor por defecto"
