# LUIGGI HOME - Kitchen Budget ERP/CRM

## Completed Tasks - Session Mar 8, 2026

### ✅ P0 - Bug Fix: Filtros de librería DESPIECE (NUEVO)
**Corregido**: La librería derecha (vertical) ahora muestra los filtros correctos según el módulo activo:

- **Modo COCINA DESPIECE:** 
  - Sección "FILTROS DESPIECE" con: FABRICANTE, MODELO, ACABADO, GROSOR
  - Contador "X tableros disponibles"
- **Modo COCINA MONTADA:**
  - Filtros: PROGRAMA, CATEGORÍA, SERIE, MEDIDAS
  
Todas las posiciones de librería (horizontal, vertical, top) funcionan correctamente.

### ✅ P2 - Bug Fix: Glitch visual sidebar colapsado
- Mejorado el comportamiento del sidebar izquierdo al colapsar
- Agregado `opacity` y `pointer-events` condicionados para transición suave

### ✅ P0 - Módulo DESPIECE (Presupuestador de Tableros)
**INTEGRADO en tab "COCINA DESPIECE"** - Funcionando al 100%

- **Modo COCINA DESPIECE:** Al seleccionar el tab, el catálogo muestra tableros ALVIC
- **Filtros de tableros:**
  - 🏭 FABRICANTE (ALVIC, etc.)
  - 📦 MODELO/COLECCIÓN (LUXE, ZENIT, SYNCRON, BASIK)
  - ✨ ACABADO (Brillo, Supermatte, Textura Madera)
  - 📏 GROSOR (18mm, 0.8mm para cantos)
- **Tabla de productos:** CÓDIGO | PRODUCTO | COLECCIÓN | COLOR | ACABADO | MM | €/M²
- **Modal "AÑADIR TABLERO":**
  - Campos: Ancho (mm), Alto (mm), Cantidad
  - Cálculo automático de área (m²) y precio estimado
  - Botón "AÑADIR AL PRESUPUESTO"
- **500+ productos DESPIECE:** LUXE, ZENIT, SYNCRON, BASIK, CANTOS

### ✅ P2 - Mejoras UX Filtros
- Labels mejoradas: "ANCHO/ALTO/FONDO" en lugar de "AN/AL/FO"
- Placeholder "cm" en lugar de "--"
- Diseño visual con fondo azul

### ✅ P2 - UI de Gestión 2FA
- Tab "Seguridad 2FA" en Panel Maestro
- Estado visible (activo/inactivo)
- Botones para configurar, desactivar y regenerar códigos

## Componentes Refactorizados

### ✅ BudgetTable.jsx Refactorizado (Mar 8, 2026)
**Reducido de 3413 a 3078 líneas (-335 líneas)**

Componentes extraídos a `/app/frontend/src/components/budget/`:
- `DespieceFilters.jsx` - DespieceFiltersHorizontal, DespieceFiltersVertical (109 líneas)
- `MontadaFilters.jsx` - MontadaFiltersHorizontal, MontadaFiltersVertical (223 líneas)
- `DespieceAddModal.jsx` - Modal para añadir tablero (136 líneas)
- `CatalogProductRow.jsx` - CatalogProductRowTable, CatalogProductRowCard (201 líneas)
- `BudgetItemRow.jsx` - Fila de ítem en presupuesto (234 líneas)
- `index.js` - Exports centralizados

### DespieceCatalog.jsx (NUEVO)
Componente avanzado con:
- 3 modos de vista: Tabla | Cuadrícula | Matriz de precios
- Filtros integrados
- Panel lateral de presupuesto
- Modal de añadir con cantos

### Backend API: /api/despiece-budgeter/*
- GET `/products` - Listar con filtros
- GET `/products/filters` - Opciones de filtros
- POST `/seed-alvic` - Poblar datos ALVIC
- POST `/seed-syncron` - Poblar datos SYNCRON (900 productos)

## Test Credentials
- **Admin User:** MARIO / MARIO

## Pending Tasks

### P0 - Prioridad Alta
- [ ] Construir `DespieceWizard.jsx` - Wizard paso a paso para despiece
- [ ] Integrar wizard en el modo "COCINA DESPIECE"

### P1 - Próximas
- [ ] Exportación de catálogo mejorada (solicitar especificaciones al usuario)
- [ ] Verificar dominio Resend para emails

### P2 - Technical Debt
- [x] ~~Refactoring `BudgetTable.jsx` (>3400 líneas)~~ ✅ Completado (3078 líneas)
- [ ] Refactoring `SettingsModal.jsx` (>4100 líneas)
- [ ] Migrar endpoints de `server.py` a routers dedicados

## Test Reports
- `/app/test_reports/iteration_23.json` - Bug fix filtros librería (100% PASS)
- `/app/test_reports/iteration_24.json` - Refactorización BudgetTable.jsx (100% PASS)
