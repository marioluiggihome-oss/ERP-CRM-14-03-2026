# Auditoría de seguridad — Luiggi Home ERP

_Fecha: 2026-06-21 · Alcance: backend (FastAPI) + autenticación · Método: escaneo
estático de los routers, dependencias de auth, manejo de errores y secretos._

## Semáforo

| Área | Estado |
|---|---|
| Autenticación de endpoints | 🔴 **Crítico** |
| Backup / mantenimiento (exfiltración de BD) | 🔴 **Crítico** |
| Manejo de errores (`except` que tragan) | 🟠 Medio |
| Secretos / claves | 🟢 Bien (de entorno, no hardcodeados) |
| CORS | 🟢 Bien (acotado a dominios) |
| Contraseñas (hash + no expuestas) | 🟢 Bien (bcrypt/passlib) |
| Rate limiting | 🟡 Parcial (solo en login/2FA) |

---

## 🔴 CRÍTICO

### 1. La mayoría de endpoints NO verifican permisos en el servidor
- De **351 endpoints**, ~**200 no tienen** dependencia de auth (`Depends(require_auth/require_admin)`).
- Ningún router usa dependencia global (`APIRouter(dependencies=[...])`) ni se monta con auth.
- Muchos reciben `userId` **por query** (p. ej. `fabrica.py:163 create_manufacturing_order(..., userId="")`). **Eso NO es autenticación**: cualquiera con la URL puede pasar cualquier `userId` y crear/leer/borrar datos.
- Afecta a datos sensibles: **pedidos, facturas, proyectos, clientes, gastos, rentabilidad, CRM, fábrica, librerías, despiece**.
- Ejemplo real corregido hoy: el informe "Uso Usuarios" sí exigía admin en el backend, pero el **frontend no enviaba el token** → al forzar auth, fallaría todo lo que llame por `fetch` sin token. Por eso la remediación debe ir **frontend primero, backend después**.

### 2. Backup de BD descargable/borrable SIN auth → exfiltración y destrucción
- `backup.py:296 download_backup`, `:313 delete_backup`, `:358 download_backup_part`, `:372 download_collections_backup` **sin `require_admin`**.
- Impacto: cualquiera puede **descargar una copia completa de la base de datos** o **borrar backups**.

### 3. Mantenimiento y backup pre-update SIN auth → DoS + exfiltración
- `maintenance.py:75 activate_maintenance_mode`, `:169 deactivate_maintenance_mode`, `:235 download_pre_update_backup` **sin auth** (0 `require_admin` en el archivo).
- Impacto: cualquiera puede **tumbar el ERP** (modo mantenimiento) o **descargar el backup pre-actualización**.

### 4. `POST /init` sin auth (`server.py:1393 init_data`)
- Endpoint de inicialización/sembrado **sin protección**. Riesgo según lo que siembre/resetee.

---

## 🟠 MEDIO

### 5. 79 bloques `except` que tragan errores
- `except Exception:` / `except:` que ocultan fallos (p. ej. `ia_lab.py`, `products.py`, `fabrica.py`, `crm_module.py`…). Dificultan detectar errores y pueden enmascarar fallos de seguridad. Revisar y, como mínimo, **loguear** el error.

### 6. `JWT_SECRET` sin valor por defecto ni fail-fast
- `jwt_service.py:15 JWT_SECRET = os.environ.get('JWT_SECRET')` (None si no está). Si en algún entorno no se define, la firma/verificación se rompe o queda insegura. **Fallar al arrancar** si no está definido.

### 7. Rate limiting solo en autenticación
- Existe `services/rate_limiter.py` y se usa en `auth_routes`/`auth_advanced`, pero no en el resto (p. ej. endpoints de IA caros, export, scan de documentos). Riesgo de abuso/coste.

---

## 🟢 BIEN (no tocar)
- **Sin secretos hardcodeados**: claves vía `os.environ`/settings.
- **CORS acotado** a dominios concretos (`server.py:2300`), no `*`.
- **Contraseñas con hash** (bcrypt/passlib en `auth_service.py`) y **excluidas** de las respuestas (`users.py:110/151/160`, `auth_advanced.py:563`).
- **Secreto JWT de entorno**.

---

## Plan de remediación (por fases, para no romper el ERP)

**Fase 0 — Tapar lo crítico ya (bajo riesgo):**
1. Añadir `Depends(require_admin)` a **backup** (download/delete/parts/collections) y **maintenance** (activate/deactivate/download), y proteger `POST /init`.
2. Ajustar sus llamadas en el frontend para que envíen `authHeaders()` (como se hizo con "Uso Usuarios").

**Fase 1 — Auditar el frontend:** localizar todas las llamadas `fetch(...)` que no usen el wrapper `api.js` (que ya añade el token) y añadirles `authHeaders()`.

**Fase 2 — Forzar auth global en el backend:** middleware/dependencia que exija token en todo `/api/*` salvo una lista blanca (login, registro, health, webhooks, verificación email). Sustituir el patrón `userId` por query por el `user` del token.

**Fase 3 — Endurecer:** loguear todos los `except`, fail-fast si falta `JWT_SECRET`, y extender rate limiting a IA/exports.

> Nota: forzar auth **cambia el comportamiento** y romperá cualquier llamada del frontend que hoy no mande token. Por eso Fase 1 va antes que Fase 2.
