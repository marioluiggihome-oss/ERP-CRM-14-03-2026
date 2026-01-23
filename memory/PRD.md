# LUIGGI HOME - ERP/CRM para Presupuestos de Cocinas

## Problema Original
ERP/CRM completo para gestión de presupuestos de cocinas con sistema de usuarios jerárquico, inventario dual, y funcionalidades de IA.

## Arquitectura Técnica

### Backend (FastAPI + MongoDB)
```
Endpoints:
├── POST /api/auth/login        # Autenticación (bcrypt)
├── POST /api/init              # Crear admin
├── CRUD /api/users             # Usuarios (sin password en respuestas)
├── CRUD /api/products          # Productos
├── CRUD /api/materials         # Materiales
├── GET/PUT /api/settings       # Configuración global
├── CRUD /api/projects          # Proyectos/Presupuestos ← NUEVO
└── POST /api/analyze-product-sheets  # Telemetría IA
```

### Frontend (React + TailwindCSS)
```
/app/frontend/src/
├── App.js                 # Estado principal
├── services/api.js        # Servicio API (incluye projectsAPI)
├── components/
│   ├── ProjectLibrary.jsx # Biblioteca de proyectos ← ACTUALIZADO
│   ├── Login.jsx          # Login via API
│   ├── SettingsModal.jsx  # Panel Maestro
│   └── ...
```

## Estado Actual (23 Enero 2026)

### ✅ Completado
1. **Migración a MongoDB** - Todos los datos persisten
2. **Seguridad** - Contraseñas bcrypt, sin password en respuestas
3. **API de Proyectos** - CRUD completo para guardar presupuestos
4. **Biblioteca de Proyectos conectada a MongoDB:**
   - Guardar presupuesto actual
   - Listar proyectos guardados
   - Cargar proyecto en mesa de trabajo
   - Eliminar proyectos
   - Búsqueda por nombre/número

### Flujo de Proyectos
1. Usuario crea presupuesto en "Presupuesto" (mesa de trabajo)
2. Click en "Archivo" → "Guardar Actual"
3. El proyecto se guarda en MongoDB con:
   - Items de Montada y Despiece
   - Datos del cliente
   - Colores y materiales
   - Total PVP
4. Puede recargar proyectos guardados en cualquier momento

## Credenciales
- **Admin:** MARIO / MARIO

## Tests Verificados
- Login con bcrypt: ✅
- CRUD proyectos: ✅
- Frontend conectado: ✅

## Próximas Tareas
1. Exportar presupuesto a PDF
2. Funciones restantes del PowerPoint
3. Auto-guardar borrador cada X minutos
