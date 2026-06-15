# Tarifas MV + Presupuestadores — Estado / Traspaso

> Para retomar en una sesión nueva. Todo el código está en `main` (desplegado).
> Datos de tarifas en `backend/data/mv_tarifas_oficiales.json`.

## 📸 Catálogo MV (escaneos)
- **Las 21 tarifas (T1–T21) + glosario (pp.127–138) están RECIBIDAS como archivo** en las subidas.
- El **visor de imágenes funciona** (se pueden leer las páginas para transcribir).

## ✅ Hecho
- **Importador** `services/mv_tariff_importer.py` + endpoint **`POST /api/libraries/MV/import-tariffs`** (admin):
  - `dry_run=true` → informe; `dry_run=false&wipe=true` → reconstruye productos MV desde el JSON (arregla P1 y P2, quita duplicados). Probado: T1+T2 → 715 SKUs correctos.
  - Botón **"Importar tarifas"** en cabecera de Presupuestador 2 (admin).
- **Presupuestador 2**: búsqueda global multi-palabra, iconos por mueble, **tema naranja**, botón **"Nomenclatura"** (modal código→descripción→icono).
- **Presupuestador 1**: scroll del panel de config arreglado, búsqueda multi-palabra; iconos propios se mantienen.
- **Cocinas 3D**: bug de imagen arreglado (rutas + token proxy); **render por Manus** (motor principal) con Gemini de respaldo (`KITCHEN_RENDER_PROVIDER`); prompts reforzados para fotorrealismo; endpoint+botón **Diagnóstico IA**.
- **muebleIcons.jsx**: iconos + `NOMENCLATURA` + `NOMENCLATURA_NOTAS`.

## ⏳ PENDIENTE (lo que falta por hacer)
1. **VOLCAR T3–T21 al JSON** (solo están T1 y T2). Hay que leer las imágenes página a página y rellenar `tariffs.Tn` en `mv_tarifas_oficiales.json` con la misma estructura que T1/T2. Truco: como las tarifas suben (T1<…<T21), verificar que cada valor encaje entre la anterior y la siguiente.
   - Mapa de páginas: cada tarifa = 6 págs. T3=13–18, T4=19–24, T5=25–30, T6=31–36, T7=37–42, … T21=121–126.
2. **PDF de la Nomenclatura** ("Módulos Técnicos 2026") con portada chula tipo página de entrada del ERP, descargable, como consulta de iconos. (PEDIDO, no hecho.)
3. **Comodidad Presupuestador 2** (auditoría): botones de cantidad más grandes y **cantidad editable** (ahora +/- de 24px). (PEDIDO, no hecho.)
4. **Duplicados en la barra lateral**: el usuario vio partes duplicadas en "esta barra lateral" (¿nav principal o lista de familias de P2?). PENDIENTE de localizar/arreglar.
5. Tras volcar todo → el admin pulsa **"Importar tarifas"** (dry-run y luego aplicar con wipe) para dejar P1 y P2 con precios reales.
6. Verificar en Railway: **`MANUS_API_KEY`** (render) y, si se usa, **`GEMINI_API_KEY`**.

| Tarifa | Páginas | Estado |
|--------|---------|--------|
| T1  | 1–6     | ✅ COMPLETA y **volcada al JSON** |
| T2  | 7–12    | ✅ COMPLETA y **volcada al JSON** |
| T3  | 13–18   | ✅ COMPLETA y **volcada al JSON** |
| T4  | 19–24   | ✅ COMPLETA y **volcada al JSON** |
| T5  | 25–30   | ✅ recibida (pág. 25 leída por OCR; verificar puertas/vitrina/rejilla) |
| T6  | 31–36   | ✅ recibida (pendiente) |
| T7  | 37–42   | ✅ recibida (pendiente) |
| T8  | 43–48   | ✅ recibida COMPLETA (pendiente de volcar) |
| T9  | 49–54   | ✅ recibida (pendiente) |
| T10 | 55–60   | ✅ recibida COMPLETA (pendiente de volcar) |
| T11 | 61–66   | ✅ COMPLETA y **volcada al JSON** |
| T12 | 67–72   | ✅ COMPLETA y **volcada al JSON** |
| T13 | 73–78   | ✅ COMPLETA y **volcada al JSON** |
| T14 | 79–84   | ✅ recibida (pendiente) |
| T15 | 85–90   | ✅ recibida (pendiente) |
| T16 | 91–96   | ✅ recibida (pendiente) |
| T17 | 97–102  | ⚠️ recibida INCOMPLETA — faltan páginas 97 y 98 (Puertas/Vitrina y Bajos) |
| T18 | 103–108 | ✅ COMPLETA y **volcada al JSON** |
| T19 | 109–114 | ⚠️ recibida INCOMPLETA — faltan páginas 110, 113 y 114 (Bajos, Alto abatible/combinado/etc y Columnas/mediacolumnas/etc) |
| T20 | 115–120 | ✅ recibida (pendiente) |
| T21 | 121–126 | ✅ recibida (pendiente) |
| Glosario | 127–138 | ✅ recibido (descripciones + dibujos + accesorios) |

