# LUIGGI HOME - ERP/CRM para Presupuestos de Cocinas

## Estado de Correcciones - 24/01/2026

### ✅ COMPLETADO (16/19 tareas del documento POR CORREGIR.docx)

| # | Corrección | Estado |
|---|------------|--------|
| 1 | Prompt IA mejorado (alturas 110cm, 220cm) | ✅ |
| 2 | Producto faltante 35A1P350 añadido | ✅ |
| 3 | Logo más grande en Digitalizador | ✅ |
| 4 | "BUDGET SYSTEM" → "PRESUPUESTO TÉCNICO" | ✅ |
| 5 | Campo REF (AUTO) editable | ✅ |
| 6 | Casilla descuento más ancha y editable | ✅ |
| 7 | Decimales con punto y coma | ✅ |
| 8 | Despiece: cliente, referencia, fecha, expediente | ✅ |
| 9 | Historial persistente (guardado en BD) | ✅ |
| 10 | Búsqueda en historial | ✅ |
| 11 | Modo Mantenimiento | ✅ |
| 12 | Backup Pre-Actualización automático | ✅ |
| 13 | Panel de control para Admin | ✅ |
| 14 | Pantalla "Sistema en actualización" | ✅ |
| 15 | **INCREMENTO POR CORTE VIGA** | ✅ NUEVO |
| 16 | **CONTADOR CORRELATIVO EXPEDIENTES** | ✅ NUEVO |

### 🔄 PENDIENTE (3/19 tareas)

| # | Tarea | Prioridad |
|---|-------|-----------|
| 17 | Conexión Digitalizador → CRM | Baja |
| 18 | Gestión armazones en pestaña separada | Baja |
| 19 | Admin ver todos los trabajos | Baja |

## Nuevas Funcionalidades Implementadas

### 1. Incremento por Corte de Viga
- Campo configurable en el panel lateral: "INCREMENTO CORTE VIGA"
- Se puede especificar un valor en € que se añadirá al precio
- Cada línea del presupuesto tiene checkbox "V" para aplicar el incremento
- Se muestra etiqueta "VIGA" junto al precio cuando está activado
- El incremento se refleja en el desglose de precio

### 2. Contador Correlativo de Expedientes
- Formato: EXP-AAAA-NNNNN (ej: EXP-2026-00001)
- Botón "AUTO" naranja junto al campo de expediente
- Genera números únicos secuenciales para TODOS los usuarios
- Se reinicia cada año (2026, 2027, etc.)
- Guardado en colección `system_counters`

### APIs de Expedientes:
- `GET /api/expedient/next` - Obtener y reservar siguiente número
- `GET /api/expedient/current` - Info del contador actual

## Sistema de Mantenimiento

### Panel de Control (solo Admin):
- Activar/desactivar modo mantenimiento
- Mensaje personalizable
- Tiempo estimado configurable
- Backup automático antes de actualización

### Pantalla de Bloqueo (usuarios no-admin):
- Muestra mensaje de mantenimiento
- Tiempo estimado restante
- Indicador de backup de seguridad
- Se actualiza automáticamente cada 30s

## Credenciales
- **Usuario**: MARIO
- **Contraseña**: MARIO

## Base de Datos
- Total productos: **3,534**
- Colecciones principales: users, products, projects, contacts, opportunities, digitalizador_history, system_counters, system_backups, system_settings

## Menú Lateral (Admin)
1. CRM
2. PRESUPUESTO
3. IA LAB
4. ARCHIVO
5. DIGITALIZADOR
6. COPIA SEGURIDAD
7. **MANTENIMIENTO** (nuevo)
8. MASTER
9. SALIR
