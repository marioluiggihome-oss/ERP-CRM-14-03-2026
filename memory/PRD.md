# LUIGGI HOME - Kitchen Budget ERP/CRM

## Original Problem Statement
Replicate a kitchen budgeting ERP/CRM application named **LUIGGI HOME** with focus on:
1. User-guided product catalog creation from master PDF (TARIFA-COMPLETA.pdf)
2. Digitalizador (draft digitizer) with image analysis, PDF export, cost/margin calculation
3. Armarios (wardrobes) component with AI-powered design
4. User roles & permissions (Admin, Gerente, Director Comercial)
5. Email registration and Two-Factor Authentication (2FA)

## User's Preferred Language
Spanish (es)

## Core Architecture
- **Frontend:** React + Shadcn/UI
- **Backend:** FastAPI (server.py + modular routers)
- **Database:** MongoDB (test_database)
- **AI Integration:** Google Gemini via emergentintegrations
- **Authentication:** JWT + TOTP (pyotp, qrcode)
- **Email:** SendGrid

## Current Statistics (Mar 2026)
- **Total Products:** 7,148
- **Programs:** ESTÁNDAR, GOLA, ALUMINIO
- **Categories:** 19+ unique categories
- **Series normalizadas:** 2,428 productos actualizados

## Completed Tasks

### Mar 7, 2026 - Session 3: Permisos, Filtros y Emails ✅

#### Bug Fixes
1. **Permiso Armarios independiente de Admin** - FIXED
   - Ahora SOLO se usa `canAccessArmarios` (sin bypass de isAdmin)
   - Admin necesita tener el permiso activo para ver Armarios
   - Files: `BudgetTable.jsx`, `App.js`

2. **Series duplicadas en librería** - FIXED
   - Normalizado ALTOS→ALTO, BAJOS→BAJO, ESTANDAR→ESTÁNDAR
   - 2,428 productos actualizados

#### New Features
3. **Filtro de medidas (📐)** - NEW
   - Campos: Ancho (AN), Alto (AL), Fondo (FO)
   - Tolerancia de ±5mm para búsqueda flexible
   - Botón X para limpiar filtros
   - Disponible en vistas horizontal y vertical

4. **Emails con diseño profesional** - NEW
   - Plantilla moderna con gradiente índigo/naranja
   - Header "LUIGGI HOME" con estilo corporativo
   - Email de verificación al usuario
   - Notificación al admin (mario@luiggihome.es) en cada registro
   - Email de recuperación de contraseña

### Mar 7, 2026 - Session 2 ✅
- Cálculo COSTO con descuento
- Expedientes duplicados
- Filtro de apertura abatible (HK, HF, HL, HS)

### Mar 7, 2026 - Session 1 ✅
- Email registration y 2FA
- Bug permiso Armarios (parcial)

## Pending Tasks

### P0 - Inmediato
- [ ] Verificar que el botón ARMARIOS desaparezca para MARIO (tiene canAccessArmarios: false)

### P1 - Próximas Tareas
- [ ] Revisar productos HS (35AVABLHS1200 y análogos) - ¿Ya no son Servo-Drive?
- [ ] Verificar envío real de emails con SendGrid (puede requerir verificación de dominio)
- [ ] Añadir panel de configuración 2FA en perfil de usuario
- [ ] Investigar otros problemas del catálogo del DOCX

### P2 - Technical Debt
- [ ] Refactoring `/app/backend/server.py` (~5,800 líneas)
- [ ] Decompose `BudgetTable.jsx` (>2000 líneas)
- [ ] Decompose `Armarios.jsx` (>3300 líneas)

### P3 - Future Features
- [ ] Rol "Gerente" con permisos específicos
- [ ] Client-Sales Rep Assignment
- [ ] Gestión de delegaciones

## Filtros de Librería Disponibles
1. **📁 PROGRAMA:** ESTÁNDAR, GOLA, ALUMINIO
2. **📂 CATEGORÍA:** BAJOS, ALTOS, COLUMNAS, etc.
3. **📄 SERIE:** Variantes por fondo y altura
4. **🚪 APERTURA:** ABATIBLES, HK-TOP, HF, HL, HS
5. **📐 MEDIDAS:** Ancho, Alto, Fondo (±5mm tolerancia) - NUEVO

## Configuration
```
ADMIN_EMAIL=mario@luiggihome.es
SENDGRID_API_KEY=configured
```

## Test Credentials
- **Admin User:** MARIO / MARIO (canAccessArmarios: false)
- **Test Email User:** nuevo_usuario@example.com / Test1234

## Key Files Modified This Session
- `/app/frontend/src/components/BudgetTable.jsx` - Filtros medidas, permiso Armarios
- `/app/frontend/src/App.js` - Permiso Armarios
- `/app/backend/routes/auth_advanced.py` - Emails modernos + notificación admin
- `/app/backend/.env` - ADMIN_EMAIL