## Páginas que faltan (lista para reenviar)
- Ninguna — **¡las 126 páginas de tarifas están recibidas!** 🎉

**Total tarifa: 126 págs · Recibidas: 126 · Faltan: 0.**

## Próximo paso
Volcar al JSON (`mv_tarifas_oficiales.json`) las tarifas recibidas pero aún no volcadas:
T5, T6, T7, T8, T9, T10, T14, T15, T16, T17 (parcial), T19 (parcial), T20, T21
(T1-T4, T11, T12, T13 y T18 ya están volcadas). Se hará tarifa por tarifa, igual que T3/T4/T11/T12/T13/T18.
T17 y T19 están bloqueadas por páginas faltantes (ver secciones dedicadas más abajo); pendiente decidir con
el usuario si se espera al reenvío o se continúa con otra tarifa de la cola (T5, T6, T7, T9, T14, T15, T16,
T20, T21). T8, T10, T17 y T19 tienen páginas sin imagen disponible (43,44,45,48 de T8; 55,56 de T10;
97,98 de T17; 110,113,114 de T19) — pendiente de reenvío del usuario.

## Hallazgos de revisión (confirmados)
- Las tarifas son columnas independientes y crecientes (T1 < T2 < … < T21).
- TECHO COLOR sólo llega a TEC240 (TEC260–360 en blanco) y se repite en varias tarifas.
- REGLETA MELAMINA es constante en todas las tarifas.
- BALDA AÉREA aparece desde la T4.
- Acabados por tarifa registrados (SYNCRO, VIGO, AR PLUS, FERIA, REINA, POLILAMINADO, ZENIT, LUXE, TOKIO, FENIX, TEXT…) e incrementos (CONTRACARA +5%, DIFUMINADO +20%, METALIZADO +23%).
- Acabados con **puntos por tirador**: EDER TEXT = T7 +8 ptos/tirador, ZELAN TEXT = T7 +7 ptos/tirador.

## T3 — ✅ COMPLETA y volcada al JSON

Las 56 familias de T3 (páginas 13-18) están en `mv_tarifas_oficiales.json` (`tariffs.T3`), con el mismo
esquema que T1/T2. Verificado con `mv_tariff_importer.expand_tariffs`: los 715 productos generan
`zonePoints.T3` (antes 713, se completó `ENCM/E` en ELEMENTOS_LINEALES para igualar a `EMC1M/E`).

Pendiente: ejecutar `POST /libraries/MV/import-tariffs` (dry_run=false, wipe=true, admin) contra Mongo
para regenerar los `zonePoints` de los productos MV y que el selector de tarifa T1-T21 del Presupuestador
muestre precios distintos para T3.

Detalle de extracción (para referencia/auditoría):

### Página 18 (CONFIRMADO, listo para volcar cuando se complete T3)
Imágenes usadas: `IMG_20251101_091418.jpg` (índice 18). Crops en `/tmp/mvrot/p18_*.jpg`.

- **LATERALES_COLOR** (h7090): LCA=[17,20], LCF=[26,30], LCB=[26,null], LCS=[26,30], LCM=[34,42], LCC=[62,67]
- **REGLETA_COLOR** (h7090, ancho 15): RA=[8,9], RM=[10,12], RS=[12,13], RC=[19,20]
- **COSTADOS_COLOR** (h7090): CCA=[17.4,19.4], CCF=[26.8,30.8], CCB=[26.4,31.4], CCS=[26.4,31.4], CCM=[34.4,43.4], CCC=[69.4,74.4]
- **REGLETA_MELAMINA** (h7090, ancho 10): RMA=[1,2], RMM=[2,3], RMS=[3,4], RMC=[4,5] — **idéntico a T1/T2** (constante)
- **COSTADOS_MELAMINA**: no aparece impreso en la página 18 de T3 (a diferencia de T1/T2 que sí lo listan).
  Dado que en T1/T2 es idéntico ([19,20],[26,27],[7,8],[13,14]) y constante, se propone usar el mismo
  valor constante para T3 — **a confirmar con el usuario o buscando si aparece en otra página de T3**.
