# LUIGGI HOME - ERP/CRM para Presupuestos de Cocinas y Armarios

## Última Actualización: 25/01/2026

---

## RESUMEN DEL SISTEMA

LUIGGI HOME es un ERP/CRM completo para la gestión de presupuestos de cocinas y armarios, incluyendo:
- Gestión de usuarios con roles (Admin, Comercial/Representante, Tienda/Punto de Venta, Colaborador Comercial)
- Presupuestador técnico con cálculo automático de precios
- Módulo de Armarios con diseñador visual, despiece e IA
- CRM completo con calendario, contactos y oportunidades (con aislamiento de datos por comercial)
- Digitalizador de borradores con IA
- Importador de catálogo IA
- Sistema de backups automáticos

---

## CORRECCIONES IMPLEMENTADAS - 25/01/2026

### ✅ P0 - Aislamiento de Datos CRM (Seguridad)
| Corrección | Estado | Descripción |
|------------|--------|-------------|
| Backend filtering | ✅ COMPLETADO | Endpoints `/api/crm/contacts`, `/api/crm/opportunities`, `/api/crm/dashboard` ahora aceptan `assignedTo` e `isAdmin` |
| ContactModel.assignedTo | ✅ COMPLETADO | Campo añadido para asignar contactos a comerciales |
| Frontend CRM filtering | ✅ COMPLETADO | Componentes CRM filtran datos según el usuario |

### ✅ P1 - Nuevo Rol Tienda/Punto de Venta
| Corrección | Estado | Descripción |
|------------|--------|-------------|
| Campo isTienda | ✅ COMPLETADO | Añadido a UserModel, UserCreate, UserUpdate, UserResponse |
| Sidebar visibility | ✅ COMPLETADO | Usuarios Tienda solo ven "Presupuesto" y "Salir" |
| No acceso a CRM | ✅ COMPLETADO | Tienda no puede ver CRM, IA Lab, Digitalizador, Master |

### ✅ P2 - Permisos Armarios
| Corrección | Estado | Descripción |
|------------|--------|-------------|
| canAccessArmarios | ✅ YA EXISTÍA | Permiso para acceso al módulo Armarios |
| Selector en usuario | ✅ COMPLETADO | Checkbox visible en formulario de creación de usuario |

### ✅ P2 - UI Panel Maestro
| Corrección | Estado | Descripción |
|------------|--------|-------------|
| Quitar iconos | ✅ COMPLETADO | Pestañas del Panel Maestro sin iconos (más espacio) |
| Texto "Asignar a Comercial / Representante" | ✅ COMPLETADO | Cambiado de "Asignar a Comercial" |

### ✅ P2 - PDF Mejoras
| Corrección | Estado | Descripción |
|------------|--------|-------------|
| Logo proporcional | ✅ COMPLETADO | Logo mantiene aspect ratio, max 50x25px |
| Espacio superior | ✅ COMPLETADO | yPos reducido de 20 a 15, layout más compacto |
| Cabecera compacta | ✅ COMPLETADO | Tamaños de fuente optimizados |

---

## ROLES DE USUARIO

| Rol | Acceso | Descripción |
|-----|--------|-------------|
| **Admin Maestro** | Todo | Control total del sistema |
| **Comercial/Representante** | CRM (solo sus datos), Presupuesto, Armarios*, Master | Gestiona sus propios clientes y tiendas |
| **Tienda/Punto de Venta** | Solo Presupuesto | Acceso limitado solo al presupuestador |
| **Colaborador Comercial** | Agenda, Aportar contactos | Solo puede aportar contactos al CRM |

*Armarios requiere permiso `canAccessArmarios`

---

## API ENDPOINTS (CRM con filtrado)

### Contactos
- `GET /api/crm/contacts?assignedTo={userId}&isAdmin={bool}` - Lista contactos filtrados
- `POST /api/crm/contacts` - Crear contacto (incluye campo assignedTo)
- `PUT /api/crm/contacts/{id}` - Actualizar contacto

### Oportunidades  
- `GET /api/crm/opportunities?assignedTo={userId}&isAdmin={bool}` - Lista oportunidades filtradas

### Dashboard
- `GET /api/crm/dashboard?assignedTo={userId}&isAdmin={bool}` - Estadísticas filtradas

---

## ARQUITECTURA

```
/app
├── backend/
│   ├── server.py (~4400 líneas)
│   │   ├── UserModel (isTienda, canAccessArmarios)
│   │   ├── ContactModel (assignedTo)
│   │   └── CRM endpoints con filtrado
│   └── tests/
│       └── test_crm_isolation_roles.py
├── frontend/
│   └── src/
│       ├── App.js (sidebar con permisos isTienda)
│       ├── components/
│       │   ├── CRMContacts.jsx (filtrado por usuario)
│       │   ├── CRMPipeline.jsx (filtrado por usuario)
│       │   ├── CRMDashboard.jsx (filtrado por usuario)
│       │   └── SettingsModal.jsx (tabs sin iconos, isTienda checkbox)
│       └── services/
│           ├── api.js (CRM API con options)
│           └── pdfGenerator.js (logo proporcional)
└── memory/
    └── PRD.md
```

---

## PRÓXIMAS TAREAS

### P1 - Próximo Sprint
- [ ] Auto-etiquetar CRM con tipo de negocio al guardar proyecto
- [ ] Probar IA Lab - Analizador de Planos con imagen real
- [ ] Exportar secciones a ventana emergente/pantalla completa

### P2 - Media Prioridad
- [ ] Quitar datos innecesarios de PDF exportado (personalizable)
- [ ] Reorganizar UI campo "expediente" para módulos nuevos

### P3 - Refactorización
- [ ] Separar server.py en routers (>4400 líneas)
- [ ] Separar Armarios.jsx en componentes (>2700 líneas)

---

## CREDENCIALES DE PRUEBA

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| MARIO | MARIO | Admin |
| TIENDSA | TIENDSA | Tienda |
| COMSA | COMERCIAL | Comercial |
| PRESCRIPTOR1 | PRESCRIPTOR1 | Colaborador Comercial |

---

## TESTS

- `/app/backend/tests/test_crm_isolation_roles.py` - Tests aislamiento CRM
- `/app/backend/tests/test_armarios_ia.py` - Tests funciones IA Armarios
- `/app/test_reports/iteration_13.json` - Último reporte de testing

---

## NOTAS TÉCNICAS

### Filtrado CRM
Los endpoints CRM filtran por `assignedTo` cuando:
- `isAdmin` = false
- `assignedTo` tiene valor

Los usuarios Admin siempre ven todos los datos.

### Modelos Gemini
- Texto: `gemini-3-flash-preview`
- Imágenes: `gemini-3-pro-image-preview` (Nano Banana)
