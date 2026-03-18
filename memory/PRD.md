# LUIGGI HOME - Kitchen Budgeting ERP/CRM

## Estado: EN DESARROLLO ACTIVO
## Última Actualización: 18 Marzo 2026

---

## ✅ COMPLETADO EN ESTA SESIÓN (18 Marzo 2026)

### 1. Cálculo de Puertas en Despiece
- **Implementado**: Detección automática de puertas (2P, 1P, D/I) en productos
- **Backend**: `/app/backend/server.py` líneas 4235-4315
- **Lógica**:
  - Detecta "2P" → 2 puertas
  - Detecta "1P" → 1 puerta
  - Detecta "D/I" → 1 puerta
  - Muebles sin especificar: 1 puerta si ancho ≤45cm, 2 si >45cm
- **Cálculo de dimensiones**:
  - Alto puerta = Alto mueble - tolerancias
  - Ancho puerta = (Ancho mueble / nº puertas) - tolerancias

### 2. Portal de Fábrica (NUEVO MÓDULO)
- **Backend**: `/app/backend/routes/fabrica.py` (nuevo archivo completo)
- **Frontend**: `/app/frontend/src/components/PortalFabrica.jsx` (nuevo)
- **API**: `/app/frontend/src/services/api.js` → `fabricaAPI`

#### Funcionalidades del Portal de Fábrica:
1. **Dashboard de Estadísticas**:
   - Órdenes activas, en producción, listas
   - Entregas esta semana
   - Piezas en producción

2. **CRUD de Órdenes de Fabricación**:
   - Crear orden manual
   - Listar con filtros (estado, prioridad, búsqueda)
   - Actualizar orden
   - Eliminar orden

3. **Gestión de Estados**:
   - draft → confirmed → in_production → ready → delivered
   - Estado "cancelled" disponible

4. **Fechas de Entrega**:
   - Establecer fecha estimada
   - Notas de entrega

5. **Importación (MOCKED)**:
   - Botón "Importar PDF" - placeholder para IA
   - Importar desde presupuesto existente

### 3. Nuevos Roles de Usuario
- `isFabrica`: Rol de usuario de fábrica
- `canAccessFabrica`: Permiso de acceso al portal
- `canManageOrders`: Gestión de órdenes
- `canSetDeliveryDates`: Establecer plazos de entrega

---

## 📋 PENDIENTE

### P0 - Crítico
- [ ] Implementar importación de PDF con IA (actualmente MOCKED)
- [ ] Implementar optimización de tableros (bin-packing 2D)

### P1 - Alta
- [ ] Implementar permisos específicos para Despiece por usuario
- [ ] Completar lógica de tabs "Bandas y Traseras" y "Casco, Puerta y Herraje"

### P2 - Media
- [ ] Casco por defecto por sección/biblioteca
- [ ] Restaurar logo empresa (requiere que usuario lo re-suba)
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
│   ├── fabrica.py          # NUEVO - Portal de Fábrica
│   ├── ia_lab.py
│   ├── auth.py
│   ├── libraries.py
│   └── despiece_budgeter.py
├── models/schemas.py       # Incluye nuevos campos isFabrica, canAccessFabrica
└── services/
    ├── jwt_service.py
    └── audit_service.py

/app/frontend/src/
├── App.js                  # Integra PortalFabrica
├── components/
│   ├── PortalFabrica.jsx   # NUEVO - Portal completo
│   ├── DespieceModal.jsx   # Modal con puertas calculadas
│   ├── BudgetTable.jsx
│   └── ...
└── services/api.js         # Incluye fabricaAPI
```

---

## CREDENCIALES
- **Usuario:** MARIO
- **Contraseña:** MARIO

## BASE DE DATOS
- **DB:** luiggi_home
- **Colecciones nuevas:**
  - `manufacturing_orders` - Órdenes de fabricación
  - `counters` - Incluye contadores para OF-YYYY-NNNN

---

## APIs NUEVAS

### Portal de Fábrica
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/fabrica/orders` | Listar órdenes (filtros: status, priority, search) |
| POST | `/api/fabrica/orders` | Crear orden |
| GET | `/api/fabrica/orders/{id}` | Obtener orden |
| PUT | `/api/fabrica/orders/{id}` | Actualizar orden |
| DELETE | `/api/fabrica/orders/{id}` | Eliminar orden |
| PATCH | `/api/fabrica/orders/{id}/status` | Cambiar estado |
| PATCH | `/api/fabrica/orders/{id}/delivery-date` | Establecer fecha |
| GET | `/api/fabrica/dashboard/stats` | Estadísticas |
| POST | `/api/fabrica/import-pdf` | Importar PDF (MOCKED) |
| POST | `/api/fabrica/import-from-budget/{id}` | Importar desde presupuesto |

---

## 3RD PARTY INTEGRATIONS
- `xlsxwriter`: Excel exports
- `pymongo/motor`: MongoDB async
- `jspdf` + `html2canvas`: PDF export (cliente)
- `sendgrid/resend`: Email
- `emergentintegrations`: Gemini Vision

---

## NOTAS DE TESTING
- **Test Report**: `/app/test_reports/iteration_26.json`
- **Backend Tests**: 17/17 PASSED
- **Frontend Tests**: 100% elementos verificados
- **APIs MOCKED**:
  - `POST /api/fabrica/import-pdf` - Placeholder para IA
  - `GET /api/fabrica/orders/{id}/despiece` - Parcialmente funcional

---

## PRÓXIMOS PASOS RECOMENDADOS
1. Implementar importación de PDF con Gemini Vision
2. Crear vista específica para usuarios de fábrica (rol `isFabrica`)
3. Implementar optimización de tableros (OpenCutList style)
4. Agregar notificaciones de estado de órdenes
