# LUIGGI HOME - ERP/CRM para Presupuestos de Cocinas y Armarios

## Última Actualización: 01/02/2026 (v4.4 - SECURITY UPDATE)

---

## RESUMEN DEL SISTEMA

LUIGGI HOME es un ERP/CRM completo para la gestión de presupuestos de cocinas y armarios, con:
- Jerarquía de usuarios: **Director Comercial > Responsable Delegación > Comercial > Tienda/Punto de Venta > Colaborador**
- **Panel de Métricas** para Director Comercial con ventas, pipeline, conversión, top performers
- **Gráficos de tendencias** con recharts (ventas mensuales, oportunidades, distribución, embudo)
- Presupuestador técnico con cálculo automático de precios
- Módulo de Armarios con diseñador visual, despiece e IA
- CRM completo con calendario, **filtros por tipo de negocio (Cocina Montada/Despiece/Armarios)** y aislamiento de datos
- Digitalizador de borradores con IA
- Importador de catálogo IA
- Sistema de backups automáticos
- **🔒 NUEVO: Sistema de Seguridad Enterprise (JWT + Rate Limiting + Auditoría)**

---

## 🔒 SEGURIDAD ENTERPRISE (01/02/2026)

### ✅ Autenticación JWT
| Componente | Estado | Descripción |
|------------|--------|-------------|
| **jwt_service.py** | ✅ | Servicio completo de JWT con access y refresh tokens |
| **Access Token** | ✅ | Expira en 24 horas, contiene roles y permisos |
| **Refresh Token** | ✅ | Expira en 7 días, permite renovar access token |
| **Endpoints** | ✅ | `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/me` |
| **Frontend** | ✅ | `authService.js` con renovación automática de tokens |

### ✅ Rate Limiting
| Endpoint | Límite | Descripción |
|----------|--------|-------------|
| **Login** | 5/min | Protección contra fuerza bruta |
| **User Create** | 10/min | Prevención de spam de usuarios |
| **User Delete** | 5/min | Operación sensible limitada |
| **Backup** | 5/min | Operación costosa limitada |
| **AI Analysis** | 10/min | Endpoints de IA costosos |
| **Default** | 60/min | Operaciones generales |

### ✅ Logs de Auditoría
| Evento | Nivel | Datos Registrados |
|--------|-------|-------------------|
| **LOGIN_SUCCESS** | INFO | usuario, IP, timestamp |
| **LOGIN_FAILED** | WARNING | intento, IP, razón |
| **USER_CREATE/UPDATE/DELETE** | INFO | acción, recurso, detalles |
| **PASSWORD_CHANGE** | INFO | usuario afectado |
| **BACKUP_CREATE** | INFO | tipo, items |
| **UNAUTHORIZED_ACCESS** | WARNING | intento, IP |

**Archivo de Log:** `/var/log/luiggi_audit.log`

### ✅ Verificación de Permisos Server-Side
- El parámetro `isAdmin` del cliente ahora se VERIFICA contra la base de datos
- Filtrado de datos se hace en el backend, no solo en frontend
- Doble capa de seguridad: backend (principal) + frontend (secundario)

---

## COMPLETADO EN ESTA SESIÓN (01/02/2026)

### ✅ P0 - Bug Fix: IA Lab Visualizer Layout
| Componente | Estado | Descripción |
|------------|--------|-------------|
| **Visualizer.jsx** | ✅ | Corregido el bug donde la imagen expandía demasiado y ocultaba el botón "Analizar" |
| **CSS Layout** | ✅ | Añadido `max-h-[50vh]` al contenedor de imagen y `shrink-0` al botón |
| **UX** | ✅ | El botón "Analizar Plano con IA" siempre es visible después de subir imagen |

### ✅ P1 - ClientSelector: Gestión de Clientes en Presupuestador
| Componente | Estado | Descripción |
|------------|--------|-------------|
| **ClientSelector.jsx** | ✅ NUEVO | Componente con búsqueda y creación de clientes |
| **Permisos por Rol** | ✅ | Admin: todos, Comerciales: asignados, Tiendas: propios, Prescriptores: sin acceso |
| **Búsqueda** | ✅ | Búsqueda por nombre, código, teléfono, email |
| **Creación** | ✅ | Formulario inline para crear clientes nuevos (nombre*, teléfono, email) |
| **Integración CRM** | ✅ | Los clientes se crean como contactos en el CRM |
| **BudgetTable.jsx** | ✅ | Integrado el nuevo selector reemplazando input simple |

### ✅ P3 - Refactorización Backend y Frontend
| Componente | Estado | Descripción |
|------------|--------|-------------|
| **Backend Models** | ✅ | Modelos extraídos a `/backend/models/` (user, product, project, client, crm) |
| **Backend Services** | ✅ | Servicios extraídos a `/backend/services/` (database, auth, email, jwt, rate_limiter, audit) |
| **Backend Routers** | ✅ | Routers creados en `/backend/routers/` (auth, products, clients) |
| **Frontend Components** | ✅ | Nuevos componentes extraídos: `ConfirmOrderModal.jsx`, `BudgetTotals.jsx` |
| **server.py** | ⚠️ | Mantiene funcionalidad pero con estructura lista para migración gradual |

---

## COMPLETADO EN SESIÓN ANTERIOR (25/01/2026)

### ✅ P1 - Etiquetado de Oportunidades por Tipo de Negocio

