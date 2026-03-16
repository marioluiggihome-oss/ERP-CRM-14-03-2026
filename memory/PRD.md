# LUIGGI HOME - Kitchen Budgeting ERP/CRM

## Estado: EN DESARROLLO ACTIVO
## Última Actualización: 16 Marzo 2026

---

## ✅ COMPLETADO EN ESTA SESIÓN

### 1. Catálogo MV TARIFA 1 - COMPLETO (452 productos)
- ✅ **PUERTAS (50 productos):** P25-P60 con alturas 14-147
- ✅ **VITRINA (36 productos):** PV30-PV60 con alturas 28-147
- ✅ **REJILLA CONFESIONARIO (24 productos):** PR30-PR60 con alturas 70-147
- ✅ **BAJOS (72 productos):** Todos los tipos incluyendo:
  - BAJO básico (B25D/I - B100)
  - BAJO FREGADERO, RINCON ESCUADRA, RINCON CIEGO
  - BAJO HORNO, TERMINAL
  - BAJO PUERTA Y CAJON, 2 CAJONES, 2 GAVETAS, 3 CAJONES
- ✅ **ALTOS (136 productos):** Incluyendo:
  - ALTO básico H70/H90
  - ALTO CAMPANA, DECORATIVO, TERMINAL
  - ALTO RINCON CIEGO, ESCUADRA, CHAFLAN
  - ALTO SOBREFRIGO, CALDERA, CALENTADOR
  - ALTO MICROONDAS, ESCURREPLATOS, VITRINA
  - ALTO ABATIBLE, COMBINADO PLUS
- ✅ **ALTILLOS (29 productos):** ALTILLO y ALTILLO VITRINA H70/H90
- ✅ **SOBREENCIMERA (34 productos):** Normal, CAJON, VITRINA, VITRINA CAJON
- ✅ **COLUMNAS (72 productos):** 
  - COLUMNA DESPENSERO H200/H220
  - COLUMNA FRIGO H200/H220
  - COLUMNA HORNO H200/H220
  - MEDIACOLUMNA, MEDIACOLUMNA HORNO
  - MEDIACOLUMNA VITRINA, MEDIACOL VITRINA GAVETA
  - MEDIA PUERTA GAVETA
- ✅ **OTROS (13 productos):** BOTELLEROS, ALTILLOS DECORATIVOS

### 2. Precios Verificados
- A100 H70 = **62 PTS** ✓
- A100 H90 = **70 PTS** ✓
- P30 H70 = **11 PTS** ✓
- PR60 H70 = **63 PTS** ✓
- B30D/I = **35 PTS** ✓

---

## 📋 PENDIENTE

### P1 - Alta
- [ ] Casco por defecto por sección/biblioteca
- [ ] **FALTA PÁGINA 6 DE TARIFA MV** - Usuario pendiente de subir

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
    └── seed_mv_products.py    # NUEVO: Script para poblar productos MV

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
- **Productos MV:** 452 (TARIFA 1 completa)
- **Productos ZC:** 2206
- **Materiales:** 7 (4 ZC, 3 MV)
- **Bibliotecas:** ZC (Zona Cocinas), MV (Muebles Valencia)

---

## NOTAS TÉCNICAS

### Estructura de Productos MV
Los productos MV usan el campo `library: "MV"` y almacenan precios en:
- `points`: Precio T1 (valor principal)
- `zonePoints.T1`: Precio Tarifa 1 (usado por el frontend)

### Script de Semilla
El script `/app/backend/scripts/seed_mv_products.py` puede ejecutarse para:
- Eliminar productos MV existentes
- Insertar todos los productos de TARIFA 1
- Comando: `MONGO_URL=mongodb://localhost:27017 DB_NAME=luiggi_home python3 scripts/seed_mv_products.py`
