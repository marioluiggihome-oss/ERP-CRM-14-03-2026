# LUIGGI HOME - ERP/CRM para Presupuestos de Cocinas

## Descripción del Producto
Sistema ERP/CRM completo para la gestión de presupuestos de cocinas industriales, incluyendo catálogo de productos, cálculo de precios por zonas geográficas, gestión de usuarios jerárquica, y sistema de backup automatizado.

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

### 6. Exportación PDF
- Generación de informe técnico
- Detalle de presupuesto completo

### 7. Sistema de Backup
- **Backups automáticos** por email (8:00 y 20:00)
- Email destino: marioluiggihome@gmail.com
- Backup manual por email
- Descarga de backup JSON
- Restauración desde archivo JSON
- Historial de backups

### 8. Telemetría IA
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

## Últimas Actualizaciones (24/01/2026)
- ✅ Reimportación completa de 3,533 productos desde catálogo PDF
- ✅ Nombres descriptivos correctos (ej: "Alto 35cm 1 Puerta 400mm Fondo Estándar")
- ✅ Precios por 12 zonas verificados
- ✅ Sistema de archivo de proyectos con filtros
- ✅ Testing completo: 25/25 backend tests passed

## Próximas Tareas (Backlog)
1. **Mejorar fiabilidad Telemetría IA** - Investigar errores API Gemini
2. **Historial de versiones** - Versionar cambios en presupuestos
3. **Dashboard de estadísticas** - Resumen de ventas/proyectos
4. **Notificaciones** - Alertas de sistema
