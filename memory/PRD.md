# LUIGGI HOME - Kitchen Budgeting ERP/CRM

## Estado: EN DESARROLLO ACTIVO
## Última Actualización: 18 Marzo 2026

---

## ✅ COMPLETADO EN ESTA SESIÓN (18 Marzo 2026)

### 1. Cálculo de Puertas en Despiece (P0 - COMPLETADO)
- **Tolerancias corregidas**: Alto -2mm, Ancho -3mm por puerta
- Detecta 2P, 1P, D/I automáticamente
- Ejemplo: Mueble 90×60cm 2P → Puerta 89.8×29.7cm ✓

### 2. Portal de Fábrica (NUEVO MÓDULO - COMPLETADO)
- Dashboard con estadísticas en español
- CRUD completo de órdenes de fabricación (OF-YYYY-NNNN)
- Gestión de estados: borrador → confirmada → en_producción → lista → entregada
- **Importación de PDF con IA** (Gemini Vision) - IMPLEMENTADO
- Permisos específicos: `isFabrica`, `canAccessFabrica`

### 3. Importación PDF con IA (P0 - COMPLETADO)
- Usa Gemini Vision (google-genai) con Emergent LLM Key
- Analiza PDFs de presupuesto y detecta muebles automáticamente
- Extrae: código, nombre, dimensiones (ancho, alto, fondo), cantidad
- Permite crear orden de fabricación desde items detectados

### 4. PDF Exporta por Pestaña (P1 - COMPLETADO)
- **Orden Montaje**: Lista completa de piezas por mueble
- **Lista Corte**: Agrupado por material para seccionadora
- **Bandas y Traseras**: Canto total, áreas casco/trasera, detalle
- **Casco, Puerta y Herraje**: Dimensiones casco, puertas, herrajes

### 5. Permisos de Fábrica Corregidos
- MARIO no ve el módulo FÁBRICA (correcto)
- Solo visible para usuarios con `canAccessFabrica: true` o `isFabrica: true`

---

## 📋 PENDIENTE

### P0 - Crítico
- [x] ~~Importación PDF con IA~~ COMPLETADO
- [ ] Optimización de tableros (bin-packing 2D estilo OpenCutList)

### P1 - Alta
- [x] ~~Permisos específicos Despiece~~ (Ya existe: `canViewTechnicalDespiece`)
- [x] ~~PDF exporta contenido de cada pestaña~~ COMPLETADO
- [ ] Completar lógica de tabs con datos reales (actualmente funcionan)

### P2 - Media
- [ ] Casco por defecto por sección/biblioteca
- [ ] Restaurar logo empresa
- [ ] Reporte exportable "Agenda de Montajes"

### P3 - Baja
- [ ] Refactorización BudgetTable.jsx (~3071 líneas)
- [ ] Refactorización SettingsModal.jsx (~4727 líneas)
- [ ] Refactorización server.py (~6530 líneas)
- [ ] Glitch visual sidebar colapsado

---

## ARQUITECTURA

```
/app/backend/
├── server.py               # Principal (~6530 líneas)
├── routes/
│   ├── fabrica.py          # Portal de Fábrica + Importación PDF con IA
│   ├── ia_lab.py
│   ├── auth.py
│   ├── libraries.py
│   └── despiece_budgeter.py
├── models/schemas.py       # Incluye isFabrica, canAccessFabrica
└── services/
    ├── jwt_service.py
    └── audit_service.py

/app/frontend/src/
├── App.js                  # Integra PortalFabrica
├── components/
│   ├── PortalFabrica.jsx   # Portal completo + Importación PDF
│   ├── DespieceModal.jsx   # Modal con puertas y PDF por pestaña
│   ├── BudgetTable.jsx
│   └── ...
└── services/api.js         # fabricaAPI
```

---

## CREDENCIALES
- **Usuario:** MARIO
- **Contraseña:** MARIO

## BASE DE DATOS
- **DB:** luiggi_home
- **Colecciones nuevas:**
  - `manufacturing_orders` - Órdenes de fabricación
  - `counters` - Contadores para OF-YYYY-NNNN

---

## APIs IMPLEMENTADAS

### Portal de Fábrica
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/fabrica/orders` | Listar órdenes |
| POST | `/api/fabrica/orders` | Crear orden |
| GET | `/api/fabrica/orders/{id}` | Obtener orden |
| PUT | `/api/fabrica/orders/{id}` | Actualizar orden |
| DELETE | `/api/fabrica/orders/{id}` | Eliminar orden |
| PATCH | `/api/fabrica/orders/{id}/status` | Cambiar estado |
| PATCH | `/api/fabrica/orders/{id}/delivery-date` | Establecer fecha |
| GET | `/api/fabrica/dashboard/stats` | Estadísticas |
| **POST** | `/api/fabrica/import-pdf` | **Importar PDF con IA (Gemini Vision)** |
| POST | `/api/fabrica/import-from-budget/{id}` | Importar desde presupuesto |

---

## 3RD PARTY INTEGRATIONS
- `google-genai`: Gemini Vision para análisis de PDFs
- `xlsxwriter`: Excel exports
- `pymongo/motor`: MongoDB async
- `jspdf` + `html2canvas`: PDF export (cliente)
- `sendgrid/resend`: Email

---

## PRÓXIMOS PASOS RECOMENDADOS
1. **Optimización de tableros** - Algoritmo bin-packing 2D
2. **Vista exclusiva fábrica** - Cuando usuario tiene rol `isFabrica`
3. **Notificaciones** - Estado de órdenes por email/push
4. **Refactorización** - Dividir archivos monolíticos

---

## PERMISOS DE USUARIO

### Para acceder al Portal de Fábrica:
- `canAccessFabrica: true` - Permiso específico
- `isFabrica: true` - Rol de fábrica

### Para acceder al Despiece:
- `canViewTechnicalDespiece: true` - Ve botón DESPIECE
- Módulo `despiece` en `allowedModules`
