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

### 3. Márgenes Maestros
- Valor de punto por módulo (€/punto)
- Incrementos por cortes especiales (ancho, alto, fondo)
- Gestión de armazones/cascos con incrementos fijos

### 4. Telemetría IA
- Importación de productos desde imágenes de fichas técnicas
- Análisis con Google Gemini Vision API
- Extracción automática: código, nombre, dimensiones, puntos por zona

## Arquitectura Técnica

### Frontend (React + TailwindCSS)
```
/app/frontend/src/
├── App.js                    # Estado principal, routing
├── components/
│   ├── BudgetTable.jsx       # Mesa de trabajo/presupuesto
│   ├── Login.jsx             # Autenticación
│   ├── SettingsModal.jsx     # Panel Maestro (usuarios, inventario, márgenes)
│   ├── TelemetryAI.jsx       # Importación IA de productos
│   ├── Visualizer.jsx        # IA Lab
│   ├── ProjectLibrary.jsx    # Archivo de proyectos
│   └── ManufacturingReport.jsx
├── constants.js              # Catálogos base, acabados, materiales
└── mock.js                   # Usuario admin por defecto
```

### Backend (FastAPI + MongoDB)
```
/app/backend/
├── server.py                 # API endpoints
├── requirements.txt          # Dependencias Python
└── .env                      # Configuración (MONGO_URL, EMERGENT_LLM_KEY)
```

### Endpoints API
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | /api/ | Health check |
| POST | /api/status | Crear status check |
| GET | /api/status | Obtener status checks |
| POST | /api/analyze-product-sheets | **Telemetría IA** - Analiza imágenes con Gemini Vision |

## Estado Actual

### ✅ Completado (23 Enero 2026)
1. **Sistema de Login** - MARIO/1234 (Admin por defecto)
2. **Panel Maestro completo:**
   - Red Distribución (gestión de usuarios con roles)
   - Inventario (catálogos Montada y Despiece)
   - Márgenes (valores de punto, cortes especiales, armazones)
   - Identidad (logo, color de marca)
3. **Telemetría IA:**
   - Frontend con selector de módulo y subida de archivos
   - Backend con endpoint `/api/analyze-product-sheets`
   - Integración con Gemini Vision via `emergentintegrations`
4. **Permisos por rol:**
   - Tiendas no ven Telemetría IA ni Panel Maestro
   - Comerciales ven según permisos asignados
5. **Bug fix:** Contraseña admin corregida (mock.js)

### 🟡 Pendiente
1. **Migración a MongoDB:** Actualmente todo en localStorage
2. **Funciones del PowerPoint:** Revisar slides restantes
3. **Sistema de Archivo:** Biblioteca de proyectos completa

## Credenciales de Prueba
- **Admin:** MARIO / 1234
- **Backend URL:** https://luiggi-erp.preview.emergentagent.com

## Integraciones de Terceros
- **Google Gemini Vision (2.5 Pro)** via `emergentintegrations` con EMERGENT_LLM_KEY

## Notas Técnicas
- Datos persistidos en **localStorage** (MOCKED - sin base de datos)
- Frontend usa React hooks + TailwindCSS + Shadcn UI
- Hot reload activo en desarrollo
