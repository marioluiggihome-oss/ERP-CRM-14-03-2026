"""Historial de fotos por proyecto (Estudio 3D).

Antes, un proyecto guardaba UNA sola foto: el historial vivía en memoria del
navegador y al recargar la pagina se perdia todo lo generado. Ahora cada imagen
es un documento propio en `render3d_images`.

Lo que se protege aqui:
  1. Guardar dos veces la misma foto NO la duplica (el guardado automatico
     reenvia el historial cada pocos segundos).
  2. Las fotos de un proyecto no se mezclan con las de otro.
  3. Borrar el proyecto borra sus fotos (si no, ocupan espacio para siempre).
  4. Otro usuario no puede leer ni escribir el historial ajeno.
  5. El tope por proyecto y el tope por foto se respetan.

Mongo se sustituye por un doble en memoria: no hace falta base de datos.
"""
import asyncio
import importlib.util
import os
import sys
import types

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _coincide(doc, filtro):
    return all(doc.get(k) == v for k, v in (filtro or {}).items())


class _Cursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, campo, orden=1):
        self.docs = sorted(self.docs, key=lambda d: d.get(campo) or "", reverse=orden < 0)
        return self

    def skip(self, n):
        self.docs = self.docs[n:]
        return self

    def limit(self, n):
        self.docs = self.docs[:n]
        return self

    async def to_list(self, n):
        return [dict(d) for d in self.docs[:n]]


class _Coleccion:
    def __init__(self):
        self.docs = []

    async def find_one(self, filtro, proj=None):
        for d in self.docs:
            if _coincide(d, filtro):
                return dict(d)
        return None

    def find(self, filtro=None, proj=None):
        return _Cursor([dict(d) for d in self.docs if _coincide(d, filtro)])

    async def insert_one(self, doc):
        self.docs.append(dict(doc))

    async def count_documents(self, filtro):
        return len([d for d in self.docs if _coincide(d, filtro)])

    async def update_one(self, filtro, upd, upsert=False):
        for d in self.docs:
            if _coincide(d, filtro):
                d.update(upd.get("$set", {}))
                return
        if upsert:
            nuevo = dict(filtro)
            nuevo.update(upd.get("$set", {}))
            self.docs.append(nuevo)

    async def delete_one(self, filtro):
        for i, d in enumerate(self.docs):
            if _coincide(d, filtro):
                self.docs.pop(i)
                return types.SimpleNamespace(deleted_count=1)
        return types.SimpleNamespace(deleted_count=0)

    async def delete_many(self, filtro):
        antes = len(self.docs)
        self.docs = [d for d in self.docs if not _coincide(d, filtro)]
        return types.SimpleNamespace(deleted_count=antes - len(self.docs))


class _BaseDatos:
    def __init__(self):
        self._c = {}

    def __getitem__(self, n):
        return self

    def __getattr__(self, n):
        return self._c.setdefault(n, _Coleccion())


DUENO = {"id": "u42", "clientName": "Mario"}
OTRO = {"id": "u99", "clientName": "Ajeno"}
ADMIN = {"id": "adm", "isAdmin": True}


@pytest.fixture()
def motor(monkeypatch):
    """Carga routes/ai_engine.py con Mongo simulado y sin el motor de IA real."""
    servicios = types.ModuleType("services")
    servicios.__path__ = [os.path.join(BACKEND, "services")]
    monkeypatch.setitem(sys.modules, "services", servicios)

    dbc = types.ModuleType("services.db_client")
    base = _BaseDatos()
    dbc.get_db = lambda: base
    monkeypatch.setitem(sys.modules, "services.db_client", dbc)

    jwt = types.ModuleType("services.jwt_service")

    async def _req():
        return DUENO
    jwt.require_auth = _req
    jwt.verify_access_token = lambda *a, **k: DUENO
    jwt.get_current_user = _req
    jwt.ADMIN_ROLE_FLAGS = ["isAdmin", "isGerente", "isDirectorComercial"]
    monkeypatch.setitem(sys.modules, "services.jwt_service", jwt)

    ia = types.ModuleType("services.luiggi_ai")
    ia.get_engine = lambda *a, **k: None
    ia.get_render_service = lambda *a, **k: None
    ia.get_ai_config = lambda *a, **k: {}
    monkeypatch.setitem(sys.modules, "services.luiggi_ai", ia)

    # ai_engine declara rutas con Form(...) y FastAPI exige python-multipart al
    # registrarlas. Aqui no se sube ningun formulario, asi que se simula: es una
    # dependencia menos que instalar para ejecutar las pruebas.
    if "python_multipart" not in sys.modules:
        pm = types.ModuleType("python_multipart")
        pm.__version__ = "0.0.20"
        monkeypatch.setitem(sys.modules, "python_multipart", pm)

    # httpx solo se usa para descargar imagenes remotas: aqui no se toca la red.
    httpx_falso = types.ModuleType("httpx")
    httpx_falso.AsyncClient = object
    httpx_falso.Timeout = lambda *a, **k: None
    monkeypatch.setitem(sys.modules, "httpx", httpx_falso)

    rutas = types.ModuleType("routes")
    rutas.__path__ = [os.path.join(BACKEND, "routes")]
    monkeypatch.setitem(sys.modules, "routes", rutas)

    spec = importlib.util.spec_from_file_location(
        "routes.ai_engine", os.path.join(BACKEND, "routes", "ai_engine.py"))
    mod = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "routes.ai_engine", mod)
    spec.loader.exec_module(mod)
    mod._db = base
    return mod


