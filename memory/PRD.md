# LUIGGI HOME - ERP/CRM para Presupuestos de Cocinas y Armarios

## Última Actualización: 01/02/2026 (v5.3)

---

## 🆕 ACTUALIZACIÓN 01/02/2026 (v5.3)

### ✅ Panel Admin Fusionado con MASTER
- El contenido del "Panel Admin" ahora está dentro del modal MASTER como pestaña "PANEL DIRECTOR"
- Incluye métricas globales, top performers, y detalles por comercial
- Gráficos de ventas mensuales y embudo de conversión

### ✅ Eliminación de Clientes Arreglada
- Corregido error "body stream already read" al eliminar clientes
- La API ahora funciona correctamente

### ✅ Iconos Removidos del Inventario
- Los iconos de muebles ya no aparecen en la vista de Inventario
- La tabla es más limpia y compacta

### ✅ Botón "Guardar Configuración" en Márgenes
- Nuevo botón para persistir los valores de incrementos
- El valor de "Corte de Viga" ahora se guarda en la base de datos
- Campo `vigaCutIncrement` añadido al modelo Settings

---

## 🆕 ACTUALIZACIÓN ANTERIOR 01/02/2026 (v5.2)

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

### P1 - Alta Prioridad
- [ ] **CSV Multi-hoja**: Exportar a Excel con datos de cliente en una hoja y lista de corte en otra
- [ ] **49 productos sin precios**: Importar precios desde Excel proporcionado por usuario
- [ ] **Panel de solicitudes de distribuidores**: UI para aprobar/rechazar registros

### Pendiente de Confirmación
- [ ] **Medidas del despiece**: Confirmar cálculo de costados/tapas
