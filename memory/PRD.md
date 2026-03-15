# LUIGGI HOME - Kitchen Budgeting ERP/CRM

## Estado del Proyecto: EN DESARROLLO ACTIVO

## Última Actualización: 15 Marzo 2026

---

## ✅ COMPLETADO EN ESTA SESIÓN

### Correcciones de Datos MV
- ✅ **Productos ALTO H70/H90**: Creadas 93 variantes H70 y 93 variantes H90 para muebles ALTO de la biblioteca MV
- ✅ Códigos actualizados: A25D/I/70, A25D/I/90, A30/70, A30/90, etc.

### Mejoras en Filtros
- ✅ **Filtro de cascos por biblioteca**: Materiales separados para ZC y MV en constants.js
- ✅ **Filtro por librería en Inventario**: Añadido selector ZC/MV/TODAS en el panel de Inventario

### Agenda de Montajes - Mejoras
- ✅ **Fechas separadas**:
  - 📦 **Fecha Recepción Cocina**: Fecha prevista de llegada del material
  - 🔧 **Fecha Montaje Comprometido**: Fecha de instalación acordada con el cliente
- ✅ Vista de lista muestra ambas fechas con iconos distintivos

### Correcciones UI
- ✅ **Label "Nombre"**: Cambiado de "Nombre Público Tienda" a "Nombre"

---

## ARQUITECTURA DE DATOS

### Materiales/Cascos
```javascript
// En constants.js - INITIAL_CARCASS_MATERIALS
ZC: mat-blanco-zc, mat-gris-zc, mat-roble-zc, mat-nogal-zc
MV: mat-blanco-mv, mat-gris-mv, mat-roble-mv
```

### Productos ALTO MV
```
Formato: {código}/70 y {código}/90
Ejemplos: A25D/I/70, A25D/I/90, A30/70, A30/90
Total: 186 productos ALTO (93 H70 + 93 H90)
```

### Montajes (MongoDB: luiggi_home.montajes)
```javascript
{
  montadorId: string,
  clientName: string,
  clientAddress: string,
  expectedDeliveryDate: string,  // 📦 Fecha recepción cocina
  scheduledDate: string,         // 🔧 Fecha montaje comprometido
  scheduledTime: string,
  estimatedDuration: string,
  status: 'pendiente' | 'en_curso' | 'completado' | 'cancelado',
  budgetRef: string,
  notes: string
}
```

---

## 🔴 PENDIENTE

### P0 - PAUSADO
1. **Cálculo presupuesto despiece** - Items no se suman al total (PAUSADO por usuario)

### P2 - MEJORAS PENDIENTES
2. **Casco predeterminado por SECCIÓN**: Configurar casco default para BAJOS, ALTOS, COLUMNAS por biblioteca
3. **Logo**: Usuario debe volver a subir el logo
4. **Glitch sidebar colapsado**: Recurrente

### P3 - BACKLOG
5. Refactorización componentes grandes
6. Preview visual catálogo antes de exportar

---

## CREDENCIALES TEST
- **Usuario**: MARIO / MARIO (Admin)
- **Otros**: ALBERTO, EDU

---

## HISTORIAL DE CAMBIOS

### 15 Marzo 2026 (Sesión actual)
- ✅ Creadas variantes H90 para productos ALTO MV
- ✅ Materiales/cascos separados por biblioteca (ZC/MV)
- ✅ Filtro por librería en Inventario
- ✅ Fechas recepción/montaje en Agenda de Montajes
- ✅ Agenda de Montajes completa
- ✅ Digitalizador filtra por biblioteca
- ✅ Exportación catálogo ZC/MV
- ✅ Corte Viga independiente por biblioteca
