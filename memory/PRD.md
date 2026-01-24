# LUIGGI HOME - ERP/CRM para Presupuestos de Cocinas

## Estado Actual (Enero 2025)

### ✅ Completado
1. **MongoDB Integration** - Todos los datos persisten en base de datos
2. **Seguridad** - Contraseñas bcrypt, sin password en respuestas API
3. **Biblioteca de Proyectos** - Guardar/cargar presupuestos desde MongoDB
4. **Exportar PDF** - Botón "EXPORTAR PDF" genera y descarga presupuesto profesional
5. **Línea Manual** - Añadir conceptos manuales a presupuestos
6. **Telemetría IA** - Importar catálogos con Gemini Vision (API poco fiable)
7. **Sistema de Backup Automático**
   - Backups automáticos 2 veces al día (8:00 y 20:00)
   - Envío por email con SendGrid a marioluiggihome@gmail.com
   - Interfaz "Archivo Maestro" para backup manual
8. **Importación Masiva de Catálogo** - 1,929 productos únicos importados
   - Verificados y sin duplicados
   - Todos con 12 zonas de precio (Z1-Z12) correctamente configuradas
9. **Sistema de Archivo de Proyectos (NUEVO)**
   - Filtros: Activos / Archivados / Todos
   - Botón para archivar/desarchivar proyectos
   - Contador de proyectos por estado
10. **Márgenes Maestros Completos**
    - Valores de Punto (Montada/Despiece)
    - Incrementos Cortes Especiales (Ancho/Alto/Fondo)
    - Gestión de Armazones/Cascos

### Endpoints API
```
POST /api/auth/login        # Autenticación (bcrypt)
CRUD /api/users             # Usuarios
CRUD /api/products          # Productos (incluye bulk delete y bulk create)
CRUD /api/materials         # Materiales
CRUD /api/projects          # Proyectos/Presupuestos (con status: draft/completed/archived)
GET/PUT /api/settings       # Configuración
POST /api/analyze-product-sheets  # Telemetría IA
POST /api/backup/manual     # Backup manual por email
GET  /api/backup/download   # Descargar backup JSON
POST /api/backup/restore    # Restaurar desde JSON
GET  /api/backup/history    # Historial de backups
GET  /api/backup/status     # Estado scheduler
```

### Productos Importados
- **Total:** 1,929 productos únicos (verificados sin duplicados)
- **Categorías:** Altos, Bajos, Columnas, Semicolumnas
- **Series:** Múltiples fondos y configuraciones
- **Zonas de Precio:** Z1-Z12 completas para todos los productos

## Credenciales
- **Admin:** MARIO / MARIO
- **Email backup:** marioluiggihome@gmail.com

## Secciones Implementadas (según PowerPoint)
| Slide | Sección | Estado |
|-------|---------|--------|
| 1 | RED DISTRIBUCIÓN | ✅ |
| 2 | INVENTARIO MAESTRO | ✅ |
| 3 | MÁRGENES MAESTROS | ✅ |
| 4 | TELEMETRÍA IA | ✅ |
| 5 | IDENTIDAD | ✅ |
| 6 | ARCHIVO MAESTRO (Backup) | ✅ |
| 7 | LIBRERÍA MAESTRA | ✅ |
| 8 | MONTADA (Mesa de trabajo) | ✅ |
| 9 | PRESUPUESTO TÉCNICO | ✅ |

## Próximas Tareas (P1)
1. Mejorar estabilidad de Telemetría IA (API Gemini poco fiable)
2. Auto-guardar borrador cada 5 minutos
3. Duplicar proyecto existente

## Futuras/Backlog (P2)
1. Historial de versiones de presupuestos
2. Exportar múltiples formatos (Excel)
3. Dashboard de estadísticas

## Arquitectura
```
/app
├── backend
│   ├── .env
│   ├── requirements.txt
│   └── server.py         # FastAPI app con scheduler
└── frontend
    ├── src
    │   ├── components
    │   │   ├── App.js
    │   │   ├── BackupManager.jsx
    │   │   ├── BudgetTable.jsx
    │   │   ├── Login.jsx
    │   │   ├── ProjectLibrary.jsx  # ACTUALIZADO con filtros archivo
    │   │   └── SettingsModal.jsx
    │   ├── services
    │   │   ├── api.js
    │   │   └── pdfGenerator.js
    │   └── index.js
    └── package.json
```

## Notas Técnicas
- **Frontend Stability:** Parche aplicado en index.js para errores de React DOM
- **AI Telemetry:** API Gemini puede fallar - usar importación manual como alternativa
- **Backup:** SendGrid configurado, scheduler APScheduler funcionando
