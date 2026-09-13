# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
from copy import deepcopy
from services.skills_cocinas import ejecutar


def proyecto():
    return {'paredes': [{'ancho': 180, 'ancho_escrito': True, 'huecos': []}], 'elementos': [
        {'id': 'bajo', 'codigo_mv': 'B60D', 'mano': 'D', 'ancho': 60,
         'fondo': 58, 'pared_idx': 0, 'posicion_cm': 0, 'medida_escrita': True,
         'espacio_frontal_cm': 100}]}


def fichas():
    # Fixture contractual, no ficha real del proveedor.
    return {'B60D/I': {'verificada': True, 'version': 'prueba-1', 'fuente': 'fixture',
        'dimensiones': {'ancho': 60, 'alto': 80, 'fondo': 58}, 'barrido_cm': 60,
        'frentes': [{'referencia': 'TEST-P', 'cantidad': 1, 'ancho': 59.7, 'alto': 79.7}],
        'herrajes': [{'referencia': 'TEST-H', 'cantidad': 2}]}}


def test_relacion_unica_y_compra_de_casco_con_desglose_verificado():
    r = ejecutar(proyecto(), fichas=fichas(), render_id='imagen-1')
    assert r['puede_aprobar']
    assert len(r['skills']) == 10
    assert all(set(['resultado', 'confianza', 'advertencias', 'datos_pendientes']) <= s.keys() for s in r['skills'])
    assert r['relacion'][0]['alto'] == 80
    assert r['skills'][6]['resultado']['cascos'][0]['unidad'] == 'casco comprado'
    assert r['skills'][6]['resultado']['herrajes'][0]['cantidad'] == 2
    assert not r['aprobado'] and not r['skills'][9]['resultado']['puede_volcar']


def test_no_fabricar_despiece_sin_ficha():
    r = ejecutar(proyecto(), render_id='imagen-1')
    assert not r['puede_aprobar']
    assert r['skills'][6]['resultado']['frentes'] == []


def test_fregadero_no_acepta_codigo_generico_bajo():
    d = proyecto(); d['elementos'][0]['id'] = 'bajo_fregadero'
    r = ejecutar(d, fichas=fichas(), render_id='imagen-1')
    assert not r['puede_aprobar']
    assert r['skills'][2]['datos_pendientes']


def test_colision_y_medidas_estimadas_bloquean():
    d = proyecto(); d['elementos'].append(deepcopy(d['elementos'][0]))
    d['elementos'][1]['posicion_cm'] = 50
    d['elementos'][0]['medida_escrita'] = False
    r = ejecutar(d, fichas=fichas(), render_id='imagen-1')
    assert not r['puede_aprobar']
    assert r['skills'][3]['datos_pendientes']
    assert r['skills'][4]['resultado']['colisiones']


def test_cambiar_ficha_o_diseno_invalida_revision():
    f = fichas(); d = proyecto()
    inicial = ejecutar(d, fichas=f, render_id='imagen-1')['revision']
    f['B60D/I']['version'] = 'prueba-2'
    assert ejecutar(d, fichas=f, render_id='imagen-1')['revision'] != inicial
    assert ejecutar(d, fichas=fichas(), render_id='imagen-2')['revision'] != inicial


def test_puerta_incompatible_no_se_acepta():
    f = fichas(); f['B60D/I']['frentes'][0]['ancho'] = 80
    r = ejecutar(proyecto(), fichas=f, render_id='imagen-1')
    assert not r['puede_aprobar']
    assert r['skills'][6]['resultado']['frentes'] == []
