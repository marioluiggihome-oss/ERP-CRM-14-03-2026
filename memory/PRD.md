# LUIGGI HOME - Kitchen Budgeting ERP/CRM

## Estado: EN DESARROLLO ACTIVO
## Última Actualización: 18 Marzo 2026

---

## ✅ COMPLETADO EN ESTA SESIÓN (18 Marzo 2026)

### 1. Permiso "Acceso Portal Fábrica" en Capacidades Técnicas
- Añadido checkbox en la sección de Capacidades Técnicas del formulario de usuario
- Campo `canAccessFabrica` en el modelo de usuario
- Badge "FÁBRICA" (verde) visible en la lista de usuarios

### 2. Portal de Fábrica Mejorado
- **Resumen por Categoría**: Altos, Bajos, Columnas, Especiales (con colores distintivos)
- **Barra de Progreso de Fabricación**:
  - ROJO: Sin empezar (0%)
  - AZUL: En proceso (parcialmente completado)
  - VERDE: Completado (100%)
- **Botones de Estado de Fabricación** por mueble:
  - 🔲 Pendiente (rojo)
  - ▶️ En proceso (azul)
  - ✓ Completado (verde)
- **Importar desde Pedidos Existentes**: Modal con lista de presupuestos guardados

### 3. Clasificación Automática de Muebles
- A* → Altos
- B* → Bajos
- CH*, CO* → Columnas
- Otros → Especiales

### 4. Tolerancias de Puertas Corregidas
- Alto: -2mm (0.2cm)
- Ancho: -3mm (0.3cm) por puerta

### 5. Importación PDF con IA (Gemini Vision)
- Analiza PDFs y detecta muebles automáticamente
- Extrae: código, nombre, dimensiones, cantidad
- Muestra resumen por categoría de items detectados

---

## 📋 PENDIENTE

### P0 - Crítico
- [ ] Optimización de tableros (bin-packing 2D estilo OpenCutList)

### P1 - Alta
- [x] ~~Permisos específicos Portal Fábrica~~ COMPLETADO
- [x] ~~Importar desde pedidos existentes~~ COMPLETADO
- [x] ~~Barra de progreso fabricación~~ COMPLETADO

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
│   ├── fabrica.py          # Portal de Fábrica + IA
│   ├── ia_lab.py
│   ├── auth.py
│   ├── libraries.py
│   └── despiece_budgeter.py
├── models/schemas.py       # isFabrica, canAccessFabrica, canManageOrders...
└── services/

/app/frontend/src/
├── App.js
├── components/
│   ├── PortalFabrica.jsx   # Portal completo con progreso y categorías
│   ├── SettingsModal.jsx   # Incluye checkbox "Acceso Portal Fábrica"
│   ├── DespieceModal.jsx
│   └── ...
└── services/api.js         # fabricaAPI, projectsAPI
```

---

## CREDENCIALES
- **Usuario:** MARIO
- **Contraseña:** MARIO
- **Permiso Fábrica:** Activado

---

## PERMISOS DE USUARIO

### Para acceder al Portal de Fábrica:
- `canAccessFabrica: true` - Permiso en Capacidades Técnicas
- `isFabrica: true` - Rol de fábrica dedicado

### Para acceder al Despiece:
- `canViewTechnicalDespiece: true`
- Módulo `despiece` en `allowedModules`

---

## FUNCIONALIDADES DEL PORTAL DE FÁBRICA

### Dashboard
- Órdenes activas
- En producción
- Listas para entrega
- Entregas esta semana
- Piezas en producción

### Órdenes de Fabricación
- Número automático: OF-YYYY-NNNN
- Estados: Borrador → Confirmada → En Producción → Lista → Entregada
- Prioridades: Baja, Normal, Alta, Urgente
- Fecha de entrega estimada

### Resumen por Categoría
- ALTOS (azul cielo)
- BAJOS (ámbar)
- COLUMNAS (violeta)
- ESPECIALES (rosa)

### Progreso de Fabricación
- Barra visual ROJO → AZUL → VERDE
- Contador X/Y muebles completados
- Estado individual por mueble (botones para marcar)

### Importación
1. **Importar Pedido**: Desde presupuestos existentes en BD
2. **Importar PDF**: Con IA (Gemini Vision) para detectar muebles

---

## 3RD PARTY INTEGRATIONS
- `google-genai`: Gemini Vision para PDFs
- `xlsxwriter`: Excel exports
- `pymongo/motor`: MongoDB async
- `jspdf` + `html2canvas`: PDF export

---

## PRÓXIMOS PASOS RECOMENDADOS
1. **Optimización de tableros** - Bin-packing 2D
2. **Notificaciones** - Email cuando cambie estado de orden
3. **Dashboard gráfico** - Gráficas de producción
4. **Historial de cambios** - Trazabilidad de estados
