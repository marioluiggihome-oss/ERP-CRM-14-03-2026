# LUIGGI HOME - Kitchen Budgeting ERP/CRM

## Estado: EN DESARROLLO ACTIVO
## Última Actualización: 26 Marzo 2026

---

## ✅ COMPLETADO EN ESTA SESIÓN (26 Marzo 2026)

### 1. Toggle Unidad de Medidas mm/cm COMPLETO (P0)
- ✅ **Bug corregido**: El toggle "UNIDAD MEDIDAS" ahora funciona en TODAS las secciones
- ✅ **Secciones corregidas**:
  - Vista horizontal/abajo (tabla de catálogo) ✅
  - Vista top/arriba (tabla de catálogo) ✅
  - Vista vertical/sidebar (tarjetas de productos) ✅
  - **TABLA DEL PRESUPUESTO** - Encabezados AN(mm/cm), AL(mm/cm), FO(mm/cm) ✅
  - Inputs de dimensiones personalizadas (edición bidireccional) ✅
- ✅ **Nueva función `parseMeasureInput()`**: Convierte valores ingresados de MM a CM para almacenamiento
- ✅ **Frontend**: `/app/frontend/src/components/BudgetTable.jsx`
- ✅ **Verificado**: Screenshots confirman conversión correcta CM↔MM en todas las vistas

### 2. Sistema de Expedientes por Provincia (P0)
- ✅ **Nuevo formato**: `EXP-2026-{PROVINCIA}-{NNN}` (ej: `EXP-2026-LE-001` para León)
- ✅ **Backend**: Endpoint `/api/expedient/next` acepta parámetro `client_code` (código de provincia)
- ✅ **Cada provincia tiene su propia secuencia** independiente de números
- ✅ **Frontend - RED DISTRIBUCIÓN** (`SettingsModal.jsx`):
  - Nuevo campo **PROVINCIA**: Desplegable con todas las provincias de España
  - Campo **USUARIO / EMAIL**: Ahora acepta emails y minúsculas
  - Preview del formato: "Se usará para numerar expedientes: EXP-2026-XX-001"
- ✅ **Frontend - Presupuestador** (`BudgetTable.jsx`):
  - Botón AUTO usa la provincia del usuario logueado
- ✅ **Verificado**: Screenshots y curl confirman generación correcta

### 3. Sistema de Backup Automático Diario (P0)
- ✅ **Backend**: Servicio de backup en `/app/backend/services/backup_service.py`
- ✅ **Backup automático**: Ejecuta diariamente a las **3:00 AM**
- ✅ **Retención**: 7 días (backups antiguos se eliminan automáticamente)
- ✅ **Formato**: `luiggi_backup_YYYYMMDD_HHMMSS.tar.gz` comprimido
- ✅ **Endpoints API**:
  - `POST /api/admin/backup/create` - Crear backup manual
  - `GET /api/admin/backup/list` - Listar backups disponibles
  - `POST /api/admin/backup/restore/{name}` - Restaurar backup
- ✅ **Frontend - Pestaña "BACKUPS DB"** en Panel Maestro:
  - Solo visible para Admin Principal (`isPrimaryAdmin`)
  - Botón "Crear Backup Ahora"
  - Lista de backups con fecha, hora y tamaño
  - Botón "Restaurar" para cada backup
- ✅ **Verificado**: Backup de 45.9 MB creado exitosamente

### 4. Informe de Uso por Usuario (P0)
- ✅ **Backend**: Sistema de tracking en `/app/backend/services/activity_tracker.py`
- ✅ **Registro automático de actividades**: logins, presupuestos, pedidos, PDFs, IA
- ✅ **Frontend - Pestaña "USO USUARIOS"**: Solo visible para Admin Principal
- ✅ **Verificado**: Muestra actividad correctamente

