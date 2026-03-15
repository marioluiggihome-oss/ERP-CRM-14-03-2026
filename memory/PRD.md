# LUIGGI HOME - Kitchen Budgeting ERP/CRM

## Estado del Proyecto: EN DESARROLLO ACTIVO
## Última Actualización: 15 Marzo 2026

---

## ✅ COMPLETADO EN ESTA SESIÓN (15 Marzo 2026)

### 1. Precios MV Tarifa 1 - COMPLETADOS AL 100%
- ✅ **383 productos MV** actualizados con precios T1 correctos
- ✅ Todas las categorías cubiertas:
  - BAJOS (B25-B100, BF, BH, BC, BG, BPC, etc.)
  - ALTOS H70 y H90 (A25-A100, AD, AV, AE, etc.)
  - COLUMNAS (CH, CHM, CD, CE, CF)
  - MEDIACOLUMNAS (M, MH, MM, MCV)
  - SOBREENCIMERAS (S, SC, SV, SVC)
  - ALTILLOS (L, LV, LD)

### 2. Analizador de Planos IA - Filtro por Biblioteca
- ✅ **Frontend modificado**: Envía biblioteca activa al backend
- ✅ **Backend modificado**: Filtra búsqueda de productos por biblioteca (ZC/MV)
- ✅ **Indicador visual**: Muestra "CATÁLOGO: ZC" o "CATÁLOGO: MV" en la UI
- ✅ Archivos modificados:
  - `/app/frontend/src/components/Visualizer.jsx`
  - `/app/backend/routes/ia_lab.py`

---

## PRECIOS TARIFA 1 (MV) - MUESTRA

### BAJOS
| Código | T1 | Código | T1 |
|--------|-----|--------|-----|
| B25D/I | 58 | B60 | 60 |
| B30D/I | 62 | B70 | 70 |
| B40D/I | 64 | B80 | 80 |
| B50D/I | 68 | B100 | 100 |
| BF60D/I | 72 | BH60 | 77 |

### ALTOS (H70 / H90)
| Código | H70 | H90 |
|--------|-----|-----|
| A25 | 35 | 38 |
| A30 | 38 | 42 |
| A40 | 42 | 46 |
| A60 | 56 | 61 |
| A100 | 75 | 82 |

### COLUMNAS
| Código | T1 |
|--------|-----|
| CH60D/I/200 | 97 |
| CHM60D/I/200 | 136 |
| CD30D/I/200 | 65 |
| CF60D/I/200 | 152 |

---

## 📋 PENDIENTE

### P1 - Prioridad Alta
- [ ] Implementar casco por defecto por sección/biblioteca
- [ ] Restaurar logo de empresa (requiere re-subida por usuario)

### P2 - Media
- [ ] Refactorización de BudgetTable.jsx (3071 líneas)
- [ ] Bug cálculo "Despiece" (PAUSADO)

### P3 - Baja
- [ ] Refactorización de SettingsModal.jsx (4685 líneas)
- [ ] Refactorización de server.py (6470 líneas)
- [ ] Glitch visual sidebar colapsado

---

## ARQUITECTURA DE ARCHIVOS

```
/app/backend/
├── server.py           # API principal (~6470 líneas)
├── routes/
│   └── ia_lab.py       # MODIFICADO: Análisis de planos con filtro biblioteca
└── models/schemas.py   # Modelos Pydantic

/app/frontend/src/
├── App.js              # Estado global, routing
├── components/
│   ├── BudgetTable.jsx     # Presupuesto principal
│   ├── Visualizer.jsx      # MODIFICADO: Analizador planos con biblioteca
│   ├── Digitalizador.jsx   # Ya tiene filtro biblioteca
│   ├── SettingsModal.jsx   # Panel admin
│   └── AgendaMontajes.jsx  # Agenda instaladores
└── services/api.js     # Llamadas API
```

---

## CREDENCIALES DE PRUEBA
- **Usuario:** MARIO
- **Contraseña:** MARIO

## BASE DE DATOS
- **DB:** luiggi_home
- **Productos ZC:** 4542
- **Productos MV:** 383 (todos con precios T1)
