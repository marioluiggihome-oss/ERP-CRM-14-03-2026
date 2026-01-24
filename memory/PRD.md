# LUIGGI HOME - ERP/CRM para Presupuestos de Cocinas

## Estado Actual (Diciembre 2025)

### ✅ Completado
1. **MongoDB Integration** - Todos los datos persisten en base de datos
2. **Seguridad** - Contraseñas bcrypt, sin password en respuestas API
3. **Biblioteca de Proyectos** - Guardar/cargar presupuestos desde MongoDB
4. **Exportar PDF** - Botón "EXPORTAR PDF" genera y descarga presupuesto profesional
5. **Línea Manual** - Añadir conceptos manuales a presupuestos
6. **Telemetría IA** - Importar catálogos con Gemini Vision (MEJORADO ✓)
   - Log de detección en tiempo real
   - Detección de duplicados (🟠 DUPLICADO - naranja)  
   - Detección de nuevos (🟢 NUEVO - verde)
   - Barra de progreso durante importación
   - Resumen final con contadores
7. **Sistema de Backup Automático**
   - Backups automáticos 2 veces al día (8:00 y 20:00)
   - Envío por email con SendGrid a marioluiggihome@gmail.com
   - Interfaz "Archivo Maestro" para backup manual
8. **Importación de Catálogo** - 22 productos ALTOS 35 FONDO 58 importados

### Endpoints API
```
POST /api/auth/login        # Autenticación (bcrypt)
CRUD /api/users             # Usuarios
CRUD /api/products          # Productos (incluye bulk delete y bulk create)
CRUD /api/materials         # Materiales
CRUD /api/projects          # Proyectos/Presupuestos
GET/PUT /api/settings       # Configuración
POST /api/analyze-product-sheets  # Telemetría IA
POST /api/backup/manual     # Backup manual por email
GET  /api/backup/download   # Descargar backup JSON
POST /api/backup/restore    # Restaurar desde JSON
GET  /api/backup/history    # Historial de backups
GET  /api/backup/status     # Estado scheduler
```

### Productos Importados (MONTADA)
- **ALTOS 35 FONDO 58** (11 productos): Alto 1/2 Puertas
- **ALTOS 35 FONDO 58 VITRINA** (11 productos): Alto 1/2 Vitrinas
- Total: 22 productos con zonas de precio Z1-Z12

## Credenciales
- **Admin:** MARIO / MARIO
- **Email backup:** marioluiggihome@gmail.com

## Próximas Tareas (P1)
1. Importar más páginas del catálogo (si el usuario las proporciona)
2. Auto-guardar borrador cada 5 minutos
3. Duplicar proyecto existente

## Futuras/Backlog (P2)
1. Sistema de Archivo de Proyectos separado
2. Historial de versiones de presupuestos
