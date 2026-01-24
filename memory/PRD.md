# LUIGGI HOME - ERP/CRM para Presupuestos de Cocinas

## Estado de Correcciones - 24/01/2026

### ✅ COMPLETADO (32/32 tareas)

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
| 29 | **CRM→Contactos: Convertir a Cliente Potencial** | ✅ | 24/01 |
| 30 | **Clientes Potenciales vs Activos (naranja/verde)** | ✅ | 24/01 |
| 31 | **Usuario hereda descuento de cliente vinculado** | ✅ | 24/01 |
| 32 | **Comercial: Botón "Mis Tiendas" para ver trabajo** | ✅ | 24/01 |
| 33 | **COPIA SEGURIDAD y MANTENIMIENTO movidos dentro de Master** | ✅ | 24/01 |
| 34 | **CRM: Alertas clientes sin oferta en 30+ días** | ✅ | 24/01 |
| 35 | **CRM: Alertas clientes sin compra en 60/90 días** | ✅ | 24/01 |
| 36 | **CRM: Calendario completo (Mes/Semana/Día)** | ✅ | 24/01 |
| 37 | **CRM: Traducción completa al español** | ✅ | 24/01 |

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

## Sistema de Clientes Potenciales y Activos (24/01/2026)

### Funcionalidad Implementada:
- **Nueva pestaña "CLIENTES"** en Panel Maestro (solo Admin)
- **Dos tipos de cliente**: Potenciales (🟠 naranja) y Activos (🟢 verde)
- **Flujo de conversión**: Potencial → Activo asignando código del programa de gestión
- **Estadísticas**: Total, Potenciales, Activos en cards superiores
- **Filtros avanzados**: Por tipo, por segmento, búsqueda de texto
- **Segmentos disponibles**: DECORADORES-INTERIORISTAS, PROMOTORES, CONSTRUCTORES, GRANDES CLIENTES, REVENDEDORES, ESTUDIOS DE COCINA Y BAÑOS, TIENDAS DE ARMARIOS, USUARIOS FINALES
- **CRUD completo**: Crear, ver, editar y eliminar clientes
- **Importación masiva CSV**: Subir archivo con múltiples clientes
- **Vinculación Usuario ↔ Cliente**: Asociar usuarios a clientes empresariales

### CRM → Contactos: Convertir a Cliente Potencial
- **Botón "Convertir a Cliente Potencial"** (icono UserCheck naranja) en cada contacto no convertido
- Copia automáticamente datos del contacto a la BD de clientes como potencial
- El contacto muestra etiqueta "CONVERTIDO" (verde) después de la conversión
- Actualiza el campo `convertedToClientId` en el contacto
- Se puede gestionar el cliente desde Maestro → Clientes

### Activación de Clientes
- **Botón "Activar"** (✓ verde) visible solo para clientes potenciales sin código
- Modal para asignar código único del programa de gestión
- El cliente pasa de tipo "potencial" a "activo"
- Se registra fecha de conversión (`convertidoAt`)

### Vinculación Usuario ↔ Cliente
- Al editar usuario, dropdown "Vincular a Cliente" con todos los clientes activos
- **Herencia de descuento**: El usuario hereda automáticamente el descuento del cliente vinculado
- Texto de ayuda explica la funcionalidad

### Vista para Comerciales: "Mis Tiendas"
- **Botón "MIS TIENDAS"** en sidebar (solo visible para comerciales, no admin)
- Muestra tiendas asignadas al comercial
- Lista proyectos creados por esas tiendas
- Lista oportunidades CRM de esas tiendas
- Filtros por tienda y búsqueda de texto

### Campos del Cliente:
| Campo | Descripción |
|-------|-------------|
| `tipo` | 'potencial' o 'activo' |
| `codigo` | Código del programa de gestión (único, asignado al activar) |
| `nombre` | Nombre comercial / Razón social |
| `cif` | CIF/NIF |
| `segmento` | Categoría del cliente |
| `direccion`, `localidad`, `provincia`, `codigoPostal` | Dirección completa |
| `telefono`, `email` | Contacto |
| `descuento` | Descuento personalizado (%) |
| `activo` | Estado activo/inactivo |
| `notas` | Observaciones |
| `origenCrmContactId` | ID del contacto CRM si fue convertido |
| `usuarioVinculadoId` | ID del usuario vinculado |
| `convertidoAt` | Fecha de activación |

