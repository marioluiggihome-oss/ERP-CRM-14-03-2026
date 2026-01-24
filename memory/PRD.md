# LUIGGI HOME - ERP/CRM para Presupuestos de Cocinas

## Descripción del Producto
Sistema ERP/CRM completo para la gestión de presupuestos de cocinas industriales, integrado con CRM de ventas, sistema de despiece y digitalizador de borradores con IA.

## Características Implementadas ✅

### 1. Autenticación y Usuarios
- Login con credenciales (usuario/contraseña)
- Sistema de roles jerárquico: Administrador > Comercial > Tienda
- Permisos granulares por rol
- Contraseñas hasheadas con bcrypt

### 2. Inventario Maestro (3,533 productos)
- **Catálogo completo** importado desde PDF del fabricante
- **12 zonas de precio** (Z1-Z12) por producto
- **Categorías**: ALTOS, BAJOS, COLUMNAS, SEMICOLUMNAS
- **Dimensiones en cm** (ancho convertido de mm a cm)
- Filtros por serie/familia y búsqueda
- CRUD completo de productos

### 3. Sistema de Presupuestos
- Mesa de trabajo interactiva
- Librería de muebles con precios por zona
- Cálculo automático de totales
- Selector de acabado y armazón
- Línea manual para items personalizados

### 4. Sistema de Archivo de Proyectos
- Guardar/cargar presupuestos
- Filtros: Activos, Archivados, Todos
- Vincular presupuestos con oportunidades CRM

### 5. Exportación PDF
- Generación de informe técnico

### 6. Sistema de Backup
- **Backups automáticos** (8:00 y 20:00)
- Backup manual por email
- Restauración desde JSON

### 7. CRM de Ventas
- Dashboard con métricas
- Pipeline Kanban (5 etapas)
- Gestión de contactos
- Actividades y tareas

### 8. Sistema de Despiece (Bill of Materials)
- Cálculo automático de componentes
- **Orden de Montaje**: Lista de componentes por mueble
- **Lista de Corte**: Tabla de piezas para producción
- Dimensiones editables

### 9. 🆕 Digitalizador de Borradores - NUEVO
Herramienta de OCR/IA para digitalizar presupuestos escritos a mano.

#### Funcionalidades:
- **Subir foto/PDF** de presupuesto manuscrito
- **IA Gemini Vision** extrae líneas automáticamente
- **Líneas editables**: cantidad, descripción, precio, descuento
- **Descuento Global**: aplica a todas las líneas de IA
- **Líneas Manuales**: con descuento independiente
- **Cálculo de totales** con IVA configurable (0%, 4%, 10%, 21%)
- **Exportar PDF** (impresión)
- **Exportar CSV** para máquina seccionadora

#### Formato CSV Máquina:
```csv
"CÓDIGO";ESPESOR;"DESCRIPCIÓN";LARGO;ALTO;ORIENT;0;0;"CÓDIGO"
"40-ESTEITEX16";16,0;"Costado 113 x 60";113;60;1;0;0;"40-ESTEITEX16"
```

#### Permiso:
- Solo usuarios con `canUseDigitalizador` o Admin pueden acceder

## Permisos de Usuario
| Permiso | Descripción |
|---------|-------------|
| canUseAIAnalysis | Acceso a IA Lab |
| canSeeCost | Ver costos |
| canSeeRetail | Ver precios |
| canViewTechnicalDespiece | Ver informes técnicos |
| canManageArticles | Gestionar inventario |
| canAccessCRM | Acceso al CRM |
| **canUseDigitalizador** | **Digitalizador de Borradores** |
| useCustomBranding | Personalizar interfaz |
| canChangeLogo | Modificar logo |

## Stack Técnico
- **Frontend**: React, TailwindCSS, Lucide Icons
- **Backend**: Python, FastAPI, Pydantic
- **Database**: MongoDB (pymongo)
- **IA**: Gemini Vision (emergentintegrations)
- **Email**: SendGrid
- **PDF**: jspdf, html2canvas

## APIs Principales

### Digitalizador (nuevo)
- `POST /api/digitalizador/analyze` - Analiza imagen con Gemini Vision
- `POST /api/digitalizador/export-csv` - Exporta a CSV para máquina seccionadora

### Despiece
- `POST /api/despiece/calculate` - Calcula bill of materials

### CRM
- `GET/POST /api/crm/contacts` - Contactos
- `GET/POST /api/crm/opportunities` - Oportunidades
- `GET/POST /api/crm/activities` - Actividades
- `GET /api/crm/dashboard` - Dashboard

## Credenciales de Prueba
- **Usuario**: MARIO
- **Contraseña**: MARIO (Admin)

## Menú Lateral (orden)
1. CRM
2. PRESUPUESTO
3. IA LAB
4. ARCHIVO
5. **DIGITALIZADOR** (nuevo)
6. COPIA SEGURIDAD
7. MASTER
8. SALIR

## Últimas Actualizaciones (24/01/2026)
- ✅ Implementación del Sistema de Despiece
- ✅ Corrección de visualización de dimensiones (mm → cm)
- ✅ **Digitalizador de Borradores completo**
- ✅ Exportación CSV para máquina seccionadora
- ✅ Permiso canUseDigitalizador

## Testing Status
- **iteration_6.json**: Despiece - 8/8 tests passed
- **iteration_7.json**: Digitalizador - 11/11 tests passed (100%)

## Próximas Tareas (Backlog)
1. Mejorar OCR del Digitalizador con más formatos
2. Historial persistente del Digitalizador
3. Exportar Despiece a Excel
4. Calendario CRM
5. Refactorizar server.py en módulos
