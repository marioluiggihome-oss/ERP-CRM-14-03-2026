# LUIGGI HOME - Kitchen Budgeting ERP/CRM

## Estado del Proyecto: EN DESARROLLO ACTIVO

## Problema Original
Replicar una aplicación de presupuestos de cocina ERP/CRM llamada LUIGGI HOME con múltiples módulos, sistemas de precios y gestión de usuarios.

## Última Actualización: 14 Marzo 2026

---

## ✅ COMPLETADO EN ESTA SESIÓN

### Sistema Multi-Biblioteca (ZC / MV)
- ✅ **Backend API de Bibliotecas** (`/api/libraries`) - CRUD completo
- ✅ **Modelo de datos actualizado** - Campo `library` en productos, `allowedLibraries` en usuarios
- ✅ **Biblioteca ZC** - 7,045 productos con sistema de ZONAS (Z1-Z12)
- ✅ **Biblioteca MV** - 656 productos extraídos de 134 imágenes JPG con sistema de TARIFAS (T1-T21)
- ✅ **384 productos MV con precios** distribuidos en las 21 tarifas
- ✅ **Gestión de permisos en UI** - Sección "Tarifas de Precios Activas" en panel de usuarios
- ✅ **Lista de usuarios muestra tarifas asignadas** - Columna "TARIFAS" en RED DISTRIBUCIÓN
- ✅ **Nombres cortos** - "ZC" y "MV" (sin nombres largos)

### Extracción de Catálogo MV
- ✅ Procesadas 134 imágenes JPG de la tarifa MV
- ✅ Datos de las 21 tarifas (T1-T21) extraídos
- ✅ Script de importación: `/app/backend/import_mv_from_images.py`

---

## 🔴 PENDIENTE / BUGS CONOCIDOS

### P0 - CRÍTICO
1. **Bug cálculo presupuesto despiece** - Items de despiece no se suman al total (BudgetTable.jsx línea ~748)

### P1 - IMPORTANTE
2. **Mejorar extracción precios MV** - OCR no captura bien tablas de precios del PDF escaneado
3. **Selector de biblioteca en presupuestador** - Permitir cambiar biblioteca activa al presupuestar

### P2 - MEJORAS
4. **Glitch visual barra lateral colapsada** - Recurrente
5. **Exportación catálogo (Excel/PDF)** - Verificar formato

### P3 - BLOQUEADOS
6. **Flujo registro email** - Requiere verificación de dominio en Resend

---

## ARQUITECTURA

### Backend (FastAPI)
```
/app/backend/
├── server.py                    # Servidor principal (~6000 líneas)
├── models/schemas.py            # Modelos Pydantic
├── routes/
│   ├── libraries.py             # NUEVO: API de bibliotecas
│   ├── despiece_budgeter.py     # API de despiece
│   ├── ia_lab.py                # IA Lab
│   ├── auth.py                  # Autenticación
│   └── ...
└── import_mv_catalog.py         # Script importación MV
```

### Frontend (React)
```
/app/frontend/src/
├── App.js                       # Componente principal
├── components/
│   ├── BudgetTable.jsx          # Presupuestador (~2930 líneas) - REFACTORIZAR
│   ├── SettingsModal.jsx        # Panel MASTER (~4400 líneas) - REFACTORIZAR
│   ├── LibrarySelector.jsx      # Selector de biblioteca (no usado actualmente)
│   └── budget/
│       └── DespieceStepByStep.jsx # Flujo despiece paso a paso
└── services/
    └── api.js                   # APIs (incluye librariesAPI)
```

### Base de Datos (MongoDB)
```
Colecciones:
- products          # Productos montada (library: ZC/MV)
- despiece_products # Productos despiece
- users             # Usuarios (allowedLibraries: [])
- libraries         # Definición de bibliotecas
- clients           # Clientes
- projects          # Proyectos
- backup_history    # Historial backups
```

---

## BIBLIOTECAS/TARIFAS

| Código | Nombre | Sistema Precios | Productos | Estado |
|--------|--------|-----------------|-----------|--------|
| ZC | Zona Cocinas | ZONAS (Z1-Z12) | 7,045 | ✅ Activa |
| MV | Muebles Valencia | TARIFAS (T1-T21) | 575 | ✅ Activa (precios parciales) |

---

## CREDENCIALES TEST
- **Usuario**: MARIO
- **Password**: MARIO
- **Rol**: Admin / Director Comercial
- **Bibliotecas**: ZC, MV

---

## PRÓXIMOS PASOS

1. **Corregir bug total presupuesto despiece** (P0)
2. **Añadir selector de biblioteca en presupuestador** para usuarios con múltiples tarifas
3. **Mejorar extracción MV** - Considerar Excel con precios limpios
4. **Refactorizar BudgetTable.jsx** - Dividir en componentes más pequeños

---

## INTEGRACIONES

- **Resend**: Email (requiere verificación de dominio)
- **Google Gemini**: Via emergentintegrations (IA Lab)
- **apscheduler**: Backups automáticos
- **openpyxl/xlsxwriter**: Procesamiento Excel
- **pdfplumber/pytesseract**: OCR de PDFs

---

## NOTAS TÉCNICAS

### Sistema de Precios
- **ZC**: `zonePoints: {Z1: 60, Z2: 62, ...Z12: 123}` - 12 niveles
- **MV**: `tariffPrices: {T1: 50, T2: 55, ...T21: 200}` - 21 niveles

### Flujo de Usuario
1. Admin asigna `allowedLibraries` a usuario en Panel MASTER
2. Usuario inicia sesión → se cargan productos de su primera biblioteca
3. Si tiene múltiples bibliotecas → puede cambiar (selector pendiente)
