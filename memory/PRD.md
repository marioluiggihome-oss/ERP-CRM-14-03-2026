# LUIGGI HOME - Kitchen Budget ERP/CRM

## Completed Tasks - Session Mar 8, 2026

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
- **18 productos ALVIC de muestra:** LUXE, ZENIT, SYNCRON, BASIK, CANTOS

### ✅ P2 - Mejoras UX Filtros
- Labels mejoradas: "ANCHO/ALTO/FONDO" en lugar de "AN/AL/FO"
- Placeholder "cm" en lugar de "--"
- Diseño visual con fondo azul

### ✅ P2 - UI de Gestión 2FA
- Tab "Seguridad 2FA" en Panel Maestro
- Estado visible (activo/inactivo)
- Botones para configurar, desactivar y regenerar códigos

## Componentes Refactorizados

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

## Test Credentials
- **Admin User:** MARIO / MARIO

## Pending Tasks

### P1 - Próximas
- [ ] Exportación de catálogo mejorada
- [ ] Verificar dominio Resend

### P2 - Technical Debt
- [ ] Refactoring `BudgetTable.jsx` (>3000 líneas)
- [ ] Refactoring `SettingsModal.jsx` (>4100 líneas)
