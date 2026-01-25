# LUIGGI HOME - ERP/CRM para Presupuestos de Cocinas y Armarios

## Última Actualización: 25/01/2026

---

## RESUMEN DEL SISTEMA

LUIGGI HOME es un ERP/CRM completo para la gestión de presupuestos de cocinas y armarios, incluyendo:
- Gestión de usuarios con roles (Admin, Comercial, Tienda, Colaborador Comercial)
- Presupuestador técnico con cálculo automático de precios
- Módulo de Armarios con diseñador visual, despiece e IA
- CRM completo con calendario, contactos y oportunidades
- Digitalizador de borradores con IA
- Importador de catálogo IA
- Sistema de backups automáticos

---

## ESTADO ACTUAL - 25/01/2026

### ✅ COMPLETADO HOY (Funciones IA Armarios)

| # | Funcionalidad | Estado | Descripción |
|---|--------------|--------|-------------|
| 1 | **IA Configuración** | ✅ PROBADO | Modal para describir necesidades y la IA configura el armario automáticamente |
| 2 | **IA Render Realista** | ✅ PROBADO | Genera imágenes fotorrealistas del armario usando Gemini Nano Banana |
| 3 | **Despiece Editable** | ✅ PROBADO | Tabla con botones mover arriba/abajo, duplicar, eliminar accesorios |
| 4 | **Añadir Accesorio** | ✅ PROBADO | Botón "+ AÑADIR ACCESORIO" para agregar filas personalizadas |
| 5 | **PDF Despiece** | ✅ PROBADO | Exportar lista de materiales a PDF |
| 6 | **Guardar/Cargar Proyectos** | ✅ PROBADO | API completa para gestión de proyectos de armarios |

### ✅ COMPLETADO ANTERIORMENTE

| # | Funcionalidad | Descripción |
|---|--------------|-------------|
| 1 | **Importación masiva de productos** | 1,027 productos importados desde tarifa técnica |
| 2 | **BAJOS GOLA** | 291 productos BAJO GOLA importados |
| 3 | **ALTOS GOLA** | 465 productos ALTO GOLA importados |
| 4 | **COLUMNAS GOLA** | 107 productos COLUMNA GOLA importados |
| 5 | **Colores FINSA 2025** | 150+ colores del catálogo oficial organizados en 14 categorías |
| 6 | **Trasera 8mm** | Corregido en Armarios y Muebles de cocina |
| 7 | **Persistencia Logo** | Logo de empresa se guarda correctamente en settings |

---

## MÓDULO ARMARIOS - FUNCIONES IA

### Configuración IA (gemini-3-flash-preview)
- Modal con campo de texto para describir necesidades
- Ejemplos rápidos predefinidos
- Genera configuración JSON con módulos, puertas, accesorios
- Aplica automáticamente al diseñador visual

### Render Realista IA (gemini-3-pro-image-preview - Nano Banana)
- Selección de estilo de habitación (Moderno, Clásico, Nórdico, Minimalista, Industrial, Rústico)
- Muestra configuración actual
- Genera imagen fotorrealista descargable
- Botón para descargar la imagen

### Despiece Editable
- Lista numerada de todos los componentes
- Botones de acción por fila: mover arriba/abajo, duplicar, eliminar
- Botón "+ AÑADIR ACCESORIO" para filas personalizadas
- Edición inline de campos
- Cálculo automático de totales
- Exportación a PDF

---

## API ENDPOINTS

### Armarios - IA
- `POST /api/armarios/ia/configure` - Configurar armario con IA
- `POST /api/armarios/ia/render` - Generar render realista

### Armarios - Proyectos
- `POST /api/armarios/projects` - Crear proyecto
- `GET /api/armarios/projects` - Listar proyectos
- `GET /api/armarios/projects/{id}` - Obtener proyecto
- `PUT /api/armarios/projects/{id}` - Actualizar proyecto
- `DELETE /api/armarios/projects/{id}` - Eliminar proyecto

---

## ARQUITECTURA

```
/app
├── backend/
│   ├── server.py (~4300 líneas)
│   ├── tests/
│   │   └── test_armarios_ia.py
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── Armarios.jsx (~2700 líneas)
│       │   ├── BudgetTable.jsx
│       │   ├── CRMContacts.jsx
│       │   └── DespieceModal.jsx
│       └── services/
│           ├── api.js
│           └── pdfGenerator.js
└── memory/
    └── PRD.md
```

---

## PRÓXIMAS TAREAS

### P1 - Alta Prioridad
- [ ] Auto-etiquetar CRM cuando se guarde proyecto de Armarios/Cocina (tipo de negocio)
- [ ] Probar IA Lab - Analizador de Planos con imagen real

### P2 - Media Prioridad
- [ ] Reorganizar UI "expediente" para nuevos módulos
- [ ] Campo `catalogOrder` para ordenar productos como en PDF

### P3 - Baja Prioridad / Refactorización
- [ ] Refactorizar `server.py` (>4300 líneas) - Separar en routers
- [ ] Refactorizar `Armarios.jsx` (>2700 líneas) - Separar componentes
- [ ] Notificaciones automáticas CRM por email
- [ ] Recordatorios calendario

---

## CREDENCIALES DE PRUEBA

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| MARIO | MARIO | Admin |
| TIENDSA | TIENDSA | Tienda |
| PRESCRIPTOR1 | PRESCRIPTOR1 | Colaborador Comercial |

---

## INTEGRACIONES

- **Google Gemini** - Via emergentintegrations:
  - `gemini-3-flash-preview` - Configuración IA texto
  - `gemini-3-pro-image-preview` (Nano Banana) - Render realista
- **SendGrid** - Envío de backups por email
- **jsPDF** - Generación de PDF en frontend
- **MongoDB** - Base de datos principal

---

## TESTS

- `/app/backend/tests/test_armarios_ia.py` - Tests para funciones IA
- `/app/test_reports/iteration_12.json` - Último reporte de testing

---

## NOTAS TÉCNICAS

### Modelos Gemini Correctos
- Texto: `gemini-3-flash-preview` (NO `gemini-3-flash`)
- Imágenes: `gemini-3-pro-image-preview` (Nano Banana)

### Emergent LLM Key
- Usar `EMERGENT_LLM_KEY` del archivo `.env`
- Clave universal para OpenAI, Anthropic, Gemini
