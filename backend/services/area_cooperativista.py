# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
EL ÁREA DE UN COOPERATIVISTA: QUÉ VE, Y SOBRE TODO QUÉ NO VE.

`comisiones.py` dice CUÁNTO cobra. `liquidaciones.py` dice CUÁNDO. Este módulo
dice QUIÉN puede mirar, que es lo que faltaba para que un montador o un
comercial pudiera entrar con su clave y ver lo suyo.

DOS REGLAS, Y LA SEGUNDA ES LA QUE HAY QUE VIGILAR

1. CADA UNO VE SOLO LO SUYO. Un comercial ve los pedidos que ha vendido; un
   montador, los que ha montado. Nunca los del compañero. Esto es nómina: ver lo
   que cobra otro no es un fallo de permisos, es un problema entre personas.

2. LA COMISIÓN NO PUEDE ABRIR LA PUERTA AL DINERO DE LA CASA. Aquí está el
   riesgo de verdad. Para calcular la comisión hace falta la base imponible del
   pedido, y de ahí a enseñar el coste, el margen o la tarifa MV hay un paso. El
   ERP tiene eso cerrado al master en el servidor (CLAUDE.md, reglas 8b y 9), y
   una pantalla nueva no puede convertirse en la puerta de atrás. La regla del
   proyecto vale igual aquí: un candado que se rodea por otra ruta no es un
   candado.

   Lo que sale de aquí: sus muebles, sus euros, su tramo y el estado. Lo que NO
   sale, jamás: coste, margen, tarifa MV, escandallo, descuentos de proveedor y
   las comisiones de cualquier otro.