| Componente | Estado | Descripción |
|------------|--------|-------------|
| **Backend** | ✅ | Campo `businessType` y `moduleType` en OpportunityModel |
| **API Filtrado** | ✅ | `GET /api/crm/opportunities?businessType=cocina&moduleType=montada` |
| **Endpoint Armarios** | ✅ | `POST /api/crm/opportunities/from-armario/{project_id}` |
| **Frontend Filtros** | ✅ | **4 botones: TODOS / COCINA MONTADA / COCINA DESPIECE / ARMARIOS** |
| **Badges** | ✅ | Etiquetas de tipo en tarjetas (amber=montada, orange=despiece, emerald=armarios) |
| **Auto-etiquetado** | ✅ | Al guardar proyecto cocina/armarios, se etiqueta oportunidad correctamente |

### ✅ P2 - Panel de Métricas con Gráficos

| Componente | Estado | Descripción |
|------------|--------|-------------|
| **Endpoint Tendencias** | ✅ | `GET /api/admin/metrics/trends` con datos mensuales |
| **Gráfico Ventas** | ✅ | BarChart de ventas mensuales (€) |
| **Gráfico Opps** | ✅ | LineChart de oportunidades creadas/ganadas/perdidas |
| **Distribución** | ✅ | PieChart de Cocina vs Armarios |
| **Embudo** | ✅ | Barra horizontal de conversión por etapa |

---

## ARQUITECTURA ACTUAL

```
/app
├── backend/
│   ├── server.py (~5400 líneas - funcional, migración gradual pendiente)
│   ├── models/                    # Modelos Pydantic extraídos
│   │   ├── __init__.py
│   │   ├── base.py               # TimestampMixin, generate_id
│   │   ├── user.py               # UserModel, UserCreate, UserUpdate, UserResponse
│   │   ├── product.py            # ProductModel, ZonePoints, MaterialModel
│   │   ├── project.py            # ProjectModel, SettingsModel, BudgetItemModel
│   │   ├── client.py             # ClientModel, CLIENT_SEGMENTS
│   │   └── crm.py                # Contact, Opportunity, Activity, CalendarEvent
│   ├── services/                  # Servicios reutilizables
│   │   ├── __init__.py
│   │   ├── database.py           # MongoDB connection (db)
│   │   ├── auth_service.py       # hash_password, verify_password
│   │   ├── email_service.py      # SendGrid integration
│   │   ├── jwt_service.py        # 🔒 JWT tokens, dependencies
│   │   ├── rate_limiter.py       # 🔒 Rate limiting con slowapi
│   │   └── audit_service.py      # 🔒 Logs de auditoría
│   ├── routers/                   # FastAPI routers (estructura base)
│   │   ├── __init__.py
│   │   ├── auth.py               # /api/auth/*, /api/users/*
│   │   ├── products.py           # /api/products/*
│   │   └── clients.py            # /api/clients/*
│   └── tests/
│       └── test_p1_p2_features.py
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── AdminWorkView.jsx
│       │   ├── CRMPipeline.jsx
│       │   ├── BudgetTable.jsx (~1400 líneas)
│       │   ├── ClientSelector.jsx        # Selector de clientes con permisos
│       │   ├── ConfirmOrderModal.jsx     # Modal confirmación pedido
│       │   ├── BudgetTotals.jsx          # Sección totales
│       │   ├── Login.jsx                 # 🔒 Integrado con JWT
│       │   ├── Visualizer.jsx (FIXED)
│       │   ├── DespieceModal.jsx
│       │   └── Armarios.jsx
│       └── services/
│           ├── api.js
│           └── authService.js            # 🔒 NUEVO - JWT management
├── var/log/
│   └── luiggi_audit.log                  # 🔒 Logs de auditoría
└── memory/
    └── PRD.md
```

---

## PRÓXIMAS TAREAS

### P1 - Alta Prioridad
- [ ] PDF Aesthetics: Ajustar encabezado según diseño del usuario
- [ ] Permisos UI: Mover checkbox de "Armarios" en panel de usuario
- [ ] Migración `totalPvp`: Script para actualizar proyectos históricos

### P2 - Media Prioridad
- [ ] Campos superpuestos: Investigar bug de overlapping (necesita más info del usuario)
- [ ] Estabilidad Frontend: Investigar error `insertBefore` de React
- [ ] Filtros temporales en métricas (mes, trimestre, año)
- [ ] Campo `catalogOrder` para ordenar productos

### P3 - Refactorización FASE 2 (Migración Gradual)
- [ ] **Migrar endpoints de auth** de server.py a routers/auth.py
- [ ] **Migrar endpoints de products** de server.py a routers/products.py
- [ ] **Crear routers CRM** (opportunities, contacts, activities, calendar)
- [ ] **Crear routers Admin** (metrics, backups, settings)
- [ ] **Integrar componentes extraídos** en BudgetTable.jsx (ConfirmOrderModal, BudgetTotals)

---

## TESTS

| Test File | Coverage |
|-----------|----------|
| test_p1_p2_features.py | 100% |
| test_admin_metrics.py | 100% |
| test_crm_isolation_roles.py | 100% |
| test_armarios_ia.py | 91% |
| test_new_roles_features.py | 100% |

---

## CREDENCIALES

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| MARIO | MARIO | Director Comercial |
| TIENDSA | TIENDSA | Tienda/Punto de Venta |
| COMSA | COMERCIAL | Comercial |
| PRESCRIPTOR1 | PRESCRIPTOR1 | Colaborador Comercial |

---

## PROBLEMA CONOCIDO (P2)

**Estabilidad del Frontend**: Error recurrente de React DOM (`insertBefore`) que podría causar crashes aleatorios. El root cause no ha sido diagnosticado completamente.

---

## INTEGRACIONES

- **Google Gemini** (via emergentintegrations): gemini-3-flash-preview para texto, gemini-3-pro-image-preview para imágenes
- **SendGrid**: Envío de backups por email
- **jspdf**: Generación de PDFs en frontend
- **recharts**: Gráficos de métricas
