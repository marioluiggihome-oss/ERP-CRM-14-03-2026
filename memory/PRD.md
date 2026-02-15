# LUIGGI HOME - ERP/CRM para Presupuestos de Cocinas y Armarios

## Última Actualización: 15/02/2026 (v5.15)

---

## 🆕 ACTUALIZACIÓN 15/02/2026 (v5.15)

### ✅ REIMPORTACIÓN COMPLETA + VALIDACIÓN SEVERA

**Problema Resuelto:** Referencias inventadas que NO existían en el PDF (ej: `G7A1P73058`).

**Solución:**
1. Extracción directa de **6,633 referencias** del `TARIFA-COMPLETA.pdf`
2. Importación de **6,575 productos** con referencias 100% validadas
3. Validación severa comparando BD vs PDF: **0 referencias inválidas**
4. Recuperación de **1,538 precios** desde backups anteriores

**Validación Severa PASADA:**
```
✅ Referencias válidas: 6,575/6,575 (100%)
❌ Referencias inválidas: 0
⚠️ "Faltantes" en PDF: 58 (son nombres de acabados, no productos)
```

**Estado del Catálogo (ACTUALIZADO):**
| Programa | Productos | Con Precio | % |
|----------|-----------|------------|---|
| ESTÁNDAR | 4,065 | 2,605 | 64.1% |
| GOLA | 2,387 | 1,276 | 53.5% |
| ALUMINIO | 161 | 108 | 67.1% |
| **TOTAL** | **6,613** | **3,989** | **60.3%** |

**Extracción de Precios del PDF:**
- ✅ Procesadas 479 páginas del PDF en múltiples pasadas
- ✅ Corregidos productos ALUMINIO (eliminados 123 incorrectos, añadidos 161 correctos)
- ✅ Extraídos precios de tablas de 12 zonas y precios únicos
- ✅ Total: 6,584 precios únicos aplicados

**Productos sin precio restantes (~2,600):**
- Productos con variantes especiales (HL, HS, decorativos)
- Referencias cuyo parsing de tablas no pudo asociar correctamente
- Algunas páginas del PDF tienen estructuras no estándar

---

## 🆕 ACTUALIZACIÓN 15/02/2026 (v5.14)

---

## 🆕 ACTUALIZACIÓN 15/02/2026 (v5.14)

### ✅ REIMPORTACIÓN COMPLETA DEL CATÁLOGO DESDE PDF

**Problema Detectado:** La base de datos contenía ~2,000 productos con referencias que NO existían en el PDF `TARIFA-COMPLETA.pdf`. Por ejemplo:
- `G7A1P73058` - No existe en el PDF
- `G7A1P35058` - Formato incorrecto (debería ser `G7A1P58350`)

**Solución Aplicada:**
1. **Backup completo** de la BD anterior
2. **Extracción directa** de 6,575 referencias válidas del PDF
3. **Reimportación limpia** con todas las referencias correctas
4. **Recuperación de precios** desde el backup anterior (936 productos con precios)

**Estructura de Referencias Correcta:**
- Fondo 33 (estándar): `G7A1P350` = GOLA ALTO 70cm, 1 PUERTA, ancho 35cm
- Fondo 58: `G7A1P58350` = GOLA ALTO 70cm, 1 PUERTA, fondo 58cm, ancho 35cm
- El `58` va DESPUÉS del tipo (`P`, `V`) y ANTES del ancho

**Resultados:**
| Métrica | Antes | Después |
|---------|-------|---------|
| Total Productos | 3,541 | **6,575** |
| Referencias Válidas | ~1,500 | **6,575 (100%)** |
| Productos GOLA | ~1,700 | **2,387** |
| Productos G7A | 0 (mal importados) | **156** |
| Con Precios | ~900 | **936** |

**Verificación:**
- ✅ `G7A1P73058` NO existe (correcto, no está en PDF)
- ✅ `G7A1P58350` SÍ existe (correcto, está en PDF)
- ✅ 6,575 productos con referencias 100% del PDF
- ✅ Excel regenerado con datos correctos

---

## 🆕 ACTUALIZACIÓN 07/02/2026 (v5.12)

### ✅ BUG P0 RESUELTO: Productos Nuevos Ahora Visibles

**Problema:** 733 productos nuevos (Costados, Regletas, Zócalos, etc.) no aparecían en el frontend.
**Causa:** Los productos importados no tenían el campo `module` asignado.
**Solución:** Asignado `module: 'montada'` a todos los productos afectados.

