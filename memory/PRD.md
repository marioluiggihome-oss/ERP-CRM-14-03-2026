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
**INTEGRADO en tab "COCINA DESPIECE"** (sin botón separado)

- **Integración directa:** Al seleccionar "COCINA DESPIECE", el catálogo muestra tableros ALVIC
- **Filtros específicos para tableros:**
  - 🏭 FABRICANTE (ALVIC, etc.)
  - 📦 MODELO/COLECCIÓN (LUXE, ZENIT, SYNCRON, BASIK)
  - ✨ ACABADO (Brillo, Supermatte, Textura Madera)
  - 📏 GROSOR (18mm, 0.8mm para cantos)
- **Tabla de productos:** CÓDIGO | PRODUCTO | COLECCIÓN | COLOR | ACABADO | MM | €/M²
- **Modal "AÑADIR TABLERO":** Al hacer clic en un producto
  - Campos: Ancho (mm), Alto (mm), Cantidad
  - Cálculo automático de área (m²) y precio estimado
  - Botón "AÑADIR AL PRESUPUESTO"
- **18 productos ALVIC de muestra:** LUXE, ZENIT, SYNCRON, BASIK, CANTOS

**Backend API:** `/api/despiece-budgeter/*`
- GET `/products` - Listar con filtros
- GET `/products/filters` - Opciones de filtros
- POST `/seed-alvic` - Poblar datos de muestra
- CRUD completo para productos y presupuestos

**Archivos modificados:**
- `/app/frontend/src/components/BudgetTable.jsx` - Lógica de modo despiece integrada
- `/app/backend/routes/despiece_budgeter.py` - API de tableros

### ✅ P2 - Mejoras UX de Filtros de Dimensiones
- **Labels mejoradas:** "AN", "AL", "FO" → "ANCHO", "ALTO", "FONDO"
- **Placeholder:** "--" → "cm" (indica unidad de medida)
- **Diseño visual:** Fondo azul claro con bordes prominentes

### ✅ P2 - UI de Gestión 2FA
- **Nuevo tab:** "Seguridad 2FA" en Panel Maestro
- **Estado visible:** Muestra si 2FA está activo/inactivo
- **Acciones disponibles:** Activar, Desactivar, Regenerar códigos

## Pending Tasks

### P1 - Próximas Tareas
- [ ] **Exportación de Catálogo mejorada** - Usuario rechazó versión actual
- [ ] **Verificar dominio Resend** - Para enviar emails a cualquier dirección

### P2 - Technical Debt
- [ ] **Refactoring `BudgetTable.jsx`** - >3000 líneas
- [ ] **Refactoring `SettingsModal.jsx`** - >4100 líneas

## Key Architecture

### Modo COCINA MONTADA
- Catálogo de muebles de cocina completos
- Filtros: PROGRAMA, CATEGORÍA, SERIE, MEDIDAS
- Puntos por zona (Z1-Z6)

### Modo COCINA DESPIECE
- Catálogo de tableros/materiales (ALVIC, VIFORMING, etc.)
- Filtros: FABRICANTE, MODELO, ACABADO, GROSOR
- Precio por m²
- Modal para especificar dimensiones de corte

## Test Credentials
- **Admin User:** MARIO / MARIO

## API Endpoints

### DESPIECE Budgeter
- `GET /api/despiece-budgeter/products` - Listar productos
- `GET /api/despiece-budgeter/products/filters` - Opciones de filtros
- `POST /api/despiece-budgeter/seed-alvic` - Poblar muestra ALVIC

### Auth 2FA
- `POST /api/auth-advanced/2fa/enable` - Iniciar 2FA
- `POST /api/auth-advanced/2fa/disable-simple` - Desactivar 2FA
- `POST /api/auth-advanced/2fa/regenerate-backup` - Regenerar códigos
