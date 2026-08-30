# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
EL ALZADO TIENE QUE SER LA COCINA QUE HAY EN EL DISEÑO.

El master, 30/08: «lo de poner medidas me refiero al dibujo que hace, que no
cuadra con el diseño».

Y no cuadraba. Con la cocina de su captura —cajonera 90 + placa 90 en una pared
de 180, y fregadero 100 + lavavajillas 45 + lavadora 60 + columna 60 en una de
265— el alzado dibujaba:

    Pared 1:  ~120 y ~60      (le habían dado 90 y 90)
    Pared 2:  ~90 ~60 ~50 ~60 y un relleno de ~5   (le habían dado 100/45/60/60)

Las sumas cuadraban con la pared, pero NINGÚN módulo era el del diseño.

LA CAUSA, Y ESTABA ESCRITA AL LADO. `ANCHO_FIJO` es —dice su propio comentario—
«lo que mide un electrodoméstico CUANDO NADIE HA DICHO NADA». Pero el código lo
aplicaba aunque el ancho VINIERA EN LA DISTRIBUCIÓN: solo respetaba el que traía
la marca `medida_escrita` (una cota leída del plano). Un ancho que llega en el
elemento ya es alguien diciéndolo — lo ha leído el detector del diseño o lo ha
tecleado el master en el panel.

Y EL DAÑO ERA DOBLE, que es lo que lo hacía tan visible: al bajar la placa de 90
a 60 sobraban 30 cm, y esos 30 cm ESTIRABAN el mueble de al lado —la cajonera de
90 pasaba a 120—. Dos módulos mal por cada aparato.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

from services.kitchen_geometry import ANCHO_FIJO, validar_distribucion  # noqa: E402

# La cocina de la captura del master, tal cual.
COCINA = {
    "tipo": "l",
    "paredes": [{"nombre": "Pared 1", "ancho": 180, "alto": 240},
                {"nombre": "Pared 2", "ancho": 265, "alto": 240}],
    "elementos": [
        {"id": "cajonera", "label": "Cajonera bajo placa", "pared_idx": 0,
         "posicion_cm": 0, "ancho": 90},
        {"id": "placa", "label": "Placa", "pared_idx": 0, "posicion_cm": 90, "ancho": 90},
        {"id": "fregadero", "label": "Mueble fregadero", "pared_idx": 1,
         "posicion_cm": 0, "ancho": 100},
        {"id": "lavavajillas", "label": "Lavavajillas", "pared_idx": 1,
         "posicion_cm": 100, "ancho": 45},
        {"id": "lavadora", "label": "Lavadora", "pared_idx": 1,
         "posicion_cm": 145, "ancho": 60},
        {"id": "columna_hornos", "label": "Columna Horno/Micro", "pared_idx": 1,
         "posicion_cm": 205, "ancho": 60},
    ],
}


def _anchos(pidx, fila="bajo"):
    r = validar_distribucion(COCINA)
    assert r["ok"], r.get("motivo")
    return [(e["label"], e["ancho"]) for e in r["elementos"]
            if e["pared_idx"] == pidx and e.get("fila") == fila]


def test_LOS_MODULOS_SALEN_CON_EL_ANCHO_DEL_DISENO():
    """El fallo del master, tal cual, en las dos paredes."""
    assert _anchos(0) == [("Cajonera bajo placa", 90), ("Placa", 90)], (
        "la pared 1 no se dibuja con los anchos del diseño (eran 90 y 90)")
    assert _anchos(1) == [("Mueble fregadero", 100), ("Lavavajillas", 45),
                          ("Lavadora", 60), ("Columna Horno/Micro", 60)], (
        "la pared 2 no se dibuja con los anchos del diseño")


def test_SI_LA_SUMA_YA_CUADRA_NO_SE_TOCA_NADA():
    """90+90 son 180 y 100+45+60+60 son 265: no hay nada que repartir.

    Aun así se reescribían los anchos, porque primero se pisaba el del aparato y
    luego se estiraban los demás para volver a cuadrar. La suma seguía dando el
    ancho de la pared —por eso no saltaba ningún aviso— y el plano parecía bueno.
    """
    r = validar_distribucion(COCINA)
    for pidx, ancho in ((0, 180), (1, 265)):
        suma = sum(e["ancho"] for e in r["elementos"]
                   if e["pared_idx"] == pidx and e["fila"] == "bajo")
        assert suma == ancho, f"pared {pidx+1}: los módulos suman {suma} y la pared mide {ancho}"


