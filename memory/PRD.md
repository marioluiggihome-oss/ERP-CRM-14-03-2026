# LUIGGI HOME - ERP/CRM para Presupuestos de Cocinas y Armarios

## Última Actualización: 01/02/2026 (v4.9)

---

## 🆕 ACTUALIZACIÓN 01/02/2026 (v4.9)

### ✅ Corrección de Medidas en Sistema de Despiece
| Vista | Antes | Ahora |
|-------|-------|-------|
| **Orden de Montaje** | Headers: Ancho/Alto (campos vacíos) | Headers: **LARGO (MM) / ANCHO (MM)** con datos |
| **Lista de Corte** | LARGO/ANCHO (campo altura vacío) | **LARGO (MM) / ANCHO (MM)** con valores correctos |
| **Datos mostrados** | length=undefined, width=330 | **length=350, width=330** ✅ |

### ✅ Filtro de Series por Categoría
| Comportamiento | Antes | Ahora |
|----------------|-------|-------|
| **Series al filtrar** | Mostraba todas (3000+) | Solo series de la categoría seleccionada |
| **Reset automático** | No | Sí, al cambiar categoría reset a "TODAS SERIES" |

### ✅ Exportación CSV con Datos del Pedido
- Cabecera con CLIENTE, EXPEDIENTE, REFERENCIA, FECHA, MATERIAL BASE
- Columnas: Material, Grosor, Nombre pieza, **Largo**, **Ancho**, Cantidad, Textura, Código, Mueble

---

## BASE DE DATOS

| Métrica | Valor |
|---------|-------|
| Total productos | 4,685 |
| **CON zonePoints** | **4,636 (99.0%)** |
| Sin precios | 49 (1.0%) |

---

## PRÓXIMAS TAREAS

### P1 - Alta Prioridad
- [ ] **49 productos sin precios**: Productos GOLA especiales que requieren datos del proveedor

### P2 - Media Prioridad
- [ ] Estabilidad Frontend: Error `insertBefore` de React

### P3 - Refactorización
- [ ] Migrar endpoints de server.py a routers

---

## CREDENCIALES

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| MARIO | MARIO | Director Comercial |
| TIENDSA | TIENDSA | Tienda |
| COMSA | COMERCIAL | Comercial |
