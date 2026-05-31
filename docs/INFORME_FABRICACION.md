# Informe — Fabricación completa y potente (auditoría + mejoras)

> Fecha: 2026-05-31 · Rama: `claude/relaxed-johnson-fLEHH`
> Alcance: módulo de Fábrica, Despiece (ambas librerías ZC y MV), exportaciones,
> privacidad de pedidos a proveedor y copia de seguridad.

---

## 1. Resumen ejecutivo

El motor de fabricación ya era sólido (~65% de un sistema de fábrica completo):
despiece geométrico real, optimizador de tableros con algoritmo de nesting 2D,
ciclo de órdenes con seguimiento por mueble y exportaciones. En esta iteración se
ha **auditado a fondo**, se han **corregido bugs** y se han **integrado mejoras de
alto valor** para acercarlo a una fabricación de taller "lista para producción".

---

## 2. Auditoría: qué se verificó

### 2.1 Despiece de las dos librerías (ZC y MV) — ✅ CORRECTO
Se ejecutó el motor `calculate_furniture_despiece` con muebles reales de ambas
nomenclaturas y los resultados son coherentes:

| Librería | Mueble | Resultado verificado |
|----------|--------|----------------------|
| ZC | 9A1P300 (alto 30×90) | 20 piezas, puerta 89,8×29,7, 2 bisagras, 2 baldas, trasera 8mm |
| ZC | 9B2P600 (bajo 60×72) | 22 piezas, 2 puertas, 4 bisagras |
| ZC | 9C2P600 (columna 60×220) | 44 piezas, 6 bisagras (3/puerta por altura), 5 baldas |
| MV | A30D/I (alto 30×70) | detecta tipo ALTO por prefijo MV, 1 puerta |
| MV | CD60 (columna despensero) | detecta COLUMNA, 5 baldas |
| MV | BF60 (bajo fregadero) | **sin puerta ni baldas** (correcto: hueco encimera) |

**Conclusión:** el cálculo es geométrico (independiente de la librería) y la
detección de tipo soporta correctamente prefijos ZC (A/B/C/9A/9B) y MV
(ASCE, AR, CD, CH, BF, etc.). La agregación por material coincide al milímetro con
el resumen del despiece (2 ALTOS → 12 piezas Blanco SUPERPAN / 1,735 m²; total 2,83 m²).

### 2.2 Optimizador de tableros — ✅ FUNCIONAL (no era un placeholder)
`BoardOptimizer.jsx` implementa **First-Fit-Decreasing-Height (FFDH)** con rotación
de piezas, tableros estándar (244×122 y otros), kerf configurable, cálculo de nº de
tableros y % de aprovechamiento, vista interactiva y exportación a seccionadora.

### 2.3 Exportaciones del despiece — auditadas
- **PDF A4** (4 vistas): completo.
- **CSV / PDF Puertas Proveedor**: correcto.
- **XML corte (CutRite/Ardis)**: tenía un fallo (cantos siempre a 0). **Corregido.**

---

## 3. Bugs corregidos en esta iteración

| # | Problema | Solución | Ventaja |
|---|----------|----------|---------|
| 1 | **Informe Industrial** en Fábrica salía con la lista de muebles **vacía** (buscaba en un catálogo que en Fábrica va vacío). | Producto de catálogo ahora opcional; usa los datos de la propia orden. | El Informe vuelve a listar los muebles. |
| 2 | **XML de corte** exportaba `EdgeBanding=0` siempre. | Calcula los cantos reales por pieza (1L/2L/4L → l1/l2/w1/w2). | La canteadora/seccionadora sabe qué lados cantear. |
| 3 | **Despiece de Fábrica** abría un modal simplificado (solo lista de piezas). | Reutiliza el `DespieceModal` completo (5 secciones + exportaciones). | Fábrica tiene el mismo despiece potente que el presupuesto. |

---

## 4. Mejoras integradas (con su ventaja)

### 4.1 🔒 Privacidad en pedidos a proveedor — INTEGRADO
**Qué:** el PDF, el CSV y el nombre de archivo XML ya **no muestran el nombre del
cliente**; usan la **Ref. Pedido** (nº de pedido de venta) como identificador.

**Ventaja:** puedes enviar el pedido de puertas/corte a un proveedor externo sin
exponer datos de tu cliente final. Más profesional y conforme a privacidad; el
proveedor identifica el pedido por referencia, no por nombre.

### 4.2 🧾 Nueva pestaña "Lista de Compra" (hoja de materiales) — INTEGRADO
**Qué:** una 6ª sección en el despiece que **agrega todo lo necesario para fabricar
la orden** en un solo vistazo:
- **Tableros por material** (m² + nº de piezas) y **estimación de tableros 244×122**
  necesarios (superficie + 15% de merma).
- **Canto por material** en metros lineales.
- **Herrajes totales**: bisagras, correderas, tiradores, soportes de balda, colgadores.

**Ventaja:** es la **lista de la compra del taller**. De un vistazo sabes cuántos
tableros pedir, cuántos metros de canto y cuántos herrajes, sin sumar a mano pieza
a pieza. Reduce errores de aprovisionamiento y acelera el pedido a almacén/proveedor.

### 4.3 🏭 Despiece + Informe Industrial accesibles desde Fábrica — INTEGRADO
Botones en la cabecera del Portal de Fábrica y dentro del Informe Industrial para
abrir el despiece completo de la orden seleccionada.

---

## 5. Lo que aún NO tiene (hoja de ruta recomendada)

Para llegar a una fábrica "100% completa", lo siguiente (por orden de valor):

1. **Coste de materiales por orden** — precio €/m² de tablero + coste de herrajes →
   margen real por proyecto. *(Alto valor, esfuerzo medio.)*
2. **Consumo de stock** — descontar tableros/herrajes del inventario al confirmar.
3. **Nesting multi-orden** — optimizar el corte de varias órdenes a la vez (−5/15% merma).
4. **Etiquetas/códigos de barras por pieza** — trazabilidad en el taller.
5. **Hoja de ruta de taller** — corte → cantear → montar → herraje → QC, por estación.

> La "Lista de Compra" integrada en 4.2 es la base directa para 1, 2 y 5.

---

## 6. Copia de seguridad

El sistema **ya incluye** backup completo con envío por email
(`create_daily_backup_with_email`), destino por defecto `marioluiggihome@gmail.com`,
ZIP con todas las colecciones en JSON. Disparable desde el Panel Maestro (BACKUPS DB)
o vía `POST /api/backup/send-email`. Requiere ejecutarse en **producción** (donde
están `MONGO_URL` y `RESEND_API_KEY`); no puede generarse desde el entorno de
desarrollo por no disponer de esas credenciales.

---

## 7. Verificación

- Despiece ZC + MV ejecutado y validado contra el resumen real del modal.
- Agregación de la Lista de Compra validada (coincide con "resumen por material").
- `yarn build` (Node 18, config de producción) → **Compiled successfully** en cada cambio.
- Todo commiteado y pusheado a `claude/relaxed-johnson-fLEHH`.
