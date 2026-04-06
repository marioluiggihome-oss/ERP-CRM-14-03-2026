# ANÁLISIS TÉCNICO COMPLETO - ERP-CRM LUIGGI HOME

**Fecha:** 6 Abril 2026  
**Analista:** E1 - Emergent Labs  
**Versión del Sistema:** v3.2

---

## 1. RESUMEN EJECUTIVO

### Descripción General
Sistema ERP-CRM completo para **LUIGGI HOME**, empresa de presupuestos profesionales de cocinas. El sistema integra gestión de presupuestos, CRM, portal de fábrica, gestión de montajes y digitalización IA.

### Stack Tecnológico
| Capa | Tecnología | Versión |
|------|------------|---------|
| **Frontend** | React | 19.0.0 |
| **Backend** | FastAPI | 0.110.1 |
| **Base de Datos** | MongoDB (Motor async) | 3.3.1 |
| **IA** | Google Gemini (genai) | 1.59.0 |
| **UI** | Tailwind CSS + Radix UI | 3.4.17 |
| **Gráficos** | Recharts | 3.6.0 |
| **PDF** | jsPDF + ReportLab | 4.0.0 / 4.2.5 |
| **Email** | SendGrid + Resend | 6.12.5 / 2.0.0 |

### Métricas de Código
| Componente | Líneas de Código |
|------------|------------------|
| Backend Total | ~16,100 líneas |
| Frontend Total | ~32,500 líneas |
| Modelos (schemas.py) | 1,148 líneas |
| Server principal | ~3,500 líneas |
| Routers modulares | ~12,600 líneas |
| Componentes React | ~32,500 líneas |

---

## 2. ARQUITECTURA DEL SISTEMA

### 2.1 Estructura de Directorios

```
/backend/
├── server.py              # Servidor principal FastAPI (~3,500 líneas)
├── config.py              # Configuración centralizada
├── requirements.txt       # 72 dependencias Python
├── models/
│   └── schemas.py         # Modelos Pydantic (1,148 líneas)
├── routes/                # 26 routers modulares
│   ├── auth.py            # Autenticación básica
│   ├── auth_advanced.py   # 2FA, registro, recuperación
│   ├── fabrica.py         # Portal de fábrica
│   ├── crm_module.py      # CRM completo
│   ├── digitalizador.py   # OCR con IA
│   ├── armarios.py        # Configurador armarios
│   ├── backup.py          # Sistema de backups
│   ├── dashboard.py       # Métricas de fábrica
│   └── [+17 routers más]
└── services/              # 12 servicios
    ├── jwt_service.py     # Tokens JWT
    ├── audit_service.py   # Auditoría de acciones
    ├── rate_limiter.py    # Limitación de requests
    ├── backup_service.py  # Backups automáticos
    └── telemetry_queue.py # Cola de procesamiento IA

/frontend/
├── src/
│   ├── App.js             # Componente principal (908 líneas)
│   ├── services/
│   │   ├── api.js         # Cliente API (1,628 líneas)
│   │   └── authService.js # Gestión de tokens
│   ├── components/        # ~30 componentes React
│   │   ├── SettingsModal.jsx      # Panel Master (2,948 líneas)
│   │   ├── DespieceModal.jsx      # Despiece técnico (2,345 líneas)
│   │   ├── Digitalizador.jsx      # OCR IA (1,679 líneas)
│   │   ├── PortalFabrica.jsx      # Fábrica (1,674 líneas)
│   │   └── BudgetTable.jsx        # Presupuestos (~3,000+ líneas)
│   └── utils/
│       └── securityGuard.js       # Protección anti-copia
└── package.json           # 58 dependencias Node
```

### 2.2 Módulos Funcionales

```
┌─────────────────────────────────────────────────────────────┐
│                    LUIGGI HOME ERP-CRM                       │
├─────────────────────────────────────────────────────────────┤
│  PRESUPUESTOS  │  CRM  │  FÁBRICA  │  MONTAJES  │  ADMIN   │
├────────────────┼───────┼───────────┼────────────┼──────────┤
│ • Cocina Mont. │ • Con │ • Órdenes │ • Montador │ • Usuar. │
│ • Despiece     │ • Opp │ • Dashboard│ • Agenda   │ • Clien. │
│ • Digitalizad. │ • Act │ • Historial│ • Tracking │ • Permi. │
│ • Armarios IA  │ • Cal │ • PDF Prod │            │ • Backup │
│ • PDF Export   │ • Pipe│ • Multi-Fab│            │ • Teleme │
└────────────────┴───────┴───────────┴────────────┴──────────┘
```

