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

## Current Statistics (Mar 2026)
- **Total Products:** 7,148
- **Programs:** 
  - ESTÁNDAR: 4,092 productos
  - GOLA: 2,518 productos
  - ALUMINIO: 144 productos
- **Categories:** 19+ unique categories
- **Abatibles:**
  - HK-TOP: 54 productos
  - HF Bi-fold: 144 productos
  - HL Aventos: 39 productos
  - HS Servo-Drive: 69 productos

## Completed Tasks

### Mar 7, 2026 - Session 2: Critical Bugs & UX Improvements ✅

#### Bug Fixes
1. **Cálculo COSTO con descuento (P0)** - FIXED
   - El modo COSTO ahora muestra correctamente los totales con descuento del usuario
   - Footer cambia a color púrpura en modo COSTO con indicador visual
   - Files: `/app/frontend/src/components/Digitalizador.jsx`

2. **Expedientes duplicados (P0)** - FIXED
   - Añadida validación de unicidad antes de guardar presupuesto
   - Creado índice único en MongoDB para `expNumber`
   - Error claro: "El número de expediente X ya existe"
   - Files: `/app/backend/server.py`

3. **Precios con 2 decimales (P1)** - FIXED
   - Todos los precios ahora muestran exactamente 2 decimales
   - Files: `/app/frontend/src/components/Digitalizador.jsx`

#### New Features
4. **Filtro de Tipos de Apertura Abatible** - NEW
   - Nuevo selector en librería: 🚪 APERTURA
   - Opciones: ABATIBLES, HK-TOP, HF BI-FOLD, HL AVENTOS, HS SERVO
   - Disponible en vista horizontal y vertical
   - Files: `/app/frontend/src/components/BudgetTable.jsx`

#### Already Implemented (Verified)
5. **Descuentos Montada/Despiece** - Ya existente
   - Usuarios pueden tener descuentos diferentes por módulo
   - Se aplica automáticamente según el módulo actual

6. **Semicolumnas sin selector de mano** - Ya existente
   - Semicolumnas con 2 puertas no muestran selector izq/der
   - Muebles con cajones/gavetas tampoco

### Mar 7, 2026 - Session 1: Permission Fix & Authentication ✅

#### Bug Fixes
1. **Armarios Permission Bug (P0)** - FIXED
   - Added permission check `(isAdmin || canAccessArmarios)` in App.js

2. **DateTime Comparison Bug** - FIXED
   - Added timezone normalization for MongoDB dates

#### New Features
3. **Email Registration System** - COMPLETE
4. **Two-Factor Authentication (2FA)** - COMPLETE
5. **Enhanced Login Flow** - COMPLETE

## Pending Tasks

### P1 - Next Tasks
- [ ] Normalización de SERIES en BD (BAJO vs BAJOS, ESTANDAR vs ESTÁNDAR)
- [ ] Añadir configuración 2FA en perfil de usuario
- [ ] Investigar otros problemas del catálogo del DOCX

### P2 - Technical Debt
- [ ] Refactoring `/app/backend/server.py` (~5,800 líneas)
- [ ] Decompose `BudgetTable.jsx` (>1900 líneas)
- [ ] Decompose `Armarios.jsx` (>3300 líneas)

### P3 - Future Features
- [ ] Rol "Gerente" con permisos específicos
- [ ] Client-Sales Rep Assignment

## Key Files Modified This Session

### Backend
- `/app/backend/server.py` - Validación expedientes duplicados, índice único

### Frontend
- `/app/frontend/src/components/Digitalizador.jsx` - Modo COSTO, decimales
- `/app/frontend/src/components/BudgetTable.jsx` - Filtro apertura abatible

## Test Credentials
- **Admin User:** MARIO / MARIO
- **Test Email User:** nuevo_usuario@example.com / Test1234

## Filtros de Librería Disponibles
1. **PROGRAMA:** ESTÁNDAR, GOLA, ALUMINIO
2. **CATEGORÍA:** BAJOS, ALTOS, COLUMNAS, etc.
3. **SERIE:** Variantes por fondo y altura
4. **APERTURA:** ABATIBLES, HK-TOP, HF, HL, HS (NUEVO)

## API Endpoints - Digitalizador

| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/digitalizador/generate-exp-number | POST | Genera número expediente único |
| /api/digitalizador/save | POST | Guarda presupuesto (valida duplicados) |
| /api/digitalizador/history | GET | Historial de presupuestos |
| /api/digitalizador/analyze | POST | Análisis IA de imagen |

## Test Reports
- Latest: `/app/test_reports/iteration_21.json`
