# LUIGGI HOME - ERP/CRM para Presupuestos de Cocinas

## Estado Actual (Diciembre 2025)

### ✅ Completado
1. **MongoDB Integration** - Todos los datos persisten en base de datos
2. **Seguridad** - Contraseñas bcrypt, sin password en respuestas API
3. **Biblioteca de Proyectos** - Guardar/cargar presupuestos desde MongoDB
4. **Exportar PDF** - Botón "EXPORTAR PDF" genera y descarga presupuesto profesional (PROBADO ✓)
5. **Línea Manual** - Añadir conceptos manuales a presupuestos
6. **Telemetría IA** - Importar catálogos con Gemini Vision

### Endpoints API
```
POST /api/auth/login        # Autenticación (bcrypt)
CRUD /api/users             # Usuarios
CRUD /api/products          # Productos (incluye bulk delete)
CRUD /api/materials         # Materiales
CRUD /api/projects          # Proyectos/Presupuestos
GET/PUT /api/settings       # Configuración
POST /api/analyze-product-sheets  # Telemetría IA
```

### Funcionalidad PDF (Implementado y Probado)
- Genera PDF profesional con jspdf + jspdf-autotable v5
- Incluye: logo empresa, cliente, items montada/despiece, especificaciones, totales
- Botón "EXPORTAR PDF" en la barra superior del presupuesto
- Archivo: `/app/frontend/src/services/pdfGenerator.js`

## Credenciales
- **Admin:** MARIO / MARIO

## Próximas Tareas (P1)
1. Revisar características del PowerPoint `SECCIONES BLINDADAS.pptx`
2. Auto-guardar borrador cada 5 minutos
3. Duplicar proyecto existente

## Futuras/Backlog (P2)
1. Sistema de Archivo de Proyectos ("ARCHIVO")
2. Historial de versiones de presupuestos
