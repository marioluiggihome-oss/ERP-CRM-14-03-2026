# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""La relación MV en PDF RELLENABLE: papel que vuelve al ERP.

Lo pidió el master para tres cosas: llevárselo en papel, enseñárselo a un
cliente y —la que más se usa— corregirlo fuera del ERP y volver a subirlo para
un pegado masivo. Por eso NO es un PDF cerrado: los campos son AcroForm y se
releen de forma determinista, sin IA de por medio.

ESTAS PRUEBAS GENERAN EL PDF Y LO VUELVEN A LEER. Un papel no se puede validar
mirando el código que lo escribe: hay que abrirlo y ver qué pone. El fallo que
acecha aquí es de FACTOR DIEZ — el PDF es en milímetros y la tarifa MV viene en
centímetros, y `_cota` no convierte: escribe el número que le den. Un bajo de
60 cm impreso como «60» significa 60 mm en ese papel, y eso llega a un taller.
"""
import asyncio
import io
import os
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKEND = os.path.join(RAIZ, "backend")
os.environ.setdefault("JWT_SECRET", "x" * 64)
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

from fastapi import HTTPException          # noqa: E402

MASTER = {"isMaster": True}


def _cocina():
    return {"tipo": "lineal",
            "paredes": [{"nombre": "Pared 1", "ancho": 360, "alto": 240}],
            "elementos": [
                {"id": "bajo_fregadero", "label": "Bajo fregadero", "pared_idx": 0,
                 "posicion_cm": 0, "ancho": 90, "fila": "bajo"},
                {"id": "alto", "label": "Alto", "pared_idx": 0,
                 "posicion_cm": 0, "ancho": 80, "fila": "alto"},
                {"id": "frigorifico", "label": "Columna frigo", "pared_idx": 0,
                 "posicion_cm": 150, "ancho": 60, "fila": "bajo"},
            ]}


def _pdf(usuario=MASTER):
    """Saca la relación MV y la pasa a PDF, como hace la pantalla."""
    from routes.estudio_cocinas import relacion_mv, relacion_mv_pdf
    r = asyncio.run(relacion_mv({"distribucion": _cocina()}, usuario))
    resp = asyncio.run(relacion_mv_pdf({"lineas": r["lineas"], "cliente": "Cliente"}, usuario))
    return r, resp.body


def _campos(pdf_bytes):
    """Los pares (campo, valor) escritos en el formulario."""
    from services.mv_relacion import extract_campos
    return extract_campos(pdf_bytes)


# ── El fallo de factor diez ─────────────────────────────────────────────────

def test_las_medidas_salen_en_MILIMETROS():
    """CANDADO. El papel es en mm; la tarifa MV, en cm. Sin convertir, un bajo
    de 60 cm sale impreso como 60 mm y eso llega a un taller."""
    relacion, pdf = _pdf()
    pares = _campos(pdf)
    anchos = [v for k, v in pares if k == "ancho"]
    assert anchos, "el PDF no lleva ni un ancho"
    cm = [ln["ancho"] for ln in relacion["lineas"]]
    assert anchos == [str(x * 10) for x in cm], (
        f"los anchos del PDF son {anchos} y los muebles miden {cm} cm: "
        "o falta el ×10, o sobra.")


def test_la_altura_de_una_columna_tambien_va_en_mm():
    """Una columna son 220 cm. En el papel, 2200.

    Esta prueba decía 200/2000 porque ése era el defecto del código hasta el
    25/08/2026; lo cambió el master al leer la auditoría («columnas de 220»). Lo
    que vigila es lo mismo —que la altura salga en MILÍMETROS en el papel, que es
    como se piden los muebles—, así que el número se lee de donde vive en vez de
    escribirlo aquí otra vez.
    """
    from services.distribucion_a_mv import ALTO_COLUMNAS
    _relacion, pdf = _pdf()
    altos = [v for k, v in _campos(pdf) if k == "alto"]
    esperado = str(ALTO_COLUMNAS * 10)
    assert esperado in altos, f"la columna no sale a {esperado} mm: {altos}"


def test_el_fondo_tambien():
    """Un bajo tiene 58 cm de fondo y un alto 33. En el papel, 580 y 330."""
    _relacion, pdf = _pdf()
    fondos = [v for k, v in _campos(pdf) if k == "fondo"]
    assert "580" in fondos and "330" in fondos, f"fondos mal escalados: {fondos}"


# ── Que el papel sirva para lo que se pidió ─────────────────────────────────

def test_el_pdf_es_RELLENABLE_y_deja_sitio_para_apuntar_a_mano():
    """Sin renglones en blanco, quien mide no puede apuntar el mueble que la IA
    no vio, y el papel deja de servir para volver al ERP."""
    from pypdf import PdfReader
    _relacion, pdf = _pdf()
    campos = PdfReader(io.BytesIO(pdf)).get_fields() or {}
    assert campos, "el PDF no tiene campos de formulario: no se puede rellenar"
    vacios = [k for k, f in campos.items() if not str(f.get("/V") or "").strip()]
    assert len(vacios) >= 30, (
        f"solo hay {len(vacios)} campos en blanco: no queda sitio para apuntar "
        "a mano lo que falte.")


def test_los_codigos_van_en_el_papel():
    """Es lo que permite el pegado masivo al volver: sin código no hay mueble."""
    relacion, pdf = _pdf()
    codigos_pdf = [v for k, v in _campos(pdf) if k == "codigo"]
    esperados = [ln["codigo"] for ln in relacion["lineas"]]
    assert codigos_pdf == esperados, f"{codigos_pdf} != {esperados}"


def test_la_mano_propuesta_sale_avisada_en_el_papel():
    """Si no se avisa, una mano que ha propuesto el programa viaja al taller
    como si la hubiera decidido alguien."""
    _relacion, pdf = _pdf()
    obs = " ".join(v for k, v in _campos(pdf) if k == "observaciones")
    assert "mano propuesta" in obs, \
        "el papel no avisa de que la mano D/I la ha propuesto el programa"


def test_NI_UN_EURO_en_un_papel_que_puede_ver_un_cliente():
    """CLAUDE.md, regla 5: el coste y los descuentos no salen en nada que vea un
    cliente. Y este papel está pensado para enseñárselo."""
    _relacion, pdf = _pdf()
    texto = " ".join(f"{k} {v}" for k, v in _campos(pdf))
    assert "€" not in texto and "EUR" not in texto.upper(), \
        f"se ha colado un importe en el PDF: {texto[:200]}"
    assert "pvp" not in texto.lower() and "punto" not in texto.lower(), \
        "se ha colado la tarifa en el PDF"


def test_sin_muebles_no_se_genera_un_papel_vacio():
    from routes.estudio_cocinas import relacion_mv_pdf
    with pytest.raises(HTTPException) as ex:
        asyncio.run(relacion_mv_pdf({"lineas": []}, MASTER))
    assert ex.value.status_code == 400