- **TECHO_COLOR** (h355060, cols 35/50/60) — **a diferencia de T1 (TEC260-360 en blanco), en T3 está
  TODO relleno hasta TEC360**:
  TEC100=[23.4,31,35.4], TEC120=[26.4,35,41.4], TEC140=[28.4,40,46.4], TEC160=[31.4,44,51.4],
  TEC180=[34.4,48,56.4], TEC200=[37.4,56,65.4], TEC220=[45.4,61,71.4], TEC240=[48.4,66,77.4],
  TEC260=[51.4,71,81.4], TEC280=[54.4,75,87.4], TEC300=[58.4,80,93.4], TEC320=[60.4,85,98.4],
  TEC340=[64.4,89,103.4], TEC360=[67.4,93,109.4]
- **ELEMENTOS_LINEALES** (ent_med): COR=[32,17], POR=[25,13], ZOC=[42,23], PER=[3,2] (=T1/T2),
  PIN=[null,2] (=T1/T2), ZOCA=[28,16] (=T1/T2), ZOCAB=[34,18] (=T1/T2), PINA=[null,2] (=T1/T2),
  ANGZOC=[null,2] (=T1/T2), **COST=[null,6]** (T1=4, T2=11 — valor distinto, posible lectura "6" a
  confirmar contra papel), EMC1M/E=[85,50] (=T1/T2). MOSE=[129,null], TANG/TLIN=[3,3],
  UENC=[null,3], COPM/E=[18,10], INT/EXT=[1,1], TAPAC=[null,1], TCAN=[null,1] — todos estos últimos
  **idénticos a T1/T2** (constantes).
  - Nota: la tabla de T3 imprime una fila extra "ENCM/E — Encimera Med/Ent" sin valores visibles,
    además de "EMC1M/E" con [85,50]. Probable duplicado/variante del mismo ítem en el catálogo;
    se usa solo `EMC1M/E` (como en T1) y se ignora `ENCM/E` salvo que el usuario indique lo contrario.

### Acabados T3 (de pág. 18, pie de página)
- FERIA = T3
- VIGO CTO CRISTAL = T3
- VIGO CTO SU COLOR = T3
- REINA = T3 -5%

### Anomalías a registrar en `_meta.notas_revision` cuando se vuelque T3
1. Los valores de T3 en PUERTAS/VITRINA/REJILLA (pág. 13) están cerca de T1 (algunos incluso por
   debajo), no por encima de T2 — rompe la suposición simple "T1<T2<T3<...". Confirmar que no es
   error de lectura antes de cerrar T3.
2. TECHO_COLOR en T3 llega hasta TEC360 (relleno completo), mientras que T1 solo llega a TEC240
   (TEC260-360 en blanco).
3. Algunos códigos de familia ALTO en el catálogo de T3 llevan sufijo "*" (p.ej. "A25D/I*") que no
   aparece en T1/T2 — decidir si afecta al nombrado de los items o es solo notación de "ver leyenda".

## T4 — ✅ COMPLETA y volcada al JSON

Las 57 familias de T4 (páginas 19-24, incluye `BALDA_AEREA` nueva desde T4) están en
`mv_tarifas_oficiales.json` (`tariffs.T4`). Verificado con `mv_tariff_importer.expand_tariffs`:
754 productos totales, solo 20 sin `zonePoints.T4` (CMBB-70/CMBC-70 + TEC260-360 x3 cols, igual
o mejor que T1/T2/T3 que tienen 39-41 huecos por las mismas razones — TECHO_COLOR de T4 solo llega
a TEC240, igual que T1).

T4 tiene **muchas más anomalías que T3** respecto al patrón "T3 < T4 < T2": quedaron registradas
en `_meta.notas_revision` (entrada `"tarifa": "T4"`), entre ellas:
- **REJILLA_CONFESIONARIO**: TODOS los valores de T4 son menores que T1 (la tarifa más barata) —
  anomalía fuerte, confirmada por zoom, pendiente de cotejar contra el papel.
