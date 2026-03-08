# LUIGGI HOME - Kitchen Budget ERP/CRM

## Original Problem Statement
Replicate a kitchen budgeting ERP/CRM application named **LUIGGI HOME**.

## User's Preferred Language
Spanish (es)

## Current Statistics (Mar 2026)
- **Total Products:** 7,148
- **Series Normalizadas:** 2,428 productos actualizados
- **DESPIECE Products (ALVIC):** 18 productos de muestra

## Completed Tasks - Session Mar 8, 2026

### ✅ P0 - Módulo DESPIECE (Presupuestador de Tableros)
- **Nuevo componente:** `DespieceBudgeter.jsx` - Modal completo para presupuestos de tableros
- **Backend API:** `/api/despiece-budgeter/*` con endpoints para productos, presupuestos y filtros
- **Productos ALVIC de muestra:** 18 productos de las colecciones LUXE, ZENIT, SYNCRON, BASIK y CANTOS
- **Funcionalidades:**
  - Filtros por fabricante, colección, acabado, grosor
  - Cálculo automático de área (m²) y precio
  - Gestión de cantos (L1, L2, W1, W2)
  - Guardar presupuestos en base de datos
- **Botón TABLEROS** añadido a la barra de herramientas principal

**Archivos creados:**
- `/app/backend/routes/despiece_budgeter.py`
- `/app/frontend/src/components/DespieceBudgeter.jsx`

### ✅ P2 - Mejoras UX de Filtros de Dimensiones
- **Labels mejoradas:** "AN", "AL", "FO" → "ANCHO", "ALTO", "FONDO"
- **Placeholder:** "--" → "cm" (indica unidad de medida)
- **Diseño visual:** Fondo azul claro con bordes prominentes
- **Focus states:** Efectos de enfoque con anillos y transiciones

**Archivos modificados:**
- `/app/frontend/src/components/BudgetTable.jsx` - Líneas 1715-1750, 1830-1875

### ✅ P2 - UI de Gestión 2FA
- **Nuevo tab:** "Seguridad 2FA" en Panel Maestro
- **Estado visible:** Muestra si 2FA está activo/inactivo
- **Acciones disponibles:**
  - Activar 2FA (botón "Configurar 2FA")
  - Desactivar 2FA (cuando está activo)
  - Regenerar códigos de respaldo
- **Información educativa:** Guía sobre cómo funciona 2FA

**Archivos modificados:**
- `/app/frontend/src/components/SettingsModal.jsx` - Tab de Seguridad 2FA
- `/app/backend/routes/auth_advanced.py` - Endpoints `2fa/disable-simple`, `2fa/regenerate-backup`

## Completed Tasks - Sessions Anteriores

### 📧 Email Service (Resend)
- Migrado de SendGrid a Resend
- Logo LUIGGI HOME embebido en emails
- Fallback a email de respaldo por limitaciones del tier gratuito

### 💰 Discount Logic Fix
- Corregido bug donde 0% descuento no se aplicaba
- Operador `||` reemplazado por `??` (nullish coalescing)

### 📄 PDF Export Fix
- Corregido bug de dimensiones divididas por 10
- Los anchos ahora se muestran correctamente (90cm en lugar de 9cm)

### 🎨 GOLA Profiles
- Añadidas opciones GOLA Alto/Bajo en el presupuesto
- Guardado en proyecto y exportación a PDF

### 📦 Catalog Export
- Endpoints para exportar catálogo a Excel y PDF
- Incluye imágenes de productos

### 💾 Backup/Restore
- Endpoints para crear y restaurar backups de base de datos

## Pending Tasks

### P1 - Próximas Tareas
- [ ] **Exportación de Catálogo mejorada** - Usuario rechazó versión actual, necesita clarificación
- [ ] **Verificar dominio Resend** - Para enviar emails a cualquier dirección

### P2 - Technical Debt
- [ ] **Refactoring `BudgetTable.jsx`** - >2800 líneas, urgente descomposición
- [ ] **Refactoring `SettingsModal.jsx`** - >4100 líneas
- [ ] **Migrar endpoints a routers** - `server.py` es monolítico

### P3 - Backlog
- [ ] Reclasificar productos "HS"
- [ ] Mejorar glitch visual del sidebar colapsado (recurrente)

## Roles del Sistema

| Rol | Permisos CRM | Permisos Generales |
|-----|--------------|-------------------|
| Gerente | Ve TODO | Acceso total |
| Director Comercial | Ve TODO | Según permisos |
| Admin | Ve TODO | Acceso total |
| Responsable Delegación | Ve su delegación | Según permisos |
| Comercial | Solo sus clientes | Según permisos |
| Tienda | Solo sus datos | Limitado |

## Test Credentials
- **Admin User:** MARIO / MARIO

## Key Files Modified This Session
- `/app/backend/routes/despiece_budgeter.py` - NUEVO: API DESPIECE
- `/app/frontend/src/components/DespieceBudgeter.jsx` - NUEVO: UI DESPIECE
- `/app/frontend/src/components/BudgetTable.jsx` - Filtros mejorados, botón TABLEROS
- `/app/frontend/src/components/SettingsModal.jsx` - Tab Seguridad 2FA
- `/app/backend/routes/auth_advanced.py` - Endpoints 2FA

## API Endpoints Principales

### DESPIECE Budgeter
- `GET /api/despiece-budgeter/products` - Listar productos con filtros
- `GET /api/despiece-budgeter/products/filters` - Obtener opciones de filtros
- `POST /api/despiece-budgeter/products` - Crear producto
- `POST /api/despiece-budgeter/products/bulk` - Crear productos masivamente
- `POST /api/despiece-budgeter/seed-alvic` - Poblar productos ALVIC de muestra
- `GET /api/despiece-budgeter/budgets` - Listar presupuestos
- `POST /api/despiece-budgeter/budgets` - Crear presupuesto
- `GET /api/despiece-budgeter/stats` - Estadísticas

### Auth 2FA
- `POST /api/auth-advanced/2fa/enable` - Iniciar configuración 2FA
- `POST /api/auth-advanced/2fa/verify` - Verificar código 2FA
- `POST /api/auth-advanced/2fa/disable-simple` - Desactivar 2FA (sin código)
- `POST /api/auth-advanced/2fa/regenerate-backup` - Regenerar códigos de respaldo