---

## 3. ANÁLISIS DE SEGURIDAD

### 3.1 Puntos Positivos ✅

1. **Autenticación JWT implementada**
   - Access tokens (24h) + Refresh tokens (7 días)
   - Servicio dedicado en `jwt_service.py`
   - Soporte para múltiples formatos de hash (bcrypt, SHA256, plaintext para migración)

2. **Rate Limiting configurado**
   - Slowapi implementado con límites por endpoint
   - Protección contra brute force en login

3. **Auditoría de acciones**
   - `audit_service.py` registra logins, cambios, fallos
   - Tracking de actividad por usuario

4. **Protección Frontend**
   - `securityGuard.js` desactiva: clic derecho, F12, Ctrl+U, selección de texto
   - Fingerprint invisible (marca de agua)
   - Limpieza periódica de consola

5. **Middleware de seguridad**
   - `security_middleware.py` para headers de seguridad

### 3.2 Vulnerabilidades Detectadas ⚠️

| Severidad | Issue | Ubicación | Recomendación |
|-----------|-------|-----------|---------------|
| **ALTA** | JWT_SECRET hardcodeado como fallback | `config.py:41` | Mover a variable de entorno sin default |
| **ALTA** | Passwords en plaintext aceptados | `server.py:214` | Migrar todos los usuarios a bcrypt |
| **MEDIA** | CORS permite cualquier origen | `server.py` | Restringir a dominios específicos |
| **MEDIA** | No hay validación de expiración de tokens | Varios | Implementar blacklist de tokens |
| **BAJA** | Logs pueden contener datos sensibles | `server.py` | Sanitizar logs |

### 3.3 Código Vulnerable Específico

```python
# config.py:41 - JWT_SECRET con fallback inseguro
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-super-secret-jwt-key-change-in-production')

# server.py:214 - Acepta passwords en plaintext
# Intento 3: Plain text (para migración de datos antiguos)
return password == hashed
```

---

## 4. ANÁLISIS DE RENDIMIENTO

### 4.1 Puntos de Optimización

| Área | Problema | Impacto | Solución |
|------|----------|---------|----------|
| **MongoDB** | Queries sin índices optimizados | Lentitud en búsquedas | Crear índices compuestos |
| **Frontend** | Componentes monolíticos | Re-renders innecesarios | Dividir en componentes más pequeños |
| **IA** | Procesamiento síncrono de imágenes | Bloquea servidor | Ya implementada cola async ✅ |
| **Productos** | Carga de 10,000+ productos | Tiempo de carga alto | Paginación server-side |

### 4.2 Componentes Monolíticos (Deuda Técnica)

| Archivo | Líneas | Prioridad Refactorización |
|---------|--------|---------------------------|
| `SettingsModal.jsx` | 2,948 | **ALTA** - Dividir en tabs |
| `BudgetTable.jsx` | ~3,000 | **ALTA** - Extraer lógica de cálculo |
| `DespieceModal.jsx` | 2,345 | MEDIA - Componentes de piezas |
| `server.py` | ~3,500 | MEDIA - Ya tiene routers extraídos |

---

## 5. FUNCIONALIDADES PRINCIPALES

### 5.1 Sistema de Presupuestos ✅ COMPLETO
- Múltiples bibliotecas (ZC, MV)
- Cálculo de puntos por zonas (Z1-Z12, T1-T21)
- Despiece técnico con exportación CSV/XML
- Tolerancias de puertas configurables
- Perfiles GOLA opcionales
- Exportación PDF profesional

### 5.2 CRM ✅ COMPLETO
- Pipeline de oportunidades con etapas
- Gestión de contactos
- Actividades (llamadas, visitas, emails)
- Calendario integrado
- Analytics de clientes inactivos

### 5.3 Portal de Fábrica ✅ COMPLETO
- Órdenes de fabricación con estados
- Dashboard con métricas en tiempo real
- Sistema multi-fábrica (SALAMANCA, ZAMORA)
- Historial y trazabilidad
- PDF de informes de producción

### 5.4 Digitalización IA ✅ COMPLETO
- OCR de borradores manuscritos
- Matching con catálogo de productos
- Detección automática de tarifas MV
- Exportación a CSV para seccionadora

### 5.5 Sistema de Permisos ✅ ROBUSTO
- 15+ roles definidos (Admin, Gerente, Director, Tienda, Fábrica, Montador...)
- Permisos granulares por funcionalidad
- Jerarquía de usuarios (tiendas → clientes finales)

---

