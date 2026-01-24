# LUIGGI HOME - ERP/CRM para Presupuestos de Cocinas

## Estado de Correcciones - 24/01/2026

### ✅ COMPLETADO (28/28 tareas)

| # | Corrección | Estado | Fecha |
|---|------------|--------|-------|
| 1 | Prompt IA mejorado (alturas 110cm, 220cm) | ✅ | 23/01 |
| 2 | Producto faltante 35A1P350 añadido | ✅ | 23/01 |
| 3 | Logo más grande en Digitalizador | ✅ | 23/01 |
| 4 | "BUDGET SYSTEM" → "PRESUPUESTO TÉCNICO" | ✅ | 23/01 |
| 5 | Campo REF (AUTO) editable | ✅ | 23/01 |
| 6 | Casilla descuento más ancha y editable | ✅ | 23/01 |
| 7 | Decimales con punto y coma | ✅ | 23/01 |
| 8 | Despiece: cliente, referencia, fecha, expediente | ✅ | 23/01 |
| 9 | Historial persistente (guardado en BD) | ✅ | 23/01 |
| 10 | Búsqueda en historial | ✅ | 23/01 |
| 11 | Modo Mantenimiento | ✅ | 23/01 |
| 12 | Backup Pre-Actualización automático | ✅ | 23/01 |
| 13 | Panel de control para Admin | ✅ | 23/01 |
| 14 | Pantalla "Sistema en actualización" | ✅ | 23/01 |
| 15 | Incremento por corte viga | ✅ | 23/01 |
| 16 | Contador correlativo expedientes | ✅ | 23/01 |
| 17 | **Conexión Digitalizador → CRM** | ✅ | 24/01 |
| 18 | **Sistema Clientes Activos** | ✅ | 24/01 |
| 19 | **Botón AUTO solo para Admin** | ✅ | 24/01 |
| 20 | **Unidades semicolumnas corregidas (110cm, 120cm...)** | ✅ | 24/01 |
| 21 | **Líneas manuales no afectadas por cambio PVP/COSTO** | ✅ | 24/01 |
| 22 | **Botón "Línea Manual" en Presupuesto Técnico** | ✅ | 24/01 |
| 23 | **Panel Admin: Ver todos los trabajos** | ✅ | 24/01 |
| 24 | **Endpoints para Comercial: Ver tiendas asignadas** | ✅ | 24/01 |
| 25 | **Volcado a CRM al guardar presupuesto** | ✅ | 24/01 |
| 26 | **Copia Seguridad en Maestro** | ✅ | 24/01 |
| 27 | **Gestión Armazones en pestaña separada** | ✅ | 24/01 |
| 28 | **Icono corte viga mejorado por línea** | ✅ | 24/01 |

### 🟢 TODO COMPLETADO

## Nuevas Funcionalidades Implementadas (24/01/2026)

### 1. Volcado Automático a CRM
- Al guardar un presupuesto, el sistema pregunta si desea crear una oportunidad en el CRM
- Se crea automáticamente: Contacto + Oportunidad con valor del presupuesto
- Stage: "proposal", Probabilidad: 50%
- Tags: ['presupuesto', 'auto']
- Vinculación directa: linkedProjectId, linkedProjectNumber

### 2. Panel de Backups en Maestro
- Nueva pestaña "BACKUPS" en Panel Maestro (solo Admin)
- Visualización de todos los backups (manuales, automáticos, pre-update)
- Botón "CREAR BACKUP MANUAL"
- Info sobre sistema de backups automáticos

### 3. Gestión de Armazones Separada
- Nueva pestaña "ARMAZONES" en Panel Maestro
- UI mejorada con tarjetas para cada material
- Muestra: Nombre, Incremento (€), Grosor (mm)
- Indicador de material predeterminado
- Explicación de qué es el incremento

### 4. Icono Corte Viga Mejorado
- Botón visual por cada línea del presupuesto
- Color naranja cuando está activo
- SVG personalizado representando un corte diagonal
- Tooltip informativo

## Sistema de Clientes Activos (NUEVO - 24/01/2026)

### Funcionalidad Implementada:
- **Nueva pestaña "CLIENTES"** en Panel Maestro (solo Admin)
- **CRUD completo**: Crear, ver, editar y eliminar clientes
- **Importación masiva CSV**: Subir archivo con múltiples clientes
- **Vinculación Usuario ↔ Cliente**: Asociar usuarios a clientes empresariales

### Campos del Cliente:
| Campo | Descripción |
|-------|-------------|
| `codigo` | Código del programa de gestión (único) |
| `nombre` | Nombre comercial / Razón social |
| `cif` | CIF/NIF |
| `direccion`, `localidad`, `provincia`, `codigoPostal` | Dirección completa |
| `telefono`, `email` | Contacto |
| `descuento` | Descuento personalizado (%) |
| `activo` | Estado activo/inactivo |
| `notas` | Observaciones |

### API Endpoints:
- `GET /api/clients` - Listar clientes
- `POST /api/clients` - Crear cliente
- `PUT /api/clients/{id}` - Actualizar cliente
- `DELETE /api/clients/{id}` - Eliminar cliente
- `POST /api/clients/import-csv` - Importar desde CSV

### Formato CSV para importación:
```
codigo;nombre;cif;direccion;localidad;provincia;cp;telefono;email;descuento;activo;notas
```

## Conexión Digitalizador → CRM (24/01/2026)

### Funcionalidad Implementada:
- **Botón "Crear Oportunidad CRM"** en Digitalizador cuando hay líneas cargadas
- **Modal de creación** con preview del presupuesto (nombre, valor total, líneas)
- **Formulario de contacto**: Nombre cliente*, Empresa, Email, Teléfono
- **Creación automática** de Contacto y Oportunidad en CRM
- **Estado visual**: Botón cambia a "Oportunidad Creada" (verde) tras éxito
- **Tags automáticos**: ['digitalizador', 'presupuesto']
- **Notas detalladas**: Base imponible, IVA, acabados, armazón, costados

### Flujo de Usuario:
1. Digitalizar presupuesto (subir foto/PDF) o cargar del historial
2. Editar líneas si es necesario
3. Click en "Crear Oportunidad CRM" (botón púrpura)
4. Rellenar datos del contacto en modal
5. Click en "Crear Oportunidad"
6. Contacto y Oportunidad creados → aparece en Dashboard CRM

### Archivos Modificados:
- `/app/frontend/src/components/Digitalizador.jsx` - UI y lógica
- Test: `/app/backend/tests/test_digitalizador_crm_integration.py`

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