- **ALTO_TERMINAL AT30D/I\*** = [42,47], muy por debajo de T1/T3/T2.
- **ALTILLO L50\*/L60\***: valores 70cm aparentemente intercambiados (L50=86 > L60=80).
- **SOBREENC_VITRINA SV30D/I y SV60**, **BAJO_TERMINAL BT30D/I y BTS30D/I**, **BAJO_5_CAJONES BC70**:
  por debajo de lo esperado (T3 o incluso T1).
- **LATERALES_COLOR/COSTADOS_COLOR**: LCM/CCM y LCC superan a T2 (T4>T2, invierte el orden esperado).
- **Patrón sistemático "T1 < T4 < T3"** (en vez de "T3 < T4 < T2") en familias completas:
  ALTO_DECORATIVO, BOTELLEROS, ALTILLOS_DECORATIVOS, y parcialmente MEDIACOLUMNA_VITRINA,
  ELEMENTOS_LINEALES (COR, ZOC, COST).

Pendiente: ejecutar `POST /libraries/MV/import-tariffs` (dry_run=false, wipe=true, admin) contra Mongo
para regenerar los `zonePoints` de los productos MV con T3 **y** T4 ya incluidos.

## T11 — ✅ COMPLETA y volcada al JSON

Las 57 familias de T11 (páginas 61-66) están en `mv_tarifas_oficiales.json` (`tariffs.T11`), con el mismo
esquema que T1/T3/T4. Verificado con `mv_tariff_importer.expand_tariffs`: 782 productos totales, 732 con
`zonePoints.T11` (50 sin valor — mismo patrón estructural que T1/T4: SOBREENCIMERA/SOBREENC_VITRINA/
SOBREENC_CAJON/SOBREENC_VIT_CAJON variantes H127, COSTADOS_MELAMINA-90, TECHO_COLOR TEC260-360, y
ENCM/E entero/medio — huecos ya presentes en T1/T3/T4 por las mismas familias).

Notas de extracción:
- VITRINA_INGLESA aparece en blanco en T11 (sin valores), igual que en T1-T4 → se omite.
- TECHO_COLOR de T11 solo llega a TEC240 (TEC260-360 en blanco), igual que T1.
- Páginas 62 (BAJOS) y 63 (ALTOS) requirieron recortes con zoom (PIL) para confirmar valores en el borde
  derecho de las tablas.
- No se ha hecho cruce numérico con T5-T10 todavía porque aún no están en el JSON.

Acabados T11 registrados en `_meta.acabados.T11`: ORLY/CADO/IBIZA BCO BRILLO/PALMA BCO BRILLO = T11;
TURIN RANURADO/ALAVA RANURADO/BURDEOS/MENDI/PARIS/IBIZA BCO SEDA MATE/PALMA BCO SEDA MATE = T11 -10%;
LACADO EFECTO GOMA = mismo precio; LACADO BRILLO COLOR = +12%.

## T12 — ✅ COMPLETA y volcada al JSON

Las 57 familias de T12 (páginas 67-72) están en `mv_tarifas_oficiales.json` (`tariffs.T12`), con el mismo
esquema que T1/T3/T4/T11. Verificado con `mv_tariff_importer.expand_tariffs`: 782 productos totales, 732
con `zonePoints.T12` (50 sin valor — mismos huecos estructurales que T11: SOBREENC* H127, COSTADOS_MELAMINA-90,
TECHO_COLOR TEC260-360, ENCM/E entero/medio).

Notas de extracción:
- VITRINA_INGLESA en blanco (igual que T1-T4/T11) → se omite.
- TECHO_COLOR solo llega a TEC240 (TEC260-360 en blanco), igual que T1/T11.
- ELEMENTOS_LINEALES imprime también una fila "ENCM/E" duplicada con los mismos valores que "EMC1M/E"
  ([85,50]); se usa solo EMC1M/E (igual que T1/T3).
- Acabados registrados en `_meta.acabados.T12`: DERBI HAYA=T12, DERBI CEREZO=T12+5%, DERBI MAPLE=T12+5%,
  DERBI ROBLE=T12; TABLERO PRECOMPUESTO +12%, TABLERO MARINO +20%.

## T13 — ✅ COMPLETA y volcada al JSON

