# LUIGGI HOME - ERP/CRM para Presupuestos de Cocinas y Armarios

## Última Actualización: 01/02/2026 (v5.2)

---

## 🆕 ACTUALIZACIÓN 01/02/2026 (v5.2)

### ✅ Volcar Muebles desde IA Lab al Presupuesto
- Añadida función `handleAddFromVisualizer` en App.js
- La prop `onAddToBudget` ahora se pasa correctamente al componente Visualizer
- Los muebles detectados por IA se pueden añadir al presupuesto con un clic

### ✅ Panel Admin Solo para Director Comercial
- **Verificado**: El botón "Panel Admin" solo es visible para usuarios con `isAdmin: true`
- Los usuarios Tienda (ej: TISA, TMA, REFLEON) solo ven: Presupuesto y Salir

### ✅ Botón "Exportar a Excel" en MASTER
- Nuevo endpoint: `GET /api/admin/export-database`
- Solo accesible para Director Comercial
- Genera Excel con pestañas: Usuarios, Productos, Proyectos
- Botón verde junto a "Crear Backup Manual"

### ✅ Exportables de Base de Datos
- **URL de descarga**: https://kitchen-manager-app.preview.emergentagent.com/export_database_latest.xlsx
- Incluye: 10 usuarios, 4685 productos, acabados/materiales, proyectos, oportunidades CRM

### ✅ CSV Seccionadora - Formato Limpio
- Sin cabeceras extra (Cliente, Expediente, etc.)
- Solo: Encabezados de columnas + datos de piezas

---

## BASE DE DATOS

| Colección | Registros |
|-----------|-----------|
| Usuarios | 10 |
| Productos | 4,685 |
| Proyectos | 6 |
| Oportunidades | Variable |

---

## CREDENCIALES

| Usuario | Contraseña | Rol | Ve Panel Admin |
|---------|------------|-----|----------------|
| MARIO | MARIO | Director Comercial | ✅ SÍ |
| JENARO | JENARO | Director Comercial | ✅ SÍ |
| COMSA | COMERCIAL | Comercial | ❌ NO |
| TISA | TISA | Tienda | ❌ NO |
| TMA | TMA | Tienda | ❌ NO |

---

## PRÓXIMAS TAREAS

### Pendiente de Confirmación
- [ ] **Medidas del despiece**: Confirmar cálculo de costados/tapas

### P1 - Alta Prioridad
- [ ] **49 productos sin precios**: Excel disponible para rellenar