## 6. INTEGRACIONES

| Servicio | Uso | Estado |
|----------|-----|--------|
| **Google Gemini** | Vision AI para OCR | ✅ Activo |
| **SendGrid** | Emails transaccionales | ✅ Activo |
| **Resend** | Fallback de emails | ✅ Activo |
| **MongoDB Atlas** | Base de datos | ✅ Producción |
| **ReportLab** | PDFs backend | ✅ Activo |
| **jsPDF** | PDFs frontend | ✅ Activo |
| **XlsxWriter** | Exportación Excel | ✅ Activo |

---

## 7. RECOMENDACIONES PRIORITARIAS

### P0 - CRÍTICAS (Seguridad)

1. **Eliminar fallback de JWT_SECRET**
   ```python
   # ANTES
   JWT_SECRET = os.environ.get('JWT_SECRET', 'your-super-secret...')
   
   # DESPUÉS
   JWT_SECRET = os.environ['JWT_SECRET']  # Falla si no existe
   ```

2. **Migrar passwords a bcrypt**
   - Script de migración para hashear todos los passwords en plaintext
   - Eliminar soporte de plaintext después de migración

3. **Restringir CORS**
   ```python
   origins = [
       "https://luiggihome.es",
       "https://app.luiggihome.es"
   ]
   ```

### P1 - ALTA (Rendimiento)

4. **Crear índices MongoDB**
   ```javascript
   db.products.createIndex({ "library": 1, "category": 1 })
   db.projects.createIndex({ "userId": 1, "status": 1 })
   db.fabrica_orders.createIndex({ "factoryId": 1, "status": 1 })
   ```

5. **Refactorizar SettingsModal.jsx**
   - Extraer cada tab a componente separado
   - Lazy loading de tabs no visibles

### P2 - MEDIA (Mantenibilidad)

6. **Implementar tests unitarios**
   - El directorio `tests/` existe pero los tests están vacíos
   - Priorizar: auth, presupuestos, despiece

7. **Documentar API**
   - Añadir docstrings a todos los endpoints
   - Generar OpenAPI spec completo

### P3 - BACKLOG

8. **Implementar WebSockets** para actualizaciones en tiempo real en Dashboard
9. **Añadir sistema de notificaciones push**
10. **Optimizar bundle frontend** (actualmente ~2MB)

---

## 8. DIAGRAMA DE BASE DE DATOS

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     users       │     │    projects     │     │    products     │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id              │←────│ userId          │     │ id              │
│ username        │     │ id              │     │ code            │
│ password (hash) │     │ budgetNumber    │     │ name            │
│ clientName      │     │ customerName    │     │ library         │
│ isAdmin/Roles   │     │ itemsMontada[]  │     │ category        │
│ allowedModules  │     │ totalPvp        │     │ zonePoints{}    │
│ factoryId       │     │ status          │     │ module          │
└────────┬────────┘     └─────────────────┘     └─────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  fabrica_orders │     │    contacts     │     │  opportunities  │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ id              │     │ id              │     │ id              │
│ orderNumber     │     │ name            │     │ title           │
│ createdBy       │     │ company         │     │ contactId       │
│ factoryId       │     │ status          │     │ value           │
│ status          │     │ stage           │     │ stage           │
│ items[]         │     │ assignedToId    │     │ probability     │
│ priority        │     │ lastContactDate │     │ expectedClose   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

---

## 9. CONCLUSIONES

### Fortalezas del Sistema
- ✅ Arquitectura modular bien definida
- ✅ Separación clara frontend/backend
- ✅ Sistema de permisos robusto y flexible
- ✅ Integración IA funcional (Gemini Vision)
- ✅ Múltiples formatos de exportación (PDF, Excel, CSV, XML)
- ✅ Auditoría y tracking de actividad

### Áreas de Mejora
- ⚠️ Seguridad: Variables de entorno y CORS
- ⚠️ Rendimiento: Componentes monolíticos y queries sin índices
- ⚠️ Testing: Cobertura muy baja
- ⚠️ Documentación: API sin documentar completamente

### Calificación General

| Área | Puntuación |
|------|------------|
| Funcionalidad | ★★★★★ (9/10) |
| Arquitectura | ★★★★☆ (8/10) |
| Seguridad | ★★★☆☆ (6/10) |
| Rendimiento | ★★★☆☆ (7/10) |
| Mantenibilidad | ★★★☆☆ (6/10) |
| **GLOBAL** | **7.2/10** |

---

*Informe generado el 6 de Abril de 2026 por E1 - Emergent Labs*
