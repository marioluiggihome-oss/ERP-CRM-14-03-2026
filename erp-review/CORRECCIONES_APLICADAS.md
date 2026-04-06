# CORRECCIONES APLICADAS - ERP-CRM LUIGGI HOME

**Fecha:** 6 Abril 2026  
**Estado:** ✅ CORREGIDO

---

## 1. CORRECCIONES DE SEGURIDAD

### 1.1 fabrica.py - Línea 35 ✅
**Problema:** API Key hardcodeada como fallback  
**Solución:** Usar variable de entorno sin fallback inseguro

```python
# ANTES
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', 'sk-emergent-4A3Ed5d56521e792e1')

# DESPUÉS
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY') or os.environ.get('GOOGLE_AI_KEY', '')
```

### 1.2 jwt_service.py - Línea 14 ✅
**Problema:** JWT_SECRET podía generar uno aleatorio sin aviso  
**Solución:** Advertencia cuando no está configurado

```python
# AHORA
_jwt_secret = os.environ.get('JWT_SECRET')
if not _jwt_secret:
    import warnings
    warnings.warn("JWT_SECRET not set! Using random secret (tokens won't persist across restarts)")
    _jwt_secret = secrets.token_hex(32)
JWT_SECRET = _jwt_secret
```

---

## 2. CORRECCIONES DE IA (Telemetría y IA Lab)

### Problema Principal ❌
El código usaba `api_version: "v1beta"` que NO soporta el modelo `gemini-1.5-flash`.

Error original:
```
404 NOT FOUND: 'models/gemini-1.5-flash is not found for API version v1beta'
```

### Archivos Corregidos ✅

| Archivo | Línea | Cambio |
|---------|-------|--------|
| `routes/ia_lab.py` | 127 | Eliminado `api_version: "v1beta"` |
| `services/telemetry_queue.py` | 235 | Eliminado `api_version: "v1beta"` |
| `routes/fabrica.py` | 492 | Usar `GEMINI_MODEL` env var |
| `routes/armarios.py` | 253, 332 | Usar `GEMINI_MODEL` env var |
| `routes/digitalizador.py` | 380 | Usar `GEMINI_MODEL` env var |
| `server.py` | 407, 582, 1982 | Usar `GEMINI_MODEL` env var |

### Modelo por Defecto
Todos los archivos ahora usan:
```python
model_name = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
```

---

## 3. ARCHIVOS MODIFICADOS (Resumen)

1. `/backend/routes/fabrica.py` - Seguridad + modelo IA
2. `/backend/routes/ia_lab.py` - Versión API Gemini
3. `/backend/routes/armarios.py` - Modelo IA configurable
4. `/backend/routes/digitalizador.py` - Modelo IA configurable
5. `/backend/services/jwt_service.py` - Validación JWT_SECRET
6. `/backend/services/telemetry_queue.py` - Versión API Gemini
7. `/backend/server.py` - Modelo IA configurable (3 lugares)

---

## 4. PRÓXIMOS PASOS

1. **Subir a GitHub** usando "Save to GitHub"
2. **Desplegar** en tu servidor con `git pull`
3. **Verificar** que la telemetría y el IA Lab funcionen
4. **Monitorear logs** para errores

---

## 5. VARIABLES DE ENTORNO REQUERIDAS

Asegúrate de tener en Railway:

```env
GEMINI_MODEL=gemini-1.5-flash
GOOGLE_AI_KEY=AIza...
EMERGENT_LLM_KEY=sk-emergent-...  # O déjalo vacío si usas GOOGLE_AI_KEY
JWT_SECRET=tu-secreto-seguro
```

---

*Correcciones aplicadas el 6 de Abril de 2026*
