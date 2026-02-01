# LUIGGI HOME - ERP/CRM para Presupuestos de Cocinas y Armarios

## Última Actualización: 01/02/2026 (v4.2)

---

## RESUMEN DEL SISTEMA

LUIGGI HOME es un ERP/CRM completo para la gestión de presupuestos de cocinas y armarios, con:
- Jerarquía de usuarios: **Director Comercial > Responsable Delegación > Comercial > Tienda/Punto de Venta > Colaborador**
- **Panel de Métricas** para Director Comercial con ventas, pipeline, conversión, top performers
- **Gráficos de tendencias** con recharts (ventas mensuales, oportunidades, distribución, embudo)
- Presupuestador técnico con cálculo automático de precios
- Módulo de Armarios con diseñador visual, despiece e IA
- CRM completo con calendario, **filtros por tipo de negocio (Cocina Montada/Despiece/Armarios)** y aislamiento de datos
- Digitalizador de borradores con IA
- Importador de catálogo IA
- Sistema de backups automáticos

---

## COMPLETADO EN ESTA SESIÓN (25/01/2026)

### ✅ P1 - Etiquetado de Oportunidades por Tipo de Negocio

| Componente | Estado | Descripción |
|------------|--------|-------------|
| **Backend** | ✅ | Campo `businessType` y `moduleType` en OpportunityModel |
| **API Filtrado** | ✅ | `GET /api/crm/opportunities?businessType=cocina&moduleType=montada` |
| **Endpoint Armarios** | ✅ | `POST /api/crm/opportunities/from-armario/{project_id}` |
| **Frontend Filtros** | ✅ | **4 botones: TODOS / COCINA MONTADA / COCINA DESPIECE / ARMARIOS** |
| **Badges** | ✅ | Etiquetas de tipo en tarjetas (amber=montada, orange=despiece, emerald=armarios) |
| **Auto-etiquetado** | ✅ | Al guardar proyecto cocina/armarios, se etiqueta oportunidad correctamente |

### ✅ P2 - Panel de Métricas con Gráficos

| Componente | Estado | Descripción |
|------------|--------|-------------|
| **Endpoint Tendencias** | ✅ | `GET /api/admin/metrics/trends` con datos mensuales |
| **Gráfico Ventas** | ✅ | BarChart de ventas mensuales (€) |
| **Gráfico Opps** | ✅ | LineChart de oportunidades creadas/ganadas/perdidas |
| **Distribución** | ✅ | PieChart de Cocina vs Armarios |
| **Embudo** | ✅ | Barra horizontal de conversión por etapa |

---

## ARQUITECTURA ACTUAL

```
/app
├── backend/
│   ├── server.py (~5100 líneas)
│   │   ├── OpportunityModel + businessType
│   │   ├── ContactModel + businessTypes[]
│   │   ├── GET /api/admin/metrics/trends (nuevo)
│   │   ├── POST /api/crm/opportunities/from-armario (nuevo)
│   │   └── GET /api/crm/opportunities?businessType (actualizado)
│   └── tests/
│       └── test_p1_p2_features.py (nuevo)
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── AdminWorkView.jsx (gráficos recharts)
│       │   ├── CRMPipeline.jsx (filtros businessType)
│       │   ├── BudgetTable.jsx (auto-etiquetado cocina)
│       │   └── Armarios.jsx (auto-etiquetado armarios)
│       └── services/
│           └── api.js (adminMetricsAPI, createFromArmario)
└── memory/
    └── PRD.md
```

---

## PRÓXIMAS TAREAS

### P2 - Media Prioridad
- [ ] Probar IA Lab - Analizador de Planos con imagen real
- [ ] Personalizar datos a quitar del PDF
- [ ] Reorganizar UI campo "expediente"
- [ ] Filtros temporales en métricas (mes, trimestre, año)

### P3 - Refactorización (URGENTE)
- [ ] Separar server.py en routers/models/services
- [ ] Separar componentes grandes (Armarios.jsx, SettingsModal.jsx)

---

## TESTS

| Test File | Coverage |
|-----------|----------|
| test_p1_p2_features.py | 100% |
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

---

## PROBLEMA CONOCIDO (P2)

**Estabilidad del Frontend**: Error recurrente de React DOM (`insertBefore`) que podría causar crashes aleatorios. El root cause no ha sido diagnosticado completamente.

---

## INTEGRACIONES

- **Google Gemini** (via emergentintegrations): gemini-3-flash-preview para texto, gemini-3-pro-image-preview para imágenes
- **SendGrid**: Envío de backups por email
- **jspdf**: Generación de PDFs en frontend
- **recharts**: Gráficos de métricas
