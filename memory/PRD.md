# LUIGGI HOME - ERP/CRM para Presupuestos de Cocinas y Armarios

## Última Actualización: 01/02/2026 (v4.7)

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

## 🆕 ACTUALIZACIÓN 01/02/2026 (v4.7)

### ✅ Dimensiones del Casco en Despiece con Botón Copiar
| Componente | Estado | Descripción |
|------------|--------|-------------|
| **DespieceModal.jsx** | ✅ | Sección "DIMENSIONES DEL CASCO ENSAMBLADO" con Ancho × Alto × Fondo en mm |
| **Botón Copiar** | ✅ | Copia al portapapeles: "CODIGO - Casco: 400 x 350 x 330 mm" |
| **Feedback Visual** | ✅ | Cambia a "Copiado" con check durante 2 segundos |

### ✅ Checkbox Armarios Reubicado
| Componente | Estado | Descripción |
|------------|--------|-------------|
| **SettingsModal.jsx** | ✅ | "Diseñador Armarios" movido a sección "MÓDULOS ACTIVOS" |
| **UI** | ✅ | Junto a "Cocina Montada" y "Formato Despiece" con fondo púrpura |
| **Badge** | ✅ | Aparece como etiqueta ARMARIOS (cyan) en lista de usuarios |

### ✅ Verificación de Precios por Zona (zonePoints)
| Métrica | Valor |
|---------|-------|
| Total productos | 4,685 |
| **CON zonePoints válidos** | **3,640 (77.7%)** |
| Sin zonePoints (productos GOLA/TIRADOR) | 1,032 (22.0%) |

---

## ARQUITECTURA ACTUAL

```
/app
├── backend/
│   ├── server.py (~5400 líneas)
│   ├── models/
│   ├── services/
│   │   ├── jwt_service.py
│   │   ├── rate_limiter.py
│   │   └── audit_service.py
│   └── routers/
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── DespieceModal.jsx  # ✅ Dimensiones casco + botón copiar
│       │   ├── SettingsModal.jsx  # ✅ Checkbox Armarios reubicado
│       │   ├── BudgetTable.jsx
│       │   └── ...
│       └── services/
└── memory/
    └── PRD.md
```

---

## PRÓXIMAS TAREAS

### P1 - Alta Prioridad
- [ ] **Importar precios GOLA/TIRADOR**: 1,032 productos pendientes de datos del proveedor
- [ ] PDF Aesthetics: Ajustar encabezado según diseño del usuario (requiere imagen)
- [ ] Migración `totalPvp`: Script para actualizar proyectos históricos (solo 1 afectado)

### P2 - Media Prioridad
- [ ] Estabilidad Frontend: Investigar error `insertBefore` de React
- [ ] Filtros temporales en métricas (mes, trimestre, año)

### P3 - Refactorización
- [ ] Migrar endpoints de server.py a routers separados
- [ ] Descomponer BudgetTable.jsx en componentes más pequeños

---

## CREDENCIALES

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| MARIO | MARIO | Director Comercial |
| TIENDSA | TIENDSA | Tienda/Punto de Venta |
| COMSA | COMERCIAL | Comercial |

---

## INTEGRACIONES

- **Google Gemini** (via emergentintegrations): gemini-2.0-flash
- **SendGrid**: Notificaciones por email
- **jspdf + jspdf-autotable**: PDFs
- **recharts**: Gráficos
