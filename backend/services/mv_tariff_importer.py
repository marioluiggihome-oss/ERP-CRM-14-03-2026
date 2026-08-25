# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Importador de tarifas MV → productos.

Lee `data/mv_tarifas_oficiales.json` (las 21 tarifas oficiales) y lo expande a
registros de producto con `zonePoints = {T1..T21}`, generando las variantes
(altura 70/90, 200/220, 127/147, anchos de puerta, normal/chapa, etc.).

NO escribe en base de datos por sí mismo: `expand_tariffs()` devuelve la lista de
productos. El endpoint decide si es dry-run o si reconstruye la colección MV.
"""
import os
import json
import re
import unicodedata
from typing import Dict, Any, List

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "mv_tarifas_oficiales.json")

# Profundidad (fondo) orientativa por familia, en cm. Best-effort para el despiece.
_DEPTH_BY_PREFIX = {
    "BAJO": 58, "BAJO_FREGADERO": 58, "BAJO_PUERTA_CAJON": 58, "BAJO_5_CAJONES": 58,
    "BAJO_3CAJ_1GAV": 58, "BAJO_2GAV_1CAJ": 58, "BAJO_2CAJ_1GAV_1FRENTE": 58,
    "BAJO_2GAV_1FRENTE": 58, "BAJO_RINCON_ESCUADRA": 58, "BAJO_RINCON_CIEGO": 58,
    "BAJO_HORNO": 58, "BAJO_TERMINAL": 58,
    "ALTO": 33, "ALTO_VITRINA": 33, "ALTO_CAMPANA": 33, "ALTO_ESCURREPLATOS": 33,
    "ALTO_MICROONDAS": 33, "ALTO_CALENTADOR": 33, "ALTO_CALDERA": 33, "ALTO_SOBREFRIGO": 33,
    "ALTO_DECORATIVO": 33, "ALTO_RINCON_CIEGO": 33, "ALTO_RINCON_ESCUADRA": 33,
    "ALTO_RINCON_CHAFLAN": 33, "ALTO_TERMINAL": 33, "ALTO_ABATIBLE": 33,
    "ALTO_COMBINADO": 33, "ALTO_COMBINADO_PLUS": 33, "ALTO_COMBINADO_PLUS_J": 33,
    "ALTILLO": 33, "ALTILLO_VITRINA": 33, "ALTILLOS_DECORATIVOS": 33,
    "COLUMNA_DESPENSERO": 56, "COLUMNA_FRIGO": 56, "COLUMNA_HORNO": 56, "COLUMNA_HORNO_MICRO": 56,
    "MEDIACOLUMNA": 56, "MEDIA_PUERTA_GAVETA": 56, "MEDIACOLUMNA_HORNO": 56,
    "MEDIACOLUMNA_VITRINA": 33, "MEDIACOL_VITRINA_GAVETA": 33,
    "SOBREENCIMERA": 33, "SOBREENC_VITRINA": 33, "SOBREENC_CAJON": 33, "SOBREENC_VIT_CAJON": 33,
    "BOTELLEROS": 33,
}


def _slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()


def _width_from_code(code: str) -> float:
    """Saca el ancho (primer número del código). Ej: B25D/I->25, A100->100, P30->30."""
    m = re.search(r"(\d{2,3})", str(code))
    return float(m.group(1)) if m else 0.0


def expand_tariffs(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Expande el JSON a una lista de productos con zonePoints {Tn: pts}."""
    tariffs = data.get("tariffs", {})
    products: Dict[str, Dict[str, Any]] = {}

    def upsert(sku: str, tariff: str, pts, *, family: str, name: str,
               width: float, height: float):
        if pts is None:
            return
        try:
            pts = float(pts)
        except Exception:
            return
        p = products.get(sku)
        if not p:
            is_bajo = family.startswith("BAJO")
            p = {
                "code": sku,
                "reference": sku,
                "name": name,
                "category": family,
                "library": "MV",
                "module": "montada",
                "width": width or 0,
                "height": 70 if (is_bajo and not height) else (height or 0),
                "heightLabel": "70/80" if is_bajo else None,
                "depth": _DEPTH_BY_PREFIX.get(family, 0),
                "zonePoints": {},
            }
            products[sku] = p
        p["zonePoints"][tariff] = pts

    for tariff, families in tariffs.items():
        if not re.match(r"^T\d+$", tariff):
            continue
        for family, fam in families.items():
            ftype = fam.get("type")
            items = fam.get("items", {})
            cols = fam.get("cols", [])

            if ftype == "single":
                for code, pts in items.items():
                    upsert(code, tariff, pts, family=family, name=f"{family} {code}",
                           width=_width_from_code(code), height=0)

            elif ftype == "a7090":
                # Costados, laterales y regletas: las dos columnas son el ANCHO
                # de la pieza («hasta 70» / «hasta 90»), no la altura del mueble
                # que rematan. Ver la nota de `services/mv_relacion.py`. Va
                # aparte de las tres de abajo a propósito: si compartiera rama
                # volvería a guardarse como altura y el buscador volvería a
                # ofrecer «Alto 70/90» para un costado de columna de 220.
                for code, vals in items.items():
                    if not isinstance(vals, list):
                        continue
                    for a, v in zip((70, 90), vals):
                        upsert(f"{code}-A{a}", tariff, v, family=family,
                               name=f"{family} {code} ancho hasta {a}",
                               width=a, height=0)

            elif ftype in ("h7090", "h127147", "h200220"):
                hs = {"h7090": (70, 90), "h127147": (127, 147), "h200220": (200, 220)}[ftype]
                for code, vals in items.items():
                    if not isinstance(vals, list):
                        continue
                    for h, v in zip(hs, vals):
                        upsert(f"{code}-{h}", tariff, v, family=family,
                               name=f"{family} {code} H{h}", width=_width_from_code(code), height=h)

            elif ftype == "h355060":
                depths = cols or ["35", "50", "60"]
                for code, vals in items.items():
                    if not isinstance(vals, list):
                        continue
                    for d, v in zip(depths, vals):
                        upsert(f"{code}-{d}", tariff, v, family=family,
                               name=f"{family} {code} F{d}", width=_width_from_code(code), height=0)

            elif ftype == "dual":
                c = cols or ["a", "b"]
                for code, vals in items.items():
                    if not isinstance(vals, list):
                        continue
                    # col0 = SKU principal (mismo código); col1 = sufijo
                    for i, v in enumerate(vals):
                        suffix = "" if i == 0 else f"-{_slug(c[i]).upper()}"
                        upsert(f"{code}{suffix}", tariff, v, family=family,
                               name=f"{family} {code} {c[i]}".strip(), width=_width_from_code(code), height=0)

            elif ftype == "matrix":
                widths = cols or []
                rows = fam.get("rows", {})
                for hrow, wmap in rows.items():
                    for wcode, v in (wmap or {}).items():
                        upsert(f"{wcode}-{hrow}", tariff, v, family=family,
                               name=f"{family} {wcode} H{hrow}", width=_width_from_code(wcode), height=float(hrow))

            elif ftype == "ent_med":
                for code, obj in items.items():
                    if not isinstance(obj, dict):
                        continue
                    desc = obj.get("desc", code)
                    if obj.get("ent") is not None:
                        upsert(f"{code}-ENT", tariff, obj.get("ent"), family=family,
                               name=f"{desc} (entero)", width=0, height=0)
                    if obj.get("med") is not None:
                        upsert(f"{code}-MED", tariff, obj.get("med"), family=family,
                               name=f"{desc} (medio)", width=0, height=0)

    # Finalizar: points (fallback T1), id
    out = []
    for sku, p in products.items():
        zp = p["zonePoints"]
        p["points"] = zp.get("T1") or (next(iter(zp.values())) if zp else 0)
        p["id"] = f"mv-{_slug(sku)}"
        out.append(p)
    return out


def load_data() -> Dict[str, Any]:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_report(products: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Resumen para dry-run: nº de SKUs, por familia, y cuántas tarifas tiene cada uno."""
    by_family: Dict[str, int] = {}
    tariffs_seen = set()
    for p in products:
        by_family[p["category"]] = by_family.get(p["category"], 0) + 1
        tariffs_seen.update(p["zonePoints"].keys())
    return {
        "total_skus": len(products),
        "tarifas_con_datos": sorted(tariffs_seen, key=lambda t: int(t[1:])),
        "skus_por_familia": dict(sorted(by_family.items())),
        "ejemplos": [
            {"code": p["code"], "name": p["name"], "zonePoints": p["zonePoints"]}
            for p in products[:8]
        ],
    }
