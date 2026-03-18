# LUIGGI HOME - Kitchen Budgeting ERP/CRM

## Estado: EN DESARROLLO ACTIVO
## Última Actualización: 18 Marzo 2026

---

## ✅ COMPLETADO EN ESTA SESIÓN (18 Marzo 2026)

### 1. Sistema de Ayuda con Manual PDF por Rol
- **Componente**: `UserManualModal.jsx`
- Botón "AYUDA" en sidebar, manual filtrado por rol, descarga PDF

### 2. Optimizador de Tableros con Vista Interactiva
- **Componente**: `BoardOptimizer.jsx`
- Algoritmo bin-packing 2D (FFDH)
- **NUEVO**: Drag & drop para mover piezas manualmente
- **NUEVO**: Exportación CSV para Seccionadora
- **NUEVO**: Exportación CSV CNC con posiciones X,Y
- Visualización de múltiples tableros con navegación
- Doble clic para rotar piezas

### 3. Despiece de Puertas
- Sección "🚪 DESPIECE DE PUERTAS" en pestaña CASCO, PUERTA Y HERRAJE
- Tolerancias: -2mm alto, -3mm ancho

### 4. Sistema Multi-Fábrica
- Fábricas: SALAMANCA (SAL) y ZAMORA (ZAM)
- CRUD completo: `/api/fabrica/factories`
- **NUEVO**: Selector de fábrica en formulario de usuario

### 5. Dashboard Gráfico de Producción
- **Componente**: `ProductionDashboard.jsx`
- Métricas en tiempo real: Órdenes Activas, En Producción, Listas, Entregadas, Retrasadas
- Gráfica donut "Órdenes por Estado"
- Gráfica barras "Órdenes por Fábrica" (SAL, ZAM, Sin asignar)
- Gráfica tendencia "Últimos 7 días"
- Barra de progreso global de fabricación
- Filtros: por fábrica, por período

### 6. Historial de Cambios y Trazabilidad
- **Componente**: `OrderHistory.jsx`
- Timeline agrupado por fecha
- Tipos de evento: Orden Creada, Cambio Estado, Mueble Fabricado
- Estadísticas: Total eventos, Cambios estado, Muebles fabricados
- Filtros: búsqueda, tipo de cambio, orden específica
- Entradas expandibles con detalles

### 7. Filtrado de Órdenes por Fábrica
- Usuarios con `factoryId` solo ven sus órdenes
- Gerente, Director Comercial, Responsable Delegación ven todas
- Badge de fábrica (SAL/ZAM) en lista de órdenes

### 8. Portal de Fábrica con Pestañas
- **Órdenes**: Lista de órdenes con filtros
- **Dashboard**: Métricas y gráficas de producción
- **Historial**: Timeline de cambios

---

## 📋 PENDIENTE

### P1 - Alta
- [x] ~~Despiece de puertas con tolerancias~~ COMPLETADO
- [x] ~~Dashboard gráfico de producción~~ COMPLETADO
- [x] ~~Historial y trazabilidad~~ COMPLETADO
- [x] ~~Filtrar órdenes por fábrica~~ COMPLETADO
- [ ] Verificar issue precio "COST" (17 vs 16)

### P2 - Media
- [ ] Casco por defecto por sección/biblioteca
- [ ] Restaurar logo empresa
- [ ] Notificaciones email cambios de estado

### P3 - Baja
- [ ] Refactorización monolitos (server.py, SettingsModal.jsx)
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
├── App.js                    # Botón de Ayuda en sidebar
├── components/
│   ├── UserManualModal.jsx   # NUEVO: Manual de ayuda por rol
│   ├── BoardOptimizer.jsx    # NUEVO: Optimización de tableros
│   ├── PortalFabrica.jsx     # Portal completo con progreso y categorías
│   ├── SettingsModal.jsx     # Incluye checkbox "Acceso Portal Fábrica"
│   ├── DespieceModal.jsx     # Integración con BoardOptimizer
│   └── ...
└── services/api.js           # fabricaAPI, projectsAPI
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
- SEMICOLUMNAS
- SOBREMÓDULOS
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
- `jspdf` + `html2canvas`: PDF export (frontend)

---

## PRÓXIMOS PASOS RECOMENDADOS
1. ~~**Optimización de tableros**~~ ✅ COMPLETADO
2. **Funcionalidad de impresión** - Para usuarios de fábrica
3. **Notificaciones** - Email cuando cambie estado de orden
4. **Dashboard gráfico** - Gráficas de producción
5. **Historial de cambios** - Trazabilidad de estados
