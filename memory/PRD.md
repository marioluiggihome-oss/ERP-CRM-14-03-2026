# LUIGGI HOME - ERP/CRM para Presupuestos de Cocinas

## Descripción del Producto
Sistema ERP/CRM completo para la gestión de presupuestos de cocinas industriales.

## Estado de Correcciones (POR CORREGIR.docx) - 24/01/2026

### ✅ COMPLETADO

| # | Corrección | Estado |
|---|------------|--------|
| 1 | **Prompt mejorado para alturas** | ✅ HECHO - Contexto de medidas de muebles (70-220cm) |
| 2 | **Logo más grande** | ✅ HECHO - h-16 en lugar de h-12 |
| 3 | **Cambiar "BUDGET SYSTEM" → "PRESUPUESTO TÉCNICO"** | ✅ HECHO |
| 4 | **Campo REF (AUTO) editable** | ✅ HECHO - Ahora es input editable |
| 5 | **Casilla descuento más ancha** | ✅ HECHO - w-16 con fondo visible |
| 6 | **Descuento editable por línea (todas)** | ✅ HECHO - Todas las líneas editables |
| 7 | **Decimales con punto y coma** | ✅ HECHO - replace(',', '.') |
| 8 | **Despiece: campos cliente, ref, fecha, expediente** | ✅ HECHO - Barra de info editable |

### 🔄 PENDIENTE (Prioridad Baja)

| # | Tarea | Descripción |
|---|-------|-------------|
| 9 | Incremento por corte viga | Añadir campo y botón |
| 10 | Contador correlativo expedientes | Nº auto para todos los usuarios |
| 11 | Historial persistente digitalizador | Guardar en BD |
| 12 | Conexión Digitalizador → CRM | Crear oportunidad desde presupuesto digitalizado |
| 13 | Gestión armazones en pestaña separada | Mover fuera de Márgenes |
| 14 | Revisar artículos faltantes sin duplicar | Verificar catálogo |
| 15 | Admin ver todos los trabajos | Listados e informes |

## Características Implementadas ✅

### Core
- Autenticación con roles (Admin > Comercial > Tienda)
- Inventario con 3,533 productos
- Sistema de presupuestos
- Archivo de proyectos
- Exportación PDF
- Backups automáticos

### CRM
- Dashboard con métricas
- Pipeline Kanban
- Gestión de contactos
- Actividades y tareas

### Despiece (Bill of Materials)
- Cálculo automático de componentes
- Orden de Montaje y Lista de Corte
- **NUEVO**: Campos cliente, referencia, fecha, expediente

### Digitalizador de Borradores
- OCR con Gemini Vision (prompt mejorado para medidas)
- Líneas editables (cantidad, descripción, precio)
- Campo REF editable
- Descuento global + descuento por línea
- Decimales con punto y coma
- Título: "PRESUPUESTO TÉCNICO"
- Logo más grande
- Exportación CSV para máquina seccionadora

## Credenciales de Prueba
- Usuario: MARIO
- Contraseña: MARIO

## Archivos Modificados (24/01/2026)
- `/app/backend/server.py` - Prompt mejorado para digitalizador
- `/app/frontend/src/components/Digitalizador.jsx` - UI mejorada
- `/app/frontend/src/components/DespieceModal.jsx` - Campos de cliente
- `/app/frontend/src/components/BudgetTable.jsx` - Props para despiece
