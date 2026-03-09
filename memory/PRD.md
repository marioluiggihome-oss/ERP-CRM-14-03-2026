# LUIGGI HOME - Kitchen Budget ERP/CRM

## Completed Tasks - Session Mar 9, 2026

### ✅ P0 - Importación Tarifa Puertas ALVIC (Excel)
- Importados **5,495 productos** desde "Tarifa cocina Puertas DF (abr-2025).xlsx"
- **PUERTAS:** 5,306 combinaciones Alto × Ancho
- **TIRADORES:** 189 combinaciones (6 modelos)
- Colecciones: VIFORMING, SYNCRON, LUXE (A, B), LUXE PLUS, ZENIT, MATTDECO, TR-MAX, EUROFORMING
- Dimensiones: Alto 138-2498mm × Ancho 100-1197mm
- Precios: 7.92€ - 406.09€

### ✅ P0 - Unificación Fabricantes DF → ALVIC
- DF y ALVIC son la misma empresa
- Todos los productos unificados bajo **ALVIC**
- Total: **5,968 productos** en `despiece_products`

### ✅ P0 - Nuevo Flujo Presupuestador DESPIECE
**Componente `DespieceStepByStep.jsx`** - Flujo paso a paso:
1. **Paso 1:** Seleccionar Categoría (Puertas/Tiradores)
2. **Paso 2:** Seleccionar Modelo/Colección
3. **Paso 3:** Ver **Matriz de Precios** (Alto × Ancho)
4. **Click en celda** → Añade item al presupuesto

**Características:**
- Matriz visual con precios exactos según tarifa
- Breadcrumb navegable (PUERTA → MODELO → MEDIDAS)
- Añadir múltiples items desde la matriz
- Sección "DESPIECE - TABLEROS" en presupuesto

### ✅ P1 - Eliminación Iconos de Exportación
- Removidos iconos Excel/PDF de las 3 vistas del catálogo
- Funcionalidad disponible solo en Panel Maestro

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
- [x] ~~Construir `DespieceWizard.jsx`~~ ✅ Wizard paso a paso IMPLEMENTADO E INTEGRADO
- [x] ~~Integrar wizard en el modo "COCINA DESPIECE"~~ ✅ Accesible desde sidebar izquierdo

### P1 - Próximas
- [ ] Exportación de catálogo mejorada (solicitar especificaciones al usuario)
- [ ] Verificar dominio Resend para emails

### P2 - Technical Debt
- [x] ~~Refactoring `BudgetTable.jsx` (>3400 líneas)~~ ✅ Completado (3122 líneas)
- [ ] Refactoring `SettingsModal.jsx` (>4100 líneas)
- [ ] Migrar endpoints de `server.py` a routers dedicados

## Importación de Tarifa DF (Mar 9, 2026)
- ✅ **Importados 5495 productos desde "Tarifa cocina Puertas DF (abr-2025).xlsx"**
  - **PUERTAS:** 5306 combinaciones Alto x Ancho
  - **TIRADORES:** 189 combinaciones Modelo x Ancho x Color

### Colecciones de Puertas DF:
- VIFORMING (2 cantos, 4 cantos): 602 productos
- SYNCRON, SYNCRON FINGERPULL: 617 productos  
- LUXE A, LUXE B, LUXE FINGERPULL: 998 productos
- LUXE PLUS A, LUXE PLUS B: 762 productos
- ZENIT METAL PLUS: 381 productos
- QUADRO SLIM (Syncron, Zenit): 326 productos
- MATTDECO (18MM, 22MM, Fingerpull): 998 productos
- TR-MAX BLANCO: 381 productos
- EUROFORMING: 241 productos

### Modelos de Tiradores DF:
- FORMENTERA, MALLORCA, MENORCA, IBIZA, TENERIFE, MADEIRA

## Limpieza de Datos (Mar 8, 2026)
- ✅ **Eliminados 103+ productos de serie ALUMINIO** de la base de datos correcta
- ✅ **Base de datos unificada y separada**:
  - `products`: 7045 productos MONTADA (muebles ensamblados)
    - ESTÁNDAR: 4409
    - GOLA: 2636
  - `despiece_products`: 5968 productos DESPIECE
    - DF: 5495 (PUERTAS + TIRADORES, nueva tarifa ABR-2025)
    - ALVIC: 473 (LUXE, ZENIT, SYNCRON, BASIK)
    - CANTOS: 2
- ✅ **Exportación Excel actualizada** con parámetro `tipo=montada|despiece`

## API de Exportación Excel Actualizada
```
GET /api/products/export/excel?tipo=montada  → Exporta muebles
GET /api/products/export/excel?tipo=despiece → Exporta tableros
GET /api/admin/export-database → Excel con 2 hojas: "Productos Montada" y "Productos Despiece"
```

## DespieceWizard - Flujo Paso a Paso
1. **Paso 1 - Fabricante**: Seleccionar fabricante (ALVIC, etc.)
2. **Paso 2 - Modelo**: Seleccionar colección (LUXE, ZENIT, SYNCRON, BASIK)
3. **Paso 3 - Color**: Seleccionar color/acabado
4. **Paso 4 - Medidas**: Matriz de precios Alto×Ancho con click para añadir

Acceso: Sidebar izquierdo → Botón "WIZARD DESPIECE" (modo COCINA DESPIECE)

## Test Reports
- `/app/test_reports/iteration_23.json` - Bug fix filtros librería (100% PASS)
- `/app/test_reports/iteration_24.json` - Refactorización BudgetTable.jsx (100% PASS)
