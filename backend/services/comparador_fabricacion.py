# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
comparador_fabricacion.py — PRESUPUESTADO vs FABRICADO.

Se presupuestan unas cosas y acaban fabricándose otras. A veces con razón (un
cambio pactado), a veces por un error de trascripción, y a veces porque alguien
tocó la orden de fabricación después. El dinero se pierde igual en los tres
casos, y hoy nadie lo ve hasta que el montador llega a la obra.

Este módulo compara las dos listas y dice EXACTAMENTE en qué se diferencian.
Solo cálculo, sin base de datos, para poder probarlo.

UNIDADES. Las dos listas salen de los mismos campos (`orders.py` construye las
líneas de fabricación a partir de las del pedido con los mismos nombres y
defaults), así que comparten unidad y se comparan en crudo. Si algún día una de
las dos pasara a milímetros, esta comparación empezaría a mentir: por eso
`comparar()` avisa cuando una medida cambia por un factor de ~10, que es la
firma de una confusión de unidades y no de un cambio real.

CÓMO SE EMPAREJAN. El problema de fondo es que el mismo mueble puede aparecer
con códigos distintos a cada lado. Se hacen dos pasadas:

  1. Por CÓDIGO, que es lo fiable cuando está.
  2. Lo que sobre, por FORMA (tipo + ancho + alto), que es como lo reconoce una
     persona mirando el plano.

Lo que no empareja en ninguna de las dos NO se fuerza: se declara "solo
presupuestado" o "solo fabricado". Emparejar a la fuerza dos cosas parecidas
escondería justo el error que se busca.
"""

CAMPOS_COMPARADOS = (
    ("quantity", "unidades"),
    ("width", "ancho"),
    ("height", "alto"),
    ("depth", "fondo"),
    ("material", "material"),
    ("doorFinish", "acabado de puerta"),
)


def _txt(v):
    return str(v).strip() if v not in (None, "") else ""


def _num(v):
    if v in (None, ""):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def normalizar(item):
    """Deja una línea en la forma común, vengan de donde vengan sus campos."""
    item = item or {}
    return {
        "codigo": _txt(item.get("productCode") or item.get("code") or item.get("cod")).upper(),
        "nombre": _txt(item.get("productName") or item.get("name") or item.get("descripcion")),
        "quantity": _num(item.get("quantity") if item.get("quantity") is not None else item.get("qty")) or 1,
        "width": _num(item.get("width") if item.get("width") is not None else item.get("ancho")),
        "height": _num(item.get("height") if item.get("height") is not None else item.get("alto")),
        "depth": _num(item.get("depth") if item.get("depth") is not None else item.get("fondo")),
        "material": _txt(item.get("material") or item.get("carcassColor")),
        "doorFinish": _txt(item.get("doorFinish") or item.get("finish")),
        "itemType": _txt(item.get("itemType")) or "cocina",
    }


def _forma(n):
    """Huella física de una línea: lo que la identifica mirando el plano."""
    return (n["itemType"], n["width"], n["height"])


def _posible_lio_de_unidades(antes, despues):
    """¿Esta diferencia huele a centímetros contra milímetros?"""
    a, d = _num(antes), _num(despues)
    if not a or not d:
        return False
    r = max(a, d) / min(a, d)
    return 9.5 <= r <= 10.5


def _diferencias(pres, fab):
    """Campos en los que dos líneas ya emparejadas no coinciden."""
    out = []
    for campo, etiqueta in CAMPOS_COMPARADOS:
        a, d = pres.get(campo), fab.get(campo)
        if isinstance(a, str) or isinstance(d, str):
            # Un texto vacío a un lado no es "cambió a nada": es que no consta.
            if _txt(a) and _txt(d) and _txt(a).lower() != _txt(d).lower():
                out.append({"campo": etiqueta, "antes": a, "despues": d, "unidades": False})
            continue
        if a is None or d is None:
            continue          # sin las dos puntas no se afirma que haya cambio
        if a != d:
            out.append({"campo": etiqueta, "antes": a, "despues": d,
                        "unidades": _posible_lio_de_unidades(a, d)})
    return out


def comparar(presupuestado, fabricado):
    """Compara las dos listas y describe en qué se diferencian."""
    pres = [normalizar(i) for i in (presupuestado or [])]
    fab = [normalizar(i) for i in (fabricado or [])]

    libres_fab = list(range(len(fab)))
    parejas = []

    # 1ª pasada: por código.
    for i, p in enumerate(pres):
        if not p["codigo"]:
            continue
        for j in list(libres_fab):
            if fab[j]["codigo"] == p["codigo"]:
                parejas.append((i, j))
                libres_fab.remove(j)
                break

    emparejados_pres = {i for i, _ in parejas}

    # 2ª pasada: lo que sobra, por forma física.
    for i, p in enumerate(pres):
        if i in emparejados_pres:
            continue
        for j in list(libres_fab):
            if _forma(fab[j]) == _forma(p) and _forma(p)[1] is not None:
                parejas.append((i, j))
                libres_fab.remove(j)
                emparejados_pres.add(i)
                break

    cambiados, iguales = [], 0
    for i, j in parejas:
        difs = _diferencias(pres[i], fab[j])
        if difs:
            cambiados.append({
                "codigo": pres[i]["codigo"] or fab[j]["codigo"],
                "nombre": pres[i]["nombre"] or fab[j]["nombre"],
                "diferencias": difs,
            })
        else:
            iguales += 1

    solo_pres = [pres[i] for i in range(len(pres)) if i not in emparejados_pres]
    solo_fab = [fab[j] for j in libres_fab]

    hay = bool(cambiados or solo_pres or solo_fab)
    return {
        "iguales": iguales,
        "cambiados": cambiados,
        "soloPresupuesto": solo_pres,
        "soloFabricacion": solo_fab,
        "hayDiferencias": hay,
        "posibleLioDeUnidades": any(
            d["unidades"] for c in cambiados for d in c["diferencias"]
        ),
        "resumen": resumen(iguales, cambiados, solo_pres, solo_fab),
    }


def resumen(iguales, cambiados, solo_pres, solo_fab):
    """Una línea en castellano para leer de un vistazo."""
    if not cambiados and not solo_pres and not solo_fab:
        return f"Todo cuadra: {iguales} línea(s) iguales."
    partes = []
    if cambiados:
        partes.append(f"{len(cambiados)} línea(s) con diferencias")
    if solo_pres:
        partes.append(f"{len(solo_pres)} presupuestada(s) que NO se fabrican")
    if solo_fab:
        partes.append(f"{len(solo_fab)} fabricada(s) que NO estaban presupuestadas")
    return "; ".join(partes) + f" ({iguales} cuadran)."
