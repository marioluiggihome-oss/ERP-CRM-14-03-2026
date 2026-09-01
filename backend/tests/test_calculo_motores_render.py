# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO del motor de render. NO se cambia sin permiso del master.

Estas pruebas no comprueban un calculo: comprueban una PROMESA. El motor que se
elige en pantalla (IA 0/1/2/3/4/5/7) es una habilidad ya adquirida del Estudio 3D, y
cambiarla en silencio significa que el usuario cree seguir en su motor y no lo
esta. Paso el 03/08: al enrutar el boton principal por el render compuesto,
este llamaba directamente a Gemini estandar y se saltaba el motor elegido.

Si alguien —persona o IA— toca el reparto de motores o vuelve a saltarse el
repartidor, estas pruebas se ponen en rojo y el CI corta. Para cambiarlo hace
falta pedirselo al master y actualizar tambien este fichero, a proposito y
dejando constancia.

Mapa que se protege (frontend `providerOf()` -> backend `_render_dispatch`):
    IA 0 -> julio11         (camino histórico del 11/07/2026; solo master)
    IA 1 -> gemini          (Gemini estandar; el de siempre, y el UNICO que ve
                             un usuario que no sea master)
    IA 3 -> gemini_premium  (prompt ultra-fotorrealista)
    IA 7 -> julio11_plus    (IA0 + geometría/vanos y referencia de mayor detalle)

TRES QUE NO ESTAN EN LA TABLA DE ARRIBA, Y POR QUE (puesto al dia el 23/08/2026,
en una auditoria: la tabla llevaba desde el 18/08 diciendo algo que ya no era
verdad, y este fichero daba VERDE a un mapa que la casa ya no usaba).

· IA 2 (manus) ESTA APAGADA desde el 18/08, a peticion del master: no es un
  modelo de imagen sino un agente, y cada render se iba hasta cinco minutos.
  El motor sigue en el codigo detras de MOTOR_MANUS_ACTIVO. `providerOf()` ya
  no puede devolver 'manus' y el boton no sale en pantalla. Su candado es
  `test_calculo_ia2_apagada.py`. Aqui ya no se comprueba, porque comprobarlo
  aqui era justo el problema: estas pruebas sustituyen `_render_dispatch` por
  un doble, o sea que miran que la ETIQUETA llegue al repartidor, no que haya
  un motor detras. IA 2 seguia en verde tres dias despues de apagarse.

· IA 4 (gemini_flash) ESTA APAGADA desde el 24/08/2026, a peticion del master.
  Y no era un motor distinto: en `_render_dispatch` hacia
  `model_override="gemini-2.5-flash-image"`, que es EXACTAMENTE el modelo que
  la IA 1 usa por defecto. Mismo modelo, mismo encargo, misma imagen — mientras
  su etiqueta decia «Gemini Flash — rapido» y prometia una velocidad que no
  existia. Es el mismo caso que la IA 2: un boton que el master pulsaba
  creyendo que cambiaba de motor. Ya no sale en pantalla; la correspondencia
  'ia4' -> gemini_flash se queda en `providerOf()` porque hay proyectos
  guardados con ese motor y al abrirlos tienen que dar el render de siempre.
  Su candado es `test_calculo_ia4_apagada.py`.

· IA 5 (julio) NO es un motor: es el ENCARGO del 22/07/2026 con el motor de
  siempre. `generate_render_composed` lo intercepta antes del repartidor y
  llama a Gemini a proposito. Por eso no puede estar en `MOTORES` —esperar
  provider='julio' seria mentira— y su candado es `test_calculo_ia5_22julio.py`.