### ✅ CATÁLOGO COMPLETO (6,438 productos)

**Resumen de Productos por Categoría:**
| Categoría | Cantidad |
|-----------|----------|
| ALTOS | 1,787 |
| ALTOS GOLA | 1,505 |
| BAJOS | 1,073 |
| BAJOS GOLA | 395 |
| SEMICOLUMNAS | 322 |
| COLUMNAS | 322 |
| **COSTADOS** | **241** |
| SEMICOLUMNAS GOLA | 218 |
| **VITRINAS** | **161** |
| **PUERTAS** | **156** |
| **ESTANTES** | **115** |
| COLUMNAS GOLA | 83 |
| **REGLETAS** | **40** |
| **ZOCALOS** | **8** |
| **CORNISAS** | **7** |
| COMPLEMENTOS | 5 |
| **TOTAL** | **6,438** |

### ✅ Tests Verificados (iteration_19.json)
- Backend: 15/15 tests passed (100%)
- Frontend: 100%
- Login MARIO/MARIO: ✅
- Búsqueda productos: ✅
- Eliminación clientes: ✅
- Añadir al presupuesto: ✅

---

## 🆕 ACTUALIZACIÓN 08/02/2026 (v5.11)

**Muebles Especiales:**
- Abatibles HK-TOP: 284
- Abatibles LIFT/HL: 209
- Abatibles SERVO/HS: 281
- Con Horno: 186
- Con Microondas: 37
- Con Fregadero: 152
- Con Placa/Vitro: 196
- Con Termo: 67
- Con Escurreplatos: 25
- Con Caceroleros: 319
- Con Cajones: 135
- Extraíbles: 18

### ✅ Correcciones Aplicadas:
1. **GV*SC** movidos a SEMICOLUMNAS GOLA (76 productos)
2. **20CD/22CD/24CD** movidos a COLUMNAS (199 productos)
3. Nombres corregidos: ALTO → COLUMNA para productos CD
4. Alturas corregidas: 20CD=200cm, 22CD=220cm, 24CD=240cm
5. 14SC y 16SC movidos a SEMICOLUMNAS (90 productos)

### ✅ Verificaciones de Integridad:
- ✅ Todos los productos tienen datos completos
- ✅ Sin códigos duplicados
- ✅ GOLA en categorías GOLA: 2,010/2,010
- ✅ SC con SEMICOLUMNA en nombre: 390
- ✅ CD con COLUMNA en nombre: 282

---

## 🆕 ACTUALIZACIÓN 08/02/2026 (v5.10)

### ✅ Filtro de Categorías Actualizado
Todas las categorías GOLA ahora aparecen en el dropdown ordenadas:
1. ALTOS
2. ALTOS GOLA
3. BAJOS
4. BAJOS GOLA  
5. SEMICOLUMNAS
6. SEMICOLUMNAS GOLA
7. COLUMNAS
8. COLUMNAS GOLA

### ✅ Iconos para Muebles Especiales
Nuevos iconos añadidos a CabinetIcon.jsx:
- **CAMPANA** - Extractor de cocina
- **EXTRAÍBLE** - Muebles con sistema extraíble
- **BOTELLERO** - Organizador de botellas
- **ESCOBERO** - Almacenamiento de escobas
- **FRIGORÍFICO** - Muebles para frigorífico
- **CAJONES/CACEROLEROS** - Muebles con cajones

### ✅ Detección Mejorada de Tipos Especiales
La función `getSpecialType` ahora detecta por código Y por nombre:
- Micro, Horno, Horno+Micro
- Placa/Vitrocerámica
- Fregadero, Termo, Escurreplatos
- Campana, Extraíble, Botellero
- Escobero, Frigorífico, Cajones

### ✅ Badges de Colores para Tipos Especiales
Nuevos colores de badges:
- CAMPANA: Púrpura
- EXTRAÍBLE: Lima
- BOTELLERO: Rosa
- ESCOBERO: Piedra
- FRIGO: Cyan
- CAJONES: Amarillo

---

## 🆕 ACTUALIZACIÓN 08/02/2026 (v5.9)

### ✅ SEMICOLUMNAS GOLA y COLUMNAS GOLA Añadidas

1. **SEMICOLUMNAS GOLA** (142 productos - código G13SC/G14SC/G16SC):
   - Productos correctamente categorizados y nombrados
   - Incluyen: puertas, vitrinas, caceroleros, cajones, horno, micro
   - Ejemplo: "SEMICOLUMNA GOLA 1 PUERTA 1 CACEROLERO + 1 CAJÓN 40 CMS. ANCHO / FONDO 58 CMS."

