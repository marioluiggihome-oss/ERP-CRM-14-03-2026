# LUIGGI HOME - Kitchen Budgeting ERP/CRM

## Estado: EN DESARROLLO ACTIVO
## Última Actualización: 16 Marzo 2026

---

## ✅ COMPLETADO EN ESTA SESIÓN

### 1. Precios MV TARIFA 1 - CORREGIDOS
- ✅ ALTOS con variantes H70/H90 tienen precios DIFERENTES:
  - A100/70 = **62**, A100/90 = **70** ✅
  - A60/70 = **62**, A60/90 = **70** ✅
  - A25D/I/70 = **36**, A25D/I/90 = **38** ✅
- ✅ 383 productos MV con precios T1 verificados

### 2. Agenda de Montajes - CALENDARIO AGREGADO
- ✅ Tab "Calendario" añadido
- ✅ Vista mensual con navegación prev/next
- ✅ Días del mes con eventos de montajes
- ✅ Día actual destacado en naranja
- ✅ Leyenda de colores

### 3. Control de Módulo Montajes
- ✅ Campo `montajesEnabled` en settings
- ✅ Toggle en MASTER > MÁRGENES > "Módulos del Sistema"
- ✅ Botón de Montajes solo visible cuando está habilitado
- ✅ Modelo Pydantic actualizado

---

## 📋 PENDIENTE

### P1 - Alta
- [ ] Casco por defecto por sección/biblioteca
- [ ] Restaurar logo empresa

### P2 - Media
- [ ] Refactorización BudgetTable.jsx
- [ ] Bug "Despiece" (PAUSADO)

---

## ARQUITECTURA

```
/app/backend/
├── server.py
├── routes/ia_lab.py
└── models/schemas.py    # MODIFICADO: montajesEnabled

/app/frontend/src/
├── App.js               # MODIFICADO: state.settings
├── components/
│   ├── AgendaMontajes.jsx   # MODIFICADO: Calendario añadido
│   ├── SettingsModal.jsx    # MODIFICADO: Toggle módulos
│   └── ...
└── services/api.js
```

---

## CREDENCIALES
- **Usuario:** MARIO
- **Contraseña:** MARIO

## BASE DE DATOS
- **DB:** luiggi_home
- **Productos MV:** 383 (precios T1 correctos)
- **Materiales:** 7 (4 ZC, 3 MV)
