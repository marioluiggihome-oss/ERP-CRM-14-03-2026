# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
EL CONTADOR DE IA ERA MENSUAL: EL DÍA NO EXISTÍA, NO ES QUE ESTUVIERA ESCONDIDO.

El master, 14/09/2026: «¿podemos saber los tokens o usos de IA gastados al
día?», y a continuación «sí hazlo, y también por usuario y día».

Había UN documento por mes (`{"month": "2026-09"}`) y cada llamada le sumaba
encima. Se veía el mes entero y bien —tokens reales, imágenes, coste por
modelo, por tipo y por usuario— pero no había fecha en ninguna parte, así que
«cuánto se gastó ayer» o «qué día se disparó» no se podía contestar. Y los días
anteriores a este cambio NO se pueden recuperar: nunca se guardaron.

LO QUE ESTE CANDADO VIGILA, que es donde está el peligro:

1. QUE LO ESCRIBAN LOS DOS CONTADORES. Hay dos funciones que cuentan
   (`record_ai_usage` y `record_ai_tokens`). Poner el día solo en una es el
   fallo de siempre de este repo —el arreglo puesto en un sitio y no en el
   otro— y aquí no daría ningún error: el total del día saldría MENOR que el
   real y nadie lo notaría, porque no hay nada con lo que compararlo.

2. QUE EL MES NO SE TOQUE. Cambiar la clave del mes a día habría partido seis
   meses de histórico y roto el umbral, la bolsa de créditos y la pantalla del
   medidor, que leen el mes.

3. QUE EL CONTADOR NUNCA ROMPA LA LLAMADA DE IA. Es la regla de todo este
   módulo: si el contador falla, el render tiene que salir igual. Un contador
   que tumba un render que el cliente ya ha pagado es peor que no contar.

4. QUE EL DÍA Y EL MES NO SE SEPAREN. Si el día sumara cosas distintas del mes,
   los dos informes darían cifras que no cuadran y no habría forma de saber
   cuál miente.

