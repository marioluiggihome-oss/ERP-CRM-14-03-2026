# LUIGGI HOME - Kitchen Budgeting ERP/CRM

## Estado: EN DESARROLLO ACTIVO
## Última Actualización: 18 Marzo 2026

---

## ✅ COMPLETADO EN ESTA SESIÓN (18 Marzo 2026)

### 1. Sistema de Ayuda con Manual PDF por Rol
- **Nuevo componente**: `UserManualModal.jsx`
- Botón "AYUDA" visible en el sidebar para todos los usuarios
- Manual filtrado por rol del usuario (Admin ve todas las secciones)
- Secciones: Introducción, Presupuestos, CRM, Portal de Fábrica, Despiece, Administración, Glosario
- Descarga PDF personalizada por rol
- Búsqueda dentro del manual

### 2. Optimizador de Tableros (estilo OpenCutList)
- **Nuevo componente**: `BoardOptimizer.jsx`
- Algoritmo de bin-packing 2D personalizado (FFDH - First Fit Decreasing Height)
- Integrado en el modal de Despiece (botón "Optimizar Tableros")
- Tamaños de tablero estándar: 2440x1220, 2440x1830, 2750x1830, 3050x1525 mm
- Kerf configurable: 0mm, 3mm, 4mm, 5mm
- Visualización gráfica con colores distintivos por pieza
- Estadísticas: tableros necesarios, eficiencia %, m² usados/desperdicio
- Exportación PDF con diagramas y lista de piezas

### 3. Actualizaciones al Manual de Usuario
- `/app/docs/MANUAL_USUARIO.md` actualizado con nueva sección de Optimizador
- Contenido del modal de ayuda actualizado

### 4. Funcionalidades Previas
- Permiso "Acceso Portal Fábrica" en Capacidades Técnicas
- Portal de Fábrica con barra de progreso (Rojo/Azul/Verde)
- Importación PDF con IA (Gemini Vision)
- Tolerancias de puertas corregidas (-2mm alto, -3mm ancho)

---

## 📋 PENDIENTE

### P0 - Crítico
- [x] ~~Optimización de tableros (bin-packing 2D estilo OpenCutList)~~ COMPLETADO
- [x] ~~Sistema de Ayuda/Manual por rol~~ COMPLETADO

### P1 - Alta
- [x] ~~Permisos específicos Portal Fábrica~~ COMPLETADO
- [x] ~~Importar desde pedidos existentes~~ COMPLETADO
- [x] ~~Barra de progreso fabricación~~ COMPLETADO
- [ ] Verificar issue precio "COST" (17 vs 16) - posible caché del navegador

### P2 - Media
- [ ] Casco por defecto por sección/biblioteca
- [ ] Restaurar logo empresa
- [ ] Reporte exportable "Agenda de Montajes"
- [ ] Funcionalidad de impresión específica para usuarios de fábrica

### P3 - Baja
- [ ] Refactorización BudgetTable.jsx (~3071 líneas)
- [ ] Refactorización SettingsModal.jsx (~4727 líneas)
- [ ] Refactorización server.py (~6530 líneas)
- [ ] Glitch visual sidebar colapsado (recurrente)

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
