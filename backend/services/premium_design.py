# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
"""Small, versioned Premium briefing payload. No images, tokens or calculated prices."""
import json
import re

def validate_premium_brief(value):
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError('El encargo PREMIUM debe ser un objeto.')
    try:
        if len(json.dumps(value, ensure_ascii=False, allow_nan=False).encode('utf-8')) > 60000:
            raise ValueError('El encargo PREMIUM supera 60 KB.')
    except (TypeError, OverflowError):
        raise ValueError('El encargo PREMIUM contiene valores no válidos.') from None
    def text(src, key, limit):
        item = src.get(key, '')
        if not isinstance(item, str) or len(item) > limit:
            raise ValueError(f'Campo PREMIUM no válido: {key}.')
        return item
    if value.get('version', 1) != 1:
        raise ValueError('Versión del encargo PREMIUM no compatible.')
    specialties = value.get('specialties', [])
    allowed = {'arquitectura', 'interiorismo', 'cocinas', 'carpinteria', 'ebanisteria', 'decoracion'}
    if not isinstance(specialties, list) or len(specialties) > 6 or any(not isinstance(s, str) or s not in allowed for s in specialties):
        raise ValueError('Especialidades PREMIUM no válidas.')
    atmosphere = value.get('atmosphere', 'fiel')
    scene = value.get('scene', 'concepto')
    if atmosphere not in ('fiel', 'calido', 'editorial') or scene not in ('concepto', 'croquis', 'obra'):
        raise ValueError('Objetivo o ambiente PREMIUM no válido.')
    rows = value.get('modules', [])
    if not isinstance(rows, list) or len(rows) > 60:
        raise ValueError('La relación PREMIUM admite hasta 60 módulos.')
    modules = []
    ids = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Módulo PREMIUM no válido.')
        item = {k: text(row, k, limit) for k, limit in [('id',100), ('wall',80), ('type',160), ('width',20), ('detail',300)]}
        if not item['id'] or item['id'] in ids:
            raise ValueError('Identificador de módulo vacío o repetido.')
        ids.add(item['id'])
        if row.get('level') not in ('bajos', 'altos', 'sobremodulos') or not isinstance(row.get('confirmed'), bool):
            raise ValueError('Nivel o confirmación de módulo no válido.')
        item.update(level=row['level'], confirmed=row['confirmed'])
        modules.append(item)
    points = value.get('installations', [])
    if not isinstance(points, list) or len(points) > 40:
        raise ValueError('Se admiten hasta 40 puntos de instalaciones.')
    installations, point_ids = [], set()
    for row in points:
        if not isinstance(row, dict):
            raise ValueError('Punto de instalación no válido.')
        item = {k: text(row, k, limit) for k, limit in [('id',100), ('label',100), ('wall',80), ('origin',160), ('height',20), ('distance',20)]}
        if not item['id'] or item['id'] in point_ids:
            raise ValueError('Identificador de instalación vacío o repetido.')
        point_ids.add(item['id'])
        if row.get('trade') not in ('electricidad', 'fontaneria') or not isinstance(row.get('confirmed'), bool):
            raise ValueError('Oficio o confirmación no válido.')
        item.update(trade=row['trade'], confirmed=row['confirmed'])
        if item['confirmed'] and (not all(item[k].strip() for k in ('label','wall','origin')) or not all(re.fullmatch(r'[0-9]+(?:[.,][0-9]+)?', item[k].strip()) for k in ('height','distance'))):
            raise ValueError('Un punto confirmado necesita altura, distancia y pared de referencia.')
        installations.append(item)
    return dict(version=1, specialties=list(dict.fromkeys(specialties)), atmosphere=atmosphere, scene=scene,
                materials=text(value, 'materials', 1200), construction=text(value, 'construction', 1200),
                sourceNotes=text(value, 'sourceNotes', 1200), modules=modules, installations=installations)
