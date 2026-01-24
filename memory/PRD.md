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
| 38 | **CRM: Título "CRM" (resto en español)** | ✅ | 24/01 |
| 39 | **Nuevo rol: Prescriptor Comercial** | ✅ | 24/01 |
| 40 | **Contactos: Segmentación (Promotor, Constructor, etc.)** | ✅ | 24/01 |
| 41 | **Contactos: Vinculación a Prescriptor** | ✅ | 24/01 |
| 42 | **API: Recordatorios automáticos desde oportunidades** | ✅ | 24/01 |

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

## Rol Prescriptor Comercial (24/01/2026) ✅ COMPLETADO

### Descripción:
Nuevo tipo de usuario con acceso **ultra-restringido**. El prescriptor comercial es un colaborador externo que solo puede aportar contactos potenciales (leads) para que el administrador los gestione y asigne.

### Características del Rol:
- **Acceso limitado:** Al loguearse, ve **SOLO** su agenda de contactos (`PrescriptorAgenda.jsx`)
- **Sin sidebar:** No tiene acceso a Presupuesto, CRM, Archivo, Digitalizador, Master, etc.
- **Solo puede:** Añadir, editar y eliminar contactos potenciales que él mismo crea
- **Contactos siempre "potenciales":** Los contactos creados tienen `source: 'prescriptor'`

### UI del Prescriptor (PrescriptorAgenda.jsx):
- **Cabecera:** "MI AGENDA DE CONTACTOS" con nombre del prescriptor
- **Estadísticas:** Total contactos, desglose por segmento
- **Filtros:** Búsqueda por nombre/empresa/teléfono, filtro por segmento
- **Lista de contactos:** Con botones editar/eliminar
- **Modal nuevo contacto:** Nombre*, teléfono, email, empresa, cargo, segmento, dirección, notas
- **Botón Salir:** Para cerrar sesión
- **Mensaje informativo:** "Los contactos que añadas aquí son clientes potenciales. El administrador los revisará y los asignará..."

### Segmentos disponibles:
- PROMOTOR, CONSTRUCTOR, PROMOTOR-CONSTRUCTOR
- DECORADOR-INTERIORISTA, ESTUDIO DE COCINA
- TIENDA DE MUEBLES, TIENDA DE COCINA Y BAÑOS, TIENDA DE ARMARIOS
- ARQUITECTO, REFORMISTA, USUARIO FINAL, OTRO

### Flujo de Trabajo:
1. **Admin crea prescriptor:** En Maestro → Usuarios → Nuevo usuario con "Prescriptor Comercial" ✓
2. **Prescriptor inicia sesión:** Ve solo PrescriptorAgenda, no la app completa
3. **Prescriptor añade contactos:** Con toda la info del lead potencial
4. **Admin ve contactos en CRM:** Dashboard → Contactos muestra columna "PRESCRIPTOR"
5. **Admin asigna contacto:** Puede asignar el contacto a un comercial para gestión

### API Endpoints:
- `GET /api/crm/contacts/by-prescriptor/{prescriptor_id}` - Contactos creados por un prescriptor
- `GET /api/crm/prescriptors` - Lista de todos los prescriptores activos
- `GET /api/crm/prescriptors/{id}/stats` - Estadísticas de un prescriptor

### Archivos Implementados:
- `/app/frontend/src/components/PrescriptorAgenda.jsx` - Componente completo del prescriptor
- `/app/frontend/src/App.js` - Líneas 219-232: Renderizado condicional para prescriptores
- `/app/backend/server.py` - Modelo User con `isPrescriptor`, endpoints de prescriptor

### Credenciales de prueba:
- **Usuario:** PRESCRIPTOR1
- **Contraseña:** PRESCRIPTOR1

## Calendario del Prescriptor (24/01/2026) ✅ COMPLETADO

### Descripción:
El prescriptor tiene un calendario simple donde puede añadir notas en fechas específicas para gestionar sus citas y recordatorios. El administrador puede ver todas las notas de prescriptores desde el calendario del CRM.

### Funcionalidades:
- **Vista de pestañas:** "Contactos" y "Calendario" en la agenda del prescriptor
- **Calendario mensual:** Navegación mes a mes, resaltado del día actual
- **Notas por fecha:** Click en cualquier día para crear/editar notas
- **Contador de notas:** Muestra "X notas este mes"

