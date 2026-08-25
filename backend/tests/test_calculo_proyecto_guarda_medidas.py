# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
UN PROYECTO GUARDADO SE ABRE CON LAS MEDIDAS CON LAS QUE SE CERRÓ.

El master, 24/08/2026: «mírate el último proyecto guardado, lo que pasa con las
medidas».

Lo que pasaba: NO SE GUARDABAN. El botón decía «Guardar el proyecto (cliente,
referencia, MEDIDAS, renders e historial)» y al servidor solo viajaban cliente,
referencia, descripción, estilo e imágenes. El ancho, el fondo y la altura
vivían únicamente en la sesión del navegador, así que mientras no cerraras la
pestaña parecía funcionar; al recargar, o al abrir el proyecto otro día o en
otro aparato, las tres casillas salían vacías.

Y de ahí venía lo de las cotas. Sin el ancho real, la pared deja de estar
anclada: `validar_distribucion` no tiene contra qué cuadrar y cada módulo pasa
de medida ESCRITA a ESTIMADA, con la virgulilla delante. Los números cambiaban
solos entre una sesión y la siguiente sin que nadie tocara nada.

Se guarda también la DISTRIBUCIÓN, que es el trabajo de detectarla y corregirla
a mano módulo por módulo, y se perdía entero al cerrar.

Esta prueba LLAMA al endpoint con una base de datos de mentira. Comprobar la
lista de claves leyendo el fichero no valdría: lo que rompe de verdad es el
`$set`, y eso solo se ve ejecutándolo.
"""
import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")


class _Coleccion:
    """Lo justo de Mongo para este endpoint: un `find_one` y un `update_one`."""

    def __init__(self):
        self.docs = {}

    async def find_one(self, filtro, proyeccion=None):
        doc = self.docs.get(filtro.get("id"))
        if doc is None:
            return None
        if not proyeccion:
            return dict(doc)
        # Se respeta la proyección A PROPÓSITO: el fallo que se persigue es
        # justo pedir menos campos de los que luego se leen.
        pedidas = [k for k, v in proyeccion.items() if v == 1]
        return {k: doc[k] for k in pedidas if k in doc}

    async def update_one(self, filtro, cambio, upsert=False):
        oid = filtro.get("id")
        actual = self.docs.get(oid, {})
        actual.update(cambio.get("$set") or {})
        self.docs[oid] = actual


class _Db:
    def __init__(self):
        self.render3d_designs = _Coleccion()


USUARIO = {"id": "u-master", "username": "master", "isAdmin": True}


@pytest.fixture()
def guardar(monkeypatch):
    from routes import ai_engine
    db = _Db()
    monkeypatch.setattr(ai_engine, "_db", db)
    return ai_engine.save_render_design, db


MEDIDAS = {"ancho": "367", "fondo": "300", "altura": "255", "aberturas": "ventana a la izquierda"}
DISTRIBUCION = {
    "tipo": "lineal",
    "paredes": [{"nombre": "Pared 1", "ancho": 367, "alto": 255, "ancho_escrito": True}],
    "elementos": [{"id": "bajo", "ancho": 120, "pared_idx": 0, "posicion_cm": 0, "medida_escrita": True}],
}


def test_al_guardar_un_proyecto_las_medidas_van_al_servidor(guardar):
    endpoint, db = guardar
    r = asyncio.run(endpoint(
        {"cliente": "Pepe", "ref": "A1", "images": ["x"], "medidas": MEDIDAS},
        current_user=USUARIO))
    oid = r["design"]["id"]
    assert db.render3d_designs.docs[oid].get("medidas") == MEDIDAS, (
        "las medidas no se han guardado. Sin ellas, al reabrir el proyecto la "
        "pared se queda sin anclar y todas las cotas pasan de escritas a "
        "estimadas — que es justo lo que vio el master el 24/08.")


def test_al_guardar_tambien_va_la_distribucion_corregida_a_mano(guardar):
    endpoint, db = guardar
    r = asyncio.run(endpoint(
        {"cliente": "Pepe", "images": ["x"], "distribucion": DISTRIBUCION, "tipo3d": "cocina"},
        current_user=USUARIO))
    doc = db.render3d_designs.docs[r["design"]["id"]]
    assert doc.get("distribucion") == DISTRIBUCION, (
        "se pierde la distribución: detectarla y corregirla módulo a módulo es "
        "el trabajo de una tarde")
    assert doc.get("tipo3d") == "cocina"


def test_guardar_otra_vez_SIN_medidas_no_borra_las_que_ya_habia(guardar):
    """El caso que se cargaría el arreglo entero.

    Se guarda con `$set` del documento completo, así que si un guardado
    posterior no trae las medidas —una foto nueva del historial, un
    autoguardado— las pondría a `None` y las borraría. Tiene que conservarlas.
    """
    endpoint, db = guardar
    primero = asyncio.run(endpoint(
        {"cliente": "Pepe", "images": ["x"], "medidas": MEDIDAS, "distribucion": DISTRIBUCION},
        current_user=USUARIO))
    oid = primero["design"]["id"]

    asyncio.run(endpoint({"id": oid, "cliente": "Pepe", "images": ["y"]}, current_user=USUARIO))

    doc = db.render3d_designs.docs[oid]
    assert doc.get("medidas") == MEDIDAS, (
        "un guardado sin medidas ha BORRADO las que ya había. Hay que partir de "
        "lo que hubiera (y pedirlo en la proyección del `find_one`), no de None.")
    assert doc.get("distribucion") == DISTRIBUCION, (
        "un guardado sin distribución ha borrado la que ya había")
    assert doc.get("images") == ["y"], "lo que sí venía debería haberse actualizado"


def test_las_medidas_se_pueden_cambiar_guardando_encima(guardar):
    """Conservar no puede convertirse en no dejar corregir."""
    endpoint, db = guardar
    primero = asyncio.run(endpoint(
        {"cliente": "Pepe", "images": ["x"], "medidas": MEDIDAS}, current_user=USUARIO))
    oid = primero["design"]["id"]
    nuevas = dict(MEDIDAS, ancho="420")
    asyncio.run(endpoint({"id": oid, "medidas": nuevas}, current_user=USUARIO))
    assert db.render3d_designs.docs[oid]["medidas"]["ancho"] == "420", (
        "no deja rectificar el ancho de un proyecto ya guardado")


def test_la_pantalla_manda_las_medidas_y_las_recupera_al_abrir():
    """Las dos mitades, en el JSX. Guardarlas sin recuperarlas no arregla nada."""
    raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ruta = os.path.join(raiz, "frontend", "src", "components", "AIRenderStudio.jsx")
    with open(ruta, "r", encoding="utf-8") as f:
        cuerpo = f.read()

    guardado = cuerpo[cuerpo.index("const saveDesign"):]
    guardado = guardado[:guardado.index("const openList")]
    assert "medidas," in guardado and "distribucion:" in guardado, (
        "`saveDesign` ha vuelto a mandar el proyecto sin las medidas ni la "
        "distribución")

    assert "full.medidas" in cuerpo and "setMedidas(m => ({ ...m, ...full.medidas }))" in cuerpo, (
        "al abrir un proyecto ya no se recuperan las medidas guardadas")
    assert "full.distribucion" in cuerpo, (
        "al abrir un proyecto ya no se recupera la distribución guardada")
