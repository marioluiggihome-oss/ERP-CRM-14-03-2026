# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""Contador de consumo de IA.

Registra CADA llamada al motor de IA (render, visión, texto, chat, búsqueda) en un
único punto (el servicio central llm_vision) e incrementa un contador mensual en
Mongo. El master puede consultarlo y fijar un umbral de alerta por exceso de uso.

Diseño defensivo: si algo falla al contar, NUNCA debe romper la llamada de IA.
"""
import contextvars
from datetime import datetime, timezone

try:
    from config import db  # instancia global de la base de datos
except Exception:  # pragma: no cover
    db = None


# ─── QUIÉN ESTÁ GASTANDO ─────────────────────────────────────────────────────
#
# El master, 15/09/2026, viendo la columna «QUIÉN» con un punto: «que ponga los
# usuarios que la han utilizado».
#
# Y no salía nadie porque NUNCA se guardó: de las doce llamadas que registran
# consumo de IA, NI UNA pasaba el usuario. Solo lo hacía la de diagnóstico del
# panel de admin. O sea que el reparto por usuario —el del día y también el del
# MES, que lleva ahí desde el principio— ha estado siempre vacío, sin dar
# ningún error: se veía un cero y parecía que nadie había gastado.
#
# POR QUÉ UNA VARIABLE DE CONTEXTO Y NO AÑADIR UN PARÁMETRO: quien registra es
# `llm_vision`, una pieza de abajo del todo que NO sabe quién ha entrado —le
# llega un prompt y una imagen—. Pasarle el usuario obligaría a cambiar la
# firma de toda la cadena y a acordarse en los doce sitios; el día que se
# olvide uno, ese consumo se cuenta sin dueño y nadie lo nota. Con una variable
# de contexto se pone en UN sitio (al comprobar la sesión) y se lee en UNO.
#
# `contextvars` es lo correcto aquí y no una variable global: cada petición
# corre en su propia tarea de asyncio con su propio contexto, así que dos
# peticiones a la vez NO se pisan el usuario. Una global sí lo haría, y el
# consumo acabaría apuntado al bolsillo de otro.
_usuario_en_curso: contextvars.ContextVar = contextvars.ContextVar(
    "usuario_en_curso", default=None)


def fijar_usuario_en_curso(user_id):
    """Lo llama la comprobación de sesión, que es donde se sabe quién entra."""
    try:
        _usuario_en_curso.set(str(user_id) if user_id else None)
    except Exception:
        pass   # el contador nunca puede tumbar una petición


def usuario_en_curso():
    try:
        return _usuario_en_curso.get()
    except Exception:
        return None


def _month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _day() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ─── EL DÍA SE GUARDA APARTE, Y ESO ES TODO EL INVENTO ───────────────────────
#
# El master, 14/09/2026: «¿podemos saber los tokens o usos de IA gastados al
# día?, y también por usuario y día».
#
# No se podía: el contador llevaba UN documento por MES (`{"month": "2026-09"}`)
# y cada llamada le sumaba encima. O sea que el mes se veía entero y el día no
# existía — y no es que estuviera escondido: no se guardaba, así que los días
# pasados no se pueden recuperar de ninguna manera.
#
# POR QUÉ UN DOCUMENTO NUEVO Y NO CAMBIAR LA CLAVE DEL MES: cambiarla a
# `%Y-%m-%d` habría partido el histórico en dos —seis meses de datos que dejan
# de sumar— y habría roto la pantalla del medidor, el umbral y la bolsa de
# créditos, que leen el mes. El mes se queda EXACTAMENTE como estaba; el día va
# al lado.
#
# LOS DOS CONTADORES TIENEN QUE ESCRIBIRLO. Hay dos funciones que cuentan
# (`record_ai_usage` y `record_ai_tokens`), y poner el día solo en una es el
# fallo de siempre en este repo: la mitad de las llamadas no saldrían en el
# informe y el total del día sería MENOR que el real, sin dar ningún error.
# Por eso existe `_suma_al_dia`, que se llama desde las dos.
async def _suma_al_dia(inc: dict, user_id: str = None):
    """Suma lo mismo que al mes, pero en el documento del día. Best-effort.

    NUNCA puede romper la llamada de IA: si el contador falla, el render tiene
    que salir igual. Es la misma regla que el resto de este módulo.
    """
    if db is None or not inc:
        return
    try:
        # POR USUARIO Y DÍA, que es lo que contesta «quién está gastando»: el
        # `inc` que llega ya trae su `by_user.<id>`, el mismo que va al mes. Se
        # copia tal cual a propósito (ver abajo).
        propio = dict(inc)
        dia = _day()
        await db.ai_usage_diario.update_one(
            {"day": dia},
            {"$inc": propio, "$setOnInsert": {"day": dia, "month": _month()}},
            upsert=True,
        )
    except Exception:
        pass


# ─── Tarifas de referencia (EUR) para el cálculo de coste ────────────────────
# €/1M tokens de entrada y salida, y €/imagen para los modelos de imagen.
# Precios de lista (Nivel de pago) aproximados; ajustables por el master.
MODEL_PRICES = {
    "gemini-2.5-flash":              {"in": 0.28, "out": 2.30, "img": 0.0},
    "gemini-flash-latest":           {"in": 0.28, "out": 2.30, "img": 0.0},
    "gemini-3-flash-preview":        {"in": 0.28, "out": 2.30, "img": 0.0},
    "gemini-2.5-pro":                {"in": 1.15, "out": 9.25, "img": 0.0},
    "gemini-2.5-flash-image":        {"in": 0.28, "out": 2.30, "img": 0.036},
    "gemini-2.5-flash-image-preview":{"in": 0.28, "out": 2.30, "img": 0.036},
    "gemini-3-pro-image-preview":    {"in": 2.00, "out": 12.0, "img": 0.12},
    # IA PREMIUM (OpenAI): Astra dirige la composición y Sunburst pinta.
    #
    # PENDIENTE DE CONFIRMAR CON LA FACTURA REAL. Va escrito aquí porque un
    # motor sin precio cuenta como 0,00 € en el informe de Consumo de IA: no
    # daría ningún error, simplemente el motor más caro sería el que menos
    # parece gastar. Mejor una cifra marcada como aproximada que un cero que
    # miente. Cuando llegue la primera factura de OpenAI, se cuadra.
    "gpt-6-astra":                   {"in": 5.00, "out": 25.0, "img": 0.0},
    # LA IMAGEN DE OPENAI NO ES UNA LÍNEA DE FACTURA. Se genera como
    # HERRAMIENTA dentro de un `responses.create`, así que OpenAI la cobra en
    # los tokens de esa respuesta —que ya se apuntan bajo el modelo director— y
    # en su panel de Usage sale «0 images, 0 requests» (master, 15/09/2026).
    # Cobrar aquí 0,17 € por imagen era sumar un importe inventado ENCIMA del
    # coste real. Se deja a 0: la imagen se sigue CONTANDO para saber el
    # volumen, pero el euro sale de los tokens, que es como se factura.
    "gpt-image-2.5-sunburst":        {"in": 5.00, "out": 30.0, "img": 0.0},
    "black-forest-labs/flux-1.1-pro":{"in": 0.00, "out": 0.00, "img": 0.04},
    # WHISPER SE TARIFA POR MINUTO DE AUDIO, no por tokens ni por imágenes
    # (master, 15/09/2026: «cuenta el whisper también»). Es la única dimensión
    # que esta tabla no tenía, y por eso el dictado del servidor no se apuntaba
    # en ningún sitio: no había dónde ponerlo. `min` son €/minuto; los demás
    # modelos no la traen y `cost_of` la pide con `.get`, así que añadirla aquí
    # no toca el precio de ninguno.
    "whisper-1":                     {"in": 0.00, "out": 0.00, "img": 0.0, "min": 0.0055},
}
# Coste estimado por TIPO de llamada cuando no se miden tokens reales.
DEFAULT_COST_PER = {"render": 0.12, "vision": 0.003, "otro": 0.003}


def modelo_de_clave(clave: str) -> str:
    """Devuelve el nombre REAL del modelo a partir de como se guarda en Mongo.

    OJO, QUE ESTO ERA UN FALLO DE VERDAD y llevaba tiempo puesto. Mongo no
    admite puntos en el nombre de un campo, así que al contar se guarda
    `gemini-2_5-flash-image`. Pero el precio está en `MODEL_PRICES` bajo
    `gemini-2.5-flash-image`, y la tarifa se buscaba con la clave ESCAPADA: no
    casaba nunca, caía en el modelo por defecto y su `img` es 0,00 €.

    Resultado: el «coste por modelo» del medidor ha estado enseñando **0 € de
    imágenes** para todos los modelos —que es justo donde está el dinero del
    Estudio 3D—. No daba ningún error, y el total del mes (`real_cost`) sí es
    correcto porque se calcula al escribir, con el nombre bien: o sea que las
    dos cifras no cuadraban entre sí y no había forma de saber cuál mentía.

    Se destapó al escribir el informe por día, comparando el coste del día con
    la tarifa a mano.

    No se adivina nada: se escapan las claves de `MODEL_PRICES` igual que al
    guardar y se busca la que coincide. Un modelo que no esté en la tabla sale
    tal cual.
    """
    if clave in MODEL_PRICES:
        return clave
    for modelo in MODEL_PRICES:
        if modelo.replace(".", "_") == clave:
            return modelo
    return clave


def cost_of(model: str, in_tokens: int = 0, out_tokens: int = 0, images: int = 0,
            segundos: float = 0) -> float:
    """Coste (EUR) de una llamada a partir de tokens, imágenes y/o segundos de audio.

    UNA IMAGEN NO SE COBRA DOS VECES (master, 15/09/2026: «mira la otra IA,
    tiene que cuadrar», con el consumo de Google y el de OpenAI delante).

    Los dos proveedores facturan la imagen generada COMO TOKENS DE SALIDA. El
    precio por imagen de esta tabla es ese mismo coste dicho de otra forma —una
    imagen de `gemini-2.5-flash-image` son ~1.290 tokens de salida, y eso es lo
    que valen los 0,036 €—. Hasta hoy se sumaban LAS DOS COSAS: los tokens de
    salida A PRECIO DE TEXTO más el precio por imagen, así que el mismo dibujo
    se pagaba dos veces en el informe. Nadie lo notaba porque el sobrante era
    pequeño y el total seguía pareciendo razonable.

    Ahora, cuando la llamada devuelve imágenes, el precio por imagen SUSTITUYE
    al de los tokens de salida — que son la imagen. Los de ENTRADA se siguen
    cobrando aparte: eso es el encargo, y se paga igual.

    OJO CON EL ORDEN: esto solo aplica si el modelo tiene precio por imagen. Un
    modelo de texto que por lo que sea devuelva `images=1` sigue cobrando sus
    tokens, que es lo correcto.

    EL AUDIO SE PAGA POR MINUTO Y SE SUMA APARTE (master, 15/09/2026: «cuenta
    el whisper también»). Whisper no da tokens ni imágenes: da minutos, y esa
    dimensión no existía en esta función — por eso el dictado del servidor no
    se apuntaba en ningún sitio, ni siquiera como llamada. Se SUMA, no
    sustituye a nada: un modelo que un día cobrara tokens Y audio pagaría los
    dos, que es lo que haría el proveedor.

    Y LOS SEGUNDOS SALEN DEL PROVEEDOR, NUNCA DEL TAMAÑO DEL FICHERO. Un webm
    de 300 KB pueden ser diez segundos o dos minutos según cómo comprima el
    móvil: deducir la duración del peso sería inventarse una cifra (regla 7).
    Si la respuesta no trae la duración, `segundos` llega a 0 y la llamada se
    cuenta con coste 0 — se ve el VOLUMEN aunque no se pueda poner el euro.
    """
    p = MODEL_PRICES.get(modelo_de_clave(model or ""), MODEL_PRICES["gemini-2.5-flash"])
    n_img = int(images or 0)
    coste = (int(in_tokens or 0) / 1_000_000) * p["in"]
    if n_img and p["img"]:
        coste += n_img * p["img"]          # la imagen YA son los tokens de salida
    else:
        coste += (int(out_tokens or 0) / 1_000_000) * p["out"]
    coste += (float(segundos or 0) / 60.0) * p.get("min", 0.0)
    return round(coste, 6)


async def record_ai_tokens(kind: str, model: str, in_tokens: int = 0, out_tokens: int = 0,
                           images: int = 0, user_id: str = None, count: bool = True,
                           segundos: float = 0):
    """Registra el consumo REAL de una llamada: tokens por modelo y coste exacto
    acumulado del mes. Best-effort (nunca rompe la llamada de IA).

    count=True suma también 1 al total y a by_kind (llamada nueva). Usar count=False
    cuando la llamada YA se contó con record_ai_usage() y solo queremos añadir el
    coste/tokens (evita el doble conteo).

    Si no se dice el usuario, se coge el de la sesión en curso: quien registra
    es una pieza de abajo del todo que no sabe quién ha entrado (ver
    `usuario_en_curso`)."""
    user_id = user_id or usuario_en_curso()
    if db is None:
        return
    try:
        eur = cost_of(model, in_tokens, out_tokens, images, segundos)
        mdl = (model or "otro").replace(".", "_")
        inc = {
            f"tokens_in.{mdl}": int(in_tokens or 0),
            f"tokens_out.{mdl}": int(out_tokens or 0),
            f"images.{mdl}": int(images or 0),
            f"calls.{mdl}": 1,
            "real_cost": eur,
        }
        # Los SEGUNDOS de audio solo se apuntan si los hay. Si se metieran
        # siempre, todos los modelos de texto y de imagen estrenarían un
        # `seconds.<modelo>` a cero y el informe se llenaría de una columna
        # vacía que no significa nada.
        if segundos:
            inc[f"seconds.{mdl}"] = float(segundos)
        if count:
            inc["total"] = 1
            inc[f"by_kind.{kind or 'otro'}"] = 1
            if user_id:
                inc[f"by_user.{user_id}"] = 1
        await db.ai_usage.update_one(
            {"month": _month()},
            {"$inc": inc, "$setOnInsert": {"month": _month()}},
            upsert=True,
        )
        # Y lo mismo en el día. Se pasa el MISMO `inc` a propósito: si el día
        # sumara cosas distintas del mes, los dos informes dirían cifras que no
        # cuadran entre sí y no habría forma de saber cuál miente.
        await _suma_al_dia(inc, user_id if count else None)
    except Exception:
        pass


def usage_from_response(resp):
    """Extrae (in_tokens, out_tokens) de la respuesta de google-genai. Best-effort."""
    um = getattr(resp, "usage_metadata", None)
    if not um:
        return 0, 0
    return int(getattr(um, "prompt_token_count", 0) or 0), int(getattr(um, "candidates_token_count", 0) or 0)


async def record_ai_usage(kind: str, user_id: str = None):
    """Suma 1 al contador del mes en curso (total y por tipo). Best-effort.

    Si no se dice el usuario, se coge el de la sesión en curso."""
    user_id = user_id or usuario_en_curso()
    if db is None:
        return
    try:
        inc = {"total": 1, f"by_kind.{kind or 'otro'}": 1}
        if user_id:
            inc[f"by_user.{user_id}"] = 1
        await db.ai_usage.update_one(
            {"month": _month()},
            {"$inc": inc, "$setOnInsert": {"month": _month()}},
            upsert=True,
        )
        await _suma_al_dia(inc, user_id)
    except Exception:
        pass  # el contador nunca bloquea una llamada de IA


async def get_usage_summary():
    """Resumen del mes en curso + histórico (6 meses) + umbral, coste estimado y alerta."""
    if db is None:
        return {"total": 0, "by_kind": {}, "threshold": 0, "over": False, "pct": 0, "history": [], "cost": {}}
    month = _month()
    cur = await db.ai_usage.find_one({"month": month}) or {"month": month, "total": 0, "by_kind": {}}
    cfg = await db.ai_usage_config.find_one({"_id": "cfg"}) or {}
    threshold = int(cfg.get("threshold", 0) or 0)
    total = int(cur.get("total", 0) or 0)
    by_kind = cur.get("by_kind", {})
    # Coste ESTIMADO: nº de llamadas por tipo × coste unitario (€). Si el master no
    # ha configurado tarifas, se usan los valores por defecto precargados.
    cost_per = cfg.get("cost_per") or DEFAULT_COST_PER
    est = 0.0
    for k, n in by_kind.items():
        est += (float(cost_per.get(k, 0) or 0)) * int(n or 0)
    # Coste REAL acumulado del mes (medido con los tokens reales de cada llamada).
    real_cost = round(float(cur.get("real_cost", 0) or 0), 4)
    history = await db.ai_usage.find({}, {"_id": 0, "by_user": 0}).sort("month", -1).to_list(6)
    calls = cur.get("calls", {})
    tokens_in = cur.get("tokens_in", {})
    tokens_out = cur.get("tokens_out", {})
    images = cur.get("images", {})
    seconds = cur.get("seconds", {})
    model_keys = set(calls) | set(tokens_in) | set(tokens_out) | set(images) | set(seconds)
    cost_by_model = {
        model: cost_of(
            model,
            tokens_in.get(model, 0),
            tokens_out.get(model, 0),
            images.get(model, 0),
            seconds.get(model, 0),
        )
        for model in model_keys
    }
    return {
        "current_month": month,
        "total": total,
        "by_kind": by_kind,
        "threshold": threshold,
        "over": threshold > 0 and total >= threshold,
        "warn": threshold > 0 and total >= threshold * 0.8,
        "pct": round(total / threshold * 100, 1) if threshold else 0,
        "history": history,
        "cost_per": cost_per,
        "estimated_cost": round(est, 2),
        "real_cost": real_cost,
        "by_model": {
            "calls": calls,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "images": images,
            "seconds": seconds,
            "cost_eur": cost_by_model,
        },
        "spend_url": cfg.get("spend_url", ""),
        "master_credits": int(cfg.get("master_credits", CUPO_MASTER_POR_DEFECTO) or 0),
        "default_credits": int(cfg.get("default_credits", 0) or 0),
        "credits_per": cfg.get("credits_per", {"render": 1, "vision": 0}) or {"render": 1, "vision": 0},
    }


async def get_usage_por_dia(dias: int = 30, nombres_de_usuario=None,
                            desde: str = None, hasta: str = None):
    """El gasto de cada uno de los últimos días, y quién lo gastó.

    Master, 14/09/2026: «¿podemos saber los tokens o usos de IA gastados al
    día?, y también por usuario y día».

    EL COSTE SE VUELVE A CALCULAR AQUÍ, desde los tokens y las imágenes
    guardados, con la misma `cost_of` que usa el mes. No se lee el `real_cost`
    acumulado y ya está: si un día se corrigiera una tarifa de `MODEL_PRICES`,
    un importe guardado se quedaría con la tarifa vieja y el informe del día no
    cuadraría con el del mes — dos cifras del mismo dinero, que es lo que este
    repo lleva evitando desde el principio.

    `nombres_de_usuario` es un diccionario {id: nombre} opcional: el documento
    guarda ids, y un informe de «quién gasta» lleno de identificadores no lo
    lee nadie. Si no se puede resolver un id, sale el id — nunca se inventa un
    nombre.
    """
    if db is None:
        return {"dias": [], "por_usuario": [], "por_modelo": [], "por_tipo": {},
                "total": {}, "desde": None, "hasta": None}
    # RANGO DE FECHAS (master, 15/09/2026: «el gasto de IA, que lo pueda
    # calcular por fechas»). Sin rango solo se podía mirar «los últimos N días»
    # contando desde hoy, que no sirve para cerrar un mes ni para comparar dos
    # semanas. Las fechas se filtran en la BASE DE DATOS y no aquí: traerse
    # 180 días para tirar 170 va bien con pocos datos y deja de ir bien
    # justo cuando hay historial, que es cuando empieza a hacer falta.
    filtro = {}
    if desde or hasta:
        rango = {}
        if desde:
            rango["$gte"] = str(desde)[:10]
        if hasta:
            rango["$lte"] = str(hasta)[:10]
        filtro["day"] = rango
        n = 400            # un rango explícito manda sobre el «últimos N»
    else:
        n = max(1, min(int(dias or 30), 180))
    filas = await db.ai_usage_diario.find(filtro, {"_id": 0}).sort("day", -1).to_list(n)
    nombres = nombres_de_usuario or {}

    def _coste(doc):
        ti, to = doc.get("tokens_in", {}), doc.get("tokens_out", {})
        im, se = doc.get("images", {}), doc.get("seconds", {})
        return round(sum(cost_of(m, ti.get(m, 0), to.get(m, 0), im.get(m, 0), se.get(m, 0))
                         for m in set(ti) | set(to) | set(im) | set(se)), 4)

    dias_out, acumulado = [], {}
    for doc in filas:
        por_usuario = {}
        for uid, veces in (doc.get("by_user") or {}).items():
            por_usuario[nombres.get(uid, uid)] = int(veces or 0)
            acumulado[uid] = acumulado.get(uid, 0) + int(veces or 0)
        dias_out.append({
            "day": doc.get("day"),
            "total": int(doc.get("total", 0) or 0),
            "by_kind": doc.get("by_kind", {}),
            "cost_eur": _coste(doc),
            "tokens_in": sum(int(v or 0) for v in (doc.get("tokens_in") or {}).values()),
            "tokens_out": sum(int(v or 0) for v in (doc.get("tokens_out") or {}).values()),
            "images": sum(int(v or 0) for v in (doc.get("images") or {}).values()),
            "by_user": por_usuario,
        })
    # ─── EL DESGLOSE POR TIPO DE IA (master, 15/09/2026: «y q diga el gasto
    # por tipos de IAS»). Se suma TODO EL RANGO, no solo el último día.
    #
    # OJO CON LO QUE NO SE PUEDE HACER, y conviene decirlo en vez de fingirlo:
    # lo que se guarda es el MODELO, no el botón. Y varios botones comparten
    # modelo —IA 0 e IA 7 piden los dos el mismo—, así que de aquí NO se puede
    # sacar «cuánto se ha ido en IA 0» sin inventárselo. Para eso habría que
    # empezar a guardar también el motor; los días ya pasados no lo tendrían.
    por_modelo, por_tipo = {}, {}
    tot_llamadas = tot_imagenes = tot_in = tot_out = 0
    tot_coste = 0.0
    for doc in filas:
        for k, v in (doc.get("by_kind") or {}).items():
            por_tipo[k] = por_tipo.get(k, 0) + int(v or 0)
        ti, to = doc.get("tokens_in", {}), doc.get("tokens_out", {})
        im, ca = doc.get("images", {}), doc.get("calls", {})
        se = doc.get("seconds", {})
        for clave in set(ti) | set(to) | set(im) | set(ca) | set(se):
            m = por_modelo.setdefault(clave, {"llamadas": 0, "imagenes": 0,
                                              "tokens_in": 0, "tokens_out": 0,
                                              "segundos": 0.0})
            m["llamadas"] += int(ca.get(clave, 0) or 0)
            m["imagenes"] += int(im.get(clave, 0) or 0)
            m["tokens_in"] += int(ti.get(clave, 0) or 0)
            m["tokens_out"] += int(to.get(clave, 0) or 0)
            m["segundos"] += float(se.get(clave, 0) or 0)
        tot_llamadas += int(doc.get("total", 0) or 0)
    lista_modelos = []
    for clave, m in por_modelo.items():
        coste = cost_of(clave, m["tokens_in"], m["tokens_out"], m["imagenes"], m["segundos"])
        tot_coste += coste
        tot_imagenes += m["imagenes"]; tot_in += m["tokens_in"]; tot_out += m["tokens_out"]
        lista_modelos.append({
            "modelo": modelo_de_clave(clave), **m,
            "cost_eur": round(coste, 4),
            # Un modelo que no está en la tabla de precios cuenta con la tarifa
            # por defecto: se DICE, en vez de dar un euro que parece firme.
            "tarifa_conocida": modelo_de_clave(clave) in MODEL_PRICES,
        })
    lista_modelos.sort(key=lambda x: -x["cost_eur"])

    return {
        "por_modelo": lista_modelos,
        "por_tipo": por_tipo,
        "total": {
            "llamadas": tot_llamadas, "imagenes": tot_imagenes,
            "tokens_in": tot_in, "tokens_out": tot_out,
            "cost_eur": round(tot_coste, 4),
            "dias": len(filas),
        },
        "hasta": filas[0].get("day") if filas else None,
        "dias": dias_out,
        "por_usuario": sorted(
            ({"id": uid, "nombre": nombres.get(uid, uid), "llamadas": v}
             for uid, v in acumulado.items()),
            key=lambda x: -x["llamadas"]),
        # Se dice DESDE CUÁNDO hay datos. El contador diario empezó el
        # 14/09/2026: antes de esa fecha no hay nada, y un informe que enseña
        # cero sin decir por qué se lee como «ese día no se gastó».
        "desde": filas[-1].get("day") if filas else None,
    }


async def set_config(payload: dict):
    """Fija umbral, coste por tipo (€) y URL del panel del proveedor."""
    if db is None:
        return
    p = payload or {}
    upd = {}
    if "threshold" in p:
        upd["threshold"] = int(p.get("threshold", 0) or 0)
    if "cost_per" in p and isinstance(p["cost_per"], dict):
        upd["cost_per"] = {k: float(v or 0) for k, v in p["cost_per"].items()}
    if "spend_url" in p:
        upd["spend_url"] = str(p.get("spend_url") or "")
    if "default_credits" in p:
        upd["default_credits"] = int(p.get("default_credits", 0) or 0)
    if "credits_per" in p and isinstance(p["credits_per"], dict):
        upd["credits_per"] = {k: int(v or 0) for k, v in p["credits_per"].items()}
    # Cupo de las cuentas de la casa. 0 = ilimitado. Se toca desde Ajustes →
    # Consumo de IA; antes solo se podia cambiar editando el codigo, asi que el
    # master se quedaba sin renders y sin forma de seguir hasta el dia 1.
    if "master_credits" in p:
        upd["master_credits"] = max(int(p.get("master_credits", 0) or 0), 0)
    if upd:
        await db.ai_usage_config.update_one({"_id": "cfg"}, {"$set": upd}, upsert=True)


# Compatibilidad: fija solo el umbral.
async def set_threshold(threshold: int):
    await set_config({"threshold": threshold})


# ─── CRÉDITOS DE IA POR USUARIO (ligados a la suscripción) ───────────────────
# Roles con acceso ILIMITADO (nunca se les descuentan créditos).
_UNLIMITED_FLAGS = ("isAdmin", "isPrimaryAdmin", "isGerente", "isDirectorComercial", "isMaster")
# Cuentas de la casa (master/administrador). A estas SÍ se les puede poner cupo,
# para medir de primera mano lo que da de sí una bolsa de renders: con acceso
# ilimitado no se entera uno de cuánto se gasta ni de si el aviso de "sin
# renders" funciona.
_MASTER_FLAGS = ("isAdmin", "isPrimaryAdmin", "isMaster")
# OJO: esta lista NO es la de `services/master.py`, aunque se llame igual. Allí
# se decide quién ve el dinero de la casa; aquí, a quién se le puede poner cupo
# de renders para medir el gasto. Un administrador entra en las dos por motivos
# distintos, así que apretar aquella no aprieta esta — y unificarlas cambiaría
# los créditos de sitio sin que nadie lo hubiera pedido.
# Cupo del master. 0 = ilimitado (como antes). Se puede cambiar sin tocar código
# escribiendo `master_credits` en ai_usage_config.
CUPO_MASTER_POR_DEFECTO = 40


def _es_master(user: dict) -> bool:
    return bool(user) and any(user.get(f) for f in _MASTER_FLAGS)


async def _cupo_master() -> int:
    """Renders al mes para las cuentas de la casa. 0 = sin límite."""
    try:
        cfg = await db.ai_usage_config.find_one({"_id": "cfg"}) or {}
        v = cfg.get("master_credits", CUPO_MASTER_POR_DEFECTO)
        return max(int(v if v is not None else CUPO_MASTER_POR_DEFECTO), 0)
    except Exception:
        return CUPO_MASTER_POR_DEFECTO


async def _sin_limite(user: dict) -> bool:
    """¿Este usuario no gasta créditos?

    Dirección (gerente, director comercial) sigue sin límite. El master pasa a
    tener cupo si está configurado, para poder medirlo.
    """
    if not user:
        return False
    if not any(user.get(f) for f in _UNLIMITED_FLAGS):
        return False
    if _es_master(user):
        return await _cupo_master() <= 0
    return True


def _is_unlimited(user: dict) -> bool:
    """Compatibilidad para código que no puede esperar (no consulta la config).

    OJO: no distingue el cupo del master; usa `_sin_limite` donde se pueda.
    """
    if not user:
        return False
    return any(user.get(f) for f in _UNLIMITED_FLAGS)


async def _get_credits_config():
    cfg = await db.ai_usage_config.find_one({"_id": "cfg"}) or {}
    default_credits = int(cfg.get("default_credits", 0) or 0)
    credits_per = cfg.get("credits_per", {}) or {}
    # Valores por defecto: render cuesta 1 crédito, visión 0.
    if "render" not in credits_per:
        credits_per["render"] = 1
    if "vision" not in credits_per:
        credits_per["vision"] = 0
    return default_credits, credits_per


async def get_saldo_comprado(user_id: str) -> int:
    """Saldo de renders COMPRADOS que le queda al usuario.

    Vive en `ai_credit_balance`, una sola ficha por usuario y SIN mes: los packs
    se pagan aparte, asi que no caducan a fin de mes. Antes se guardaban en el
    campo `extra` de (user_id, month) y el dia 1 se evaporaba lo pagado y no
    consumido.
    """
    if db is None or not user_id:
        return 0
    try:
        doc = await db.ai_credit_balance.find_one({"user_id": str(user_id)}, {"_id": 0, "saldo": 1})
        return max(int((doc or {}).get("saldo", 0) or 0), 0)
    except Exception:
        return 0


async def get_user_credits(user: dict) -> dict:
    """Estado de créditos del usuario en el mes en curso.

    Hay tres bolsas y se gastan en este orden, de la que antes caduca a la que
    no caduca nunca:
      1. `asignados`  - los del plan, se renuevan cada mes y se pierden.
      2. `extraMes`   - packs antiguos guardados en el mes (formato heredado).
      3. `saldo`      - packs comprados, permanentes.

    Admin/master → ilimitado=True. Si el campo del usuario `aiCreditsMonthly`
    está a 0/vacío, se usa el default global `ai_usage_config.default_credits`.
    """
    if db is None:
        return {"asignados": 0, "consumidos_mes": 0, "restantes": 0, "ilimitado": True}
    if await _sin_limite(user):
        return {"asignados": 0, "consumidos_mes": 0, "restantes": 0, "ilimitado": True}

    default_credits, _ = await _get_credits_config()
    try:
        assigned = int(user.get("aiCreditsMonthly", 0) or 0)
    except (TypeError, ValueError):
        assigned = 0
    if assigned <= 0:
        assigned = default_credits
    # El cupo de la casa manda sobre el del plan: es el que se quiere medir.
    if _es_master(user):
        cupo = await _cupo_master()
        if cupo > 0:
            assigned = cupo

    uid = str(user.get("id") or user.get("_id") or "")
    consumed = 0
    extra_mes = 0
    try:
        doc = await db.ai_credits.find_one({"user_id": uid, "month": _month()})
        consumed = int((doc or {}).get("consumed", 0) or 0)
        # Formato heredado: packs concedidos al mes en curso antes de que el
        # saldo fuera permanente. Se siguen respetando hasta que se agoten.
        extra_mes = int((doc or {}).get("extra", 0) or 0)
    except Exception:
        consumed = 0

    saldo = await get_saldo_comprado(uid)
    # `consumed` cuenta TODO el consumo del mes, incluido lo que ya se descontó
    # del saldo comprado; sin ese ajuste se restaría dos veces.
    gastado_de_saldo = 0
    try:
        gastado_de_saldo = int((doc or {}).get("gastado_saldo", 0) or 0)
    except Exception:
        gastado_de_saldo = 0
    consumido_del_mes = max(consumed - gastado_de_saldo, 0)

    restante_plan = max(assigned + extra_mes - consumido_del_mes, 0)
    return {
        "asignados": assigned,
        "extra": extra_mes,
        "saldo": saldo,
        "total": assigned + extra_mes + saldo,
        "consumidos_mes": consumed,
        "restantes": restante_plan + saldo,
        "ilimitado": False,
    }


def mensaje_sin_creditos(user: dict, credits: dict) -> str:
    """Aviso de bolsa agotada, dicho a quien lo lee.

    A un cliente hay que decirle que hable con su administrador. Al master eso
    no le sirve de nada: el administrador ES él, y quedarse mirando el mensaje
    sin saber dónde se toca el cupo es exactamente lo que pasaba.
    """
    bolsa = int((credits or {}).get("asignados", 0) or 0)
    base = f"Sin créditos de IA: has agotado tu bolsa mensual ({bolsa})."
    if _es_master(user):
        return (f"{base} Es el cupo que te pusiste para medir: cámbialo o "
                f"reinicia la bolsa en Ajustes → Consumo de IA.")
    return f"{base} Contacta con tu administrador."


async def reiniciar_consumo_mes(user_id: str) -> bool:
    """Pone a cero lo consumido ESTE MES por un usuario.

    Es el "vuelve a empezar" de la bolsa mensual, sin esperar al día 1 y sin
    tocar el saldo comprado (que es dinero pagado y vive aparte, en
    `ai_credit_balance`). Sirve para que el master no se quede tirado cuando
    agota el cupo que él mismo se puso para medir.
    """
    if db is None or not user_id:
        return False
    try:
        await db.ai_credits.update_one(
            {"user_id": str(user_id), "month": _month()},
            {"$set": {"consumed": 0, "gastado_saldo": 0,
                      "reiniciado": datetime.now(timezone.utc).isoformat()},
             "$setOnInsert": {"user_id": str(user_id), "month": _month()}},
            upsert=True,
        )
        return True
    except Exception:
        return False


async def añadir_saldo(user_id: str, renders: int) -> int:
    """Suma saldo permanente conservando marca/tenant en la misma contabilidad."""
    if db is None or not user_id or renders <= 0:
        return await get_saldo_comprado(user_id)
    metadata = {}
    try:
        from services.plataformas import organizacion_de, plataforma_de
        owner = await db.users.find_one({"id": str(user_id)}, {"_id": 0}) or {}
        metadata = {
            "plataforma": plataforma_de(owner),
            "organizationId": organizacion_de(owner),
        }
    except Exception:
        metadata = {}
    await db.ai_credit_balance.update_one(
        {"user_id": str(user_id)},
        {"$inc": {"saldo": int(renders)},
         "$set": {"updatedAt": datetime.now(timezone.utc).isoformat(), **metadata},
         "$setOnInsert": {"user_id": str(user_id)}},
        upsert=True,
    )
    return await get_saldo_comprado(user_id)


# ─── Lo que cuesta cada motor, en créditos ───────────────────────────────────
#
# El mapa admite factores diferentes por perfil. IA0 y la prueba mejorada
# comparten coste; el factor 3,3 se conserva solo para el perfil legado Pro.
#
# Los números salen de la propia nota del repositorio: banana_pro es «3,3x por
# render». Se redondea HACIA ARRIBA al descontar, que es como se cobra: nadie
# regala el trozo suelto.
COSTE_POR_MOTOR = {
    # IA PREMIUM (ChatGPT). Por decisión comercial del master, cada generación
    # descuenta un único crédito igual que el resto. Su coste real para la
    # empresa se sigue mostrando por separado en MASTER → Consumo IA.
    "chatgpt": 1.0,
    "julio11": 1.0,
    "julio11_plus": 1.0,
    "banana_pro": 3.3,
    "flux": 1.0,
    "manus": 1.0,
    "gemini": 1.0,
    "gemini_premium": 1.0,
}


def coste_de_motor(kind: str, base: float, motor) -> int:
    """Créditos que cuesta una llamada, contando con el motor que la ha hecho."""
    import math
    if kind != "render" or not motor:
        return int(base)
    factor = COSTE_POR_MOTOR.get(str(motor).strip().lower(), 1.0)
    return int(math.ceil(float(base) * factor))


async def consume_credits(user: dict, kind: str, motor=None) -> dict:
    """Descuenta el coste (en créditos) de una llamada de tipo `kind`.

    Se gasta primero lo del plan (que caduca a fin de mes) y solo cuando se
    agota se toca el saldo comprado, que no caduca. Al revés, un cliente podría
    perder renders pagados teniendo cupo del plan sin usar.

    Admin/master no consumen. Devuelve el estado de créditos actualizado.
    Best-effort: si algo falla, no lanza (el enforcement decide si bloquea).
    """
    if db is None or await _sin_limite(user):
        return await get_user_credits(user)

    _, credits_per = await _get_credits_config()
    try:
        cost = int(credits_per.get(kind, 0) or 0)
    except (TypeError, ValueError):
        cost = 0
    # Aplica el factor del perfil efectivo antes de descontar.
    cost = coste_de_motor(kind, cost, motor)

    if cost > 0:
        uid = str(user.get("id") or user.get("_id") or "")
        try:
            antes = await get_user_credits(user)
            saldo_actual = int(antes.get("saldo", 0) or 0)
            # Lo que queda del plan ANTES de este consumo.
            del_plan = max(int(antes.get("restantes", 0) or 0) - saldo_actual, 0)
            # Nunca se descuenta mas saldo del que hay: si quedara en negativo,
            # la siguiente recarga PAGADA llegaria mermada.
            del_saldo = min(max(cost - del_plan, 0), saldo_actual)
            # `consumed` sigue contando el consumo total del mes: lo usan el
            # medidor por cliente y las estadisticas de carpinteros.
            inc = {"consumed": cost}
            if del_saldo > 0:
                inc["gastado_saldo"] = del_saldo
            from services.plataformas import organizacion_de, plataforma_de
            await db.ai_credits.update_one(
                {"user_id": uid, "month": _month()},
                {
                    "$inc": inc,
                    "$set": {
                        "plataforma": plataforma_de(user),
                        "organizationId": organizacion_de(user),
                        "updatedAt": datetime.now(timezone.utc).isoformat(),
                    },
                    "$setOnInsert": {"user_id": uid, "month": _month()},
                },
                upsert=True,
            )
            if del_saldo > 0:
                await db.ai_credit_balance.update_one(
                    {"user_id": uid},
                    {"$inc": {"saldo": -del_saldo},
                     "$set": {"updatedAt": datetime.now(timezone.utc).isoformat()}},
                    upsert=True,
                )
        except Exception:
            pass  # no bloquear por un fallo del contador
    return await get_user_credits(user)
