# LUIGGI HOME - Kitchen Budgeting ERP/CRM

## Estado: EN DESARROLLO ACTIVO
## Última Actualización: 16 Marzo 2026

---

## ✅ COMPLETADO EN ESTA SESIÓN (16 Marzo 2026)

### Catálogo MV TARIFA 1 - COMPLETO (611 productos)

#### Páginas 1-5 (538 productos):
- **PUERTAS:** 50 productos (P25-P60, alturas 14-147)
- **VITRINA:** 36 productos (PV30-PV60)
- **REJILLA CONFESIONARIO:** 24 productos (PR30-PR60)
- **BAJOS:** 22 productos (B25-B100, H70/H80)
- **BAJO FREGADERO:** 32 productos
- **BAJO RINCON:** 14 productos
- **BAJO HORNO:** 8 productos
- **BAJO TERMINAL:** 6 productos
- **BAJO 2/3 CAJONES:** 56 productos
- **ALTOS:** 22 productos (H70/H90)
- **ALTO CAMPANA, RINCON, DECORATIVO, TERMINAL, etc.**
- **COLUMNAS:** DESPENSERO, FRIGO, HORNO (36 productos)
- **SOBREENCIMERA:** 28 productos
- **ALTILLOS:** 29 productos
- **BOTELLEROS:** 3 productos

#### Página 6 (73 productos nuevos):
- **LATERALES COLOR:** 12 productos (Ancho 15)
- **REGLETA COLOR:** 8 productos (Ancho 15)
- **COSTADOS MELAMINA:** 6 productos (Ancho 10)
- **COSTADOS COLOR:** 8 productos (Ancho 10)
- **REGLETA MELAMINA:** 6 productos (Ancho 10)
- **TECHO COLOR:** 14 productos (TEC100-TEC360)
- **ELEMENTOS LINEALES:** 19 productos (COR, POR, ZOC, etc.)

### Precios Verificados:
- B25 = **40 PTS** ✓ (confirmado por usuario)
- B30 = **41 PTS** ✓ (confirmado por usuario)
- B100 = **64 PTS** ✓ (corregido por usuario)
- A100 H70 = **62 PTS** ✓
- A100 H90 = **70 PTS** ✓

### UI Verificada:
- ✅ Las categorías NO muestran "MV" (UI limpia)
- ✅ Las series están limpias
- ✅ Los precios se visualizan correctamente

---

## 📋 PENDIENTE

### P2 - Media
- [ ] Casco por defecto por sección/biblioteca
- [ ] Restaurar logo empresa (requiere que usuario lo re-suba)
- [ ] Reporte exportable "Agenda de Montajes"

### P3 - Baja
- [ ] Refactorización BudgetTable.jsx (~3071 líneas)
- [ ] Refactorización SettingsModal.jsx (~4727 líneas)
- [ ] Refactorización server.py (~6470 líneas)
- [ ] Glitch visual sidebar colapsado
- [ ] Bug "Despiece" (PAUSADO por usuario)

---

## ARQUITECTURA

```
/app/backend/
├── server.py
├── routes/ia_lab.py
├── models/schemas.py
└── scripts/
    ├── seed_mv_products.py         # Script original
    ├── update_mv_prices_tarifa1.py # Actualización precios p1-5
    └── add_mv_page6_products.py    # Productos página 6

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
- **Productos MV:** 611 (TARIFA 1 completa, 6 páginas)
- **Productos ZC:** 4542
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

### Categorías con Dimensiones Específicas (Página 6):
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

---

## 3RD PARTY INTEGRATIONS
- `xlsxwriter`: Excel exports
- `pymongo`: MongoDB
- `sendgrid/resend`: Email

---

## SCRIPTS DE MANTENIMIENTO

### Actualizar precios TARIFA 1 (Páginas 1-5):
```bash
cd /app/backend && python3 scripts/update_mv_prices_tarifa1.py
```

### Añadir productos Página 6:
```bash
cd /app/backend && python3 scripts/add_mv_page6_products.py
```