### 5. Cambio de Credenciales del Usuario Principal (P0)
- ✅ **Usuario anterior**: MARIO / MARIO
- ✅ **Usuario nuevo**: `mario@luiggihome.es` / `Mario2025*`
- ✅ **Campo `isPrimaryAdmin: true`** añadido para identificar al admin principal
- ✅ **Backend verificado con curl**: Login exitoso

### 6. Sistema de Caducidad de Acceso (P0)
- ✅ **Campo `accessExpirationDate`** añadido al modelo de usuario
- ✅ **Frontend - Formulario de Usuario**:
  - Selector de fecha tipo calendario
  - Indicador de estado (Activo/Expirado)
  - Botón "Renovar +1 año"
  - Texto informativo
- ✅ **Backend - Validación en Login**:
  - Verifica fecha de caducidad
  - Bloquea acceso si expiró
  - Mensaje de error descriptivo

### 7. Mejoras en Adjuntos de Pedidos (P0)
- ✅ **Refactorizado** proceso de adjuntos en `/app/backend/routes/orders.py`
- ✅ **Archivos se leen una sola vez** al inicio y se reutilizan para:
  - Envío por email (SendGrid)
  - Almacenamiento en DB
- ✅ **Logs mejorados** para debugging de adjuntos

### Pendiente/En Progreso:
- ⚠️ **Bug Frontend Login**: Error "body stream already read" al hacer login desde la UI
  - curl funciona correctamente
  - Puede ser causado por scripts externos de la plataforma
  - Backend funcionando correctamente

---

## ✅ COMPLETADO EN SESIÓN ANTERIOR (25 Marzo 2026)

### 1. Informe de Producción PDF con Logo y Despiece (P0 - Requisito Word)
- ✅ **Nueva funcionalidad**: Generación de PDF completo para órdenes de fabricación
- ✅ **Contenido del PDF**:
  - Logo de la empresa (desde configuración global)
  - Información del pedido (número, cliente, fecha, estado, prioridad)
  - Lista de muebles a fabricar (código, descripción, dimensiones)
  - Despiece detallado por mueble (laterales, tapas, trasera)
  - Resumen de materiales (total piezas y área por material)
  - Footer con timestamp y versión del sistema
- ✅ **Backend**: Nuevo módulo `/app/backend/routes/factory_reports.py`
- ✅ **Endpoints**:
  - `GET /api/fabrica/reports/production/{order_id}` - PDF desde orden de fabricación
  - `GET /api/fabrica/reports/production-from-budget/{budget_id}` - PDF desde presupuesto
- ✅ **Frontend**: Botón "Informe PDF" en Portal de Fábrica (PortalFabrica.jsx línea 580+)
- ✅ **Verificado**: Testing agent pasó 15/15 tests, PDF de 33KB generado correctamente

### 2. Envío de Copias de Pedidos con Archivos Adjuntos (P0 - Requisito Word)
- ✅ **Nueva funcionalidad**: Reenvío de pedidos confirmados incluyendo adjuntos del cliente
- ✅ **Guardado de adjuntos**: Los archivos adjuntos se almacenan en base64 en el pedido
- ✅ **Backend**: Endpoint `POST /api/orders/{order_id}/send-copy` en `/app/backend/routes/orders.py`
- ✅ **Opciones de envío**:
  - Email de destino personalizado
  - Mensaje adicional opcional
  - Checkbox para incluir/excluir adjuntos guardados
- ✅ **Frontend**: Modal "Enviar Copia del Pedido" en Mis Pedidos (MisPedidos.jsx)
- ✅ **UI elementos**:
  - Botón de envío (icono avión de papel azul)
  - Input de email con auto-completado
  - Textarea para mensaje adicional
  - Checkbox "Incluir archivos adjuntos del cliente"
- ✅ **Verificado**: Testing agent confirmó funcionamiento completo

### 3. Logo Integrado en PDFs de Pedidos (P0 - Requisito Word)
- ✅ **Funcionalidad existente mejorada**: El logo ya se guardaba en settings, ahora se usa en:
  - Informes de producción PDF (factory_reports.py)
  - Presupuestos PDF existentes (pdfGenerator.js)
