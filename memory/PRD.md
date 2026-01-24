# LUIGGI HOME - ERP/CRM para Presupuestos de Cocinas

## Descripción del Producto
Sistema ERP/CRM completo para la gestión de presupuestos de cocinas industriales, ahora integrado con un CRM de ventas completo. Incluye catálogo de productos, cálculo de precios por zonas geográficas, gestión de usuarios jerárquica, sistema de backup automatizado, y pipeline de ventas.

## Características Implementadas ✅

### 1. Autenticación y Usuarios
- Login con credenciales (usuario/contraseña)
- Sistema de roles jerárquico: Administrador > Comercial > Tienda
- Permisos granulares por rol
- Contraseñas hasheadas con bcrypt

### 2. Inventario Maestro (3,533 productos)
- **Catálogo completo** importado desde PDF del fabricante
- **12 zonas de precio** (Z1-Z12) por producto
- **Categorías**: ALTOS (2175), BAJOS (608), COLUMNAS (585), SEMICOLUMNAS (163)
- **Tipos**: Programa Estándar, Programa GOLA
- Filtros por serie/familia y búsqueda
- CRUD completo de productos
- Eliminación masiva

### 3. Márgenes Maestros
- Valor de punto configurable (Montada/Despiece)
- Incrementos por corte (Ancho, Alto, Fondo)
- Gestión de armazones/cascos

### 4. Sistema de Presupuestos
- Mesa de trabajo interactiva
- Librería de 3,533 muebles con precios por zona
- Cálculo automático de totales
- Selector de acabado y armazón
- Línea manual para items personalizados

### 5. Sistema de Archivo de Proyectos
- Guardar/cargar presupuestos
- **Filtros**: Activos, Archivados, Todos
- Archivar/desarchivar proyectos
- Búsqueda por nombre/número
- **Vincular presupuestos con oportunidades CRM**

### 6. Exportación PDF
- Generación de informe técnico
- Detalle de presupuesto completo

### 7. Sistema de Backup
- **Backups automáticos** por email (8:00 y 20:00)
- Email destino: marioluiggihome@gmail.com
- Backup manual por email
- Descarga de backup JSON
- Restauración desde archivo JSON

### 8. 🆕 CRM de Ventas (INTEGRADO)
#### Dashboard CRM
- Métricas en tiempo real: Contactos, Oportunidades, Pipeline
- Top oportunidades
- Próximas actividades
- Actividad reciente

#### Pipeline de Ventas (Embudo)
- **5 Etapas**: Nuevo Lead → Contactado → Propuesta → Negociación → Ganada
- Vista Kanban con drag & drop
- Valor y probabilidad por etapa
- Vinculación con presupuestos

#### Gestión de Contactos
- CRUD completo de contactos
- Filtros por estado (Lead, Activo, Cliente, Inactivo)
- Búsqueda por nombre, empresa, email
- Vinculación automática con clientes de presupuestos

#### Actividades y Tareas
- Tipos: Llamada, Reunión, Email, Tarea, Nota
- Fecha y hora de vencimiento
- Prioridad (baja, media, alta)
- Estado completado/pendiente

### 9. Telemetría IA
- Importación de catálogos mediante Gemini Vision
- Detección de productos nuevos vs duplicados
- (API externa puede ser inestable)

## Stack Técnico
- **Frontend**: React, TailwindCSS, Lucide Icons
- **Backend**: Python, FastAPI, Pydantic
- **Database**: MongoDB (pymongo)
- **Email**: SendGrid
- **PDF**: jspdf, html2canvas, pymupdf
- **Scheduler**: APScheduler

## Credenciales de Prueba
- **Usuario**: MARIO
- **Contraseña**: MARIO (Admin)

## Estructura de Base de Datos
- **products**: 3,533 documentos (código, nombre, categoría, serie, dimensiones, zonePoints Z1-Z12)
- **users**: 3 usuarios (admin + comerciales)
- **projects**: Presupuestos guardados
- **materials**: Materiales/armazones
- **settings**: Configuración del sistema
- **contacts**: Contactos del CRM
- **opportunities**: Oportunidades de venta
- **activities**: Actividades y tareas CRM

## APIs del CRM
- `GET/POST /api/crm/contacts` - Gestión de contactos
- `GET/POST /api/crm/opportunities` - Pipeline de ventas
- `POST /api/crm/opportunities/from-project/{id}` - Crear oportunidad desde presupuesto
- `GET/POST /api/crm/activities` - Actividades y tareas
- `GET /api/crm/dashboard` - Métricas del dashboard

## Últimas Actualizaciones (24/01/2026)
- ✅ Integración completa del CRM de ventas
- ✅ Dashboard CRM con métricas en tiempo real
- ✅ Pipeline Kanban con 5 etapas
- ✅ Gestión de contactos con filtros y búsqueda
- ✅ Vinculación presupuestos → oportunidades
- ✅ Testing completo: 16/16 tests CRM passed

## Próximas Tareas (Backlog)
1. **Calendario CRM** - Vista de calendario para actividades
2. **Informes CRM** - Dashboard de estadísticas de ventas
3. **Notificaciones** - Alertas de actividades pendientes
4. **Mejorar fiabilidad Telemetría IA** - Investigar errores API Gemini
