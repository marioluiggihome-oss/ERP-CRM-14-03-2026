# LUIGGI HOME - ERP/CRM para Presupuestos de Cocinas

## Estado Actual (Diciembre 2025)

### ✅ Completado
1. **MongoDB Integration** - Todos los datos persisten en base de datos
2. **Seguridad** - Contraseñas bcrypt, sin password en respuestas API
3. **Biblioteca de Proyectos** - Guardar/cargar presupuestos desde MongoDB
4. **Exportar PDF** - Botón "EXPORTAR PDF" genera y descarga presupuesto profesional (PROBADO ✓)
5. **Línea Manual** - Añadir conceptos manuales a presupuestos
6. **Telemetría IA** - Importar catálogos con Gemini Vision
7. **Sistema de Backup Automático** - ✅ NUEVO
   - Backups automáticos 2 veces al día (8:00 y 20:00)
   - Envío por email con SendGrid a marioluiggihome@gmail.com
   - Interfaz "Archivo Maestro" para backup manual
   - Descarga/Importación de archivos JSON

### Endpoints API
```
POST /api/auth/login        # Autenticación (bcrypt)
CRUD /api/users             # Usuarios
CRUD /api/products          # Productos (incluye bulk delete)
CRUD /api/materials         # Materiales
CRUD /api/projects          # Proyectos/Presupuestos
GET/PUT /api/settings       # Configuración
POST /api/analyze-product-sheets  # Telemetría IA

# NUEVOS - Backup
POST /api/backup/manual     # Disparar backup manual por email
GET  /api/backup/download   # Descargar backup como JSON
POST /api/backup/restore    # Restaurar desde backup JSON
GET  /api/backup/history    # Historial de backups
GET  /api/backup/status     # Estado del scheduler
```

### Sistema de Backup
- **Scheduler:** APScheduler con cron triggers a las 8:00 y 20:00
- **Email:** SendGrid API (marioluiggihome@gmail.com)
- **Archivos:** `/app/backend/server.py` (endpoints y scheduler)
- **Frontend:** `/app/frontend/src/components/BackupManager.jsx`
- **Colecciones exportadas:** users, products, materials, projects, settings, status_checks

### Funcionalidad PDF (Implementado y Probado)
- Genera PDF profesional con jspdf + jspdf-autotable v5
- Incluye: logo empresa, cliente, items montada/despiece, especificaciones, totales
- Botón "EXPORTAR PDF" en la barra superior del presupuesto
- Archivo: `/app/frontend/src/services/pdfGenerator.js`

## Credenciales
- **Admin:** MARIO / MARIO
- **Email backup:** marioluiggihome@gmail.com

## Próximas Tareas (P1)
1. Revisar características del PowerPoint `SECCIONES BLINDADAS.pptx`
2. Auto-guardar borrador cada 5 minutos
3. Duplicar proyecto existente

## Futuras/Backlog (P2)
1. Sistema de Archivo de Proyectos ("ARCHIVO") - separar de biblioteca
2. Historial de versiones de presupuestos
