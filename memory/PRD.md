# LUIGGI HOME - Kitchen Budgeting ERP/CRM

## Estado del Proyecto: EN DESARROLLO ACTIVO
## Última Actualización: 15 Marzo 2026

---

## ✅ COMPLETADO EN ESTA SESIÓN

### Correcciones de Datos MV
- ✅ **Productos ALTO H70/H90**: Creadas 93 variantes H70 y 93 variantes H90
- ✅ **IDs únicos**: Corregidos IDs duplicados (ahora prod-mv-{code}-70, prod-mv-{code}-90)
- ✅ **Precios Tarifa 1 corregidos**: 
  - A100/70: 77 pts, A100/90: 85 pts
  - A25/70: 36 pts, A25/90: 39 pts
  - A30/70: 38 pts, A30/90: 41 pts

### Bug "Desconocidos" en Presupuesto
- ✅ **SOLUCIONADO**: Los productos MV ya no aparecen como "REFERENCIA DESCONOCIDA"
- Causa: IDs duplicados en productos con variantes de altura
- Solución: IDs únicos basados en código completo incluyendo variante

### Mejoras en Filtros
- ✅ **Filtro de cascos por biblioteca**: ZC y MV separados
- ✅ **Filtro por librería en Inventario**: Selector ZC/MV/TODAS

### Agenda de Montajes
- ✅ **Fechas separadas**:
  - 📦 Fecha Recepción Cocina
  - 🔧 Fecha Montaje Comprometido

### Correcciones UI
- ✅ **Label "Nombre"**: Corregido

---

## PRECIOS TARIFA 1 (MV) - ACTUALIZADOS

### ALTOS (H70 / H90)
| Código | H70 | H90 |
|--------|-----|-----|
| A25 | 36 | 39 |
| A30 | 38 | 41 |
| A35 | 40 | 44 |
| A40 | 43 | 46 |
| A45 | 46 | 49 |
| A50 | 48 | 52 |
| A60 | 57 | 62 |
| A70 | 63 | 70 |
| A80 | 69 | 77 |
| A90 | 77 | 83 |
| A100 | 77 | 85 |

---

## 🔴 PENDIENTE

### P0 - PAUSADO
1. **Cálculo presupuesto despiece** - PAUSADO por usuario

### P2 - MEJORAS PENDIENTES
2. **Casco predeterminado por SECCIÓN** (BAJOS/ALTOS/COLUMNAS)
3. **Logo**: Usuario debe volver a subir
4. **Glitch sidebar colapsado**: Recurrente
5. **Revisar precios completos** de todas las categorías MV

---

## CREDENCIALES TEST
- **Usuario**: MARIO / MARIO

---

## HISTORIAL

### 15 Marzo 2026
- ✅ IDs únicos para productos MV con variantes
- ✅ Precios ALTOS MV actualizados según Tarifa 1
- ✅ Bug "desconocidos" en presupuesto SOLUCIONADO
- ✅ Variantes H70/H90 para ALTOS MV
- ✅ Filtro librería en Inventario
- ✅ Fechas recepción/montaje en Agenda de Montajes