- ✅ **Configuración**: Logo almacenado como base64 en `db.settings.logo`
- ✅ **Verificado**: Logo presente en configuración global y usado en generación de PDFs

### 4. Refactorización Frontend P1 - SettingsModal.jsx
- ✅ **Reducción**: De 5332 líneas a 4853 líneas (-480 líneas)
- ✅ **Componentes extraídos a `/app/frontend/src/components/settings/`**:
  - `TelemetryTab.jsx` (Telemetría IA - 290 líneas)
  - `IdentityTab.jsx` (Color y Logo corporativo - 120 líneas)
  - `SecurityTab.jsx` (Autenticación 2FA - 180 líneas)
  - `DashboardTab.jsx` (Dashboard de fábrica - 350 líneas)
  - `SettingsContext.jsx` (Contexto compartido)
  - `index.js` (Exportaciones)
- ✅ **Reducción total**: De 5332 líneas a 4538 líneas (-794 líneas, 15%)
- ✅ **Verificado**: Frontend compila sin errores

### 5. Manual de Usuario P2 - Completado
- ✅ **Archivo**: `/app/docs/MANUAL_USUARIO.md`
- ✅ **Versión**: Actualizado a 2.0
- ✅ **Nuevas secciones añadidas**:
  - Sección 5.7: Informe de Producción PDF
  - Sección 8: Mis Pedidos (completa con envío de copias)
  - Sección 9: Dashboard Fábrica (KPIs y gráficos)
  - Sección 10: Telemetría IA (reconocimiento óptico)

---

## ✅ COMPLETADO EN SESIÓN ANTERIOR (22 Marzo 2026)

### 1. Fix Error "body stream already read" en Telemetría IA (P0)
- ✅ **Bug corregido**: El frontend consumía el stream de respuesta dos veces al manejar errores
- ✅ **Solución**: `productsAPI.bulkCreate` y `bulkUpsert` ahora usan `response.text()` + `JSON.parse()` en lugar de `response.json()`
- ✅ **Frontend**: `/app/frontend/src/services/api.js` líneas 298-346
- ✅ **Verificado**: Testing agent confirmó que no hay error de stream

### 2. Sistema UPSERT para Evitar Duplicación de Productos (P0)
- ✅ **Problema original**: Al importar tarifa T1, T2, T3 para MV, se creaban productos duplicados
- ✅ **Solución**: Nuevo endpoint `POST /api/products/bulk-upsert` que:
  - Si el producto existe (por código + biblioteca): actualiza `zonePoints` con la nueva tarifa
  - Si no existe: crea el producto con `zonePoints` inicial
- ✅ **Backend**: `/app/backend/server.py` líneas 1781-1867
- ✅ **Frontend**: Telemetría IA ahora usa `productsAPI.bulkUpsert()` en lugar de `bulkCreate()`
- ✅ **Verificado**: Producto con zonePoints: {T1: 100, T2: 150, T3: 200} funciona correctamente

### 3. Selector de Tarifa en UI de Telemetría IA (P0)
- ✅ **Nueva funcionalidad**: Dropdown para seleccionar tarifa antes de importar imágenes
- ✅ **MV**: Dropdown con opciones T1-T21 (21 tarifas)
- ✅ **ZC**: Dropdown con opciones Z1-Z12 (12 zonas)
- ✅ **Persistencia**: Guardar selección en localStorage
- ✅ **UI mejorada**: Labels dinámicos ("Tarifa MV" vs "Zona ZC")
- ✅ **Frontend**: `/app/frontend/src/components/SettingsModal.jsx` líneas 4469-4531
- ✅ **Verificado**: Screenshots confirman UI funcional

