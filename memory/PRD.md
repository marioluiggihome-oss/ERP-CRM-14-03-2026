# LUIGGI HOME - ERP/CRM para Presupuestos de Cocinas y Armarios

## Última Actualización: 25/01/2026 (v2)

---

## RESUMEN DEL SISTEMA

LUIGGI HOME es un ERP/CRM completo para la gestión de presupuestos de cocinas y armarios, con:
- Jerarquía de usuarios: **Director Comercial > Responsable Delegación > Comercial > Tienda/Punto de Venta > Colaborador**
- Presupuestador técnico con cálculo automático de precios
- Módulo de Armarios con diseñador visual, despiece e IA
- CRM completo con calendario y aislamiento de datos por usuario
- Digitalizador de borradores con IA
- Importador de catálogo IA
- Sistema de backups automáticos

---

## CORRECCIONES IMPLEMENTADAS - 25/01/2026 (Segunda Tanda)

### ✅ PDF Mejoras
| Corrección | Estado | Descripción |
|------------|--------|-------------|
| Texto "PRESUPUESTO" más pequeño | ✅ COMPLETADO | Reducido de 9pt a 7pt |
| Nombres capitalizados | ✅ COMPLETADO | Función `capitalizeName()` para nombres y direcciones |
| Especificaciones al final | ✅ COMPLETADO | Movidas abajo en formato horizontal compacto |
| Campo Armazón | ✅ YA EXISTÍA | Se muestra en especificaciones |

### ✅ Nuevos Roles Jerárquicos
| Rol | Descripción | Permisos |
|-----|-------------|----------|
| **Director Comercial** | Antes "Administrador" | Control total del sistema |
| **Responsable Delegación** | NUEVO | Reporta al Director. Puede autorizar permisos a comerciales |
| **Comercial/Representante** | Sin cambios | Gestiona sus clientes y tiendas asignadas |
| **Tienda/Punto de Venta** | Sin cambios | Solo acceso al presupuestador |
| **Colaborador Comercial** | Sin cambios | Solo aporta contactos |

### ✅ Vinculación de Tiendas
| Corrección | Estado | Descripción |
|------------|--------|-------------|
| Vincular Tienda a Comercial | ✅ COMPLETADO | Antes se vinculaba a Cliente, ahora a Comercial/Responsable/Director |
| Selector actualizado | ✅ COMPLETADO | Muestra rol entre paréntesis: "(Director)", "(Resp. Deleg.)", "(Comercial)" |

### ✅ Cambios de Texto
| Corrección | Estado | Descripción |
|------------|--------|-------------|
| "Selección de artículos" | ✅ COMPLETADO | Cambiado de "Selección de muebles" |
| "Añade artículos" | ✅ COMPLETADO | Cambiado de "Añade muebles" |
| "ARTÍCULOS" en librería | ✅ COMPLETADO | Cambiado de "MUEBLES" |

---

## JERARQUÍA DE ROLES

```
Director Comercial (isAdmin)
    │
    ├── Responsable Delegación (isResponsableDelegacion)
    │       │
    │       ├── Comercial (isRepresentative)
    │       │       │
    │       │       └── Tienda/PdV (isTienda) [linkedRepresentativeId]
    │       │
    │       └── Tienda/PdV (isTienda) [linkedRepresentativeId]
    │
    ├── Comercial (isRepresentative)
    │       │
    │       └── Tienda/PdV (isTienda) [linkedRepresentativeId]
    │
    └── Colaborador Comercial (isPrescriptor)
```

---

## CAMPOS NUEVOS EN MODELO USUARIO

```python
# Backend: server.py
class UserModel:
    isAdmin: bool = False  # Director Comercial
    isResponsableDelegacion: bool = False  # Responsable de Delegación
    isRepresentative: bool = False  # Comercial
    isPrescriptor: bool = False  # Colaborador Comercial
    isTienda: bool = False  # Tienda/Punto de Venta
    linkedRepresentativeId: Optional[str] = None  # ID del Comercial/Responsable/Director
    canAuthorizePermissions: bool = False  # Puede autorizar permisos (Resp. Delegación)
```

---

## ARQUITECTURA

```
/app
├── backend/
│   ├── server.py (~4500 líneas)
│   │   ├── UserModel (nuevos campos: isResponsableDelegacion, canAuthorizePermissions)
│   │   ├── ContactModel (assignedTo)
│   │   └── CRM endpoints con filtrado por usuario
│   └── tests/
│       ├── test_crm_isolation_roles.py
│       ├── test_armarios_ia.py
│       └── test_new_roles_features.py
├── frontend/
│   └── src/
│       ├── App.js (sidebar con permisos por rol)
│       ├── components/
│       │   ├── BudgetTable.jsx (texto "artículos")
│       │   ├── SettingsModal.jsx (nuevos roles en formulario)
│       │   └── CRM*.jsx (filtrado por usuario)
│       └── services/
│           ├── api.js (CRM API con filtrado)
│           └── pdfGenerator.js (capitalizeName, layout compacto)
└── memory/
    └── PRD.md
```

---

## PRÓXIMAS TAREAS

### P1 - Próximo Sprint
- [ ] Probar IA Lab - Analizador de Planos con imagen real
- [ ] Auto-etiquetar CRM al guardar proyecto (tipo de negocio)
- [ ] Exportar secciones a ventana emergente/pantalla completa

### P2 - Media Prioridad
- [ ] Quitar datos innecesarios del PDF (personalizable)
- [ ] Reorganizar UI campo "expediente"

### P3 - Refactorización
- [ ] Separar server.py en routers (>4500 líneas)
- [ ] Separar Armarios.jsx en componentes (>2700 líneas)

---

## CREDENCIALES DE PRUEBA

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| MARIO | MARIO | Director Comercial |
| TIENDSA | TIENDSA | Tienda/Punto de Venta |
| COMSA | COMERCIAL | Comercial |
| PRESCRIPTOR1 | PRESCRIPTOR1 | Colaborador Comercial |

---

## TESTS CREADOS

- `/app/backend/tests/test_new_roles_features.py` - Tests nuevos roles
- `/app/backend/tests/test_crm_isolation_roles.py` - Tests aislamiento CRM
- `/app/backend/tests/test_armarios_ia.py` - Tests funciones IA Armarios
- `/app/test_reports/iteration_14.json` - Último reporte: 100% backend, 100% frontend

---

## NOTAS TÉCNICAS

### PDF Generator
- `capitalizeName()` - Capitaliza nombres correctamente (Primera Letra Mayúscula)
- Especificaciones en formato horizontal al final: `Acabado • Bajo • Alto • Columnas • Costados • Armazón`
- "PRESUPUESTO" reducido a 7pt

### Permisos Responsable Delegación
- `canAuthorizePermissions: true` por defecto cuando se crea
- Puede ver y editar Comerciales y Tiendas de su delegación
- No puede crear otros Responsables ni Director Comercial
