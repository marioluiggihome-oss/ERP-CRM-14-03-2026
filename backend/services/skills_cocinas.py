# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
"""Skills técnicas puras. Una relación, unidades cm y tarifa identificada por SHA.

No llama a una IA ni transforma estimaciones en medidas. Consume la lectura del
estudio y fichas MV verificadas del servidor. Los cascos se compran como unidades;
solo se generan frentes/herrajes cuando la ficha incluye su despiece exacto.
"""
import hashlib
import json
import math
import re
import unicodedata
from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from services.distribucion_a_mv import MAPA, SIN_CASCO
from services.mv_relacion import _puntos

CATALOGO = Path(__file__).resolve().parents[1] / 'data' / 'mv_tarifas_oficiales.json'
VERSION = 'skills-cocinas-1'
ETAPAS = ['Analizar plano o boceto', 'Detectar muebles y posiciones',
          'Identificar referencias MV', 'Validar medidas reales',
          'Comprobar huecos, colisiones y aperturas', 'Generar relación única',
          'Despiece de cascos, frentes y herrajes', 'Presupuesto trazable',
          'Revisión y aprobación humana', 'Volcar junto al diseño']


def huella(valor):
    return hashlib.sha256(json.dumps(valor, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def numero(valor):
    try:
        n = float(str(valor).replace(',', '.'))
        return n if math.isfinite(n) and n >= 0 else None
    except (ValueError, TypeError):
        return None


def nombre(valor):
    return ''.join(c for c in unicodedata.normalize('NFD', str(valor or '').lower())
                   if unicodedata.category(c) != 'Mn').replace(' ', '_')


def skill(numero_etapa, resultado, pendientes=(), advertencias=()):
    p = list(dict.fromkeys(pendientes))
    return {'skill': numero_etapa, 'nombre': ETAPAS[numero_etapa - 1],
            'resultado': resultado, 'confianza': 'baja' if p else 'alta',
            'criterio_confianza': 'Completitud y validaciones; no es una probabilidad de acierto visual.',
            'advertencias': list(advertencias), 'datos_pendientes': p,
            'estado': 'pendiente' if p else 'comprobado'}


def ejecutar(distribucion, tarifa='T1', fichas=None, render_id=None, catalogo=None):
    catalogo = deepcopy(catalogo) if catalogo is not None else json.loads(CATALOGO.read_text())
    familias = catalogo.get('tariffs', {}).get(tarifa)
    if not familias:
        raise ValueError('La tarifa MV solicitada no existe.')
    fichas = fichas or {}
    indice = {cod.upper(): {'familia': fam, 'e': puntos, 't': datos.get('type')}
              for fam, datos in familias.items() if isinstance(datos.get('items'), dict)
              for cod, puntos in datos['items'].items()}
    tarifa_version = huella({'tarifa': tarifa, 'familias': familias, 'meta': catalogo.get('_meta')})
    dist = deepcopy(distribucion or {})
    if not isinstance(dist, dict):
        raise ValueError('Distribución inválida.')
    paredes = dist.get('paredes') or []
    entrada = dist.get('elementos') or []
    pasos = [skill(1, {'render_id': render_id, 'paredes': paredes},
                   ([] if render_id else ['Vincular el diseño de origen.']) +
                   ([] if paredes and entrada else ['Faltan paredes o muebles en la lectura.']))]
    relacion, pendientes_pos, pendientes_ref, pendientes_med, avisos = [], [], [], [], []
    for i, e in enumerate(entrada):
        uid = f'M{i + 1:03d}'
        tipo = nombre(e.get('id') or e.get('label'))
        ancho, alto, fondo = (numero(e.get(c)) for c in ('ancho', 'alto', 'fondo'))
        fila = 'sobremodulo' if tipo in {'altillo', 'sobremodulo', 'sobre_modulo'} else e.get('fila', 'bajo')
        pos, pared = numero(e.get('posicion_cm')), numero(e.get('pared_idx'))
        cantidad = numero(e.get('qty', 1))
        cod = str(e.get('codigo_mv') or e.get('codigo') or '').strip().upper()
        es_hueco = tipo in SIN_CASCO or tipo == 'hueco'
        es_costado = tipo in {'costado', 'lateral', 'regleta', 'panel', 'relleno'}
        pendiente = []
        if not cod and not es_hueco and ancho and ancho.is_integer():
            propuesta = MAPA.get(tipo)  # Igualdad exacta, nunca «bajo» in descripción.
            if propuesta:
                prefijo, _, seguro = propuesta
                if not seguro:
                    pendiente.append(f'{uid}: confirmar familia MV, no basta la apariencia del frente.')
                for candidato in (f'{prefijo}{int(ancho)}D/I', f'{prefijo}{int(ancho)}'):
                    if candidato in indice:
                        cod = candidato
                        break
        # La mano final D o I corresponde a la referencia D/I, sin alias de familia.
        canon = cod if cod in indice else re.sub(r'(?<=\d)[DI]$', 'D/I', cod)
        ref = indice.get(canon)
        if not es_hueco and not ref:
            pendiente.append(f'{uid}: referencia MV exacta pendiente.')
        propuesta = MAPA.get(tipo)
        if ref and propuesta and re.match(r'^[A-Z]+', canon).group() != propuesta[0]:
            pendiente.append(f'{uid}: la referencia no corresponde al tipo de mueble detectado.')
        pendientes_ref += pendiente
        familia = ref['familia'] if ref else ('HUECO' if es_hueco else 'PENDIENTE')
        if canon.endswith('D/I') and e.get('mano') not in ('D', 'I') and not re.search(r'\d[DI]$', cod):
            pendientes_ref.append(f'{uid}: confirmar mano de apertura D o I.')
        if fila in ('alto', 'sobremodulo'):
            pendientes_med.append(f'{uid}: validar cota de montaje y separación vertical respecto a bajos y columnas.')
        if alto is None and fila != 'sobremodulo':
            if familia.startswith('BAJO'):
                alto = 80
            elif familia.startswith('ALTO'):
                alto = 90
        if ancho is None or ancho <= 0 or e.get('ancho_desconocido') or not (e.get('medida_escrita') or e.get('corregida')):
            pendientes_med.append(f'{uid}: confirmar ancho real; una estimación del render no sirve para aprobar.')
        if alto is None or alto <= 0 or e.get('alto_desconocido'):
            pendientes_med.append(f'{uid}: confirmar altura del casco o hueco.')
        if fondo is None or fondo <= 0:
            pendientes_med.append(f'{uid}: confirmar fondo real.')
        if ref and not es_costado:
            m = re.search(r'\d+', canon)
            if m and ancho != float(m.group()):
                pendientes_med.append(f'{uid}: el ancho no coincide con {canon}.')
            alturas = {'h7090': [70, 90], 'h200220': [200, 220], 'h127147': [127, 147]}.get(ref['t'])
            if alturas and alto not in alturas:
                pendientes_med.append(f'{uid}: la altura no existe en la tarifa de {canon}.')
        ficha = fichas.get(canon) or {}
        if fila == 'sobremodulo':
            if not ficha.get('verificada') or ficha.get('categoria') != 'sobremodulo':
                pendientes_med.append(f'{uid}: sobremódulo independiente, falta ficha técnica MV verificada.')
        if pos is None or pared is None or not pared.is_integer() or int(pared) >= len(paredes):
            pendientes_pos.append(f'{uid}: posición o pared pendiente.')
        if not cantidad or not cantidad.is_integer():
            pendientes_med.append(f'{uid}: cantidad inválida.')
        if cod.endswith('D/I') and e.get('mano') in ('D', 'I'):
            cod = cod[:-3] + e['mano']
        relacion.append({'uid': uid, 'tipo': tipo, 'descripcion': e.get('label') or tipo,
                         'codigo': cod or None, 'referencia_mv': canon if ref else None,
                         'familia': familia, 'fila': fila, 'pared_idx': pared, 'posicion_cm': pos,
                         'ancho': ancho, 'alto': alto, 'fondo': fondo, 'cantidad': cantidad,
                         'modo_suministro': 'hueco' if es_hueco else 'pieza' if es_costado else 'casco',
                         'origen': {'indice': i, 'render_id': render_id, 'tarifa_version': tarifa_version},
                         'mano': e.get('mano'), 'espacio_frontal_cm': numero(e.get('espacio_frontal_cm'))})
    pasos += [skill(2, relacion, pendientes_pos), skill(3, relacion, pendientes_ref), skill(4, relacion, pendientes_med)]

    pendientes_obra, choques = [], []
    for p in paredes:
        if not isinstance(p.get('huecos'), list):
            pendientes_obra.append('Confirmar puertas, ventanas y otros huecos de cada pared, aunque no haya ninguno.')
        elif p['huecos']:
            pendientes_obra.append('Revisar las cotas y aperturas de los huecos de obra antes de aprobar.')
    for i, a in enumerate(relacion):
        uid = a['uid']
        if a['pared_idx'] is not None and a['pared_idx'].is_integer() and int(a['pared_idx']) < len(paredes):
            p = paredes[int(a['pared_idx'])]
            limite = numero(p.get('ancho'))
            if not limite or not (p.get('ancho_escrito') or dist.get('medidasReales')):
                pendientes_obra.append('Confirmar el ancho útil de cada pared.')
            elif a['posicion_cm'] is not None and a['ancho'] and a['posicion_cm'] + a['ancho'] > limite:
                choques.append(f'{uid}: el mueble rebasa la pared.')
        for b in relacion[i + 1:]:
            if a['pared_idx'] == b['pared_idx'] and a['fila'] == b['fila'] and all(x is not None for x in [a['posicion_cm'], b['posicion_cm'], a['ancho'], b['ancho']]):
                if min(a['posicion_cm'] + a['ancho'], b['posicion_cm'] + b['ancho']) > max(a['posicion_cm'], b['posicion_cm']):
                    choques.append(f"{uid} colisiona con {b['uid']}.")
        ficha = fichas.get(a['referencia_mv']) or {}
        if a['modo_suministro'] == 'hueco':
            pendientes_obra.append(f'{uid}: comprobar ficha e instalación del electrodoméstico o hueco.')
        elif a['modo_suministro'] == 'casco':
            barrido = numero(ficha.get('barrido_cm'))
            if barrido is None or a['espacio_frontal_cm'] is None:
                pendientes_obra.append(f'{uid}: faltan barrido de apertura o espacio libre frontal.')
            elif barrido > a['espacio_frontal_cm']:
                choques.append(f'{uid}: la apertura rebasa el espacio libre.')
        if not ficha.get('verificada'):
            pendientes_obra.append(f'{uid}: verificar encuentros, costados y compatibilidad en ficha MV.')
    if len(paredes) > 1:
        pendientes_obra.append('Validar encuentros entre paredes y pasillos con cotas de obra; no deducirlos de la perspectiva.')
    pasos.append(skill(5, {'colisiones': choques}, pendientes_obra + choques))
    pasos.append(skill(6, relacion, pendientes_pos + pendientes_ref + pendientes_med))

    cascos, frentes, herrajes, pendientes_despiece = [], [], [], []
    for m in relacion:
        if m['modo_suministro'] == 'hueco':
            continue
        uid = m['uid']; ficha = fichas.get(m['referencia_mv']) or {}
        cascos.append({**m, 'unidad': 'casco comprado' if m['modo_suministro'] == 'casco' else 'pieza a medida'})
        if not ficha.get('verificada') or not ficha.get('version') or not ficha.get('fuente'):
            pendientes_despiece.append(f'{uid}: falta ficha verificada y versionada de frentes y herrajes.')
            continue
        dims = ficha.get('dimensiones') or {}
        if any(numero(dims.get(k)) != m[k] for k in ('ancho', 'alto', 'fondo')):
            pendientes_despiece.append(f'{uid}: ficha y dimensiones del mueble no coinciden.')
            continue
        # Listas vacías explícitas significan que el proveedor confirma cero piezas.
        for grupo, destino in [('frentes', frentes), ('herrajes', herrajes)]:
            if not isinstance(ficha.get(grupo), list):
                pendientes_despiece.append(f'{uid}: falta relación de {grupo}.')
                continue
            for pieza in ficha[grupo]:
                qty = numero(pieza.get('cantidad'))
                valida = pieza.get('referencia') and qty and qty.is_integer()
                if grupo == 'frentes':
                    h, w = numero(pieza.get('alto')), numero(pieza.get('ancho'))
                    valida = valida and h and w and h <= m['alto'] and w <= m['ancho']
                if not valida:
                    pendientes_despiece.append(f'{uid}: pieza de {grupo} sin referencia, cantidad o medida válida.')
                    continue
                destino.append({**{k: pieza[k] for k in ('referencia', 'descripcion', 'alto', 'ancho') if k in pieza},
                                'mueble_uid': uid, 'cantidad': qty * (m['cantidad'] or 0),
                                'ficha_version': ficha['version'], 'fuente': ficha['fuente']})
    pasos.append(skill(7, {'cascos': cascos, 'frentes': frentes, 'herrajes': herrajes}, pendientes_despiece))
    importes, pendientes_precio = [], []
    pv = numero(catalogo.get('_meta', {}).get('pointValue'))
    for m in relacion:
        if m['modo_suministro'] == 'hueco':
            pendientes_precio.append(f"{m['uid']}: electrodoméstico/hueco excluido del precio de muebles; revisar partida.")
            continue
        entry = indice.get(m['referencia_mv'])
        puntos = _puntos(entry, m['alto'], m['ancho']) if entry else None
        if entry and entry['t'] == 'dual':
            variante = (fichas.get(m['referencia_mv']) or {}).get('variante_tarifa')
            if type(variante) is not int or variante not in (0, 1):
                puntos = None
            else:
                puntos = entry['e'][variante]
        if puntos is None or pv is None or m['cantidad'] is None:
            pendientes_precio.append(f"{m['uid']}: sin precio verificado.")
            continue
        importe = (Decimal(str(puntos)) * Decimal(str(pv)) * Decimal(str(m['cantidad']))).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
        importes.append({'mueble_uid': m['uid'], 'referencia_mv': m['referencia_mv'], 'importe_tarifa': float(importe),
                         'puntos': puntos, 'valor_punto': pv, 'tarifa': tarifa, 'tarifa_version': tarifa_version})
    presupuesto = {'lineas': importes, 'importe_tarifa_conocido': round(sum(x['importe_tarifa'] for x in importes), 2),
                   'alcance': 'Tarifa de muebles MV. No sumar otra vez frentes/herrajes incluidos. Venta, descuentos e IVA se revisan en el presupuestador.',
                   'tarifa': tarifa, 'version': tarifa_version}
    pasos.append(skill(8, presupuesto, pendientes_precio + pendientes_ref + pendientes_med))
    pendientes = list(dict.fromkeys(x for s in pasos for x in s['datos_pendientes']))
    if not relacion:
        pendientes.append('No hay relación de muebles.')
    revision = huella({'relacion': relacion, 'paredes': paredes, 'fichas': fichas, 'tarifa_version': tarifa_version, 'version': VERSION})
    pasos += [skill(9, {'puede_aprobar': not pendientes, 'aprobado': False}, pendientes),
              skill(10, {'puede_volcar': False, 'revision': revision}, ['Requiere aprobación humana de esta revisión.'])]
    return {'version_skills': VERSION, 'revision': revision, 'render_id': render_id, 'relacion': relacion,
            'tarifa_version': tarifa_version, 'tarifa': tarifa, 'skills': pasos,
            'puede_aprobar': not pendientes, 'aprobado': False, 'datos_pendientes': pendientes}
