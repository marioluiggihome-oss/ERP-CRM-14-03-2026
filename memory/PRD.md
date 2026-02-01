# LUIGGI HOME - ERP/CRM para Presupuestos de Cocinas y Armarios

## Última Actualización: 01/02/2026 (v5.1)

---

## 🆕 ACTUALIZACIÓN 01/02/2026 (v5.1)

### ✅ CSV Seccionadora - Formato Limpio
- **Eliminadas** líneas de cabecera (Cliente, Expediente, Referencia, Fecha, Hora)
- **Eliminado** resumen final (Total piezas)
- **Formato**: Solo encabezados de columnas + datos de piezas
- El nombre del archivo incluye Expediente y Cliente para identificación

### ✅ IA Lab - Mejora de Detección de Muebles
- Añadida detección de **COSTADOS** (paneles decorativos, costados de frigorífico)
- Añadida detección de **ALTILLOS COMBI** (muebles sobre frigoríficos)
- Mejora en el prompt para contar elementos individualmente

---

## CAMBIOS ANTERIORES (v5.0)

- Categorías GOLA visibles (477 ALTO GOLA, 292 BAJO GOLA, 124 COLUMNA GOLA)
- Excel de 49 productos sin precio: /productos_sin_precio.xlsx
- Corrección nombres 11cm → 110cm (115 productos)
- 4685 productos con module=montada

---

## PRÓXIMAS TAREAS

### Pendiente de Confirmación
- [ ] **Medidas del despiece**: Confirmar cálculo correcto de costados/tapas

### P1 - Alta Prioridad
- [ ] **49 productos sin precios**: Excel disponible para rellenar

### P2 - Media Prioridad
- [ ] Estabilidad Frontend: Error `insertBefore` de React

---

## CREDENCIALES

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| MARIO | MARIO | Director Comercial |
| TIENDSA | TIENDSA | Tienda |
| COMSA | COMERCIAL | Comercial |
