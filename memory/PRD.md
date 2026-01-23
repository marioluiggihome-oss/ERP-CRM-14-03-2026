# LUIGGI HOME - ERP/CRM para Presupuestos de Cocinas

## Problema Original
Clonar y mejorar la aplicación LUIGGI HOME, un ERP/CRM completo para la gestión de presupuestos de cocinas con sistema de usuarios jerárquico, gestión de inventario dual (Cocina Montada y Formato Despiece), y funcionalidades de IA para digitalización de catálogos.

## Requisitos del Producto

### 1. Sistema de Usuarios (Red Distribución)
- **Administrador:** Control total del sistema
- **Comercial:** Gestiona tiendas asignadas, puede ver inventario y márgenes si tiene permisos
- **Tienda:** Acceso limitado, solo módulos asignados

### 2. Gestión de Inventario (Inventario Maestro)
- **Cocina Montada:** 12 zonas de precio (Z1-Z12)
- **Formato Despiece:** 1 punto base único
- Catálogos independientes con contadores dinámicos
- Borrado masivo de productos

### 3. Márgenes Maestros
- Valor de punto por módulo (€/punto)
- Incrementos por cortes especiales (ancho, alto, fondo)
- Gestión de armazones/cascos con incrementos fijos

### 4. Telemetría IA
- Importación de productos desde imágenes de fichas técnicas
- Análisis con Google Gemini Vision API (2.5 Pro)
- Extracción automática: código, nombre, dimensiones, puntos por zona

### 5. Control de Permisos
- Telemetría IA: visible solo para Admin o usuarios con `canManageArticles`
- IA Lab: visible solo para Admin o usuarios con `canUseAIAnalysis`

## Arquitectura Técnica

### Frontend (React + TailwindCSS)
```
/app/frontend/src/
├── App.js                    # Estado principal, carga datos desde API
├── services/
│   └── api.js                # Servicio API para comunicación con backend
├── components/
│   ├── BudgetTable.jsx       # Mesa de trabajo/presupuesto
│   ├── Login.jsx             # Autenticación via API
│   ├── SettingsModal.jsx     # Panel Maestro (CRUD via API)
│   ├── TelemetryAI.jsx       # Importación IA de productos
│   └── ...
├── constants.js              # Catálogos base, acabados, materiales
└── mock.js                   # Usuario admin por defecto (fallback)
```

### Backend (FastAPI + MongoDB)
```
/app/backend/
├── server.py                 # API completa con todos los endpoints
├── tests/
│   └── test_luiggi_crud.py   # Tests exhaustivos (25 tests)
├── requirements.txt
└── .env                      # MONGO_URL, EMERGENT_LLM_KEY
```

### Endpoints API
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | /api/auth/login | Autenticación |
| POST | /api/init | Crear admin si no existe |
| GET/POST/PUT/DELETE | /api/users | CRUD usuarios |
| GET/POST/PUT/DELETE | /api/products | CRUD productos |
| DELETE | /api/products/bulk/delete | Borrado masivo |
| GET/POST/PUT/DELETE | /api/materials | CRUD materiales |
| GET/PUT | /api/settings | Configuración global |
| POST | /api/analyze-product-sheets | Telemetría IA (Gemini Vision) |

## Estado Actual

### ✅ Completado (23 Enero 2026)
1. **Migración a MongoDB** - Todos los datos persisten en base de datos
2. **API REST completa** - Endpoints CRUD para todas las entidades
3. **Frontend conectado a API** - Login, usuarios, productos, materiales, settings
4. **Sistema de permisos** - Telemetría IA y IA Lab controlados por permisos
5. **Borrado masivo** - Productos pueden seleccionarse y eliminarse en batch
6. **Tests automatizados** - 25 tests backend pasando (100%)

### 🟡 Pendiente
1. **Hashear contraseñas** - Actualmente se guardan en texto plano
2. **Excluir password de respuestas** - El login devuelve la contraseña
3. **Implementar más funciones del PowerPoint** - Revisar slides restantes

### 🔴 Items del presupuesto
Los items del presupuesto (`budgetItems`) aún se guardan en localStorage del navegador. 
Esto es temporal y deberá migrarse a MongoDB en el futuro.

## Credenciales de Prueba
- **Admin:** MARIO / MARIO
- **Backend URL:** https://luiggi-erp.preview.emergentagent.com

## Integraciones de Terceros
- **Google Gemini Vision (2.5 Pro)** via `emergentintegrations` con EMERGENT_LLM_KEY

## Tests
- **Backend:** 25/25 tests pasando (pytest)
- **Frontend:** Todas las funcionalidades verificadas
- **Reporte:** `/app/test_reports/iteration_1.json`