CÓMO SE COMPRUEBA: EJECUTANDO el módulo real contra un doble de Mongo que
aplica los `$inc` de verdad, no leyendo si la palabra «day» está en el fichero.
Y el doble APLICA las operaciones —no las apunta y ya está—, porque un doble
más corto que la pieza real obliga a escribir el código peor de lo que se puede
(lección de la auditoría del 10/09, regla 35).
"""
import asyncio
import importlib
import os
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")


class _Coleccion:
    """Un doble que APLICA los `$inc` y los `$setOnInsert`, como Mongo."""

    def __init__(self):
        self.docs = {}
        self.fallar = False

    def _clave(self, filtro):
        return tuple(sorted(filtro.items()))

    async def update_one(self, filtro, cambios, upsert=False):
        if self.fallar:
            raise RuntimeError("Mongo no responde")
        k = self._clave(filtro)
        doc = self.docs.get(k)
        if doc is None:
            if not upsert:
                return
            doc = dict(cambios.get("$setOnInsert") or {})
            self.docs[k] = doc
        for campo, valor in (cambios.get("$inc") or {}).items():
            trozos = campo.split(".")
            d = doc
            for t in trozos[:-1]:
                d = d.setdefault(t, {})
            d[trozos[-1]] = d.get(trozos[-1], 0) + valor

    def find(self, filtro=None, *a, **k):
        """APLICA el filtro de rango, como lo haría Mongo.

        Antes lo ignoraba, y eso hacía que la prueba del rango de fechas
        pasara en verde SIN que el rango se ejerciera: el doble devolvía todos
        los días y el recorte de más arriba lo tapaba. Un doble más corto que
        la pieza real no prueba lo que dice probar (regla 35).
        """
        docs = list(self.docs.values())
        rango = (filtro or {}).get("day")
        if isinstance(rango, dict):
            if "$gte" in rango:
                docs = [d for d in docs if str(d.get("day", "")) >= rango["$gte"]]
            if "$lte" in rango:
                docs = [d for d in docs if str(d.get("day", "")) <= rango["$lte"]]
        elif rango is not None:
            docs = [d for d in docs if d.get("day") == rango]

        class _Cursor:
            def sort(self, campo, orden=1):
                docs.sort(key=lambda d: d.get(campo, ""), reverse=orden < 0)
                return self

            async def to_list(self, n):
                return docs[:n]
        return _Cursor()

    async def find_one(self, filtro, *a, **k):
        return self.docs.get(self._clave(filtro))


class _Db:
    def __init__(self):
        self.ai_usage = _Coleccion()
        self.ai_usage_diario = _Coleccion()
        self.ai_usage_config = _Coleccion()


@pytest.fixture()
def au():
    """El módulo REAL, con su `db` cambiada por el doble."""
    mod = importlib.import_module("services.ai_usage")
    importlib.reload(mod)
    mod.db = _Db()
    return mod


def _corre(c):
    """Cada llamada en su propio bucle.

    Con `asyncio.get_event_loop()` estas pruebas pasaban EN SOLITARIO y fallaban
    en la suite entera —«There is no current event loop»—, porque otra prueba
    deja el bucle cerrado y el orden de los ficheros decide quién va antes. Es
    el mismo tipo de trampa que la regla 25 (un doble que se queda en
    `sys.modules`): un candado que solo funciona según el orden no protege nada.
    """
    return asyncio.run(c)


def test_UNA_LLAMADA_SE_APUNTA_EN_EL_DIA_Y_EN_EL_MES():
    mod = importlib.import_module("services.ai_usage")
    importlib.reload(mod)
    mod.db = _Db()
    _corre(mod.record_ai_usage("render", user_id="u1"))
    mes = list(mod.db.ai_usage.docs.values())
    dia = list(mod.db.ai_usage_diario.docs.values())
    assert mes and mes[0]["total"] == 1, "el mes ha dejado de contar"
    assert dia, ("la llamada no se ha apuntado en ningún día: el informe diario "
                 "saldría vacío sin dar ningún error")
    assert dia[0]["total"] == 1
    assert dia[0]["day"] == mod._day()
    assert dia[0]["by_user"]["u1"] == 1, "no se guarda QUIÉN gastó ese día"


def test_LOS_DOS_CONTADORES_ESCRIBEN_EL_DIA():
    """`record_ai_tokens` es el que trae los tokens reales. Si solo contara el
    otro, el día enseñaría llamadas sin tokens ni coste."""
    mod = importlib.import_module("services.ai_usage")
    importlib.reload(mod)
    mod.db = _Db()
    _corre(mod.record_ai_tokens("render", "gemini-2.5-flash-image",
                                in_tokens=1000, out_tokens=500, images=2,
                                user_id="u2"))
    dia = list(mod.db.ai_usage_diario.docs.values())
    assert dia, "record_ai_tokens no escribe el día"
    d = dia[0]
    assert d["tokens_in"]["gemini-2_5-flash-image"] == 1000
    assert d["tokens_out"]["gemini-2_5-flash-image"] == 500
    assert d["images"]["gemini-2_5-flash-image"] == 2
    assert d["by_user"]["u2"] == 1


def test_EL_DIA_SUMA_EXACTAMENTE_LO_MISMO_QUE_EL_MES():
    """Dos cifras del mismo dinero que no cuadran es lo que este repo lleva
    evitando desde el principio."""
    mod = importlib.import_module("services.ai_usage")
    importlib.reload(mod)
    mod.db = _Db()
    for _ in range(3):
        _corre(mod.record_ai_tokens("render", "gemini-3-pro-image-preview",
                                    in_tokens=10, out_tokens=20, images=1,
                                    user_id="u3"))
    mes = list(mod.db.ai_usage.docs.values())[0]
    dia = list(mod.db.ai_usage_diario.docs.values())[0]
    for campo in ("total", "real_cost"):
        assert mes.get(campo) == dia.get(campo), (
            "el día y el mes no cuadran en «%s»: %s contra %s"
            % (campo, mes.get(campo), dia.get(campo)))
    assert mes["images"] == dia["images"]


def test_SI_EL_CONTADOR_DIARIO_FALLA_LA_LLAMADA_DE_IA_SIGUE():
    """Un contador que tumba un render ya cobrado es peor que no contar."""
    mod = importlib.import_module("services.ai_usage")
    importlib.reload(mod)
    mod.db = _Db()
    mod.db.ai_usage_diario.fallar = True
    _corre(mod.record_ai_usage("render", user_id="u4"))   # no puede lanzar
    _corre(mod.record_ai_tokens("render", "gemini-2.5-flash", in_tokens=5, user_id="u4"))
    mes = list(mod.db.ai_usage.docs.values())
    assert mes and mes[0]["total"] == 2, (
        "un fallo del contador diario se ha llevado por delante el del mes")


def test_EL_MES_SIGUE_GUARDANDOSE_POR_MES():
    """Cambiar la clave del mes a día partiría seis meses de histórico y
    rompería el umbral, la bolsa de créditos y la pantalla del medidor."""
    mod = importlib.import_module("services.ai_usage")
    importlib.reload(mod)
    mod.db = _Db()
    _corre(mod.record_ai_usage("vision", user_id="u5"))
    claves = list(mod.db.ai_usage.docs.keys())
    assert claves == [(("month", mod._month()),)], (
        "el contador mensual ha cambiado de clave: %s" % claves)


def test_EL_INFORME_DIARIO_TRAE_COSTE_Y_NOMBRES():
    mod = importlib.import_module("services.ai_usage")
    importlib.reload(mod)
    mod.db = _Db()
    _corre(mod.record_ai_tokens("render", "gemini-2.5-flash-image",
                                images=10, user_id="u6"))
    r = _corre(mod.get_usage_por_dia(30, {"u6": "Mario"}))
    assert r["dias"], "el informe diario sale vacío"
    d = r["dias"][0]
    assert d["images"] == 10
    assert d["cost_eur"] == pytest.approx(0.36, abs=1e-6), (
        "el coste del día no cuadra con la tarifa del modelo: %s" % d["cost_eur"])
    assert d["by_user"] == {"Mario": 1}, (
        "el informe enseña ids en vez de nombres: %s" % d["by_user"])
    assert r["por_usuario"][0]["nombre"] == "Mario"
    assert r["desde"] == mod._day(), "no se dice desde cuándo hay registro"


def test_UN_USUARIO_QUE_YA_NO_EXISTE_SALE_CON_SU_ID_Y_NO_SE_INVENTA_UN_NOMBRE():
    mod = importlib.import_module("services.ai_usage")
    importlib.reload(mod)
    mod.db = _Db()
    _corre(mod.record_ai_usage("render", user_id="borrado9"))
    r = _corre(mod.get_usage_por_dia(30, {}))
    assert r["dias"][0]["by_user"] == {"borrado9": 1}


def test_EL_COSTE_DEL_DIA_SE_RECALCULA_CON_LA_TARIFA_DE_HOY():
    """No se lee el importe acumulado: si se corrigiera una tarifa, el día
    seguiría con la vieja y no cuadraría con el mes."""
    mod = importlib.import_module("services.ai_usage")
    importlib.reload(mod)
    mod.db = _Db()
    _corre(mod.record_ai_tokens("render", "gemini-2.5-flash-image",
                                images=1, user_id="u7"))
    mod.MODEL_PRICES["gemini-2.5-flash-image"] = {"in": 0.0, "out": 0.0, "img": 1.0}
    try:
        r = _corre(mod.get_usage_por_dia(30, {}))
        assert r["dias"][0]["cost_eur"] == pytest.approx(1.0), (
            "el coste del día viene congelado del momento de la llamada")
    finally:
        importlib.reload(mod)


def test_LA_TARIFA_SE_ENCUENTRA_AUNQUE_MONGO_ESCAPE_EL_PUNTO():
    """EL FALLO QUE DESTAPÓ ESTE INFORME, y es del MES, no del día.

    Mongo no admite puntos en el nombre de un campo, así que al contar se
    guarda `gemini-2_5-flash-image`. El precio está bajo
    `gemini-2.5-flash-image`, y la tarifa se buscaba con la clave ESCAPADA: no
    casaba nunca, caía en el modelo por defecto y su `img` es 0,00 €. O sea que
    el «coste por modelo» del medidor enseñaba CERO euros de imágenes — que es
    justo donde está el dinero del Estudio 3D — mientras el total del mes sí
    era correcto. Dos cifras del mismo dinero sin cuadrar, y ninguna parecía un
    error.
    """
    mod = importlib.import_module("services.ai_usage")
    importlib.reload(mod)
    escapada = "gemini-2_5-flash-image"
    assert mod.modelo_de_clave(escapada) == "gemini-2.5-flash-image"
    assert mod.cost_of(escapada, images=10) == pytest.approx(0.36, abs=1e-6), (
        "la tarifa no se encuentra con la clave escapada: el coste por modelo "
        "vuelve a salir a 0,00 €")
    # Un modelo desconocido sale tal cual y cae en el precio por defecto, sin
    # inventarse una correspondencia.
    assert mod.modelo_de_clave("modelo-que-no-existe") == "modelo-que-no-existe"


def test_EL_RESUMEN_DEL_MES_TAMBIEN_COBRA_BIEN_POR_MODELO():
    """El arreglo puesto en el día y no en el mes no sería un arreglo."""
    mod = importlib.import_module("services.ai_usage")
    importlib.reload(mod)
    mod.db = _Db()
    _corre(mod.record_ai_tokens("render", "gemini-2.5-flash-image",
                                images=5, user_id="u8"))
    r = _corre(mod.get_usage_summary())
    costes = r["by_model"]["cost_eur"]
    assert costes, "el resumen del mes ya no desglosa coste por modelo"
    assert sum(costes.values()) == pytest.approx(0.18, abs=1e-6), (
        "el coste por modelo del MES sigue saliendo mal: %s" % costes)


def test_SI_FALLA_EL_CONTADOR_MENSUAL_TAMPOCO_SE_CAE_LA_LLAMADA():
    """La otra mitad: el contador entero es best-effort, no solo el diario."""
    mod = importlib.import_module("services.ai_usage")
    importlib.reload(mod)
    mod.db = _Db()
    mod.db.ai_usage.fallar = True
    _corre(mod.record_ai_usage("render", user_id="u9"))       # no puede lanzar
    _corre(mod.record_ai_tokens("render", "gemini-2.5-flash",
                                in_tokens=5, user_id="u9"))   # tampoco


def test_EL_CONTADOR_DIARIO_SE_TRAGA_SUS_PROPIOS_ERRORES():
    """Se llama DIRECTAMENTE para que no lo tape el `except` de quien lo usa:
    si un día se le llama desde un sitio sin red, tiene que aguantar solo."""
    mod = importlib.import_module("services.ai_usage")
    importlib.reload(mod)
    mod.db = _Db()
    mod.db.ai_usage_diario.fallar = True
    _corre(mod._suma_al_dia({"total": 1}, "u10"))   # no puede lanzar
    # Y sin base de datos tampoco.
    mod.db = None
    _corre(mod._suma_al_dia({"total": 1}, "u10"))


# ── Rango de fechas y desglose por tipo de IA ────────────────────────────────
#
# El master, 15/09/2026: «el gasto de IA, que lo pueda calcular por fechas,
# ahora sólo muestra el del día actual» y «q diga el gasto por tipos de IAS».
#
# Antes solo se podían pedir «los últimos N días» contando desde hoy, que no
# sirve para cerrar un mes ni para comparar dos semanas. Y el total que salía
# arriba era el del ÚLTIMO DÍA: al elegir un rango, la cifra grande habría
# seguido contestando a otra pregunta.


def _siembra(mod, dias_y_modelos):
    """Mete días a mano en el doble, saltándose el reloj.

    Hace falta porque el contador siempre escribe HOY: sin esto no se puede
    probar un rango de verdad, y un candado que solo mira un día no comprueba
    nada de lo que se pide aquí.
    """
    for dia, modelo, imagenes, tipo in dias_y_modelos:
        clave = modelo.replace(".", "_")
        mod.db.ai_usage_diario.docs[(("day", dia),)] = {
            "day": dia, "month": dia[:7], "total": 1,
            "by_kind": {tipo: 1}, "by_user": {"u1": 1},
            "calls": {clave: 1}, "images": {clave: imagenes},
            "tokens_in": {clave: 100}, "tokens_out": {clave: 50},
        }


def _mod():
    m = importlib.import_module("services.ai_usage")
    importlib.reload(m)
    m.db = _Db()
    return m


def test_SE_PUEDE_PEDIR_UN_RANGO_DE_FECHAS():
    mod = _mod()
    _siembra(mod, [
        ("2026-09-10", "gemini-2.5-flash-image", 1, "render"),
        ("2026-09-12", "gemini-2.5-flash-image", 1, "render"),
        ("2026-09-15", "gemini-2.5-flash-image", 1, "render"),
    ])
    r = _corre(mod.get_usage_por_dia(desde="2026-09-11", hasta="2026-09-13"))
    assert [d["day"] for d in r["dias"]] == ["2026-09-12"], (
        "el rango no recorta: salen días de fuera (%s)" % [d["day"] for d in r["dias"]])


def test_EL_RANGO_MANDA_SOBRE_LOS_ULTIMOS_N_DIAS():
    """Si `dias` siguiera mandando, pedir un mes entero devolvería 30 días
    contados desde hoy y el informe diría otra cosa de la que se pide."""
    mod = _mod()
    _siembra(mod, [("2026-01-%02d" % d, "gemini-2.5-flash-image", 1, "render")
                   for d in range(1, 29)])
    r = _corre(mod.get_usage_por_dia(dias=3, desde="2026-01-01", hasta="2026-01-28"))
    assert len(r["dias"]) == 28, (
        "el rango se ha quedado recortado por `dias`: %d" % len(r["dias"]))


def test_SIN_RANGO_SE_SIGUEN_DANDO_LOS_ULTIMOS_DIAS():
    """Quitar el filtro tiene que volver al comportamiento de siempre."""
    mod = _mod()
    _siembra(mod, [("2026-02-%02d" % d, "gemini-2.5-flash-image", 1, "render")
                   for d in range(1, 11)])
    r = _corre(mod.get_usage_por_dia(dias=4))
    assert len(r["dias"]) == 4


def test_EL_TOTAL_ES_DEL_RANGO_ENTERO_Y_NO_DEL_ULTIMO_DIA():
    """ESTE es el fallo que señaló el master: «ahora sólo muestra el del día
    actual»."""
    mod = _mod()
    _siembra(mod, [
        ("2026-03-01", "gemini-2.5-flash-image", 10, "render"),
        ("2026-03-02", "gemini-2.5-flash-image", 10, "render"),
    ])
    r = _corre(mod.get_usage_por_dia(desde="2026-03-01", hasta="2026-03-02"))
    # 20 imágenes x 0,036 EUR, más los tokens de los dos días.
    assert r["total"]["imagenes"] == 20, (
        "el total no suma el rango: %s" % r["total"])
    assert r["total"]["cost_eur"] > 0.7, r["total"]
    assert r["total"]["dias"] == 2
    # Y las llamadas SE SUMAN. Sin esto, cambiar el `+=` por un `=` dejaba el
    # total con el del último día y la prueba pasaba igual: es justo el fallo
    # que el master señaló («sólo muestra el del día actual»).
    assert r["total"]["llamadas"] == 2, (
        "el total de llamadas no acumula el rango: %s" % r["total"])


def test_EL_GASTO_SE_DESGLOSA_POR_MOTOR_Y_POR_TIPO_DE_TRABAJO():
    """«Q diga el gasto por tipos de IAS». Son dos cortes distintos: QUÉ se le
    pidió a la IA y CON QUÉ se pintó, que es de donde sale el euro."""
    mod = _mod()
    _siembra(mod, [
        ("2026-04-01", "gemini-2.5-flash-image", 10, "render"),
        ("2026-04-02", "gemini-3-pro-image-preview", 10, "render"),
        ("2026-04-03", "gemini-2.5-flash", 0, "vision"),
    ])
    r = _corre(mod.get_usage_por_dia(desde="2026-04-01", hasta="2026-04-03"))
    modelos = {m["modelo"]: m for m in r["por_modelo"]}
    assert "gemini-2.5-flash-image" in modelos, (
        "el desglose por motor enseña la clave escapada de Mongo: %s" % list(modelos))
    assert modelos["gemini-2.5-flash-image"]["cost_eur"] == pytest.approx(0.36, abs=1e-3)
    assert modelos["gemini-3-pro-image-preview"]["cost_eur"] == pytest.approx(1.2, abs=1e-2)
    # Y ordenado por lo que más cuesta, que es lo que se mira primero.
    assert r["por_modelo"][0]["modelo"] == "gemini-3-pro-image-preview"
    assert r["por_tipo"] == {"render": 2, "vision": 1}


def test_UN_MOTOR_SIN_TARIFA_SE_MARCA_EN_VEZ_DE_DAR_UN_EURO_QUE_PARECE_FIRME():
    """Regla 7: un dato que no se sabe no se rellena con algo plausible. Aquí
    el coste cae en la tarifa por defecto, así que se DICE."""
    mod = _mod()
    _siembra(mod, [("2026-05-01", "modelo-que-nadie-ha-tarifado", 5, "render")])
    r = _corre(mod.get_usage_por_dia(desde="2026-05-01", hasta="2026-05-01"))
    assert r["por_modelo"][0]["tarifa_conocida"] is False
    # Y uno que sí está, marcado como conocido.
    mod2 = _mod()
    _siembra(mod2, [("2026-05-01", "gemini-2.5-flash-image", 5, "render")])
    r2 = _corre(mod2.get_usage_por_dia(desde="2026-05-01", hasta="2026-05-01"))
    assert r2["por_modelo"][0]["tarifa_conocida"] is True


def test_EL_RANGO_SE_FILTRA_EN_LA_BASE_DE_DATOS():
    """Traerse 180 días para tirar 170 va bien con pocos datos y deja de ir
    bien justo cuando hay historial, que es cuando hace falta."""
    mod = _mod()
    vistos = {}
    original = mod.db.ai_usage_diario.find

    def _espia(filtro=None, *a, **k):
        vistos["filtro"] = filtro
        return original(filtro, *a, **k)
    mod.db.ai_usage_diario.find = _espia
    _corre(mod.get_usage_por_dia(desde="2026-06-01", hasta="2026-06-30"))
    assert vistos["filtro"].get("day") == {"$gte": "2026-06-01", "$lte": "2026-06-30"}, (
        "el rango no llega a la consulta: se filtra en memoria")