Las 57 familias de T13 (páginas 73-78) están en `mv_tarifas_oficiales.json` (`tariffs.T13`), con el mismo
esquema que T1/T3/T4/T11/T12. Verificado con `mv_tariff_importer.expand_tariffs`: 782 productos totales,
732 con `zonePoints.T13` (50 sin valor — mismos huecos estructurales que T11/T12).

Notas de extracción:
- VITRINA_INGLESA en blanco (igual que T1-T4/T11/T12) → se omite.
- TECHO_COLOR solo llega a TEC240 (TEC260-360 en blanco).
- ELEMENTOS_LINEALES repite la fila "ENCM/E" duplicada con "EMC1M/E" ([85,50]); se usa solo EMC1M/E.
- Página 78 (LATERALES_COLOR, REGLETA_COLOR/MELAMINA, BALDA_AEREA, TECHO_COLOR, COSTADO_MELAMINA,
  ELEMENTOS_LINEALES, ALTILLOS_DECORATIVOS, BOTELLEROS) es **idéntica a T12**, salvo COSTADOS_COLOR
  (T13: CCA=[18,22], CCF=[30,35], CCB=[29,32], CCS=[31,35], CCM=[41,52], CCC=[85,93] vs T12: [18,24],
  [30,37],[29,36],[31,36],[41,54],[85,88]).
- Acabados: BOREAL HAYA=T13, BOREAL CEREZO=T13+5%, BOREAL MAPLE=T13+5%.

### Anomalías a registrar (confirmadas por zoom)
1. **BTP33D/I** (BAJO_TERMINAL) = 181, muy por encima de BT30D/I=96/BTZ30D/I=118 (en T12, BTP33D/I=119
   era similar a BT30D/I=96). Salto fuerte respecto a T12.
2. **ATP33D/I** (ALTO_TERMINAL) = [173,211], muy por encima de AT30D/I=[79,86] (en T12, ATP33D/I=[112,137]
   era similar a AT30D/I=[79,86]). Mismo patrón que BTP33D/I — posible cambio de precio real o error de
   imprenta, pendiente de cotejar contra el catálogo físico.
3. **AC45** (ALTO_COMBINADO) = [158,156], leve inversión (90 < 70 por 2 puntos), confirmado por zoom.

## T18 — ✅ COMPLETA y volcada al JSON

Las 58 familias de T18 (páginas 103-108) están en `mv_tarifas_oficiales.json` (`tariffs.T18`). Verificado
con `mv_tariff_importer.expand_tariffs`: 806 productos totales (subió de 782 porque se añadió
`VITRINA_INGLESA` como familia nueva, +24 productos), 756 con `zonePoints.T18` (50 sin valor — mismos
huecos estructurales que T11/T12/T13).

Notas de extracción:
- **Novedad**: T18 es la primera tarifa transcrita con **VITRINA_INGLESA con valores reales** (en
  T1-T4/T11-T13 aparece en blanco y se omite). Se añadió como familia `matrix` nueva con cols
  PVI30-PVI60 y filas 70/90/127/147. Esto añade 24 productos nuevos al catálogo total (de 782 a 806),
  que no tienen `zonePoints` para T1-T13/T17 (no se ha vuelto a esas tarifas para rellenar este hueco).
- TECHO_COLOR solo llega a TEC240 (TEC260-360 en blanco).
- ELEMENTOS_LINEALES repite la fila "ENCM/E" duplicada con "EMC1M/E" ([85,50]); se usa solo EMC1M/E.
- COST=[null,10] (en T11-T13 era [null,6]).
- Acabados: PIRINEO CASTAÑO=T18, CELTA CASTAÑO=T18, AROSA CASTAÑO=T18; TUDOR BLANCO +7%, PATINADO +3%,
  ACABADO ANTICUARIO +12%.

### Anomalía (patrón recurrente)
- **BTP33D/I** (BAJO_TERMINAL) = 154, por encima de BT30D/I=100/BTZ30D/I=124 — mismo patrón que la
  anomalía detectada en T13 (BTP33D/I=181, mucho más extrema).
- **ATP33D/I** (ALTO_TERMINAL) = [142,161], por encima de AT30D/I=[83,90] — mismo patrón que T13
  ([173,211], más extremo). Parece un patrón sistemático en estas dos referencias "P33" en varias
  tarifas; pendiente de cotejar contra el catálogo físico.

