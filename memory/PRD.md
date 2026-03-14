# LUIGGI HOME - Kitchen Budgeting ERP/CRM

## Estado del Proyecto: EN DESARROLLO ACTIVO

## Problema Original
Replicar una aplicación de presupuestos de cocina ERP/CRM llamada LUIGGI HOME con múltiples módulos, sistemas de precios y gestión de usuarios.

## Última Actualización: 14 Marzo 2026

---

## ✅ COMPLETADO EN ESTA SESIÓN (14 Marzo 2026)

### Sistema de Valor de Punto por Biblioteca
- ✅ **UI de configuración**: Sección "VALOR DE PUNTO POR TARIFA (MONTADA)" en MÁRGENES
- ✅ **Campos separados**: MV (€/punto) y ZC (€/punto) configurables independientemente
- ✅ **Backend**: Endpoint PUT `/api/libraries/{code}` actualiza `pointValue` por biblioteca
- ✅ **Frontend**: `BudgetTable.jsx` usa `libraryPointValues[currentLibrary]` para cálculos
- ✅ **App.js**: Carga `librariesAPI.getAll()` al iniciar y construye `libraryPointValues`

### Mejora de Datos MV
- ✅ **256 productos MV** con precios completos T1-T21
- ✅ **Fondo estándar BAJO**: 58cm
- ✅ **Fondo estándar ALTO**: 33cm  
- ✅ **Altura estándar**: 70cm (bajos y altos), 220cm (columnas)
- ✅ **Multiplicadores de tarifa**: T1=1.0 hasta T21=2.20 (~6% incremento por tarifa)

### Sistema Multi-Biblioteca (ZC / MV) - Sesión Anterior
- ✅ Backend API de Bibliotecas (`/api/libraries`) - CRUD completo
- ✅ Modelo de datos con `library` en productos, `allowedLibraries` en usuarios
- ✅ Biblioteca ZC - 7,045 productos con sistema de ZONAS (Z1-Z12)
- ✅ Biblioteca MV - 256 productos con sistema de TARIFAS (T1-T21)
- ✅ Gestión de permisos en Panel MASTER
- ✅ Selectores "TARIFA ACTIVA" y "TARIFA DE PRECIOS" en BudgetTable

---

## 🔴 PENDIENTE / BUGS CONOCIDOS

### P0 - CRÍTICO (PAUSADO POR USUARIO)
1. **Bug cálculo presupuesto despiece** - Items de despiece no se suman al total

### P2 - MEJORAS
2. **Glitch visual barra lateral colapsada** - Recurrente
3. **Exportación catálogo (Excel/PDF)** - Verificar formato

### P3 - BLOQUEADOS
4. **Flujo registro email** - Requiere verificación de dominio en Resend

---

## ARQUITECTURA

### Backend (FastAPI)
```
/app/backend/
├── server.py                    # Servidor principal
├── models/schemas.py            # Modelos Pydantic
├── routes/
│   ├── libraries.py             # API de bibliotecas con pointValue
│   ├── despiece_budgeter.py     # API de despiece
│   └── ...
├── mv_products_v2.py            # Datos MV con precios T1 y multiplicadores
└── import_mv_from_images.py     # Script OCR (referencia)
```

### Frontend (React)
```
/app/frontend/src/
├── App.js                       # Carga bibliotecas y libraryPointValues
├── components/
│   ├── BudgetTable.jsx          # Cálculo con pointValue por biblioteca
│   └── SettingsModal.jsx        # UI de márgenes por biblioteca
└── services/
    └── api.js                   # librariesAPI.update para pointValue
```

### Base de Datos (MongoDB: test_database)
```
Colecciones:
- products          # library: ZC/MV, tariffPrices/zonePoints, fondo, height
- libraries         # code, pointValue, pricingSystem, priceLevels
- users             # allowedLibraries: []
```

---

## BIBLIOTECAS/TARIFAS

| Código | Sistema Precios | Productos | Fondo Bajo | Fondo Alto | pointValue |
|--------|-----------------|-----------|------------|------------|------------|
| ZC | ZONAS (Z1-Z12) | 7,045 | 60cm | 35cm | 1.0€ |
| MV | TARIFAS (T1-T21) | 256 | 58cm | 33cm | 1.0€ |

---

## CREDENCIALES TEST
- **Usuario**: MARIO
- **Password**: MARIO
- **Rol**: Admin / Director Comercial
- **Bibliotecas**: ZC, MV

---

## PRÓXIMOS PASOS

1. **P0 (Pausado)**: Corregir bug total presupuesto despiece - cuando usuario lo indique
2. **P2**: Corregir glitch visual del sidebar colapsado
3. **P2**: Verificar formato de exportación de catálogo
4. **Refactorización**: BudgetTable.jsx (~2990 líneas) y SettingsModal.jsx (~4400 líneas)

---

## INTEGRACIONES

- **Resend**: Email (requiere verificación de dominio)
- **Google Gemini**: Via emergentintegrations (IA Lab)
- **apscheduler**: Backups automáticos
- **openpyxl/xlsxwriter**: Procesamiento Excel

---

## NOTAS TÉCNICAS

### Sistema de Precios MV
- **Bajos**: Fondo fijo 58cm, precio fijo independiente de altura
- **Altos**: Fondo fijo 33cm
  - Columna "70": Precios para alturas 10-70cm
  - Columna "90": Precios para alturas 71-90cm
- **Multiplicadores**: T1=1.0, T2=1.06, ..., T21=2.20 (incremento ~6% por tarifa)

### Flujo de Cálculo de Precio
1. Usuario selecciona biblioteca (TARIFA ACTIVA)
2. Usuario selecciona nivel de precio (TARIFA DE PRECIOS: T1-T21 o Z1-Z12)
3. Sistema obtiene puntos del producto según tarifa seleccionada
4. Precio = puntos × libraryPointValues[biblioteca] + extras