### 4. Dashboard Fábrica (antes Dashboard de Métricas) (P1)
- ✅ **Renombrado**: "Dashboard" → "Dashboard Fábrica"
- ✅ **Nueva pestaña "DASHBOARD FÁBRICA"** en Panel Maestro (MASTER)
- ✅ **Backend**: Nuevo módulo `/app/backend/routes/dashboard.py` con endpoint `/api/dashboard/metrics`
- ✅ **Selector de período**: Semana / Mes / Trimestre / Año / Todo el histórico
- ✅ **7 KPIs principales**:
  - Órdenes de Fabricación
  - Pedidos Confirmados
  - Presupuestos
  - Ventas € (valor total)
  - Presupuestos Valor €
  - Piezas en Producción
  - Tasa de Conversión
- ✅ **Gráficos interactivos (recharts)**:
  - Tendencia Mensual (BarChart - Pedidos vs Presupuestos)
  - Estado de Producción (PieChart - Borrador/Confirmado/En Producción/Listo/Entregado)
- ✅ **Secciones adicionales**:
  - Prioridad de Órdenes (Urgente/Alta/Normal/Baja)
  - Clientes (Total/Activos/Potenciales)
  - Catálogo de Productos (Total/ZC/MV)
  - Últimos Pedidos Confirmados (tabla)
  - Fabricación Pendiente (tabla)
  - Presupuestos por Estado
- ✅ **Verificado**: Testing agent pasó 14/14 tests backend + todos los elementos UI

### 5. Renombrado de Pestañas y Nuevo Rol "Director de Fábrica" (P1)
- ✅ **Renombrado**: "Panel Director" → "Panel Director Comercial"
- ✅ **Renombrado**: "Dashboard" → "Dashboard Fábrica"
- ✅ **Nuevo rol**: `isDirectorFabrica` en el modelo de usuario
- ✅ **Backend**: Campo añadido en `/app/backend/models/schemas.py` (UserBase, UserCreate, UserUpdate)
- ✅ **Frontend**: Checkbox con fondo cyan en formulario de usuario
- ✅ **Permisos automáticos**: Director Fábrica tiene acceso a:
  - Dashboard Fábrica (pestaña en Panel Maestro)
  - Módulo FÁBRICA en sidebar
  - canAccessFabrica se activa automáticamente
- ✅ **Verificado**: Testing agent pasó 7/7 tests

### 6. Detección Automática de Tarifa MV por IA (P1)
- ✅ **Funcionalidad**: La IA (Gemini Vision) detecta automáticamente la tarifa (T1-T21) desde el encabezado de cada imagen MV
- ✅ **Backend**: Modificado prompt en `/app/backend/server.py` para extraer "detectedTariff" del encabezado
- ✅ **Frontend**: Para MV ya no muestra selector dropdown manual, sino mensaje "🤖 Detección Automática"
- ✅ **ZC mantiene selector manual**: Para librería ZC sigue mostrando dropdown Z1-Z12
- ✅ **Agrupación inteligente**: El frontend agrupa productos por tarifa detectada y hace upserts separados
- ✅ **Logs mejorados**: Muestra en el log la tarifa detectada por la IA para cada imagen

---

## ✅ COMPLETADO EN SESIÓN ANTERIOR (21 Marzo 2026)

### 0. Fix Selector MV/ZC en Telemetría IA (P0)
- ✅ **Bug corregido**: El agente anterior añadió el selector de biblioteca MV/ZC pero olvidó declarar el estado `telemetryLibrary`
- ✅ **Error original**: `ReferenceError: telemetryLibrary is not defined` bloqueaba toda la aplicación
- ✅ **Solución**: Añadido `const [telemetryLibrary, setTelemetryLibrary] = useState('ZC')` en línea 102
- ✅ **UI funcional**: Selector con opciones "📘 ZC (Z1)" y "📙 MV (T1)" antes de cargar fichas
- ✅ **Frontend**: `/app/frontend/src/components/SettingsModal.jsx` líneas 102, 4469-4491
- ✅ **Verificado**: Screenshot confirma UI correcta sin errores de consola