def test_NO_SE_INVENTA_UN_RELLENO_QUE_NO_HACE_FALTA():
    """Salía un «Relleno 5» al final de la pared 2 que no existía en el diseño:
    era el sobrante de haber encogido los aparatos."""
    r = validar_distribucion(COCINA)
    rellenos = [e for e in r["elementos"] if e["id"] == "relleno"]
    assert not rellenos, f"se ha inventado un relleno: {[e['label'] for e in rellenos]}"


def test_EL_CATALOGO_SOLO_ENTRA_CUANDO_NADIE_HA_DICHO_EL_ANCHO():
    """La otra mitad: sin dato SÍ se usa el estándar del aparato, que es para lo
    que está. Lo que no vale es usarlo pisando lo que sí se sabe."""
    sin_dato = dict(COCINA)
    sin_dato["elementos"] = [
        {"id": "cajonera", "label": "Cajonera", "pared_idx": 0, "posicion_cm": 0, "ancho": 120},
        {"id": "lavavajillas", "label": "Lavavajillas", "pared_idx": 0, "posicion_cm": 120},
    ]
    sin_dato["paredes"] = [{"nombre": "P", "ancho": 180, "alto": 240}]
    r = validar_distribucion(sin_dato)
    assert r["ok"], r.get("motivo")
    lv = next(e for e in r["elementos"] if e["id"] == "lavavajillas")
    assert lv["ancho"] == ANCHO_FIJO["lavavajillas"], (
        "sin ancho, un lavavajillas tiene que salir con su medida de catálogo")
    assert lv["ancho_desconocido"] is True, (
        "y su cota tiene que rotularse «?», no como si fuera un dato")


def test_UN_ANCHO_QUE_NO_EXISTE_CAE_AL_DE_CATALOGO_Y_SE_DICE():
    """La otra cara, y por la que hay una lista corta de anchos reales.

    Una placa de 90 existe y se respeta. Una «de 70» no es una placa: es una
    lectura floja del diseño, así que se dibuja con la de catálogo Y SE AVISA.
    Corregir por detrás y callarse es como se cuela una medida inventada en un
    plano que va a fábrica (regla de oro).
    """
    raro = {
        "paredes": [{"nombre": "P", "ancho": 180, "alto": 240}],
        "elementos": [
            {"id": "bajo", "label": "Bajo", "pared_idx": 0, "posicion_cm": 0, "ancho": 120},
            {"id": "placa", "label": "Placa", "pared_idx": 0, "posicion_cm": 120, "ancho": 70},
        ],
    }
    r = validar_distribucion(raro)
    placa = next(e for e in r["elementos"] if e["id"] == "placa")
    assert placa["ancho"] == 60, (
        f"una placa «de 70» se ha dibujado tal cual ({placa['ancho']} cm): ese "
        "ancho no existe en una placa")
    avisos = " ".join(r.get("avisos") or [])
    assert "Placa" in avisos and "no es un ancho real" in avisos, (
        f"se ha corregido por detrás, sin decirlo. Avisos: {avisos}")


def test_PERO_LA_PLACA_DE_90_SI_SE_RESPETA():
    """Es el caso del master, y el que distingue esto de no hacer nada."""
    r = validar_distribucion(COCINA)
    placa = next(e for e in r["elementos"] if e["id"] == "placa")
    assert placa["ancho"] == 90


def test_LA_TABLA_DE_ANCHOS_SIGUE_AHI_PARA_CUANDO_HACE_FALTA():
    for aparato in ("lavavajillas", "placa", "horno", "frigorifico"):
        assert aparato in ANCHO_FIJO, (
            f"«{aparato}» ha salido de `ANCHO_FIJO`: sin dato no habría con qué "
            "dibujarlo")


def test_UNA_LAVADORA_NO_CAMBIA_DE_TAMANO_PARA_CUADRAR_LA_PARED():
    """`lavadora` NO estaba en la tabla, así que se trataba como un mueble
    flexible: se estiraba y se encogía para cuadrar. En la cocina del master
    salió dibujada de 50 cm. Una lavadora mide 60 y no negocia."""
    assert ANCHO_FIJO.get("lavadora") == 60
    apretada = {
        "paredes": [{"nombre": "P", "ancho": 200, "alto": 240}],
        "elementos": [
            {"id": "lavadora", "label": "Lavadora", "pared_idx": 0, "posicion_cm": 0},
            {"id": "bajo", "label": "Bajo", "pared_idx": 0, "posicion_cm": 60, "ancho": 100},
        ],
    }
    r = validar_distribucion(apretada)
    lav = next(e for e in r["elementos"] if e["id"] == "lavadora")
    assert lav["ancho"] == 60, (
        f"la lavadora se ha encogido a {lav['ancho']} cm para que cuadre la pared")