def _foto(n, tam=200):
    """Una foto distinta por cada n (el contenido es lo que la identifica)."""
    return {"dataUrl": "data:image/jpeg;base64," + (str(n) * tam), "descripcion": f"foto {n}"}


async def _proyecto(m, ident="r3d-1", usuario=DUENO):
    await m.save_render_design({"id": ident, "cliente": "PRUEBA OLG", "ref": "Cocina"}, usuario)
    return ident


def test_las_fotos_se_guardan_y_se_recuperan_del_proyecto(motor):
    async def esc():
        pid = await _proyecto(motor)
        r = await motor.add_design_images(pid, {"imagenes": [_foto(1), _foto(2), _foto(3)]}, DUENO)
        assert r["guardadas"] == 3 and r["total"] == 3
        lista = await motor.list_design_images(pid, 0, 12, DUENO)
        assert lista["total"] == 3
        assert len(lista["imagenes"]) == 3
        assert all(i.get("dataUrl") for i in lista["imagenes"]), "una foto guardada sin contenido"
    asyncio.run(esc())


def test_guardar_dos_veces_la_misma_foto_no_la_duplica(motor):
    """El guardado automatico reenvia el historial: no puede acumular copias."""
    async def esc():
        pid = await _proyecto(motor)
        await motor.add_design_images(pid, {"imagenes": [_foto(1), _foto(2)]}, DUENO)
        r = await motor.add_design_images(pid, {"imagenes": [_foto(1), _foto(2), _foto(3)]}, DUENO)
        assert r["repetidas"] == 2 and r["guardadas"] == 1
        assert r["total"] == 3, "el historial se ha duplicado al volver a guardar"
    asyncio.run(esc())


def test_cada_foto_devuelve_su_id_para_poder_borrarla(motor):
    async def esc():
        pid = await _proyecto(motor)
        r = await motor.add_design_images(pid, {"imagenes": [_foto(1), _foto(2)]}, DUENO)
        ids = [x.get("id") for x in r["resultados"] if x["estado"] == "guardada"]
        assert len(ids) == 2 and all(ids)
        b = await motor.delete_design_image(pid, ids[0], DUENO)
        assert b["borradas"] == 1 and b["total"] == 1
    asyncio.run(esc())


def test_las_fotos_no_se_mezclan_entre_proyectos(motor):
    async def esc():
        a = await _proyecto(motor, "r3d-a")
        b = await _proyecto(motor, "r3d-b")
        await motor.add_design_images(a, {"imagenes": [_foto(1), _foto(2)]}, DUENO)
        await motor.add_design_images(b, {"imagenes": [_foto(9)]}, DUENO)
        assert (await motor.list_design_images(a, 0, 12, DUENO))["total"] == 2
        lb = await motor.list_design_images(b, 0, 12, DUENO)
        assert lb["total"] == 1, "se han colado fotos de otro proyecto"
        assert "9" in lb["imagenes"][0]["dataUrl"]
    asyncio.run(esc())


def test_borrar_el_proyecto_borra_sus_fotos(motor):
    async def esc():
        pid = await _proyecto(motor)
        await motor.add_design_images(pid, {"imagenes": [_foto(1), _foto(2)]}, DUENO)
        await motor.delete_render_design(pid, DUENO)
        quedan = await motor._db.render3d_images.count_documents({"designId": pid})
        assert quedan == 0, "las fotos quedan huerfanas ocupando espacio"
    asyncio.run(esc())


def test_otro_usuario_no_ve_ni_escribe_el_historial_ajeno(motor):
    async def esc():
        pid = await _proyecto(motor)
        await motor.add_design_images(pid, {"imagenes": [_foto(1)]}, DUENO)
        with pytest.raises(motor.HTTPException) as e1:
            await motor.list_design_images(pid, 0, 12, OTRO)
        assert e1.value.status_code == 403
        with pytest.raises(motor.HTTPException) as e2:
            await motor.add_design_images(pid, {"imagenes": [_foto(5)]}, OTRO)
        assert e2.value.status_code == 403
        # El admin si entra.
        assert (await motor.list_design_images(pid, 0, 12, ADMIN))["total"] == 1
    asyncio.run(esc())


