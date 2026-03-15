# LUIGGI HOME - Kitchen Budgeting ERP/CRM

## Estado del Proyecto: EN DESARROLLO ACTIVO
## Última Actualización: 15 Marzo 2026

---

## ✅ COMPLETADO EN ESTA SESIÓN (15 Marzo 2026)

### 1. Precios MV Tarifa 1 - CORREGIDOS AL 100%
- ✅ **383 productos MV** con precios T1 corregidos
- ✅ Precios verificados:
  - A100/70 = **62** ✅
  - A100/90 = **70** ✅
  - A60/70 = **62** ✅
  - A60/90 = **68** ✅
- ✅ Todas las categorías: BAJOS, ALTOS (H70/H90), COLUMNAS, SOBREENCIMERAS, ALTILLOS

### 2. Analizador de Planos IA - Filtro por Biblioteca
- ✅ Frontend envía biblioteca activa al backend
- ✅ Backend filtra productos por biblioteca (ZC/MV)
- ✅ Indicador visual "CATÁLOGO: ZC" o "CATÁLOGO: MV"

### 3. Error Guardar Casco - SOLUCIONADO
- ✅ Causa: No existían materiales en la BD
- ✅ Solución: Insertados 7 materiales (4 ZC, 3 MV)
- ✅ Materiales MV: Blanco SUPERPAN (+0€), Gris MV (+15€), Roble MV (+22€)

---

## 📋 PENDIENTE

### P1 - Prioridad Alta
- [ ] Casco por defecto por sección/biblioteca
- [ ] Restaurar logo empresa (re-subida por usuario)

### P2 - Media
- [ ] Refactorización BudgetTable.jsx (3071 líneas)
- [ ] Bug cálculo "Despiece" (PAUSADO)

### P3 - Baja
- [ ] Refactorización SettingsModal.jsx, server.py
- [ ] Glitch visual sidebar colapsado

---

## ARQUITECTURA

```
/app/backend/
├── server.py           # API principal
├── routes/ia_lab.py    # Análisis planos con filtro biblioteca
└── models/schemas.py

/app/frontend/src/
├── components/
│   ├── BudgetTable.jsx
│   ├── Visualizer.jsx      # Modificado: filtro biblioteca
│   ├── Digitalizador.jsx   # Filtro biblioteca
│   └── SettingsModal.jsx
└── services/api.js
```

---

## CREDENCIALES
- **Usuario:** MARIO
- **Contraseña:** MARIO

## BASE DE DATOS
- **DB:** luiggi_home
- **Productos ZC:** 4542
- **Productos MV:** 383 (todos con precios T1 correctos)
- **Materiales:** 7 (4 ZC, 3 MV)
