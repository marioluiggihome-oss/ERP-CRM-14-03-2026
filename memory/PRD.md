# LUIGGI HOME - ERP/CRM para Presupuestos de Cocinas

## Estado Actual (23 Enero 2026)

### ✅ Completado
1. **MongoDB Integration** - Todos los datos persisten en base de datos
2. **Seguridad** - Contraseñas bcrypt, sin password en respuestas API
3. **Biblioteca de Proyectos** - Guardar/cargar presupuestos desde MongoDB
4. **Exportar PDF** - Botón para descargar presupuesto como PDF profesional

### Endpoints API
```
POST /api/auth/login        # Autenticación (bcrypt)
CRUD /api/users             # Usuarios
CRUD /api/products          # Productos
CRUD /api/materials         # Materiales
CRUD /api/projects          # Proyectos/Presupuestos
GET/PUT /api/settings       # Configuración
POST /api/analyze-product-sheets  # Telemetría IA
```

### Funcionalidad PDF
- Genera PDF profesional con datos del presupuesto
- Incluye: cliente, items montada/despiece, especificaciones, totales
- Botón "EXPORTAR PDF" en la barra superior del presupuesto

## Credenciales
- **Admin:** MARIO / MARIO

## Próximas Tareas
1. Auto-guardar borrador cada 5 minutos
2. Funciones restantes del PowerPoint
3. Duplicar proyecto existente
