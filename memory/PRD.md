# LUIGGI HOME - ERP/CRM para Presupuestos de Cocinas y Armarios

## Última Actualización: 08/02/2026 (v5.9)

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
