# -*- coding: utf-8 -*-
# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""LOS MUEBLES DE RINCÓN: ESCUADRA, CHAFLÁN Y CIEGO.

El master, 07/09/2026, enseñando dos fotos: «necesito que el sistema Estudio 3D
distinga entre muebles en escuadra y mueble con chaflán».

QUÉ SON, PORQUE NO ES LO MISMO NI DE LEJOS:

  ESCUADRA  Dos frentes que se encuentran a 90°. Se ven las dos puertas y la
            arista del rincón. Puede llevarlas INDEPENDIENTES (ARI/BRI) o
            UNIDAS (ARU/BRU), que abren a la vez.
  CHAFLÁN   UN solo frente en diagonal, a 45° sobre el rincón. Una puerta, y el
            mueble corta la esquina. Puede ser ciego o con VITRINA (ARCV).
  CIEGO     No tiene frente propio en el rincón: se accede por el mueble de al
            lado y el fondo se pierde. Es el más barato y el peor de usar.

POR QUÉ ESTO ES DINERO Y NO ESTÉTICA. En la tarifa MV los tres existen, con
ANCHO PROPIO Y PRECIO PROPIO:

    ARC63D/I   chaflán           63 cm    54 pts (alto 70) · 58 (alto 90)
    ARCV63D/I  chaflán vitrina   63 cm    84 pts           · 95
    ARI65D/I   escuadra indep.   65 cm    84 pts           · 90
    ARU65D/I   escuadra unidas   65 cm    82 pts           · 89
    AR60/65    ciego alto        60/65    54/60 pts        · 60/67
    BRI95D/I   escuadra bajo     95 cm    88 pts
    BRU95D/I   escuadra unidas   95 cm    87 pts
    BR90…110   ciego bajo        90-110   62-68 pts

Con el valor de punto en 2, un alto de rincón a 90 sale a 116 € en chaflán y a
180 € en escuadra: **64 € de diferencia en un solo mueble**, un 55 % más.
Confundirlos no da ningún error — da un presupuesto plausible y equivocado.

Y CAMBIA EL ANCHO, que es peor todavía: 63 el chaflán contra 65 la escuadra,
95 el bajo. Ninguno de esos tres está entre los anchos estándar de fabricación
(15, 20, 30, 40, 45, 50, 60, 70, 80, 90, 100, 120), así que un rincón que pase
por el ajuste al estándar se convierte en un 60 o en un 90 EN SILENCIO — y
entonces ni existe el código ni cuadra la pared. Son ANCHO FIJO, igual que un
lavavajillas: no se estiran para cuadrar un hueco.

NO HAY BAJO RINCÓN CHAFLÁN EN LA TARIFA MV. Existen el alto chaflán y el bajo
escuadra, pero el bajo chaflán no lo fabrica. No es un olvido de esta tabla: es
lo que hay en el catálogo del proveedor, comprobado código a código. Si alguien
dibuja uno, se dice; no se sustituye por un escuadra a escondidas.

