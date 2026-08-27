# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
instalaciones_cocina.py — Plan de instalaciones DERIVADO de la cocina real.

Este documento lo lee un electricista, un fontanero y un gasista, y con él
hacen rozas antes de alicatar. Un punto mal puesto se paga picando pared, así
que aquí no se inventa nada: cada punto sale de un módulo que EXISTE en la
distribución y lleva su posición real en cm desde el inicio de la pared.

Qué se corrigió el 05/08/2026 (el plan anterior era genérico y con errores):

· No miraba la cocina. Listaba «circuito lavavajillas» y «circuito frigorífico»
  hubiera o no, y las ubicaciones eran de plantilla («pared norte, cada 120 cm»).
· «Potencia total estimada: <suma de amperios> A». Sumar los calibres de los
  magnetotérmicos no es la potencia: ocho circuitos de 16 A no demandan 128 A.
  Ahora se calcula la potencia en W con coeficiente de simultaneidad.
· «Placa de inducción — línea trifásica». En vivienda va MONOFÁSICA a 230 V.
· «RITE para fontanería». El RITE es de instalaciones térmicas; la fontanería
  va por CTE DB-HS4 (suministro) y DB-HS5 (evacuación), y el gas por el
  RD 919/2006.

Referencias: REBT ITC-BT-25 (circuitos C1–C5 de vivienda), CTE DB-HS4/HS5.
"""
from typing import Dict, List, Optional

# ── Alturas de montaje (cm desde suelo acabado) ──────────────────────────────
# Derivadas de la geometría real de la cocina, no elegidas a ojo.
H_ENCIMERA = 94          # cara superior de la encimera (zócalo 10 + casco 80 + 4)
H_ENCHUFE_SALPICADERO = 115   # ~20 cm sobre encimera: fuera de salpicaduras
H_TOMA_ELECTRO_BAJO = 30      # dentro del mueble, por debajo del cajón
H_AGUA_FREGADERO = 55         # llaves de escuadra dentro del bajo fregadero
H_DESAGUE = 45                # sifón con registro
H_CAMPANA = 220               # salida de humos, rasante con los altos

# ── Circuitos del ITC-BT-25 que aplican en cocina ────────────────────────────
# (nombre, calibre A, sección mm², para qué)
C1 = ("C1", 10, 1.5, "Alumbrado")
C2 = ("C2", 16, 2.5, "Tomas de uso general")
C3 = ("C3", 25, 6.0, "Cocina y horno")
C4 = ("C4", 20, 4.0, "Lavadora, lavavajillas y termo")
C5 = ("C5", 16, 2.5, "Tomas de cocina y baños (encimera)")

# Potencia de cálculo por aparato (W). Son las previsiones habituales de un
# proyecto de vivienda; no el consumo real, que depende del modelo.
POTENCIA_W = {
    "placa": 7400, "placa_induccion": 7400, "cocina": 7400, "vitroceramica": 7400,
    "horno": 3500, "columna_hornos": 3500, "microondas": 1500,
    "lavavajillas": 2200, "lavadora": 2200, "secadora": 2500,
    "frigorifico": 300, "congelador": 300, "vinoteca": 200,
    "campana": 300, "extractor": 300,
}
# Coeficiente de simultaneidad: no todo funciona a la vez. Es lo que evita
# dimensionar una acometida para un consumo que nunca se da.
SIMULTANEIDAD = 0.65
TENSION_V = 230


def _es(elem_id: str, *claves) -> bool:
    t = (elem_id or "").lower()
    return any(k in t for k in claves)


def _centro(e: Dict) -> int:
    return int(e.get("posicion_cm") or 0) + int(e.get("ancho") or 60) // 2


def _punto(tipo: str, circuito, x: Optional[int], y: int, detalle: str,
           modulo: str = "") -> Dict:
    codigo, amp, seccion, para_que = circuito
    return {
        "tipo": tipo,
        "circuito": codigo,
        "amperios": amp,
        "seccion_mm2": seccion,
        "uso": para_que,
        # x = distancia en cm desde el inicio de la pared. None = no se sabe, y
        # se dice: es preferible a poner un número que nadie ha medido.
        "x_cm": x,
        "altura_cm": y,
        "detalle": detalle,
        "modulo": modulo,
    }


def plan_electrico(elementos: List[Dict], ancho_pared: int, con_isla: bool) -> Dict:
    """Puntos eléctricos, cada uno colgado de un módulo que existe."""
    puntos: List[Dict] = []
    potencias: List[int] = []

    for e in elementos:
        eid = str(e.get("id") or "").lower()
        etiqueta = str(e.get("label") or eid)
        x = _centro(e)
        if _es(eid, "placa", "vitro", "induccion", "cocina"):
            puntos.append(_punto(
                "Toma placa de cocción", C3, x, H_TOMA_ELECTRO_BAJO,
                "Monofásica 230 V, línea dedicada desde cuadro. NO trifásica: "
                "en vivienda la placa va a 230 V.", etiqueta))
            potencias.append(POTENCIA_W["placa"])
        elif _es(eid, "horno"):
            puntos.append(_punto("Toma horno", C3, x, H_TOMA_ELECTRO_BAJO,
                                 "Línea dedicada. Base 16 A con toma de tierra.", etiqueta))
            potencias.append(POTENCIA_W["horno"])
            # Una columna de "horno y microondas" son DOS aparatos y DOS tomas.
            # Antes se quedaba en una y el electricista se encontraba el micro
            # sin enchufe al montar.
            if _es(eid + " " + etiqueta, "micro"):
                puntos.append(_punto("Toma microondas", C5, x, 160,
                                     "Dentro del hueco de la columna, por encima "
                                     "del horno.", etiqueta))
                potencias.append(POTENCIA_W["microondas"])
        elif _es(eid, "microondas"):
            puntos.append(_punto("Toma microondas", C5, x, 160,
                                 "Dentro del hueco de la columna.", etiqueta))
            potencias.append(POTENCIA_W["microondas"])
        elif _es(eid, "lavavajillas"):
            puntos.append(_punto("Toma lavavajillas", C4, x, H_TOMA_ELECTRO_BAJO,
                                 "Base con toma de tierra; NO detrás del aparato "
                                 "(inaccesible): en el mueble contiguo.", etiqueta))
            potencias.append(POTENCIA_W["lavavajillas"])
        elif _es(eid, "lavadora", "secadora"):
            puntos.append(_punto("Toma lavadora/secadora", C4, x, H_TOMA_ELECTRO_BAJO,
                                 "Base con toma de tierra en mueble contiguo.", etiqueta))
            potencias.append(POTENCIA_W["lavadora"])
        elif _es(eid, "frigorifico", "congelador", "vinoteca"):
            puntos.append(_punto("Toma frigorífico", C5, x, H_TOMA_ELECTRO_BAJO,
                                 "Base accesible sin mover el aparato.", etiqueta))
            potencias.append(POTENCIA_W["frigorifico"])
        elif _es(eid, "campana", "extractor"):
            puntos.append(_punto("Toma campana", C5, x, H_CAMPANA - 20,
                                 "Dentro del alto de la campana.", etiqueta))
            potencias.append(POTENCIA_W["campana"])

    # Tomas de encimera: van donde HAY encimera, no "cada 120 cm por la pared".
    # Se colocan en los tramos de bajo, evitando placa y fregadero.
    prohibido = [(int(e.get("posicion_cm") or 0), int(e.get("ancho") or 60))
                 for e in elementos
                 if _es(str(e.get("id") or ""), "placa", "vitro", "induccion",
                        "fregadero", "frigorifico", "columna", "despensa")]
    # Se recorren los TRAMOS LIBRES de encimera y se pone al menos una base en
    # cada uno. Antes se avanzaba a ciegas de 90 en 90 desde x=45: si una placa
    # caía justo en ese paso, un tramo entero de encimera se quedaba sin enchufe
    # (en la cocina del croquis, 407 cm con UNA sola base).
    ocupado = sorted((px - 10, px + pw + 10) for (px, pw) in prohibido)
    libres, cursor = [], 0
    for a0, a1 in ocupado:
        if a0 > cursor:
            libres.append((cursor, min(a0, ancho_pared)))
        cursor = max(cursor, a1)
    if cursor < ancho_pared:
        libres.append((cursor, ancho_pared))

    n_tomas = 0
    for ini, fin in libres:
        largo = fin - ini
        if largo < 40:
            continue                      # no cabe una base con holgura
        cuantas = max(1, int(largo // 90))
        paso = largo / (cuantas + 1)
        for k in range(1, cuantas + 1):
            n_tomas += 1
            puntos.append(_punto(
                f"Enchufe encimera {n_tomas}", C5, int(ini + paso * k),
                H_ENCHUFE_SALPICADERO,
                "Base doble sobre encimera, fuera de la zona de salpicaduras "
                "del fregadero y de la placa."))
    if n_tomas:
        potencias.append(2000)   # previsión conjunta de pequeño electrodoméstico

    puntos.append(_punto("Alumbrado general", C1, None, 240,
                         "Techo. Circuito independiente."))
    puntos.append(_punto("Alumbrado bajo muebles altos", C1, None, 150,
                         "Tira LED bajo los altos, con driver accesible."))
    potencias.append(500)
    if con_isla:
        puntos.append(_punto("Alumbrado sobre isla", C1, None, 240,
                             "Suspensión centrada sobre la isla."))

    # POTENCIA DE VERDAD: en vatios y con simultaneidad. Sumar los calibres de
    # los magnetotérmicos no es la potencia (ocho de 16 A no dan 128 A).
    p_instalada = sum(potencias)
    p_simultanea = int(round(p_instalada * SIMULTANEIDAD))
    intensidad = round(p_simultanea / TENSION_V, 1)
    circuitos = sorted({p["circuito"] for p in puntos})

    resumen = (
        f"{len(circuitos)} circuitos ({', '.join(circuitos)}) según REBT ITC-BT-25. "
        f"Potencia instalada {p_instalada / 1000:.1f} kW; con coeficiente de "
        f"simultaneidad {SIMULTANEIDAD:g}, potencia de cálculo "
        f"{p_simultanea / 1000:.1f} kW ({intensidad} A a {TENSION_V} V). "
        "Protección diferencial 30 mA y conductor de protección en todos los circuitos."
    )
    return {
        "puntos": puntos,
        "circuitos": resumen,
        "potencia_instalada_w": p_instalada,
        "potencia_calculo_w": p_simultanea,
        "intensidad_a": intensidad,
        "simultaneidad": SIMULTANEIDAD,
    }


def plan_fontaneria(elementos: List[Dict], con_isla: bool) -> Dict:
    """Agua y desagüe. Solo si hay un módulo que lo pida."""
    puntos: List[Dict] = []
    fregaderos = [e for e in elementos if _es(str(e.get("id") or ""), "fregadero", "seno")]
    lavavajillas = [e for e in elementos if _es(str(e.get("id") or ""), "lavavajillas")]
    lavadoras = [e for e in elementos if _es(str(e.get("id") or ""), "lavadora")]

    for e in fregaderos:
        x = _centro(e)
        etiqueta = str(e.get("label") or "Fregadero")
        puntos.append({"tipo": "Agua fría", "x_cm": x, "altura_cm": H_AGUA_FREGADERO,
                       "detalle": "Llave de escuadra individual, accesible con el "
                                  "mueble montado.", "modulo": etiqueta})
        puntos.append({"tipo": "Agua caliente (ACS)", "x_cm": x, "altura_cm": H_AGUA_FREGADERO,
                       "detalle": "Llave de escuadra individual.", "modulo": etiqueta})
        puntos.append({"tipo": "Desagüe fregadero", "x_cm": x, "altura_cm": H_DESAGUE,
                       "detalle": "Sifón con registro, ∅40 mm, con pendiente hacia "
                                  "la bajante (CTE DB-HS5).", "modulo": etiqueta})
    for e in lavavajillas:
        x = _centro(e)
        puntos.append({"tipo": "Agua fría lavavajillas", "x_cm": x, "altura_cm": H_AGUA_FREGADERO,
                       "detalle": "Toma independiente con llave de corte propia.",
                       "modulo": str(e.get("label") or "Lavavajillas")})
        puntos.append({"tipo": "Desagüe lavavajillas", "x_cm": x, "altura_cm": H_DESAGUE,
                       "detalle": "Conexión al sifón del fregadero con válvula "
                                  "antirretorno.", "modulo": str(e.get("label") or "Lavavajillas")})
    for e in lavadoras:
        x = _centro(e)
        puntos.append({"tipo": "Agua fría lavadora", "x_cm": x, "altura_cm": H_AGUA_FREGADERO,
                       "detalle": "Toma con llave de corte propia.",
                       "modulo": str(e.get("label") or "Lavadora")})
        puntos.append({"tipo": "Desagüe lavadora", "x_cm": x, "altura_cm": H_DESAGUE,
                       "detalle": "Bote sifónico o conexión con sifón propio.",
                       "modulo": str(e.get("label") or "Lavadora")})
    if con_isla and fregaderos:
        puntos.append({"tipo": "Paso de instalación a isla", "x_cm": None,
                       "altura_cm": 0,
                       "detalle": "Si el fregadero va a la isla, agua y desagüe "
                                  "cruzan por el suelo: hay que preverlo ANTES de "
                                  "solar.", "modulo": "Isla"})
    return {"puntos": puntos}


def plan_gas(elementos: List[Dict], descripcion: str) -> Optional[Dict]:
    """Gas solo si lo hay. No se supone nunca."""
    texto = (descripcion or "").lower()
    hay_placa_gas = any(
        _es(str(e.get("id") or "") + " " + str(e.get("label") or ""), "gas")
        for e in elementos) or "gas" in texto
    if not hay_placa_gas:
        return None
    placas = [e for e in elementos if _es(str(e.get("id") or ""), "placa", "cocina")]
    x = _centro(placas[0]) if placas else None
    return {"puntos": [
        {"tipo": "Toma de gas para placa", "x_cm": x, "altura_cm": H_TOMA_ELECTRO_BAJO,
         "detalle": "Llave de corte individual accesible sin desmontar el mueble."},
        {"tipo": "Llave de paso general", "x_cm": None, "altura_cm": 150,
         "detalle": "Fuera del mueble, visible y accesible."},
        {"tipo": "Ventilación permanente", "x_cm": None, "altura_cm": 10,
         "detalle": "Obligatoria en local con aparato de gas (RD 919/2006)."},
    ]}


NORMATIVA = (
    "Electricidad: REBT (RD 842/2002), ITC-BT-25 para circuitos de vivienda. "
    "Fontanería: CTE DB-HS4 (suministro de agua) y DB-HS5 (evacuación). "
    "Gas: RD 919/2006. "
    "Ejecución por instalador habilitado y con certificado."
)
