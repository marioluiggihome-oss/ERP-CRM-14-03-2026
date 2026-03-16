# LUIGGI HOME - Kitchen Budgeting ERP/CRM

## Estado: EN DESARROLLO ACTIVO
## Última Actualización: 16 Marzo 2026

---

## ✅ COMPLETADO EN ESTA SESIÓN

### Catálogo MV TARIFA 1 - COMPLETO (524 productos)

#### Páginas 1-5 (452 productos originales):
- **PUERTAS:** 50 productos (P25-P60, alturas 14-147)
- **VITRINA:** 36 productos (PV30-PV60)
- **REJILLA CONFESIONARIO:** 24 productos (PR30-PR60)
- **BAJOS:** 72 productos (todos los tipos)
- **ALTOS:** 136 productos (H70/H90)
- **COLUMNAS:** 72 productos (H200/H220)
- **OTROS:** ALTILLOS, SOBREENCIMERA, BOTELLEROS, etc.

#### Página 6 (72 productos nuevos con anchos/fondos):
- **LATERALES COLOR:** 12 productos (Ancho 15)
- **REGLETA COLOR:** 8 productos (Ancho 15)
- **COSTADOS MELAMINA:** 6 productos (Ancho 10)
- **COSTADOS COLOR:** 10 productos (Ancho 10)
- **REGLETA MELAMINA:** 6 productos (Ancho 10)
- **TECHO COLOR:** 14 productos (TEC100-TEC360)
- **ELEMENTOS LINEALES:** 16 productos (COR, POR, ZOC, etc.)

### Precios Verificados:
- A100 H70 = **62 PTS** ✓
- A100 H90 = **70 PTS** ✓
- P30 H70 = **11 PTS** ✓
- PR60 H70 = **63 PTS** ✓
- LCA H70 = **10 PTS** (Ancho 15) ✓
- TEC200 = **20.4 PTS** (Ancho 200) ✓

---

## 📋 PENDIENTE

### P1 - Alta
- [ ] Casco por defecto por sección/biblioteca

### P2 - Media
- [ ] Restaurar logo empresa (requiere que usuario lo re-suba)
- [ ] Refactorización BudgetTable.jsx (~3071 líneas)
- [ ] Bug "Despiece" (PAUSADO por usuario)

### P3 - Baja
- [ ] Refactorización SettingsModal.jsx (~4727 líneas)
- [ ] Refactorización server.py (~6470 líneas)
- [ ] Glitch visual sidebar colapsado

---

## ARQUITECTURA

```
/app/backend/
├── server.py
├── routes/ia_lab.py
├── models/schemas.py
└── scripts/
    └── seed_mv_products.py    # Script para poblar productos MV

/app/frontend/src/
├── App.js
├── components/
│   ├── AgendaMontajes.jsx
│   ├── SettingsModal.jsx
│   ├── BudgetTable.jsx
│   └── ...
└── services/api.js
```

---

## CREDENCIALES
- **Usuario:** MARIO
- **Contraseña:** MARIO

## BASE DE DATOS
- **DB:** luiggi_home
- **Productos MV:** 524 (TARIFA 1 completa, 6 páginas)
- **Productos ZC:** 2206
- **Bibliotecas:** ZC (Zona Cocinas), MV (Muebles Valencia)

---

## NOTAS TÉCNICAS

### Estructura de Productos MV
Los productos MV tienen las siguientes características:
- `library: "MV"` - Identificador de biblioteca
- `points`: Precio T1 (valor principal)
- `zonePoints.T1`: Precio Tarifa 1 (usado por el frontend)
- `width`: Ancho del mueble en cm
- `height`: Alto del mueble en cm
- `depth`: Fondo del mueble en cm

### Categorías con Dimensiones Específicas:
- **LATERALES COLOR:** Ancho 15 cm
- **REGLETA COLOR:** Ancho 15 cm  
- **COSTADOS MELAMINA:** Ancho 10 cm
- **COSTADOS COLOR:** Ancho 10 cm
- **REGLETA MELAMINA:** Ancho 10 cm
- **TECHO COLOR:** Ancho variable (100-360 cm)

### Notas de Tarifa:
- SYNCRO = T1 + 5%
- ECO = T1
- MOTA = T1
- TEXTIL = T1