POR QUÉ ESTO NO HABLA CON MONGO. Recibe los pedidos ya leídos y devuelve el
panel. Así se puede probar entero sin base de datos, que es la única forma de
tener candados de verdad sobre quién ve el dinero de quién.
"""
from __future__ import annotations

from typing import Iterable, Optional

from services import comisiones as C
from services import liquidaciones as L
from services import origen_pedidos as OP
from services import plataformas as P

COMERCIAL = L.COMERCIAL
MONTADOR = L.MONTADOR

# Lo único que sale de un pedido hacia el panel de un cooperativista. Es una
# lista BLANCA a propósito: con una lista negra, cualquier campo nuevo del
# pedido —un coste, un margen— saldría solo el día que alguien lo añada.
CAMPOS_VISIBLES = ("pedidoId", "estado", "euros", "muebles", "periodo",
                   "porMueble", "tramo", "anomalia", "sinDesglose", "soloCascos")


def rol_de(user: Optional[dict]) -> Optional[str]:
    """Con qué sombrero entra. `None` si no es SOCIO cooperativista.

    SER COOPERATIVISTA SE MARCA, NO SE DEDUCE DEL ROL DEL ERP (master, 27/08):
    «comercial cooperativista sí, montador cooperativista también; los demás son
    independientes; el rol de comisiones solamente es para estos dos».

    La primera versión miraba `isMontador` / `isRepresentative`, y eso metía en
    la nómina al comercial y al montador de toda la vida de la casa, que son
    roles genéricos del ERP y no socios. Ahora hacen falta las dos cosas: estar
    en la cooperativa Y llevar la marca de socio.

    Un socio puede ser las dos cosas (un montador que además vende). Se devuelve
    MONTADOR primero por ser el más restrictivo en importes: su comisión es la
    mano de obra, que no depende de la valoración del pedido y por tanto no deja
    deducir nada del PVP.
    """
    if not user:
        return None
    # LA PLATAFORMA MANDA SOBRE EL ROL. carpinter.io y Studio3K son negocios de
    # suscripción que comparten este ERP «de momento»: un suscriptor marcado
    # como cooperativista sigue siendo un suscriptor. Se comprueba aquí, antes
    # que nada, porque este es el único sitio por el que se entra al área y a la
    # liquidación. (`es_cooperativista_*` ya lo comprueba; se deja explícito
    # porque este orden —plataforma primero— es la regla, no un detalle.)
    if not P.puede_tener_comision(user):
        return None
    if P.es_cooperativista_montador(user):
        return MONTADOR
    if P.es_cooperativista_comercial(user):
        return COMERCIAL
    return None


def filtro_de(user: Optional[dict]) -> Optional[dict]:
    """El filtro de Mongo con los pedidos de ESE cooperativista, y de nadie más.

    Devuelve `None` cuando el usuario no es cooperativista. `None` no es «sin
    filtro»: quien llama tiene que tratarlo como «no hay área que enseñar». Un
    filtro vacío `{}` aquí significaría TODOS los pedidos de la casa.
    """
    rol = rol_de(user)
    uid = (user or {}).get("id")
    if not rol or not uid:
        return None
    return {"montadorUserId": uid} if rol == MONTADOR else {"comercialUserId": uid}


def normaliza_pedido(order: dict, mano_por_mueble: float = 0.0,
                    familia_por_codigo: Optional[dict] = None) -> dict:
    """Del documento del pedido a lo poco que necesita la liquidación.

    SOLO LOS MUEBLES ENTRAN EN LA COMISIÓN (master, 25/08). Las unidades y la
    valoración NO son las del pedido entero: se recalculan de sus líneas
    dejando fuera puertas, costados, regletas y las líneas manuales de
    servicios. En un pedido corriente eso es la diferencia entre 990 € y 420 €
    de comisión — se pagaba un 136% de más.

    SI EL PEDIDO NO TRAE SUS LÍNEAS no se puede saber qué era mueble y qué no,
    así que no se cuenta nada y se marca `sinDesglose`. Contar el pedido entero
    sería pagar de más, y pagar de más no se devuelve; pagar de menos, al menos,
    se reclama. Que aparezca marcado es justo lo que hace falta para arreglarlo.
    """
    o = order or {}
    # LOS CASCOS NO PAGAN COMISIÓN (master, 30/08: «los pedidos de cascos solo
    # son para separar cascos, cuando un cliente se lleva la cocina
    # desmontada»). Cocina Desmontada CUENTA para la cooperativa —entra en COOP,
    # se le asigna montador, se sigue en producción— pero no reparte nada.
    #
    # Se sale ANTES de contar, y no es lo mismo que `sinDesglose`: aquel dice
    # «no se sabe lo que lleva» y hay que ir a arreglarlo; este dice «no
    # comisiona, y así tiene que ser». Marcar un pedido de cascos como dato roto
    # es mandar a alguien a buscar un fallo que no existe.
    if OP.es_solo_cascos(o):
        return {
            "id": o.get("id") or "",
            "muebles": 0,
            "baseImponible": 0.0,
            "sinDesglose": False,
            "soloCascos": True,
            "aceptadoAt": o.get("aceptadoAt") or o.get("confirmedAt"),
            "servidoAt": L.servido_de(o),
            "cobradoAt": L.cobrado_de(o),
            "pendienteCobro": o.get("pendienteCobro") or 0,
            "anulado": bool(o.get("anulado") or o.get("status") == "cancelled"),
            "manoPorMueble": mano_por_mueble,
            L.LIQUIDADO_LEGADO: o.get(L.LIQUIDADO_LEGADO),
            L.CONGELADA: o.get(L.CONGELADA),
            **{k: o.get(k) for k in L.LIQUIDADO_POR_ROL.values()},
            **{k: o.get(k) for k in L.CONGELADA_POR_ROL.values()},
        }
    lineas = o.get("items") or o.get("lineas") or []
    # LOS PEDIDOS DE VERDAD NO GUARDAN LA FAMILIA en la línea: guardan el código
    # (`B60D/I`) y la familia vive en el catálogo, en `category`. Quien llama
    # pasa ese mapa; sin él, las líneas antiguas no se pueden clasificar.
    if lineas and familia_por_codigo:
        lineas = [dict(l, _familiaResuelta=(
                    C.familia_de(l)
                    or familia_por_codigo.get(str((l or {}).get("code") or "").strip().upper(), "")))
                  for l in lineas]
    if lineas:
        b = C.base_de_comision(lineas, o.get("descuentoPct") or 0)
        muebles, base = b["muebles"], b["baseImponible"]
        # NO SE SABE NO ES CERO. Si NINGUNA línea se ha podido clasificar, este
        # pedido no tiene «0 muebles»: es que no se sabe lo que lleva. Se marca
        # `sinDesglose` para que salga «?» y no pague, en vez de un 0 que parece
        # un dato y que dejaría a alguien sin cobrar sin decir por qué
        # (CLAUDE.md, regla 7). Se vio en producción el 28/08.
        sin_desglose = b["sinClasificar"] >= b["lineas"] > 0
        if sin_desglose:
            muebles, base = 0, 0.0
    else:
        muebles, base, sin_desglose = 0, 0.0, True
    return {
        "id": o.get("id") or "",
        "muebles": muebles,
        "baseImponible": base,
        "sinDesglose": sin_desglose,
        "soloCascos": False,
        "aceptadoAt": o.get("aceptadoAt") or o.get("confirmedAt"),
        # NO SE LEEN A MANO. `deliveredAt` y `paidAt` son los nombres que el
        # ERP ya usa para lo mismo, y aquí se copiaban SOLO `servidoAt` y
        # `cobradoAt`: un pedido entregado y cobrado de verdad llegaba a
        # `liquidaciones` con las dos fechas vacías y se quedaba EN PROGRESO
        # para siempre. La alternativa estaba escrita allí, pero allí ya no
        # quedaba nada que leer — la habíamos tirado en esta línea.
        "servidoAt": L.servido_de(o),
        "cobradoAt": L.cobrado_de(o),
        "pendienteCobro": o.get("pendienteCobro") or 0,
        "anulado": bool(o.get("anulado") or o.get("status") == "cancelled"),
        "manoPorMueble": mano_por_mueble,
        # QUÉ SE HA PAGADO YA, Y A QUIÉN. Va por rol —del mismo pedido cobran el
        # comercial y el montador— y se copian también las claves viejas, que
        # `liquidaciones` sigue sabiendo leer para los pedidos de antes.
        L.LIQUIDADO_LEGADO: o.get(L.LIQUIDADO_LEGADO),
        L.CONGELADA: o.get(L.CONGELADA),
        **{k: o.get(k) for k in L.LIQUIDADO_POR_ROL.values()},
        **{k: o.get(k) for k in L.CONGELADA_POR_ROL.values()},
    }


def _linea_publica(l: dict) -> dict:
    """Recorta una línea a lo que puede ver un cooperativista."""
    return {k: l.get(k) for k in CAMPOS_VISIBLES if k in l}


def _a_tiro(normalizados, rol):
    """Los pedidos EN PROGRESO que están a un paso de subir de tramo.

    Es el plan de estimulación del master: no basta con enseñar lo ganado, hay
    que enseñar lo que está a tiro. «Este pedido va por 11.400 €; con 600 € más
    pasas a 60 € por mueble y son 140 € más para ti.»

    Solo COMERCIALES: la comisión del montador es la mano de obra por mueble y
    no depende de la valoración, así que para él no hay tramo que perseguir.

    Y solo lo que está EN PROGRESO: perseguir un pedido ya cerrado no sirve de
    nada, y enseñarlo sería recordarle lo que se dejó por el camino.

    OJO: aquí se usa la base imponible para CALCULAR, pero no sale ni un euro de
    ella hacia el panel. Lo que se devuelve es cuánto falta y cuánto se gana —
    nunca el PVP ni el coste del pedido.
    """
    if rol != COMERCIAL:
        return []
    fuera = []
    for p in normalizados:
        # CON EL ROL: «liquidada» es de una persona, no del pedido. Sin pasarlo,
        # un pedido que ya se le pagó al montador desaparecería de lo que el
        # comercial todavía tiene a tiro.
        if L.estado_de(p, COMERCIAL) != L.EN_PROGRESO:
            continue
        g = C.cuanto_falta_para_el_siguiente_tramo(p["baseImponible"], p["muebles"])
        if not g:
            continue
        fuera.append({
            "pedidoId": p["id"],
            "faltan": g["faltan"],
            "porMuebleAhora": g["porMuebleAhora"],
            "porMuebleSiSalta": g["porMuebleSiSalta"],
            "extraTotal": g["extraTotal"],
            "muebles": g["muebles"],
        })
    # Lo más cerca primero: es lo que de verdad se puede empujar hoy.
    fuera.sort(key=lambda x: x["faltan"])
    return fuera


# Lo único que sale de un usuario hacia la pantalla de asignación. Lista BLANCA,
# igual que `CAMPOS_VISIBLES`: el documento del usuario lleva dentro la
# contraseña, los descuentos comerciales y sus permisos, y una pantalla de
# «elige quién montó esto» no tiene por qué enseñar nada de eso.
CAMPOS_DEL_SOCIO = ("id", "nombre", "rol", "manoObraPorMueble")


def socio_publico(user: Optional[dict]) -> Optional[dict]:
    """Un socio, reducido a lo que hace falta para elegirlo en una lista.

    Devuelve `None` si no es socio, para que la lista no se pueda rellenar por
    accidente con usuarios que no cobran.
    """
    rol = rol_de(user)
    if not rol:
        return None
    u = user or {}
    ficha = {
        "id": u.get("id") or "",
        "nombre": (u.get("clientName") or u.get("username") or "").strip(),
        "rol": rol,
    }
    # La mano de obra solo tiene sentido —y solo se enseña— para el montador.
    if rol == MONTADOR:
        ficha["manoObraPorMueble"] = C.mano_de_obra_de(u)
    return ficha


def socios_de(usuarios: Iterable[dict]) -> dict:
    """Los socios que hay, separados por rol y listos para dos desplegables."""
    fichas = [f for f in (socio_publico(u) for u in (usuarios or [])) if f]
    return {
        "comerciales": sorted([f for f in fichas if f["rol"] == COMERCIAL],
                              key=lambda f: f["nombre"].lower()),
        "montadores": sorted([f for f in fichas if f["rol"] == MONTADOR],
                             key=lambda f: f["nombre"].lower()),
    }


# Lo único que sale de un pedido hacia la lista de obras del cooperativista.
# Lista BLANCA, igual que todo lo demás de este módulo: dentro del pedido hay
# líneas, precios, descuentos y totales, y para saber QUÉ COCINA hay que montar
# no hace falta nada de eso.
CAMPOS_DE_LA_OBRA = ("id", "referencia", "cliente", "fecha", "origen", "kind")


def obra_publica(order: dict) -> dict:
    """Una obra en la lista del cooperativista: la justa para reconocerla.

    NO LLEVA UN EURO. El Expediente ya recorta importes por su cuenta
    (`services/expediente.py`), pero esta lista es una ruta nueva y el dinero no
    viaja por rutas nuevas «por si acaso»: se decide aquí que no viaja.
    """
    o = order or {}
    return {
        "id": o.get("id") or "",
        "referencia": (o.get("budgetNumber") or o.get("projectReference")
                       or o.get("ref") or o.get("id") or ""),
        "cliente": (o.get("customerName") or o.get("cliente") or "").strip(),
        "fecha": o.get("confirmedAt") or o.get("createdAt") or "",
        "origen": o.get("origenNombre") or o.get("origen") or "",
        "kind": o.get("kind") or "pedido",
    }


def obras_de(pedidos: Iterable[dict]) -> list:
    """Las obras de ese cooperativista, la más reciente primero."""
    fuera = [obra_publica(p) for p in (pedidos or [])]
    fuera.sort(key=lambda o: str(o.get("fecha") or ""), reverse=True)
    return fuera


def pedido_para_asignar(order: dict, nombres: Optional[dict] = None,
                        familia_por_codigo: Optional[dict] = None) -> dict:
    """Una línea de la pantalla de asignación del master.

    Trae el nombre del cliente y la fecha para poder reconocer el pedido, quién
    lo tiene asignado ahora, y los muebles que cuentan para la comisión — que no
    son los del pedido entero (puertas, costados y servicios no incentivan).

    NO trae el importe. La pantalla es del master y podría verlo, pero para
    decidir quién montó un pedido no hace falta: cuanto menos dinero viaje por
    rutas nuevas, menos sitios hay por los que se pueda escapar.
    """
    o = order or {}
    n = normaliza_pedido(o, 0.0, familia_por_codigo)
    quien = nombres or {}
    com = o.get("comercialUserId") or ""
    mon = o.get("montadorUserId") or ""
    return {
        "pedidoId": o.get("id") or "",
        "referencia": o.get("budgetNumber") or o.get("projectReference") or "",
        "cliente": (o.get("customerName") or "").strip(),
        # De qué sección salió. No es un adorno: si vuelve a colarse un pedido
        # que no toca, se ve de dónde ha entrado (services/origen_pedidos.py).
        "origen": o.get("origenNombre") or o.get("origen") or "",
        "fecha": o.get("confirmedAt") or "",
        "muebles": n["muebles"],
        "sinDesglose": n["sinDesglose"],
        # «No comisiona» no es «falta un dato»: un pedido de cascos sale así a
        # propósito y no hay nada que ir a arreglar.
        "soloCascos": n.get("soloCascos", False),
        "comercialUserId": com,
        "montadorUserId": mon,
        "comercial": quien.get(com, ""),
        "montador": quien.get(mon, ""),
        "sinAsignar": not com or not mon,
    }


def panel_de(user: Optional[dict], pedidos: Iterable[dict],
             mano_por_mueble: float = 0.0,
             familia_por_codigo: Optional[dict] = None) -> Optional[dict]:
    """Lo que ve al entrar en su área. `None` si no es cooperativista.

    OJO con `pedidos`: tienen que venir YA filtrados por `filtro_de`. Esta
    función no vuelve a comprobar de quién son —no puede, no conoce la consulta
    que los trajo—, así que quien llama es responsable de no traerle los del
    vecino. El candado lo comprueba desde la ruta, que es donde se decide.
    """
    rol = rol_de(user)
    if not rol:
        return None
    normalizados = [normaliza_pedido(p, mano_por_mueble, familia_por_codigo)
                    for p in (pedidos or [])]
    pan = L.panel(normalizados, rol)
    return {
        "rol": rol,
        "aTiro": _a_tiro(normalizados, rol),
        "enProgreso": {"euros": pan["enProgreso"]["euros"],
                       "pedidos": pan["enProgreso"]["pedidos"],
                       "lineas": [_linea_publica(x) for x in pan["enProgreso"]["lineas"]]},
        "consolidada": {"euros": pan["consolidada"]["euros"],
                        "pedidos": pan["consolidada"]["pedidos"],
                        "lineas": [_linea_publica(x) for x in pan["consolidada"]["lineas"]]},
        "liquidada": {"euros": pan["liquidada"]["euros"],
                      "pedidos": pan["liquidada"]["pedidos"],
                      "lineas": [_linea_publica(x) for x in pan["liquidada"]["lineas"]]},
    }
