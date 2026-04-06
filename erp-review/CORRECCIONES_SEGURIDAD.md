# CORRECCIONES DE SEGURIDAD APLICADAS

## 1. fabrica.py - Línea 35
**ANTES:**
```python
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', 'sk-emergent-4A3Ed5d56521e792e1')
```

**DESPUÉS:**
```python
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')
```

---

## 2. jwt_service.py - Línea 14
**ANTES:**
```python
JWT_SECRET = os.environ.get('JWT_SECRET', secrets.token_hex(32))
```

**DESPUÉS:**
```python
JWT_SECRET = os.environ.get('JWT_SECRET')
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET environment variable is required")
```

---

## 3. server.py - Verificación de passwords (mejorar logging)
Añadir logging cuando se use plaintext para identificar usuarios que necesitan migración.

---

## 4. CORS - Restringir orígenes
Verificar que CORS_ORIGINS esté configurado con dominios específicos en producción.

---

## Archivos a modificar:
1. `/backend/routes/fabrica.py`
2. `/backend/services/jwt_service.py`