### API Endpoints:
- `GET /api/clients` - Listar clientes (con filtros ?tipo=, ?segmento=)
- `GET /api/clients/segments` - Lista de segmentos disponibles
- `POST /api/clients` - Crear cliente
- `PUT /api/clients/{id}` - Actualizar cliente
- `DELETE /api/clients/{id}` - Eliminar cliente
- `POST /api/clients/from-contact/{contact_id}` - Crear cliente potencial desde contacto CRM
- `POST /api/clients/{id}/activate` - Activar cliente potencial (body: {codigo: "..."})
- `POST /api/clients/{id}/link-user` - Vincular cliente a usuario
- `POST /api/clients/import-csv` - Importar desde CSV
- `GET /api/commercial/my-shops-work` - Ver trabajo de tiendas asignadas (para comerciales)

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

## CRM Analytics: Alertas de Clientes Inactivos (24/01/2026)

### Funcionalidad Implementada:
- **Dashboard CRM ampliado** con dos nuevas secciones de alertas:
  - 🟠 **Sin Oferta +30 días**: Contactos que no han recibido una oferta/presupuesto en más de 30 días
  - 🔴 **Sin Compra +60/90 días**: Contactos que no han realizado una compra (oportunidad ganada) en más de 60 días

### Características:
- Listado de contactos ordenados por días de inactividad (mayor primero)
- Muestra nombre, empresa, días sin actividad
- Indicador visual de última oferta/compra
- Estadísticas resumidas en cabecera

### API Endpoint:
- `GET /api/crm/analytics/inactive-clients?days_without_offer=30&days_without_purchase=60`
- Devuelve:
  - `withoutRecentOffer`: Lista de contactos sin ofertas recientes (max 50)
  - `withoutRecentPurchase`: Lista de contactos sin compras recientes (max 50)
  - `summary`: Totales (30 días sin oferta, 60 días sin compra, 90 días sin compra)

### Archivos Modificados:
- `/app/backend/server.py` - Nuevo endpoint de analytics
- `/app/frontend/src/services/api.js` - Nueva función `crmAnalyticsAPI`
- `/app/frontend/src/components/CRMDashboard.jsx` - UI de alertas

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
- Colecciones principales: users, products, projects, contacts, opportunities, digitalizador_history, system_counters, system_backups, system_settings, calendar_events

## Menú Lateral (Admin)
1. CRM (Gestión Comercial)
2. PRESUPUESTO
3. IA LAB
4. ARCHIVO
5. DIGITALIZADOR
6. PANEL ADMIN
7. MASTER (incluye Backups y Mantenimiento)
8. SALIR

## CRM - Gestión Comercial (24/01/2026)

### Pestañas del CRM:
1. **Resumen** - Dashboard con estadísticas, alertas de clientes inactivos
2. **Oportunidades** - Embudo de ventas (Kanban)
3. **Contactos** - Gestión de contactos con conversión a clientes
4. **Calendario** - Planificación de citas, seguimientos, llamadas

### Calendario CRM:
- **Vistas:** Mensual, Semanal, Diaria (tipo Google Calendar)
- **Tipos de eventos:** Cita/Visita, Seguimiento, Llamada, Reunión, Otro
- **Visibilidad:**
  - Usuario normal: Solo sus eventos
  - Admin: Todos los eventos (con checkbox "Ver todos")
  - Comercial: Eventos de sus tiendas asignadas
- **Integración:** Vincular eventos a contactos y oportunidades
- **Funcionalidades:** Crear, editar, eliminar, marcar completado

### Estados del Embudo de Ventas (Pipeline):
1. Nuevo → 2. Contactado → 3. Presupuesto Enviado → 4. En Negociación → 5. Venta Cerrada / Perdida

### Estados de Contactos:
- Nuevo, Activo, Cliente, Inactivo

### Endpoints del Calendario:
- `GET /api/crm/calendar/event-types` - Tipos de eventos
- `GET /api/crm/calendar/events` - Listar eventos (con filtros)
- `POST /api/crm/calendar/events` - Crear evento
- `PUT /api/crm/calendar/events/{id}` - Actualizar evento
- `DELETE /api/crm/calendar/events/{id}` - Eliminar evento
- `POST /api/crm/calendar/events/{id}/complete` - Marcar completado
