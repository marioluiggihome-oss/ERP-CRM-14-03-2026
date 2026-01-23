# LUIGGI HOME - ERP/CRM para Presupuestos de Cocinas

## Problema Original
Clonar y mejorar la aplicación LUIGGI HOME, un ERP/CRM completo para la gestión de presupuestos de cocinas con sistema de usuarios jerárquico, gestión de inventario dual (Cocina Montada y Formato Despiece), y funcionalidades de IA para digitalización de catálogos.

## Arquitectura Técnica

### Backend (FastAPI + MongoDB)
```
Endpoints:
├── POST /api/auth/login        # Autenticación con bcrypt
├── POST /api/init              # Crear admin si no existe
├── GET/POST/PUT/DELETE /api/users       # CRUD usuarios (sin password en respuestas)
├── GET/POST/PUT/DELETE /api/products    # CRUD productos
├── DELETE /api/products/bulk/delete     # Borrado masivo
├── GET/POST/PUT/DELETE /api/materials   # CRUD materiales
├── GET/PUT /api/settings                # Configuración global
├── GET/POST/PUT/DELETE /api/projects    # CRUD proyectos/presupuestos
└── POST /api/analyze-product-sheets     # Telemetría IA (Gemini Vision)
```

### Frontend (React + TailwindCSS)
```
/app/frontend/src/
├── App.js                 # Estado principal, carga desde API
├── services/api.js        # Servicio API completo
├── components/
│   ├── Login.jsx          # Autenticación via API
│   ├── SettingsModal.jsx  # Panel Maestro (CRUD via API)
│   ├── TelemetryAI.jsx    # Importación IA
│   └── ...
└── constants.js           # Datos base
```

## Mejoras de Seguridad Implementadas (23 Enero 2026)

### ✅ Contraseñas Hasheadas
- Todas las contraseñas se almacenan con **bcrypt**
- La verificación soporta contraseñas antiguas (migración automática)
- El endpoint `/api/init` hashea automáticamente contraseñas en texto plano

### ✅ Password Excluido de Respuestas
- GET /api/users → No incluye password
- POST /api/auth/login → No incluye password en el usuario
- GET /api/users/{id} → No incluye password
- Modelo `UserResponse` separado del modelo interno

### ✅ Endpoints de Proyectos
- CRUD completo para guardar presupuestos en MongoDB
- Los proyectos incluyen: items, cliente, colores, materiales
- Filtrado por usuario (user_id)

## Estado Actual

### ✅ Completado
1. **Migración a MongoDB** - Todos los datos persisten
2. **Seguridad de contraseñas** - bcrypt + exclusión de respuestas
3. **API REST completa** - Usuarios, productos, materiales, settings, proyectos
4. **Telemetría IA** - Gemini Vision para importar productos
5. **Control de permisos** - Telemetría IA y IA Lab controlados

### 🟡 Pendiente Frontend
- Conectar ProjectLibrary.jsx a la API de proyectos
- Auto-guardar presupuesto actual en MongoDB

## Credenciales de Prueba
- **Admin:** MARIO / MARIO

## Integraciones
- **Google Gemini Vision (2.5 Pro)** via `emergentintegrations`

## Tests
- **Backend:** 25+ tests pasando (pytest)
- **Reporte:** `/app/test_reports/iteration_1.json`
