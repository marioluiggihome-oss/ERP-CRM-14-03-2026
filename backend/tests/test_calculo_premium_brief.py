# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
"""Executes real Premium metadata validation and save route with a fake DB."""
import ast
import asyncio
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('premium_validation_test', ROOT/'backend/services/premium_design.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
validate = module.validate_premium_brief


def test_draft_roundtrip_and_whitelist():
    value = dict(materials='Alvic Agave', modules=[dict(id='a', wall='Pared 1', level='bajos', type='Fregadero', width='', detail='2 gavetas', confirmed=False)], unwanted='discard')
    output = validate(value)
    assert output['modules'][0]['width'] == ''
    assert output['materials'] == 'Alvic Agave'
    assert 'unwanted' not in output
    assert validate(output) == output


@pytest.mark.parametrize('value', [[], 'oops', {'modules':[None]}, {'modules': [{}]}, {'materials':'a'*1201}, {'version':2}, {'specialties':[{}]}, {'modules':[dict(id='x',wall='',type='',width='',detail='',level='bajos',confirmed='true')]}])
def test_reject_malformed(value):
    with pytest.raises(ValueError): validate(value)


def test_old_studio_save_does_not_touch_premium_metadata():
    # Execute the actual save function, not a copy of its implementation.
    source = ast.parse((ROOT/'backend/routes/ai_engine.py').read_text())
    fn = next(n for n in source.body if isinstance(n, ast.AsyncFunctionDef) and n.name == 'save_render_design')
    fn.decorator_list = []
    fn.args.defaults = []
    from datetime import datetime, timezone
    import uuid, sys
    db = SimpleNamespace(render3d_designs=SimpleNamespace(find_one=AsyncMock(return_value=None), update_one=AsyncMock()))
    class HttpError(Exception):
        def __init__(self, status_code, detail): self.status_code, self.detail = status_code, detail
    ns = dict(_db=db, datetime=datetime, timezone=timezone, uuid=uuid, HTTPException=HttpError)
    exec(compile(ast.Module(body=[fn], type_ignores=[]), '<actual-save-route>', 'exec'), ns)
    from unittest.mock import patch
    fake_modules = {'services.master': SimpleNamespace(es_master=lambda _:False), 'services.plataformas': SimpleNamespace(organizacion_de=lambda _:'org',plataforma_de=lambda _:'coop'), 'services.premium_design': module}
    with patch.dict(sys.modules, fake_modules):
        asyncio.run(ns['save_render_design']({'description':'original'}, {'id':'u'}))
        assert 'premiumBrief' not in db.render3d_designs.update_one.call_args.args[1]['$set']
        result = asyncio.run(ns['save_render_design']({'premiumBrief':{'materials':'Agave'}}, {'id':'u'}))
        assert result['design']['premiumBrief']['materials'] == 'Agave'
        db.render3d_designs.find_one.return_value = {'userId':'another'}
        with pytest.raises(HttpError) as error:
            asyncio.run(ns['save_render_design']({'premiumBrief':{}}, {'id':'u'}))
        assert error.value.status_code == 403


def test_installations_preserve_cotas_and_reject_false_confirmation():
    point = dict(id='e1', label='Luz bajo altos', wall='Fondo', origin='Pared izquierda hacia derecha', height='165', distance='120,5', trade='electricidad', confirmed=True)
    assert validate(dict(installations=[point]))['installations'] == [point]
    for change in [dict(height=''), dict(distance='-1'), dict(distance='NaN'), dict(origin=''), dict(confirmed='yes')]:
        with pytest.raises(ValueError):
            validate(dict(installations=[dict(point, **change)]))
    with pytest.raises(ValueError):
        validate(dict(installations=[point, point]))
    draft = dict(point, height='', distance='', confirmed=False)
    assert validate(dict(installations=[draft]))['installations'] == [draft]