### 0.1. Mejora: Persistencia de Biblioteca en localStorage
- ✅ **Funcionalidad**: El selector MV/ZC ahora recuerda la última selección
- ✅ **Implementación**: useState con inicializador lazy que lee de localStorage
- ✅ **onClick actualizado**: Guarda en localStorage al cambiar biblioteca
- ✅ **Verificado**: Test confirma `localStorage.telemetryLibrary = MV` persistido

### 0.2. Refactorización Backend Completa
- ✅ **`/app/backend/routes/montajes.py`** (264 líneas): CRUD Montadores y Montajes
- ✅ **`/app/backend/routes/backup.py`** (349 líneas): Sistema de backups, scheduler, email
- ✅ **`/app/backend/routes/armarios.py`** (533 líneas): Proyectos de Armarios con IA
- ✅ **`/app/backend/routes/digitalizador.py`** (667 líneas): Reconocimiento óptico, expedientes
- ✅ **`/app/backend/routes/crm_module.py`** (797 líneas): Contactos, Oportunidades, Actividades
- ✅ **`/app/backend/routes/orders.py`** (440 líneas): Confirmación de pedidos, fabricación
- ✅ **server.py reducido**: De 7006 a 3718 líneas (**-3288 líneas, -47%**)
- ✅ **Total routers modulares**: 17 archivos
- ✅ **Verificado**: Todos los endpoints funcionan correctamente

### 0.3. UI: Eliminado Botón "Registrarse con Email"
- ✅ **Login simplificado**: Eliminado el botón "REGISTRARSE CON EMAIL" y la sección "¿Nuevo distribuidor?"
- ✅ **Frontend**: `/app/frontend/src/components/Login.jsx`

### 1. Números de Fabricación para Órdenes (P0)
- ✅ **Campo manufacturingNumber añadido**: Número secuencial global para identificación interna en fábrica
- ✅ **Formato**: Número entero simple (1, 2, 3...) complementario al orderNumber (OF-2026-0001)
- ✅ **Generación automática**: Usa MongoDB counter con upsert para garantizar secuencia
- ✅ **Visualización en Portal**: Badge "Nº FAB: X" junto al orderNumber en la tarjeta de cada orden
- ✅ **Backend**: `/app/backend/routes/fabrica.py` líneas 166-172

### 2. Sección Editable de Puertas para Proveedores (P0)
- ✅ **Nueva pestaña "PUERTAS PROVEEDOR"** en el modal de Despiece
- ✅ **Tabla editable completa** con columnas:
  - Mueble (código y descripción)
  - Tipo (ALTOS, BAJOS, COLUMNAS)
  - Color (editable)
  - Alto cm (editable)
  - Ancho cm (editable)
  - Veta (selector Vertical/Horizontal)
  - Observaciones (campo de texto)
- ✅ **Resumen visual**: Tarjetas con totales por tipo (P. ALTOS, P. BAJOS, P. COLUMNAS)
- ✅ **Exportación CSV**: Genera archivo con dimensiones agrupadas para enviar al proveedor
- ✅ **Exportación PDF**: Documento profesional con tabla de puertas y totales
- ✅ **Frontend**: `/app/frontend/src/components/DespieceModal.jsx`

### 3. Manual de Ayuda Dinámico según Permisos (P1)
- ✅ **Filtrado inteligente de secciones**: El manual solo muestra contenido de módulos accesibles
- ✅ **Permisos verificados**:
  - `canAccessFabrica` → Sección "Portal de Fábrica"
  - `canAccessMontajes` → Sección "Agenda de Montajes"
  - `canAccessCRM` → Sección "Módulo CRM"
  - `isAdmin` → Sección "Administración"
- ✅ **Nueva sección añadida**: "Agenda de Montajes" con documentación del módulo
- ✅ **Frontend**: `/app/frontend/src/components/UserManualModal.jsx` función `getSectionsForUser()`