LOS ANCHOS NO SE ESCRIBEN AQUÍ: SE LEEN DE LA TARIFA. Una lista copiada a mano
se separa del catálogo el día que MV añada una medida, y entonces esta tabla
diría que un mueble no existe cuando sí, o al revés.
"""
from typing import Dict, List, Optional

# ─── LOS TIPOS ───────────────────────────────────────────────────────────────
#
# `forma` es lo que el master quiere distinguir y lo que hay que dibujar:
#   escuadra → dos frentes a 90°
#   chaflan  → un frente en diagonal a 45°
#   ciego    → sin frente propio
#
# `prefijo` es el del código MV; el número del código ES el ancho (CLAUDE.md).
TIPOS: Dict[str, dict] = {
    "alto_rincon_escuadra": {
        "prefijo": "ARI", "fila": "alto", "forma": "escuadra",
        "label": "Alto rincón escuadra (puertas independientes)",
        "puertas": "independientes"},
    "alto_rincon_escuadra_unidas": {
        "prefijo": "ARU", "fila": "alto", "forma": "escuadra",
        "label": "Alto rincón escuadra (puertas unidas)",
        "puertas": "unidas"},
    "alto_rincon_chaflan": {
        "prefijo": "ARC", "fila": "alto", "forma": "chaflan",
        "label": "Alto rincón chaflán", "puertas": "una"},
    "alto_rincon_chaflan_vitrina": {
        "prefijo": "ARCV", "fila": "alto", "forma": "chaflan",
        "label": "Alto rincón chaflán con vitrina", "puertas": "una"},
    "alto_rincon_ciego": {
        "prefijo": "AR", "fila": "alto", "forma": "ciego",
        "label": "Alto rincón ciego", "puertas": "ninguna"},
    "bajo_rincon_escuadra": {
        "prefijo": "BRI", "fila": "bajo", "forma": "escuadra",
        "label": "Bajo rincón escuadra (puertas independientes)",
        "puertas": "independientes"},
    "bajo_rincon_escuadra_unidas": {
        "prefijo": "BRU", "fila": "bajo", "forma": "escuadra",
        "label": "Bajo rincón escuadra (puertas unidas)",
        "puertas": "unidas"},
    "bajo_rincon_ciego": {
        "prefijo": "BR", "fila": "bajo", "forma": "ciego",
        "label": "Bajo rincón ciego", "puertas": "ninguna"},
}

# Lo que la tarifa MV NO fabrica, dicho a propósito para poder explicarlo en vez
# de callarlo. Comprobado contra `mv_tarifas_oficiales.json` el 07/09/2026.
NO_EXISTE_EN_MV = {
    "bajo_rincon_chaflan": (
        "MV no fabrica el BAJO rincón chaflán: en su tarifa el chaflán solo "
        "existe en ALTO (ARC/ARCV). Abajo hay escuadra (BRI/BRU) o ciego (BR)."),
}


def es_rincon(elem_id: Optional[str]) -> bool:
    """¿Este módulo es un mueble de rincón?"""
    return str(elem_id or "").lower().strip() in TIPOS


def forma_de(elem_id: Optional[str]) -> Optional[str]:
    """«escuadra», «chaflan», «ciego» — o `None` si no es un rincón.

    Es lo único que hace falta para DIBUJARLO y para describírselo al render:
    un chaflán corta la esquina con un frente diagonal, una escuadra la deja
    en ángulo recto con dos frentes.
    """
    t = TIPOS.get(str(elem_id or "").lower().strip())
    return t["forma"] if t else None


def fila_de(elem_id: Optional[str]) -> Optional[str]:
    t = TIPOS.get(str(elem_id or "").lower().strip())
    return t["fila"] if t else None


def _codigos_de_tarifa(tarifa: str = "T1"):
    """Los códigos que EXISTEN en la tarifa. Se lee de la misma fuente que usa
    la relación MV para no tener dos catálogos."""
    from services.distribucion_a_mv import _catalogo
    return _catalogo(tarifa)


def anchos_de(elem_id: str, tarifa: str = "T1") -> List[int]:
    """Los anchos en los que MV fabrica ESE rincón, LEÍDOS DE LA TARIFA.

    Lista vacía si el tipo no existe. No se escriben a mano: una lista copiada
    se separa del catálogo en cuanto el proveedor toque una medida, y entonces
    diría que un mueble no existe cuando sí (o al revés, y entraría en un
    pedido un código que MV no sirve).

    OJO CON LOS PREFIJOS QUE SE SOLAPAN: «AR» es el ciego y «ARC» el chaflán,
    así que buscar por «AR» a secas se llevaría también los ARC y los ARI. Por
    eso lo que sigue al prefijo tiene que ser un NÚMERO.
    """
    t = TIPOS.get(str(elem_id or "").lower().strip())
    if not t:
        return []
    pre = t["prefijo"]
    anchos = set()
    for cod in _codigos_de_tarifa(tarifa):
        if not cod.startswith(pre):
            continue
        resto = cod[len(pre):].split("D")[0]
        if resto.isdigit():
            anchos.add(int(resto))
    return sorted(anchos)


def ancho_fijo_de(elem_id: str, tarifa: str = "T1") -> Optional[int]:
    """El ancho de un rincón que solo se fabrica en UNA medida.

    Devuelve `None` cuando hay varias (los ciegos): ahí el ancho lo elige quien
    diseña, y no se puede dar uno por defecto sin inventarlo.
    """
    anchos = anchos_de(elem_id, tarifa)
    return anchos[0] if len(anchos) == 1 else None


def descripcion_para_render(elem_id: str) -> str:
    """Cómo se le explica al modelo de imagen, en inglés y sin ambigüedad.

    Un modelo de imagen no sabe qué es «un rincón en escuadra»: hay que
    describirle la GEOMETRÍA. Y la diferencia entre los dos es exactamente lo
    que el master pidió que se distinguiera.
    """
    forma = forma_de(elem_id)
    if forma == "chaflan":
        return ("a CHAMFERED (45-degree angled) corner unit: ONE single flat door "
                "set diagonally across the inside corner, cutting it off at 45 "
                "degrees. The two runs do NOT meet at a sharp right angle here — "
                "the corner is bevelled by this single angled front")
    if forma == "escuadra":
        return ("a SQUARE (right-angle) corner unit: the two runs meet at a sharp "
                "90-degree inside corner, and BOTH fronts are visible meeting at "
                "that corner edge. There is NO diagonal or bevelled door")
    if forma == "ciego":
        return ("a BLIND corner unit: it has no door of its own on the corner; the "
                "adjacent cabinet's door is the only access and the corner front "
                "is a plain filler panel")
    return ""
