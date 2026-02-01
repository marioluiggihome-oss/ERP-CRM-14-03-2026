# LUIGGI HOME - ERP/CRM para Presupuestos de Cocinas y Armarios

## Última Actualización: 01/02/2026 (v4.6)

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
- **🔒 Sistema de Seguridad Enterprise (JWT + Rate Limiting + Auditoría)**
- **Sistema de Registro de Distribuidores con notificación por email**

---

## 🆕 ACTUALIZACIÓN 01/02/2026 (v4.6)

### ✅ Dimensiones del Casco en Despiece
| Componente | Estado | Descripción |
|------------|--------|-------------|
| **DespieceModal.jsx** | ✅ | Nueva sección "DIMENSIONES DEL CASCO ENSAMBLADO" |
| **UI** | ✅ | Muestra Ancho × Alto × Fondo en mm con diseño destacado |
| **Utilidad** | ✅ | Para usuarios que trabajan con cascos prefabricados |

### ✅ Verificación de Precios por Zona (zonePoints)
| Métrica | Valor |
|---------|-------|
| Total productos | 4,685 |
| **CON zonePoints válidos** | **3,640 (77.7%)** |
| Sin zonePoints (null) | 1,032 (22.0%) |
| Con zonePoints vacíos/0 | 13 (0.3%) |

**Nota:** Los 1,032 productos sin precios son principalmente:
- **GOLA** (893): Acabado especial sin tirador
- **TIRADOR** (139): Productos con tirador integrado

Estos requieren datos del proveedor y no son un error del sistema.

---

## ARQUITECTURA ACTUAL

```
/app
├── backend/
│   ├── server.py (~5400 líneas - funcional, migración gradual pendiente)
│   ├── models/                    # Modelos Pydantic extraídos
│   ├── services/                  # Servicios reutilizables
│   │   ├── jwt_service.py        # JWT tokens
│   │   ├── rate_limiter.py       # Rate limiting
│   │   └── audit_service.py      # Logs de auditoría
│   └── routers/                   # FastAPI routers
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── DespieceModal.jsx  # ✅ ACTUALIZADO - Dimensiones del casco
│       │   ├── BudgetTable.jsx
│       │   ├── Login.jsx
│       │   └── ...
│       └── services/
│           ├── api.js
│           ├── authService.js
│           └── pdfGenerator.js
└── memory/
    └── PRD.md
```

---

## PRÓXIMAS TAREAS

### P1 - Alta Prioridad
- [ ] PDF Aesthetics: Ajustar encabezado según diseño del usuario (requiere imagen)
- [ ] Permisos UI: Mover checkbox de "Armarios" en panel de usuario
- [ ] Migración `totalPvp`: Script para actualizar proyectos históricos (solo 1 afectado)

### P2 - Media Prioridad
- [ ] Campos superpuestos: Investigar bug de overlapping (necesita más info)
- [ ] Estabilidad Frontend: Investigar error `insertBefore` de React
- [ ] Importar precios para productos GOLA y TIRADOR (1,032 productos)
- [ ] Filtros temporales en métricas (mes, trimestre, año)

### P3 - Refactorización FASE 2
- [ ] Migrar endpoints de auth de server.py a routers/auth.py
- [ ] Migrar endpoints de products de server.py a routers/products.py
- [ ] Crear routers CRM (opportunities, contacts, activities, calendar)
- [ ] Descomponer BudgetTable.jsx en componentes más pequeños

---

## BASE DE DATOS

### Productos
- **Total:** 4,685 productos
- **Con precios válidos:** 3,640 (77.7%)
- **Catálogo:** ZC (ZonaCocinas)
- **Estructura zonePoints:** `{Z1: float, Z2: float, ..., Z12: float}`

### Proyectos
- **Total:** 6 proyectos
- **Con totalPvp:** 5
- **Sin totalPvp:** 1

---

## CREDENCIALES

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| MARIO | MARIO | Director Comercial |
| TIENDSA | TIENDSA | Tienda/Punto de Venta |
| COMSA | COMERCIAL | Comercial |
| PRESCRIPTOR1 | PRESCRIPTOR1 | Colaborador Comercial |

---

## INTEGRACIONES

- **Google Gemini** (via emergentintegrations): gemini-2.0-flash para análisis
- **SendGrid**: Envío de backups y notificaciones
- **jspdf + jspdf-autotable**: Generación de PDFs
- **recharts**: Gráficos de métricas

---

## PROBLEMAS CONOCIDOS (P2)

1. **Estabilidad del Frontend**: Error recurrente de React DOM (`insertBefore`) que podría causar crashes aleatorios.
2. **Productos sin precios**: 1,032 productos GOLA/TIRADOR sin zonePoints configurados.