---

## ✅ COMPLETADO EN SESIÓN ANTERIOR (20 Marzo 2026)

### 1. Nueva Sección "Puertas por Color" en Modal Despiece
- ✅ **Resumen de Puertas por Color**: Nueva sección en pestaña "CASCO, PUERTA Y HERRAJE"
- ✅ **Tarjetas visuales**: P.ALTOS (azul), P.BAJOS (naranja), P.COLUMNAS (púrpura)
- ✅ **Agrupación automática**: Puertas clasificadas según tipo de mueble (A=ALTOS, B=BAJOS, C=COLUMNAS)
- ✅ **Colores desde configuración**: Usa los valores de P.Bajos, P.Altos, P.Colum y Costados del presupuesto
- ✅ **Tablas detalladas por tipo**: Cada tipo de puerta tiene su propia tabla con dimensiones
- ✅ **Exportación PDF**: El PDF de herrajes ahora incluye puertas agrupadas por color
- ✅ **Props pasadas correctamente**: doorColorLow, doorColorHigh, doorColorColumns, sideColor

### 2. Campo de Veta para Puertas (Seccionadora)
- ✅ **Veta VERTICAL por defecto**: Todas las puertas tienen veta vertical (la veta sigue el ALTO)
- ✅ **Leyenda visual**: Banner informativo "📐 ORIENTACIÓN DE VETA: ↕ VERTICAL (por defecto)"
- ✅ **Columna en tabla**: Nueva columna "VETA" con badge verde "↕ V"
- ✅ **CSV actualizado**: Campo Textura=1 para puertas (veta vertical)
- ✅ **XML actualizado**: Elementos `<Grain>1</Grain>` y `<GrainDirection>vertical</GrainDirection>`

### 3. Nomenclaturas MV Integradas
- ✅ **Detección completa de tipos de mueble** para biblioteca MV:
  - **ALTOS**: A, ASCE, ASC, AR, ARI, ARU, ARC, AD, AV, AE, AM, AMF, ACA, ACC, ASF, AT, ATP, AA, AC, ACP, ACPJ, L, LV, S, SV, SC, SVC, BOA, BOS
  - **BAJOS**: B, BF, BRI, BRU, BR, BH, BHC, BHZ, BHG, BT, BTP, BPC, BC, BCG, BGC, BCGF, BGF
  - **COLUMNAS**: CD, CE, CF, CH, CHPC, CHGC, CHC, CHM, CHMG, CHMC, CHMCG, BOC, M, MV, MPG, MVG, MPH, MPM, MGHM, MCHM
- ✅ **Compatible con ZC**: Mantiene soporte para códigos 9A, 9B, etc.

### 4. Fix Glitch Visual Sidebar (P3)
- ✅ **Transiciones optimizadas**: Cambiado de `transition-all` a `transition-colors duration-200`
- ✅ **Overflow controlado**: Añadido `overflow-hidden` al sidebar y sus contenedores
- ✅ **Animaciones estables**: Transiciones suaves sin "saltos" visuales

### 5. Fix Precio COST (P2) - Muestra 17 en vez de 16
- ✅ **Bug identificado**: El código usaba siempre `zonePoints.Z1` para calcular puntos, ignorando que MV usa `zonePoints.T1`
- ✅ **Corrección en BudgetTable.jsx**:
  - Líneas 729-735: Detección de biblioteca para usar T1 (MV) o Z1 (ZC)
  - Líneas 574-580: Ordenación de productos por puntos usando la zona correcta
  - Líneas 2302, 2558, 2759: Display de puntos en catálogo usando biblioteca del producto
- ✅ **Validado**: El producto COST ahora muestra 16 puntos correctamente