QUE MOTORES EXISTEN es cosa de `test_la_pantalla_ofrece_exactamente_estos_motores`,
mas abajo: si alguien añade un IA 8 o borra uno, esa se pone roja y este fichero
deja de poder quedarse antiguo en silencio.
"""
import asyncio
import importlib.util
import os
import re
import sys
import types

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Los motores que viajan TAL CUAL desde la pantalla hasta `_render_dispatch`.
# IA 2 e IA 4 (apagadas) e IA 5 (camino histórico alternativo) tienen su
# propio candado; ver la nota de arriba.
MOTORES = {
    "IA 0": "julio11",
    "IA 1": "gemini",
    "IA 3": "gemini_premium",
    "IA 7": "julio11_plus",
}

# Los motores ya no se anuncian en la interfaz: se conserva un único flujo
# predeterminado y no se expone el proveedor al usuario.
MOTORES_EN_PANTALLA_MASTER = set()
MOTORES_EN_PANTALLA_USUARIO = set()
MOTORES_INTERNOS = {
    "ia0": "julio11",
    "ia1": "gemini",
    "ia3": "gemini_premium",
    "ia5": "julio",
    "ia7": "julio11_plus",
}


@pytest.fixture()
def servicio(monkeypatch):
    """Carga el servicio de render con la configuracion simulada."""
    paquete = types.ModuleType("services")
    paquete.__path__ = [os.path.join(BACKEND, "services")]
    monkeypatch.setitem(sys.modules, "services", paquete)

    lai = types.ModuleType("services.luiggi_ai")
    lai.__path__ = [os.path.join(BACKEND, "services", "luiggi_ai")]
    monkeypatch.setitem(sys.modules, "services.luiggi_ai", lai)

    cfg = types.ModuleType("services.luiggi_ai.config")
    cfg.get_ai_config = lambda: types.SimpleNamespace(
        brand_name="Motor 3D", provider_api_key="", render_enabled=True,
        render_default_style="photorealistic")
    monkeypatch.setitem(sys.modules, "services.luiggi_ai.config", cfg)

    core = types.ModuleType("services.luiggi_ai.engine_core")
    core.get_engine = lambda: types.SimpleNamespace(
        _sanitize_response=lambda t: t)
    monkeypatch.setitem(sys.modules, "services.luiggi_ai.engine_core", core)

    spec = importlib.util.spec_from_file_location(
        "services.luiggi_ai.render_3d",
        os.path.join(BACKEND, "services", "luiggi_ai", "render_3d.py"))
    mod = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "services.luiggi_ai.render_3d", mod)
    spec.loader.exec_module(mod)
    return mod.Render3DService()


def _capturar_dispatch(servicio):
    """Sustituye el repartidor y devuelve una caja con lo que le llega."""
    caja = {}

    async def falso(task_prompt, prompt, parsed_params=None, **kw):
        caja.update(kw)
        caja["parsed_params"] = parsed_params
        return {"success": True, "result": {"images": ["data:image/png;base64,x"]}}

    servicio._render_dispatch = falso
    return caja


def _imagen():
    return "data:image/png;base64,iVBORw0KGgo="


@pytest.mark.parametrize("etiqueta,provider", sorted(MOTORES.items()))
def test_el_render_compuesto_respeta_el_motor_elegido(servicio, etiqueta, provider):
    """CANDADO: generar con plano NO puede cambiarte de motor por su cuenta."""
    caja = _capturar_dispatch(servicio)
    servicio._prepare_reference = lambda img, mime, **kw: ("iVBORw0KGgo=", "image/png")
    asyncio.run(servicio.generate_render_composed(
        description="cocina blanca", floor_plan=_imagen(), provider=provider))
    assert caja.get("provider") == provider, (
        f"{etiqueta} deberia renderizar con '{provider}' y se ha ido a "
        f"'{caja.get('provider')}'. Si el cambio es a proposito, pideselo al "
        f"master y actualiza este fichero.")


def test_el_render_compuesto_pasa_por_el_repartidor_de_motores(servicio):
    """Llamar directo a un motor concreto salta el reparto: prohibido."""
    fuente = open(os.path.join(
        BACKEND, "services", "luiggi_ai", "render_3d.py"), encoding="utf-8").read()
    ini = fuente.index("async def generate_render_composed")
    fin = fuente.index("def _is_sketch_reference", ini)
    cuerpo = fuente[ini:fin]
    assert "_render_dispatch" in cuerpo, "el render compuesto ya no reparte por motor"
    assert "_render_with_gemini(" not in cuerpo, (
        "el render compuesto vuelve a llamar directamente a Gemini y se salta "
        "el motor elegido en pantalla")


def test_el_tipo_de_proyecto_lo_manda_la_pantalla(servicio):
    """Con el tipo delante no se adivina del texto: cocina es cocina."""
    caja = _capturar_dispatch(servicio)
    servicio._prepare_reference = lambda img, mime, **kw: ("iVBORw0KGgo=", "image/png")
    asyncio.run(servicio.generate_render_composed(
        description="mueble a medida", floor_plan=_imagen(), project_type="bano"))
    tipo = (caja.get("parsed_params") or {}).get("space_type") or ""
    assert "bath" in tipo.lower() or "bano" in tipo.lower() or "baño" in tipo.lower(), \
        f"el tipo de proyecto se ha perdido por el camino (space_type={tipo!r})"


def test_las_referencias_de_acabado_viajan_con_el_plano(servicio):
    """Habilidad adquirida: plano y referencia se usan A LA VEZ."""
    caja = _capturar_dispatch(servicio)
    servicio._prepare_reference = lambda img, mime, **kw: ("iVBORw0KGgo=", "image/png")
    asyncio.run(servicio.generate_render_composed(
        description="", floor_plan=_imagen(), wall_sketches=[_imagen()],
        reference_images=[_imagen()]))
    assert len(caja.get("reference_images") or []) == 3, \
        "se ha perdido alguna imagen entre el plano, el alzado y la referencia"


def test_el_tope_de_imagenes_juntas_no_baja_de_siete(servicio):
    """El master lo subio a 7 a proposito: no se recorta sin pedirselo."""
    assert servicio.MAX_IMAGENES_COMPUESTAS >= 7


# ── Que motores EXISTEN, no solo a donde va cada uno ─────────────────────────

ESTUDIO_3D = os.path.join(
    os.path.dirname(BACKEND), "frontend", "src", "components", "AIRenderStudio.jsx")


def test_la_pantalla_no_expone_motores_ni_proveedores():
    """CANDADO: la interfaz no revela la tecnología interna utilizada."""
    fuente = open(ESTUDIO_3D, encoding="utf-8").read()
    assert "Render 3D IA" not in fuente
    assert ">Motor<" not in fuente
    assert ">IA 0<" not in fuente
    assert ">IA 1<" not in fuente
    assert "Motor principal (Gemini)" not in fuente
    assert "Motor Pro" not in fuente
    assert "motorUsado" not in fuente
    assert "motorDeRespaldo" not in fuente


def test_cada_motor_de_la_pantalla_tiene_a_donde_ir():
    """Un boton que no lleva a ningun sitio acaba en Gemini sin decirlo.

    `_render_dispatch` termina con un `return` a Gemini estandar para lo que no
    reconoce. Esta bien como red —mejor un render que un error— pero significa
    que un motor mal escrito NO da error: da un render del motor de siempre con
    la etiqueta de otro. O sea, exactamente lo que paso el 03/08."""
    fuente = open(os.path.join(ESTUDIO_3D), encoding="utf-8").read()
    ini = fuente.index("const providerOf = ()")
    cuerpo = fuente[ini:fuente.index("};", ini)]
    dispatch = open(os.path.join(
        BACKEND, "services", "luiggi_ai", "render_3d.py"), encoding="utf-8").read()
    for motor, expected in sorted(MOTORES_INTERNOS.items()):
        if motor == "ia1":
            assert "return 'gemini';" in cuerpo
            continue
        assert f"motor === '{motor}'" in cuerpo, (
            f"el motor interno {motor} ya no tiene traducción en providerOf()")
        provider = re.search(
            rf"motor === '{motor}'\) return '([a-z0-9_]+)'", cuerpo).group(1)
        assert provider == expected
        if motor == "ia5":
            continue  # se intercepta antes del repartidor
        assert f'provider == "{provider}"' in dispatch, (
            f"el provider interno '{provider}' no está contemplado en el backend")