def test_proyecto_inexistente_da_404(motor):
    with pytest.raises(motor.HTTPException) as e:
        asyncio.run(motor.list_design_images("no-existe", 0, 12, DUENO))
    assert e.value.status_code == 404


def test_se_pagina_y_no_se_devuelve_todo_de_golpe(motor):
    """Devolver 40 fotos en una respuesta son decenas de MB: se pagina."""
    async def esc():
        pid = await _proyecto(motor)
        for i in range(0, 20, 5):
            await motor.add_design_images(
                pid, {"imagenes": [_foto(n) for n in range(i, i + 5)]}, DUENO)
        p1 = await motor.list_design_images(pid, 0, 12, DUENO)
        assert len(p1["imagenes"]) == 12 and p1["total"] == 20 and p1["hayMas"] is True
        p2 = await motor.list_design_images(pid, 12, 12, DUENO)
        assert len(p2["imagenes"]) == 8 and p2["hayMas"] is False
        # Aunque se pida mas, el tope por respuesta manda.
        assert len((await motor.list_design_images(pid, 0, 999, DUENO))["imagenes"]) == 20
    asyncio.run(esc())


def test_una_foto_enorme_no_se_guarda(motor):
    async def esc():
        pid = await _proyecto(motor)
        enorme = {"dataUrl": "data:image/jpeg;base64," + ("x" * (motor.MAX_BYTES_IMAGEN + 10))}
        r = await motor.add_design_images(pid, {"imagenes": [enorme, _foto(1)]}, DUENO)
        assert r["descartadas"] == 1 and r["guardadas"] == 1
    asyncio.run(esc())


class _DriveFalso(types.ModuleType):
    """Drive simulado: guarda lo que le suben y puede fallar a voluntad."""

    def __init__(self, funciona=True):
        super().__init__("services.drive_fotos")
        self.funciona = funciona
        self.archivos = {}
        self.carpetas = []

    def esta_configurado(self):
        return True

    def carpeta_de_proyecto(self, nombre):
        if not self.funciona:
            return {"ok": False, "error": "Drive caido"}
        self.carpetas.append(nombre)
        return {"ok": True, "id": "carp-1", "nombre": nombre, "creada": True}

    def subir_imagen(self, data_url, nombre, carpeta_id):
        if not self.funciona or getattr(self, "falla_subida", False):
            return {"ok": False, "error": "Drive caido"}
        fid = f"drive-{len(self.archivos) + 1}"
        self.archivos[fid] = data_url
        return {"ok": True, "id": fid, "nombre": nombre, "enlace": f"https://drive/{fid}"}

    def descargar_imagen(self, file_id):
        if file_id not in self.archivos:
            return {"ok": False, "error": "no esta"}
        return {"ok": True, "datos": b"contenido", "mime": "image/jpeg"}

    def a_papelera(self, file_id):
        self.archivos.pop(file_id, None)
        return {"ok": True}

    def trocear_data_url(self, data_url):
        if not isinstance(data_url, str) or not data_url.startswith("data:"):
            return None, None
        return b"contenido", "image/jpeg"


def _con_drive(motor, monkeypatch, funciona=True):
    falso = _DriveFalso(funciona)
    monkeypatch.setitem(sys.modules, "services.drive_fotos", falso)
    setattr(sys.modules["services"], "drive_fotos", falso)
    return falso


def _foto_con_miniatura(n):
    f = _foto(n, tam=400)
    f["miniatura"] = "data:image/jpeg;base64,mini" + str(n)
    return f


def test_con_drive_la_foto_grande_va_a_drive_y_aqui_queda_la_miniatura(motor, monkeypatch):
    """Es la razon de ser de esto: no llenar los 5 GB de MongoDB con renders."""
    async def esc():
        drive = _con_drive(motor, monkeypatch)
        pid = await _proyecto(motor)
        r = await motor.add_design_images(
            pid, {"imagenes": [_foto_con_miniatura(1), _foto_con_miniatura(2)]}, DUENO)
        assert r["drive"] is True and r["guardadas"] == 2
        assert len(drive.archivos) == 2, "las fotos no han llegado a Drive"
        guardadas = motor._db.render3d_images.docs
        assert all(d["dataUrl"].startswith("data:image/jpeg;base64,mini") for d in guardadas), \
            "se ha guardado la foto grande en la base de datos"
        assert all(d.get("enDrive") and d.get("driveId") for d in guardadas)
        # La carpeta se crea una sola vez y lleva el nombre del proyecto.
        assert drive.carpetas == ["PRUEBA OLG · Cocina"]
    asyncio.run(esc())


