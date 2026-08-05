# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""Recarga de renders con tarjeta: lo que puede costar dinero.

Stripe y Mongo se simulan; el router y el servicio son el codigo real. Se atacan
los tres fraudes posibles: firma falsa, webhook repetido (Stripe REINTENTA) y
precio o cantidad manipulados desde el navegador.
"""
import pytest
import asyncio, importlib.util, sys, types

import os
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, B)


def _match(d, f):
    return all(d.get(k) == v for k, v in f.items())


class Cur:
    def __init__(self, docs): self.docs = docs
    def sort(self, *a, **k): return self
    async def to_list(self, n): return [dict(d) for d in self.docs[:n]]


class Coll:
    def __init__(self): self.docs = []
    async def find_one(self, flt, proj=None):
        for d in self.docs:
            if _match(d, flt): return dict(d)
        return None
    def find(self, flt=None, proj=None): return Cur([d for d in self.docs if _match(d, flt or {})])
    async def insert_one(self, d): self.docs.append(dict(d))
    async def update_one(self, flt, upd, upsert=False):
        for d in self.docs:
            if _match(d, flt):
                for k, v in upd.get('$inc', {}).items(): d[k] = d.get(k, 0) + v
                d.update(upd.get('$set', {})); return
        if upsert:
            nd = dict(flt); nd.update(upd.get('$setOnInsert', {})); nd.update(upd.get('$set', {}))
            for k, v in upd.get('$inc', {}).items(): nd[k] = nd.get(k, 0) + v
            self.docs.append(nd)


class DB:
    def __init__(self): self._c = {}
    def __getitem__(self, n): return self
    def __getattr__(self, n): return self._c.setdefault(n, Coll())


DBI = DB()
svc = types.ModuleType('services'); svc.__path__ = [B + '/services']; sys.modules['services'] = svc
dbc = types.ModuleType('services.db_client'); dbc.get_db = lambda: DBI; sys.modules['services.db_client'] = dbc
jw = types.ModuleType('services.jwt_service')
async def _ra(): return {'id': 'u42', 'email': 'taller@x.es'}
jw.require_auth = _ra; jw.ADMIN_ROLE_FLAGS = ['isAdmin']; sys.modules['services.jwt_service'] = jw

# ai_usage real, con su Mongo simulado
sp = importlib.util.spec_from_file_location('services.ai_usage', B + '/services/ai_usage.py')
AU = importlib.util.module_from_spec(sp); sys.modules['services.ai_usage'] = AU; sp.loader.exec_module(AU)
AU.db = DBI
DBI.ai_usage_config.docs.append({"_id": "cfg", "default_credits": 0, "credits_per": {"render": 1}})

# stripe simulado
FIRMA_BUENA = 'firma-correcta'
stripe_fake = types.ModuleType('stripe')
class _Sess:
    @staticmethod
    def create(**kw):
        _Sess.ultimo = kw
        return types.SimpleNamespace(url='https://checkout.stripe.com/x', id='cs_test_1')
stripe_fake.checkout = types.SimpleNamespace(Session=_Sess)
class _WH:
    @staticmethod
    def construct_event(cuerpo, firma, secreto):
        if firma != FIRMA_BUENA: raise ValueError('Invalid signature')
        import json; return json.loads(cuerpo)
stripe_fake.Webhook = _WH
sys.modules['stripe'] = stripe_fake

import os
os.environ['STRIPE_SECRET_KEY'] = 'sk_test_x'
os.environ['STRIPE_WEBHOOK_SECRET'] = 'whsec_x'
os.environ['CORS_ORIGINS'] = 'https://erp.luiggihome.es'

s2 = importlib.util.spec_from_file_location('services.stripe_pagos', B + '/services/stripe_pagos.py')
SP = importlib.util.module_from_spec(s2); sys.modules['services.stripe_pagos'] = SP; s2.loader.exec_module(SP)
rp = types.ModuleType('routes'); rp.__path__ = [B + '/routes']; sys.modules['routes'] = rp
s3 = importlib.util.spec_from_file_location('routes.render_packs', B + '/routes/render_packs.py')
R = importlib.util.module_from_spec(s3); sys.modules['routes.render_packs'] = R; s3.loader.exec_module(R)

USER = {'id': 'u42', 'email': 'taller@x.es', 'aiCreditsMonthly': 10}


class Req:
    def __init__(self, cuerpo, firma): self._c = cuerpo; self.headers = {'stripe-signature': firma}
    async def body(self): return self._c


def evento(session_id='cs_test_1', pack='pack50', uid='u42', pagado=True, total=4235):
    import json
    return json.dumps({"type": "checkout.session.completed", "data": {"object": {
        "id": session_id, "payment_status": "paid" if pagado else "unpaid",
        "amount_total": total, "customer_email": "taller@x.es",
        "metadata": {"user_id": uid, "pack_id": pack, "renders": "999"}}}}).encode()


async def saldo():
    return (await AU.get_user_credits(USER))['saldo']




def _correr(coro):
    return asyncio.run(coro)


async def _saldo():
    return (await AU.get_user_credits(USER))["saldo"]


def test_el_precio_lo_pone_el_servidor_no_el_navegador():
    async def esc():
        await R.comprar({"packId": "pack50", "price": 1, "renders": 9999}, USER)
        importe = _Sess.ultimo["line_items"][0]["price_data"]["unit_amount"]
        assert importe == 4235, "se ha usado un precio enviado por el cliente"
    _correr(esc())


def test_no_se_abona_nada_al_abrir_la_pasarela():
    async def esc():
        antes = await _saldo()
        await R.comprar({"packId": "pack50"}, USER)
        assert await _saldo() == antes, "abonar antes de pagar permite renders gratis"
    _correr(esc())


def test_pack_inexistente_se_rechaza():
    with pytest.raises(R.HTTPException) as e:
        _correr(R.comprar({"packId": "pack_regalo"}, USER))
    assert e.value.status_code == 400


def test_firma_falsa_no_abona_renders():
    async def esc():
        antes = await _saldo()
        with pytest.raises(R.HTTPException) as e:
            await R.webhook(Req(evento(session_id="cs_falsa"), "firma-inventada"))
        assert e.value.status_code == 400
        assert await _saldo() == antes, "una firma falsa ha abonado renders"
    _correr(esc())


def test_el_pago_correcto_abona_y_el_reintento_no_duplica():
    async def esc():
        antes = await _saldo()
        w = await R.webhook(Req(evento(session_id="cs_ok"), FIRMA_BUENA))
        assert w["renders"] == 50
        assert await _saldo() == antes + 50
        # Stripe REINTENTA los webhooks: el mismo pago no puede abonar dos veces.
        w2 = await R.webhook(Req(evento(session_id="cs_ok"), FIRMA_BUENA))
        assert w2.get("duplicado") is True
        assert await _saldo() == antes + 50, "un reintento ha abonado dos veces"
    _correr(esc())


def test_sesion_sin_pagar_se_ignora():
    async def esc():
        antes = await _saldo()
        await R.webhook(Req(evento(session_id="cs_impagada", pagado=False), FIRMA_BUENA))
        assert await _saldo() == antes, "se ha abonado una sesion sin pagar"
    _correr(esc())


def test_los_renders_salen_del_catalogo_no_de_los_metadatos():
    """Los metadatos del evento dicen 999; deben valer los 50 del catalogo."""
    async def esc():
        await R.webhook(Req(evento(session_id="cs_meta"), FIRMA_BUENA))
        compras = (await R.mis_compras(USER))["compras"]
        assert all(c["renders"] in (20, 50, 100) for c in compras), "se ha colado el 999"
    _correr(esc())


def test_sin_claves_queda_inerte_pero_no_rompe():
    async def esc():
        os.environ.pop("STRIPE_SECRET_KEY", None)
        try:
            cat = await R.catalogo(USER)
            assert cat["pagoTarjeta"] is False
            assert len(cat["packs"]) == 3, "el catalogo debe verse aunque no se pueda cobrar"
            with pytest.raises(R.HTTPException) as e:
                await R.comprar({"packId": "pack50"}, USER)
            assert e.value.status_code == 503
        finally:
            os.environ["STRIPE_SECRET_KEY"] = "sk_test_x"
    _correr(esc())


def test_los_packs_no_caducan():
    cat = _correr(R.catalogo(USER))
    assert cat["caducan"] is False