### 6. Módulo de Actividades CRM (NUEVO)
- ✅ **Nuevo componente CRMActivities.jsx** con registro de:
  - Llamadas, Visitas, Reuniones, Videollamadas, Emails, Notas
  - Fecha, hora y duración configurable
  - Vinculación con contactos del CRM
  - Campo de asunto, notas y resultado/seguimiento
- ✅ **UI completa con**:
  - Estadísticas rápidas (HOY, SEMANA, TOTAL)
  - Búsqueda y filtros por tipo/fecha
  - Lista agrupada por fecha
  - Vista expandible con detalles
  - Edición y eliminación de actividades
- ✅ **100% Responsive para móvil**:
  - Grid de estadísticas adaptable
  - Tabs scrollables horizontalmente
  - Modal tipo "bottom sheet" para formulario
  - Botón flotante (FAB) para nueva actividad
- ✅ **Backend actualizado**:
  - Modelo ActivityModel con campos: date, time, duration, subject, notes, outcome
  - Endpoints GET/POST/PUT/DELETE en /api/crm/activities

### 7. Consolidación de Piezas en Despiece
- ✅ **Piezas iguales unificadas**: Cuando hay muebles idénticos (x2, x3...), las piezas con mismas características se consolidan
- ✅ **En lugar de líneas duplicadas**: Se muestra CANTIDAD multiplicada (ej: Lateral izquierdo x2)
- ✅ **Afecta a**: Vista PDF, exportación CSV para seccionadora, vista en pantalla
- ✅ **Criterio de consolidación**: mismo nombre, dimensiones (largo, ancho) y grosor

### 8. Grosor de Trasera Configurable en Armazones
- ✅ **Nuevo campo en gestión de armazones**: "Grosor Trasera (mm)" junto a Incremento y Grosor Casco
- ✅ **3 columnas en tarjetas**: INCREMENTO | GROSOR CASCO | GROSOR TRASERA
- ✅ **Se usa en el cálculo de despiece**: La trasera usa el grosor configurado del armazón seleccionado
- ✅ **Backend actualizado**: DespieceRequest y calculate_furniture_despiece aceptan backThickness

---

## ✅ COMPLETADO EN SESIÓN ANTERIOR (19 Marzo 2026)

### 1. Códigos de Fábricas Corregidos
- ✅ **SALAMANCA = 37**
- ✅ **ZAMORA = 49**

### 2. Sección "MIS PEDIDOS" Completa
- ✅ **Estado de fabricación** visible con badge (Confirmado → En Producción → Listo → Enviado)
- ✅ **Sincronización automática** con fabrica_orders
- ✅ **Botón Imprimir** con formato profesional
- ✅ **Limpieza automática del presupuesto** al confirmar pedido (CORREGIDO)

### 3. Botón Ayuda
- ✅ Visible para todos excepto Tiendas y Montadores

### 4. Otras mejoras
- ✅ Selector de fábrica en "Rol y Jerarquía"
- ✅ BD fortalecida con índices MongoDB
- ✅ Email fallback a Resend
- ✅ Modal CRM scrolleable

---

## ✅ COMPLETADO EN SESIÓN ANTERIOR (18 Marzo 2026)

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
- `reportlab`: PDF generation (backend)
- `sendgrid`: Email service

---

## PRÓXIMOS PASOS RECOMENDADOS (P3 - Backlog)
1. ~~**Optimización de tableros**~~ ✅ COMPLETADO
2. ~~**Informe de producción PDF**~~ ✅ COMPLETADO
3. ~~**Envío copias con adjuntos**~~ ✅ COMPLETADO
4. ~~**Manual de usuario**~~ ✅ COMPLETADO v2.0
5. ~~**Refactorización frontend**~~ ✅ PARCIAL (-480 líneas)
6. **Refactorización backend** - Extraer más lógica de server.py a routers
7. **Notificaciones** - Email cuando cambie estado de orden
8. **Integración facturación externa**
9. **Alertas automáticas producción urgente**
10. **Permisos granulares por fábrica** para rol Director Fábrica

