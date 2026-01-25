# LUIGGI HOME - ERP/CRM para Presupuestos de Cocinas y Armarios

## Última Actualización: 25/01/2026 (v3)

---

## RESUMEN DEL SISTEMA

LUIGGI HOME es un ERP/CRM completo para la gestión de presupuestos de cocinas y armarios, con:
- Jerarquía de usuarios: **Director Comercial > Responsable Delegación > Comercial > Tienda/Punto de Venta > Colaborador**
- **Panel de Métricas** para Director Comercial con ventas, pipeline, conversión, top performers
- Presupuestador técnico con cálculo automático de precios
- Módulo de Armarios con diseñador visual, despiece e IA
- CRM completo con calendario y aislamiento de datos por usuario
- Digitalizador de borradores con IA
- Importador de catálogo IA
- Sistema de backups automáticos

---

## NUEVA FUNCIONALIDAD - PANEL MÉTRICAS DIRECTOR COMERCIAL

### ✅ Implementado y Probado (100% Backend + 100% Frontend)

#### Endpoint: GET /api/admin/metrics
```json
{
  "global": {
    "totalValue": 0,
    "pipelineValue": 7056,
    "conversionRate": 0,
    "totalContacts": 6,
    "totalProjects": 3,
    "totalTiendas": 1,
    "totalComerciales": 2,
    "totalResponsables": 0
  },
  "byUser": [...],
  "topPerformers": [...],
  "roleBreakdown": {...}
}
```

#### UI Components
| Componente | Descripción |
|------------|-------------|
| **Tabs** | Métricas (default) / Trabajos |
| **Cards Globales** | Ventas Cerradas, Pipeline, Conversión, Contactos, Red Distribución |
| **Top Performers** | Ranking de comerciales con métricas |
| **Tabla Detallada** | Usuario, Rol, Ventas, Pipeline, Conv., Opps, Contactos, Tiendas |

---

## CORRECCIONES ANTERIORES

### PDF Mejoras
- Texto "PRESUPUESTO" más pequeño (7pt)
- Nombres capitalizados con `capitalizeName()`
- Especificaciones al final en formato horizontal

### Nuevos Roles
- Director Comercial (antes Administrador)
- Responsable Delegación (nuevo)
- Tiendas vinculadas a Comercial (no a Cliente)

### UI
- "Selección de artículos" (no "muebles")
- Iconos quitados del Panel Maestro
- Aislamiento CRM por usuario

---

## ARQUITECTURA

```
/app
├── backend/
│   ├── server.py (~4700 líneas)
│   │   ├── GET /api/admin/metrics (nuevo)
│   │   ├── UserModel (isResponsableDelegacion, canAuthorizePermissions)
│   │   └── CRM endpoints con filtrado
│   └── tests/
│       ├── test_admin_metrics.py (nuevo)
│       ├── test_crm_isolation_roles.py
│       └── test_armarios_ia.py
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── AdminWorkView.jsx (métricas + trabajos)
│       │   ├── SettingsModal.jsx (nuevos roles)
│       │   └── BudgetTable.jsx (texto "artículos")
│       └── services/
│           └── pdfGenerator.js (capitalizeName)
└── memory/
    └── PRD.md
```

---

## PRÓXIMAS TAREAS

### P1 - Próximo Sprint
- [ ] Probar IA Lab - Analizador de Planos con imagen real
- [ ] Auto-etiquetar CRM al guardar proyecto (tipo de negocio)
- [ ] Exportar secciones a ventana emergente

### P2 - Media Prioridad
- [ ] Personalizar datos a quitar del PDF
- [ ] Reorganizar UI campo "expediente"
- [ ] Filtros temporales en métricas (mes, trimestre, año)

### P3 - Refactorización
- [ ] Separar server.py en routers
- [ ] Separar componentes grandes (Armarios.jsx)

---

## TESTS

| Test File | Coverage |
|-----------|----------|
| test_admin_metrics.py | 100% |
| test_crm_isolation_roles.py | 100% |
| test_armarios_ia.py | 91% |
| test_new_roles_features.py | 100% |

---

## CREDENCIALES

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| MARIO | MARIO | Director Comercial |
| TIENDSA | TIENDSA | Tienda/Punto de Venta |
| COMSA | COMERCIAL | Comercial |
| PRESCRIPTOR1 | PRESCRIPTOR1 | Colaborador Comercial |