2. **COLUMNAS GOLA** (83 productos - código G20CD/G22CD/G24CD):
   - Productos correctamente categorizados y nombrados  
   - Incluyen: puertas, vitrinas, caceroleros, cajones, horno, micro, frigorífico
   - Ejemplo: "COLUMNA GOLA 2 PUERTAS 60 CMS. ANCHO / FONDO 58 CMS."

### ✅ Resumen de Categorías Actualizadas:
| Categoría | Cantidad |
|-----------|----------|
| ALTOS | 2,126 |
| ALTOS GOLA | 1,792 |
| BAJOS | 1,073 |
| BAJOS GOLA | 395 |
| SEMICOLUMNAS | 238 |
| SEMICOLUMNAS GOLA | 142 |
| COLUMNAS | 123 |
| COLUMNAS GOLA | 83 |

---

## 🆕 ACTUALIZACIÓN 08/02/2026 (v5.8)

### ✅ Revisión Completa de COLUMNAS y SEMICOLUMNAS

1. **COLUMNAS** (123 productos - código 20CH/22CH/24CH):
   - Nombres actualizados con descripción completa del PDF
   - Incluyen: puertas, vitrinas, cajones BAX/LUX, caceroleros, horno, micro
   - Fondo según prefijo: 20CH=58cm, 22CH=65cm, 24CH=70cm
   - Ejemplos: "COLUMNA 2 PUERTAS + HORNO 60 CMS. ANCHO / FONDO 58 CMS."

2. **SEMICOLUMNAS** (246 productos - código 13SC/11SM):
   - Nombres actualizados con descripción correcta
   - Incluyen: puertas, vitrinas, cajones, caceroleros, horno, micro
   - Fondo según prefijo: 13SC=58cm, 11SM=estándar
   - Ejemplos: "SEMICOLUMNA 4 CAJONES BAX + HORNO 60 CMS. ANCHO / FONDO 58 CMS."

### ✅ Tipos de productos incluidos:
- **Solo puertas/vitrinas**: 1P, 2P, 1V, 2V
- **Con horno**: +H en código (ejemplo: 13SC1PH600)
- **Con horno + micro**: +HM en código (ejemplo: 13SC1PHM600)
- **Con cajones BAX**: CB en código (cajones económicos)
- **Con cajones LUX**: CL en código (cajones premium)
- **Con caceroleros**: 1G, 2G en código
- **Puertas extraíbles**: PE en código

---

## 🆕 ACTUALIZACIÓN 08/02/2026 (v5.7)

### ✅ Correcciones de Catálogo de Productos
1. **BAJOS GOLA**: Los productos G8B* ahora están correctamente categorizados como "BAJOS GOLA" (395 productos)
   - Antes: Categoría "ALTOS GOLA" ❌
   - Después: Categoría "BAJOS GOLA" ✅
   - Nombres actualizados de "GOLA" a "BAJO GOLA"

2. **SEMICOLUMNA HORNO**: Los productos con código SC+BH/CH ahora se llaman "SEMICOLUMNA HORNO" (32 productos)
   - Antes: "BAJO HORNO ALTO" ❌
   - Después: "SEMICOLUMNA HORNO" ✅
   - Fondo actualizado a 58 cms
   - Categoría: SEMICOLUMNAS

3. **HK-TOP**: Los productos abatibles sin sufijo HL/HS/HF ahora muestran "HK-TOP" (284 productos)
   - Son los productos con código APABL/AVABL que NO terminan en HL, HS, o HF
   - Badge rojo "HK" visible en la librería
   - Búsqueda por "hk" o "hk-top" funciona correctamente

### ✅ Casco Predeterminado (Simplificado)
- Eliminada la sección compleja "Casco por Serie"
- Añadido botón "Establecer como Predeterminado" en cada tarjeta de material de armazón
- El material predeterminado se guarda en settings y persiste entre sesiones

### ✅ Mejoras en Búsqueda de Herrajes
- `hk` / `hk-top` → Encuentra productos HK-TOP (284)
- `hl` / `lift` → Encuentra productos LIFT (209)
- `hs` / `servo` → Encuentra productos SERVO-DRIVE (281)
- `horno` → Encuentra productos con horno
- `micro` → Encuentra productos con microondas

---

## 🆕 ACTUALIZACIÓN 08/02/2026 (v5.6)

