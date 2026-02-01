# LUIGGI HOME - ERP/CRM para Presupuestos de Cocinas y Armarios

## Última Actualización: 01/02/2026 (v4.8)

---

## RESUMEN DEL SISTEMA

LUIGGI HOME es un ERP/CRM completo para la gestión de presupuestos de cocinas y armarios.

---

## 🆕 ACTUALIZACIÓN 01/02/2026 (v4.8)

### ✅ Exportaciones con Datos del Pedido
| Funcionalidad | Estado | Descripción |
|---------------|--------|-------------|
| **CSV Seccionadora** | ✅ | Incluye cabecera con Cliente, Expediente, Referencia, Fecha, Material |
| **XML CutRite** | ✅ | Estructura completa con metadatos del proyecto y datos por pieza |
| **Nombre Archivo** | ✅ | `CORTE_EXP-2026-001_CLIENTE_2026-02-01.csv/xml` |

### ✅ Importación Masiva de Precios GOLA/TIRADOR
| Métrica | Antes | Después |
|---------|-------|---------|
| Productos con zonePoints | 3,640 (77.7%) | **4,636 (99.0%)** |
| Sin precios válidos | 1,045 | **49** |

Se generaron automáticamente los `zonePoints` para 996 productos usando ratios estándar.

### ✅ Dimensiones del Casco + Botón Copiar
- Sección verde con Ancho × Alto × Fondo en mm
- Botón "COPIAR" copia: `"35A1P400 - Casco: 400 x 350 x 330 mm"`

### ✅ Checkbox Armarios Reubicado
- Movido a sección "MÓDULOS ACTIVOS" junto a Cocina Montada/Despiece

---

## BASE DE DATOS

| Métrica | Valor |
|---------|-------|
| Total productos | 4,685 |
| **CON zonePoints** | **4,636 (99.0%)** |
| Sin precios (requieren proveedor) | 49 (1.0%) |

---

## PRÓXIMAS TAREAS

### P1 - Alta Prioridad
- [ ] **49 productos sin precios**: Productos GOLA especiales que requieren datos del proveedor
- [ ] PDF Aesthetics: Ajustar encabezado según diseño del usuario

### P2 - Media Prioridad
- [ ] Estabilidad Frontend: Investigar error `insertBefore` de React
- [ ] Filtros temporales en métricas

### P3 - Refactorización
- [ ] Migrar endpoints de server.py a routers separados
- [ ] Descomponer BudgetTable.jsx

---

## CREDENCIALES

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| MARIO | MARIO | Director Comercial |
| TIENDSA | TIENDSA | Tienda/Punto de Venta |
| COMSA | COMERCIAL | Comercial |

---

## INTEGRACIONES

- **Google Gemini** (via emergentintegrations)
- **SendGrid**: Notificaciones por email
- **jspdf**: PDFs
- **recharts**: Gráficos
