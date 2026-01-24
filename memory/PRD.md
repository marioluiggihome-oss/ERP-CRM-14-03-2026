# LUIGGI HOME - ERP/CRM para Presupuestos de Cocinas

## Descripción del Producto
Sistema ERP/CRM completo para la gestión de presupuestos de cocinas industriales.

## Estado de Correcciones (POR CORREGIR.docx) - 24/01/2026

### ✅ COMPLETADO (14/19 tareas)

| # | Corrección | Estado |
|---|------------|--------|
| 1 | **Prompt IA mejorado** (alturas 110cm, 220cm) | ✅ HECHO |
| 2 | **Producto faltante 35A1P350** añadido | ✅ HECHO |
| 3 | **Logo más grande** en Digitalizador | ✅ HECHO |
| 4 | **"BUDGET SYSTEM" → "PRESUPUESTO TÉCNICO"** | ✅ HECHO |
| 5 | **Campo REF (AUTO) editable** | ✅ HECHO |
| 6 | **Casilla descuento más ancha** y editable | ✅ HECHO |
| 7 | **Decimales con punto y coma** | ✅ HECHO |
| 8 | **Despiece: cliente, referencia, fecha, expediente** | ✅ HECHO |
| 9 | **Historial persistente** (guardado en BD) | ✅ HECHO |
| 10 | **Búsqueda en historial** por proyecto/cliente | ✅ HECHO |
| 11 | **Modo Mantenimiento** | ✅ HECHO |
| 12 | **Backup Pre-Actualización automático** | ✅ HECHO |
| 13 | **Panel de control para Admin** | ✅ HECHO |
| 14 | **Pantalla de "Sistema en actualización"** | ✅ HECHO |

### 🔄 PENDIENTE (5/19 tareas)

| # | Tarea | Prioridad |
|---|-------|-----------|
| 15 | Incremento por corte viga | Media |
| 16 | Contador correlativo de expedientes | Media |
| 17 | Conexión Digitalizador → CRM | Baja |
| 18 | Gestión armazones en pestaña separada | Baja |
| 19 | Admin ver todos los trabajos | Baja |

## Sistema de Mantenimiento (NUEVO)

### Funcionalidades:
1. **Panel de Mantenimiento** (solo Admin)
   - Activar/desactivar modo mantenimiento
   - Mensaje personalizable para usuarios
   - Tiempo estimado configurable
   - Opción de backup automático

2. **Backup Pre-Actualización**
   - Se crea automáticamente al activar mantenimiento
   - Guarda: usuarios, productos, proyectos, contactos, oportunidades, etc.
   - Descargable en formato JSON
   - Histórico de todos los backups

3. **Pantalla de Mantenimiento**
   - Solo para usuarios NO admin
   - Muestra mensaje, tiempo estimado
   - Indica si hay backup de seguridad
   - Se actualiza automáticamente cada 30s

### APIs de Mantenimiento:
- `GET /api/maintenance/status` - Estado actual
- `POST /api/maintenance/activate` - Activar (con backup opcional)
- `POST /api/maintenance/deactivate` - Desactivar
- `GET /api/maintenance/backups` - Lista de backups
- `GET /api/maintenance/backups/{id}/download` - Descargar backup

## Credenciales de Prueba
- Usuario: MARIO
- Contraseña: MARIO

## Productos en Base de Datos
- Total: **3,534 productos**

## Colecciones en MongoDB:
- users
- products
- projects
- materials
- settings
- contacts
- opportunities
- activities
- catalogs
- digitalizador_history
- system_settings (modo mantenimiento)
- system_backups (backups pre-actualización)