## T17 — ⚠️ INCOMPLETA, bloqueada
Faltan las páginas 97 (Puertas/Vitrina/Vitrina inglesa/Rejilla) y 98 (Bajos) de T17. El resto (99-102) sí
se recibió esta sesión. **No se puede volcar al JSON hasta recibir esas 2 páginas.**

## T19 — ⚠️ INCOMPLETA, bloqueada
Solo se han localizado las páginas 109 (Puertas/Vitrina/Vitrina inglesa/Rejilla), 111 (Altos, recibida por
duplicado) y 112 (Alto abatible/combinado/altillo/sobreencimera) de T19. Faltan las páginas 110 (Bajos),
113 (Columnas/mediacolumnas/botelleros/altillos decorativos) y 114 (Laterales/costados color/regletas/
balda aérea/techo color/elementos lineales + acabados). Se revisaron las 44 imágenes disponibles en la
sesión y ninguna corresponde a estas 3 páginas. **No se puede volcar al JSON hasta recibir esas 3 páginas.**

## Pendientes de trabajo (para continuar)
1. **Volcar T5–T10, T14–T17 (parcial), T19 (parcial), T20–T21** al JSON (vía OCR + verificación cruzada Tn
   entre Tn-1 y Tn+1), siguiendo el mismo método usado para T3/T4/T11/T12/T13/T18 (tabla por tabla, alta
   resolución, cruzando con tarifas vecinas para detectar shifts de fila por el desenfoque/perspectiva de
   las fotos, y zoom para confirmar anomalías). **T3, T4, T11, T12, T13 y T18 ya están completas** (ver
   secciones arriba). **T17 y T19 están bloqueadas** (ver secciones arriba) — siguiente disponible en la
   cola: alguna de T5, T6, T7, T9, T14, T15, T16, T20, T21 (pendiente confirmar cuáles tienen las 6
   páginas completas).
2. **Páginas pendientes de reenvío del usuario**:
   - T8: páginas 43, 44, 45, 48 (1, 2, 3 y 6 de la tarifa; ya se tienen 46 y 47).
   - T10: páginas 55, 56 (1 y 2 de la tarifa; ya se tienen 57, 58, 59, 60).
   - T17: páginas 97, 98 (1 y 2 de la tarifa; ya se tienen 99-102).
   - T19: páginas 110, 113, 114 (2, 5 y 6 de la tarifa; ya se tienen 109, 111, 112).
3. **VITRINA_INGLESA**: ahora que se sabe que algunas tarifas (T14, T18) tienen valores reales para esta
   familia, revisar T1-T4/T11-T13/T17 contra el papel para confirmar si realmente están en blanco o si
   se trata de páginas no enviadas/mal leídas.
   Tras completar cada Tn, ejecutar `import-tariffs` (dry-run y luego aplicar) para regenerar `zonePoints`.
2. **PDF de verificación** por tarifa para cotejar contra el papel antes de tocar precios.
3. **Corregir el catálogo MV** en BD (afecta a Presupuestador 1 y 2 a la vez) + quitar duplicados fantasma (p.ej. "A100" con precio de otra tarifa).
4. **Arreglar Presupuestador 1** (parcial, hecho hoy):
   - ✅ Selector de tarifa MV ampliado de T1-T15 a T1-T21 (`BudgetTable.jsx`, `MV_TARIFFS` en `constants.js`).
   - ✅ `pointValue` por defecto de la biblioteca MV corregido de 1.0 a 3.33 €/punto (`backend/routes/libraries.py`). Si la biblioteca MV ya existe en Mongo con `pointValue=1.0`, ejecutar `backend/scripts/fix_mv_point_value.py` para corregirla.
   - ✅ Código muerto `tariffPrices` eliminado de `BudgetTable.jsx` (siempre usa `zonePoints`).
   - Pendiente: nombres "TARIFA n" vs "Tn" siguen conviviendo (constants.js usa "TARIFA n" como label visible, "Tn" como clave interna — es el diseño actual, no se ha tocado); revisar scripts de import antiguos (`import_mv_catalog.py`, `mv_products_data.py`, `mv_products_v2.py`) que aún generan/usan `tariffPrices` y `TARIFA_1` — parecen código muerto/no usado por el flujo activo, pendiente de confirmar y eliminar.
5. **Presupuestador 2 — iconos/dibujos por mueble** (encargo del usuario): asociar cada familia/código a su icono. Decidir: dibujos recortados del catálogo vs iconos de línea limpios.