### Modal de Nota:
- **Campos:** Título, Contenido
- **Acciones:** Guardar, Cancelar, Eliminar (solo edición)
- **Fecha:** Muestra la fecha seleccionada

### Visibilidad Admin:
- El admin puede ver notas de prescriptores en el CRM → Calendario
- **Toggle "Notas Prescriptores"** para activar/desactivar visualización
- Las notas aparecen en **color ámbar** para diferenciarse de eventos normales
- Al pasar el ratón muestra el nombre del prescriptor

### API Endpoints:
- `GET /api/prescriptor/notes?prescriptor_id=X&start=Y&end=Z` - Notas del prescriptor
- `GET /api/prescriptor/notes/all?start=Y&end=Z` - Todas las notas (admin)
- `POST /api/prescriptor/notes` - Crear nota
- `PUT /api/prescriptor/notes/{id}` - Actualizar nota
- `DELETE /api/prescriptor/notes/{id}` - Eliminar nota

### Colección MongoDB:
- **prescriptor_notes:** {id, title, content, date, prescriptorId, prescriptorName, createdAt, updatedAt}

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

## Correcciones de Layout y Persistencia (24/01/2026) ✅ COMPLETADO

### 1. BUG CRÍTICO: Guardado de Presupuestos
- **Problema:** Los presupuestos se guardaban solo en memoria (React state), no en MongoDB
- **Solución:** `handleSaveBudget()` ahora llama a `POST /api/projects?user_id=X` para persistir
- **Verificación:** Los proyectos ahora aparecen en ARCHIVO después de guardar

### 2. Layout de BudgetTable.jsx Mejorado
- **Cambio:** Migración de sistema `grid-cols-12` a sistema `flex` con anchos fijos
- **Mejoras:**
  - Columna REF ampliada (w-28) para códigos largos
  - Icono "Corte Viga" movido al inicio de cada fila (columna V)
  - Precios siempre alineados a la derecha (w-20)
  - Selector D/I deshabilitado automáticamente para muebles de 2 puertas
  - Líneas manuales con diseño diferenciado (fondo verde claro)

### 3. Muebles de 2 Puertas
- **Detección:** `isTwoDoor` detecta si nombre contiene "2 puerta", "2P" o visualType "2P"
- **Comportamiento:** Columna AP muestra "-" en lugar del selector D/I

### 4. Estilos de Impresión
- **Archivo:** `/app/frontend/src/index.css`
- **Mejoras:** Oculta sidebar, header, botones y catálogo al imprimir
- **Solo imprime:** El contenedor `#budget-pdf` con el presupuesto

### Estructura de columnas del presupuesto:
| Columna | Ancho | Contenido |
|---------|-------|-----------|
| V (Viga) | w-7 | Icono corte viga |
| UD | w-8 | Cantidad |
| REF | w-28 | Referencia del producto |
| DESCRIPCIÓN | flex-1 | Nombre del producto |
| AN | w-10 | Ancho (cm) |
| AL | w-10 | Alto (cm) |
| FO | w-10 | Fondo (cm) |
| AP | w-8 | Apertura D/I/- |
| OBS | w-24 | Observaciones |
| € | w-20 | Precio |
| 🗑 | w-6 | Eliminar |


## Correcciones Adicionales (24/01/2026)

### 4. Aislamiento de Datos por Usuario
- **Problema:** Los items del presupuesto se guardaban en localStorage y se compartían entre usuarios
- **Solución:** Al hacer login (`handleLogin`), se limpian los items del presupuesto local
- **Archivo:** `/app/frontend/src/App.js`

### 5. Iconos Removidos de Librería Maestra
- **Cambio:** Los iconos/dibujos de muebles ya NO aparecen en la librería inferior
- **Nota:** Los iconos pueden usarse en la ficha individual del artículo
- **Archivo:** `/app/frontend/src/components/BudgetTable.jsx` (removido import y columna de iconos)

### 6. Descripción Línea Manual Expandida
- El campo de descripción de líneas manuales ahora ocupa el espacio de AN+AL+FO+AP
- Mayor área para escribir conceptos personalizados