### ✅ P0: Búsqueda por Tipos de Herraje (HL, HS, HK, HF)
- **Problema**: Los productos con herrajes especiales no se podían encontrar buscando por código de herraje
- **Solución**: Implementada búsqueda mejorada en `filteredCatalog` con mapeo de términos:
  - `hl`, `lift` → Productos LIFT (209 productos)
  - `hs`, `servo`, `servo-drive` → Productos SERVO-DRIVE (281 productos)
  - `hk`, `lift top` → Productos HK-TOP
  - `hf`, `free fold` → Productos FREE-FOLD
  - `micro`, `horno`, `placa`, `freg`, `termo`, `escurre` → Tipos especiales de muebles
- **Badges Visuales**: Añadidos badges de color junto al nombre del producto:
  - HL: Violeta | HS: Verde esmeralda | HK: Rojo | HF: Cyan
- **Archivos modificados**: `/app/frontend/src/components/BudgetTable.jsx`

### ✅ P1: Casco Predeterminado por Serie
- **Requisito**: Permitir configurar un armazón/casco por defecto para cada serie de productos
- **Solución**: 
  - Nuevo campo `defaultCarcassBySeries` en modelo Settings (backend)
  - Nueva sección en Settings > Armazones: "CASCO PREDETERMINADO POR SERIE"
  - Lista de 64 series con selector de material predeterminado
  - Al añadir producto, se aplica automáticamente el casco configurado para su serie
- **Archivos modificados**:
  - `/app/backend/server.py` - SettingsModel, SettingsUpdate
  - `/app/frontend/src/App.js` - Estado defaultCarcassBySeries
  - `/app/frontend/src/components/BudgetTable.jsx` - addItemToBudget()
  - `/app/frontend/src/components/SettingsModal.jsx` - UI nueva sección

### ✅ Testing Completo
- Testing agent ejecutado: 100% tests pasados (6/6)
- Archivo de reporte: `/app/test_reports/iteration_18.json`

---

## 🆕 ACTUALIZACIÓN 01/02/2026 (v5.5)

### ✅ BUG CRÍTICO CORREGIDO: Eliminación de Clientes
- **Problema**: Error "body stream already read" al eliminar clientes desde Panel Maestro
- **Solución**: Implementado `response.clone()` en `clientsAPI.delete()` para manejar correctamente el stream del body
- **Verificación**: Probado con testing agent - 100% de tests pasaron
- **Archivo modificado**: `/app/frontend/src/services/api.js`
- Añadido mensaje de éxito al eliminar cliente

### ✅ Email de Confirmación de Pedido
- Endpoint `/api/orders/confirm` verificado y funcionando
- Template HTML profesional con branding corporativo
- Incluye especificaciones de acabados (armazón, puertas, costados)
- Soporta archivos adjuntos (hasta 5)

---

## 🆕 ACTUALIZACIÓN 01/02/2026 (v5.4)

### ✅ Precios GOLA Importados desde PDF
- Importados precios de productos GOLA desde el PDF "TARIFA-TECNICA-ZONACOCINAS_GOLA.pdf"
- 34 productos GOLA que no tenían precios ahora tienen zonePoints (Z1-Z4)
- Total: 1642 productos GOLA con precios completos

### ✅ Nuevo Endpoint PATCH para Actualizar zonePoints
- Creado `PATCH /api/products/{product_id}/zone-points` para actualizar solo los precios por zona
- Permite actualizar precios sin necesidad de enviar todos los campos del producto

### ✅ Panel Admin Fusionado con MASTER
- El contenido del "Panel Admin" ahora está dentro del modal MASTER como pestaña "PANEL DIRECTOR"
- Incluye métricas globales, top performers, y detalles por comercial
- Gráficos de ventas mensuales y embudo de conversión

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

### ✅ Completadas en v5.6
- [x] **P0: Búsqueda por tipos de herraje** (HL, HS, HK, HF) - Completado
- [x] **P1: Casco Predeterminado por Serie** - Completado

### P1 - Alta Prioridad
- [ ] **Series Especiales de Casco + Lógica Coste Cero**: Añadir nuevas series para cascos especiales y manejar cascos con coste 0
- [ ] **CSV Multi-hoja**: Exportar a Excel con datos de cliente en una hoja y lista de corte en otra
- [ ] **Panel de solicitudes de distribuidores**: UI para aprobar/rechazar registros

### P2 - Media Prioridad
- [ ] **Nuevo CRM y Workflow de Pedidos**: Implementar flujo completo cuando el catálogo esté aprobado

### Pendiente de Confirmación
- [ ] **Medidas del despiece**: Confirmar cálculo de costados/tapas
