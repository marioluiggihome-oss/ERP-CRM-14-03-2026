# LUIGGI HOME - Kitchen Budgeting ERP/CRM

## Estado del Proyecto: EN DESARROLLO ACTIVO

## Problema Original
Replicar una aplicación de presupuestos de cocina ERP/CRM llamada LUIGGI HOME con múltiples módulos, sistemas de precios y gestión de usuarios.

## Última Actualización: 15 Marzo 2026

---

## ✅ COMPLETADO EN ESTA SESIÓN (15 Marzo 2026)

### P0 - Mejoras UI/Datos
- ✅ **Botón CATÁLOGO MODELOS**: Solo visible para tarifa ZC (oculto en MV)
- ✅ **Variantes de altura COLUMNAS MV**: 68 productos con H200 y H220 (34 cada uno)

### P1 - Corte Viga por Biblioteca
- ✅ **UI configuración separada**: Campos "Corte Viga ZC (€)" y "Corte Viga MV (€)" en MÁRGENES
- ✅ **Backend**: Campo `libraryVigaCutIncrements` en SettingsModel
- ✅ **Cálculo de precios**: BudgetTable usa el valor correcto según biblioteca activa

### P1 - Exportación Catálogo por Biblioteca
- ✅ **Endpoint API**: `GET /api/products/export/library/{ZC|MV}` genera Excel
- ✅ **Botones UI**: En tab INVENTARIO - botones "ZC" y "MV" para descarga directa
- ✅ **Formato ZC**: Columnas REF, DESC, CATEGORÍA, SERIE, AN, AL, FO, Z1-Z12
- ✅ **Formato MV**: Columnas REF, DESC, CATEGORÍA, SERIE, AN, AL, FO, T1-T21

---

## 🔴 PENDIENTE / BUGS CONOCIDOS

### P0 - CRÍTICO (PAUSADO POR USUARIO)
1. **Bug cálculo presupuesto despiece** - Items de despiece no se suman al total (PAUSADO)

### P2 - MEJORAS
2. **Glitch visual barra lateral colapsada** - Recurrente
3. **Refactorización componentes grandes** - BudgetTable.jsx (~3078 líneas), SettingsModal.jsx (~4647 líneas)

### P3 - BLOQUEADOS
4. **Flujo registro email** - Requiere verificación de dominio en Resend

---

## ARQUITECTURA

### Backend (FastAPI)
```
/app/backend/
├── server.py                    # Servidor principal + endpoint exportación
├── models/schemas.py            # SettingsModel con libraryVigaCutIncrements
├── routes/
│   ├── libraries.py             # API de bibliotecas con pointValue
│   └── ...
├── mv_products_v2.py            # Datos MV con precios T1 y multiplicadores
└── add_columna_height_variants.py # Script para crear variantes H200/H220
```

### Frontend (React)
```
/app/frontend/src/
├── App.js                       # Estado libraryVigaCutIncrements
├── components/
│   ├── BudgetTable.jsx          # Cálculo con viga por biblioteca, botón CATÁLOGO condicional
│   └── SettingsModal.jsx        # UI Corte Viga ZC/MV, botones exportación
└── services/
    └── api.js                   # API calls
```

### Base de Datos (MongoDB: luiggi_home)
```
Colecciones:
- products          # library: ZC/MV, height: 200/220 para COLUMNAS MV
- system_settings   # libraryVigaCutIncrements: {ZC: €, MV: €}
- users             # allowedLibraries: ['ZC', 'MV']
```

---

## BIBLIOTECAS/TARIFAS

| Código | Sistema Precios | Productos | Columnas | Viga Cut Default |
|--------|-----------------|-----------|----------|------------------|
| ZC | ZONAS (Z1-Z12) | ~4505 | Z1-Z12 | 0€ |
| MV | TARIFAS (T1-T21) | ~290 | T1-T21 | 0€ |

---

## CREDENCIALES TEST
- **Usuario**: MARIO
- **Password**: MARIO
- **Rol**: Admin / Director Comercial
- **Bibliotecas**: ZC, MV

---

## PRÓXIMAS TAREAS

### Backlog
1. (P2 - PAUSADO) Fix cálculo total presupuesto despiece
2. (P2) Fix glitch sidebar colapsado
3. (P3) Refactorización BudgetTable.jsx
4. (P3) Refactorización SettingsModal.jsx
5. (P3) Verificar flujo registro email

---

## HISTORIAL DE CAMBIOS

### 15 Marzo 2026
- ✅ P0: Botón CATÁLOGO MODELOS solo visible en ZC
- ✅ P0: Variantes de altura COLUMNAS MV (H200, H220)
- ✅ P1: Corte Viga independiente por biblioteca (ZC/MV)
- ✅ P1: Endpoint y UI para exportación catálogo ZC/MV
- 🔧 Fix: DB_NAME en .env (de test_database a luiggi_home)
- 🔧 Fix: allowedLibraries para usuario MARIO

### 14 Marzo 2026
- Sistema de valor de punto por biblioteca
- Mejora de datos MV (256 productos)
- Sistema Multi-Biblioteca ZC/MV