def test_si_drive_falla_la_foto_se_guarda_igual_en_el_erp(motor, monkeypatch):
    """Un fallo de Google no puede hacer que se pierda el trabajo."""
    async def esc():
        _con_drive(motor, monkeypatch, funciona=False)
        pid = await _proyecto(motor)
        r = await motor.add_design_images(pid, {"imagenes": [_foto_con_miniatura(1)]}, DUENO)
        assert r["guardadas"] == 1, "se ha perdido la foto por un fallo de Drive"
        assert r["driveAviso"] is None or "Drive" in r["driveAviso"]
        doc = motor._db.render3d_images.docs[0]
        assert doc["dataUrl"].startswith("data:image/jpeg;base64,1"), \
            "sin Drive hay que guardar la foto entera aqui"
        assert not doc.get("enDrive")
    asyncio.run(esc())


def test_si_falla_la_subida_se_avisa_y_la_foto_queda_entera_en_el_erp(motor, monkeypatch):
    async def esc():
        drive = _con_drive(motor, monkeypatch)
        drive.falla_subida = True  # la carpeta se crea, pero la subida se cae
        pid = await _proyecto(motor)
        r = await motor.add_design_images(pid, {"imagenes": [_foto_con_miniatura(1)]}, DUENO)
        assert r["guardadas"] == 1
        assert r["driveAviso"] and "Drive" in r["driveAviso"], "hay que avisar del fallo"
        doc = motor._db.render3d_images.docs[0]
        assert doc["dataUrl"].startswith("data:image/jpeg;base64,1") and not doc.get("enDrive")
        assert doc.get("driveError"), "no queda constancia del fallo"
    asyncio.run(esc())


def test_la_foto_de_drive_se_sirve_por_el_erp_y_no_por_enlace_publico(motor, monkeypatch):
    async def esc():
        _con_drive(motor, monkeypatch)
        pid = await _proyecto(motor)
        r = await motor.add_design_images(pid, {"imagenes": [_foto_con_miniatura(1)]}, DUENO)
        iid = [x["id"] for x in r["resultados"] if x["estado"] == "guardada"][0]
        resp = await motor.get_design_image_file(pid, iid, None, DUENO)
        assert resp.body == b"contenido" and resp.media_type == "image/jpeg"
        # Y un extrano no puede descargarla.
        with pytest.raises(motor.HTTPException) as e:
            await motor.get_design_image_file(pid, iid, None, OTRO)
        assert e.value.status_code == 403
    asyncio.run(esc())


def test_borrar_una_foto_la_manda_a_la_papelera_de_drive(motor, monkeypatch):
    async def esc():
        drive = _con_drive(motor, monkeypatch)
        pid = await _proyecto(motor)
        r = await motor.add_design_images(pid, {"imagenes": [_foto_con_miniatura(1)]}, DUENO)
        iid = [x["id"] for x in r["resultados"] if x["estado"] == "guardada"][0]
        await motor.delete_design_image(pid, iid, DUENO)
        assert drive.archivos == {}, "la foto sigue ocupando sitio en Drive"
    asyncio.run(esc())


def test_borrar_el_proyecto_no_se_lleva_por_delante_el_drive(motor, monkeypatch):
    """El archivo de fotos de la empresa no se borra desde el ERP."""
    async def esc():
        drive = _con_drive(motor, monkeypatch)
        pid = await _proyecto(motor)
        await motor.add_design_images(pid, {"imagenes": [_foto_con_miniatura(1)]}, DUENO)
        await motor.delete_render_design(pid, DUENO)
        assert len(drive.archivos) == 1, "se han borrado las fotos del Drive de la empresa"
    asyncio.run(esc())


def test_el_tope_por_proyecto_se_respeta(motor):
    async def esc():
        pid = await _proyecto(motor)
        motor.MAX_IMGS_PROYECTO = 5  # el tope real es 120; se baja para la prueba
        try:
            await motor.add_design_images(pid, {"imagenes": [_foto(n) for n in range(4)]}, DUENO)
            r = await motor.add_design_images(pid, {"imagenes": [_foto(n) for n in range(4, 9)]}, DUENO)
            assert r["total"] == 5, "se ha pasado del tope de fotos por proyecto"
            assert r["lleno"] is True, "hay que avisar de que el proyecto esta lleno"
        finally:
            motor.MAX_IMGS_PROYECTO = 120
    asyncio.run(esc())
