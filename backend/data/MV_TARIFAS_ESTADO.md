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

## T14, T15, T17 — ✅ VOLCADAS al JSON (esta sesión). T16 — ⚠️ VOLCADA PARCIAL (16/58 familias)

Verificado con `mv_tariff_importer.expand_tariffs`: T14=756, T15=756, T17=756 productos con `zonePoints`
(igual que T18, incluye VITRINA_INGLESA real). **T16 solo tiene 226/756** — faltan las familias ALTO*,
SOBREENC*, COLUMNA*, MEDIACOLUMNA*, BOTELLEROS, ALTILLOS_DECORATIVOS, LATERALES/COSTADOS_COLOR,
REGLETA*, BALDA_AEREA, TECHO_COLOR, COSTADOS_MELAMINA, ELEMENTOS_LINEALES — **pendiente releer las
imágenes de T16 págs. 93-96 (4 imágenes) en una sesión nueva** para completarlas (los datos de la
sesión anterior al compactado no se confirmaron con re-lectura fresca, así que no se volcaron para
evitar transcribir errores al JSON).

Pendiente tras completar T16: ejecutar `POST /libraries/MV/import-tariffs` (dry_run=true primero,
luego `dry_run=false&wipe=true`, admin) para regenerar `zonePoints` en Mongo.

### Detalle de extracción T14/T15/T16(parcial)/T17 (referencia/auditoría)

**IMPORTANTE para la próxima sesión**: estos datos ya están transcritos de las fotos del catálogo
(páginas 79-102) y NO requieren volver a leer imágenes. Solo falta darles el mismo formato JSON que
T13 (`tariffs.T13` en `mv_tarifas_oficiales.json`) y pegarlos en `tariffs.T14`, `tariffs.T15`,
`tariffs.T16`, `tariffs.T17`. **T17 ya está COMPLETA** (las 6 páginas, incluida la que faltaba antes
con ALTO/ALTO_VITRINA/etc., pág. 99) — ya NO está bloqueada.

Estructura por familia: igual que T13 (mismas claves de family, mismo `type`: `single`, `dual`,
`matrix`, `h7090`, `h127147`, `h200220`, `h355060`, `ent_med`). `VITRINA_INGLESA` SÍ tiene valores
reales en T14, T15, T16 y T17 (igual que T18) — familia `matrix` cols PVI30-PVI60, filas 70/90/127/147.

### T14 (páginas 79-84)
- PUERTAS (matrix P25/P30/P35/P40/P45/P50/P60): 14:[-,20,22,23,24,26,28] · 28:[-,27,27,27,29,30,34] · 40:[-,36,39,42,45,48,54] · 56:[-,36,39,42,45,48,54] · 70:[42,42,45,49,52,56,64] · 90:[50,50,54,59,63,68,76] · 127:[-,68,74,79,85,92,104] · 147:[-,81,88,95,103,110,125]
- VITRINA (PV30-60): 28:[31,32,33,34,35,39] · 40:[41,45,48,51,55,62] · 70:[47,52,57,62,68,77] · 90:[56,63,69,76,82,93] · 127:[76,85,95,104,113,128] · 147:[91,102,113,125,136,154]
- VITRINA_INGLESA (PVI30-60): 70:[71,78,86,93,102,116] · 90:[84,95,104,114,123,140] · 127:[114,128,143,156,170,192] · 147:[137,153,170,188,204,231]
- REJILLA_CONFESIONARIO (PR30-60): 70:[48,54,59,65,70,83] · 90:[59,66,73,81,86,101] · 127:[80,90,100,109,120,139] · 147:[95,107,119,130,142,216] ⚠️ último valor (216) parece alto vs progresión de la fila, revisar zoom contra papel
- BAJO (single): B25D/I=73,B30D/I=74,B35D/I=78,B40D/I=82,B45D/I=87,B50D/I=90,B60D/I=101,B60=120,B70=128,B80=137,B90=145,B100=154
- BAJO_FREGADERO (dual normal/chapa): BF45D/I=[82,88],BF50D/I=[86,92],BF60D/I=[96,102],BF60=[115,121],BF70=[123,129],BF80=[130,137],BF90=[137,144],BF100=[145,153],BF120=[162,175]
- BAJO_RINCON_ESCUADRA: BRI95D/I=159,BRU95D/I=157
- BAJO_RINCON_CIEGO: BR90D/I=128,BR95D/I=129,BR100D/I=130,BR105D/I=132,BR110D/I=134
- BAJO_HORNO: BH60=64,BHC60=74,BHZ60=103,BHG60=108
- BAJO_TERMINAL: BT30D/I=96,BTS30D/I=103,BTZ30D/I=119,BTP33D/I=161
- BAJO_PUERTA_CAJON: BPC30D/I=116,BPC35D/I=121,BPC40D/I=126,BPC45D/I=132,BPC50D/I=138,BPC60D/I=147,BPC60=203,BPC70=214,BPC80=223,BPC90=235,BPC100=246
- BAJO_5_CAJONES: BC30=250,BC35=258,BC40=266,BC45=276,BC50=285,BC60=301,BC70=372,BC80=389,BC90=401
- BAJO_3CAJ_1GAV: BCG30=211,BCG35=216,BCG40=221,BCG45=229,BCG50=237,BCG60=251,BCG70=305,BCG80=309,BCG90=313
- BAJO_2GAV_1CAJ: BGC30=173,BGC35=176,BGC40=178,BGC45=185,BGC50=191,BGC60=215,BGC70=290,BGC80=294,BGC90=299
- BAJO_2CAJ_1GAV_1FRENTE: BCGF60=226,BCGF70=254,BCGF80=264,BCGF90=276
- BAJO_2GAV_1FRENTE: BGF60=174,BGF70=227,BGF80=233,BGF90=246,BGF120=270
- ALTO (h7090): A25D/I=[71,80],A30D/I=[71,81],A35D/I=[75,86],A40D/I=[79,91],A45D/I=[83,96],A50D/I=[88,101],A60D/I=[97,111],A60=[117,134],A70=[125,144],A80=[132,154],A90=[140,164],A100=[149,174]
- ALTO_VITRINA: AV30D/I=[76,87],AV35D/I=[82,94],AV40D/I=[88,101],AV45D/I=[93,108],AV50D/I=[99,115],AV60D/I=[110,128],AV60=[126,147],AV70=[137,161],AV80=[149,175],AV90=[160,189],AV100=[172,204]
- ALTO_CAMPANA: ASCE60D/I=[82,96],ASCE60=[101,115],ASCE90=[121,140],ASC60D/I=[78,91],ASC60=[97,111]
- ALTO_ESCURREPLATOS: AE45D/I=[89,105],AE50D/I=[94,112],AE60D/I=[105,123],AE60=[125,147],AE70=[132,157],AE80=[141,167],AE90=[150,179],AE100=[158,190]
- ALTO_RINCON_CIEGO: AR60D/I=[119,137],AR65D/I=[124,143]
- ALTO_MICROONDAS: AM60D/I=[69,88],AM60=[91,106],AMF60D/I=[90,104],AMF60=[109,123]
- ALTO_RINCON_ESCUADRA: ARI65D/I=[151,169],ARU65D/I=[149,167]
- ALTO_CALENTADOR: ACA45D/I=[76,88],ACA50D/I=[80,92],ACA60D/I=[88,101],ACA60=[107,124]
- ALTO_RINCON_CHAFLAN: ARC63D/I=[95,108],ARCV63D/I=[103,118]
- ALTO_CALDERA: ACC60D/I=[119,134],ACC60=[146,164]
- ALTO_DECORATIVO: AD40=[74,92],AD45=[79,98],AD50=[83,104],AD60=[92,116],AD70=[101,127],AD80=[110,139],AD90=[119,151],AD100=[128,163]
- ALTO_SOBREFRIGO: ASF60D/I=[82,95],ASF60=[101,114],ASF60A=[92,105],ASF60F=[112,125]
- ALTO_TERMINAL: AT30D/I=[79,86],ATP33D/I=[153,180]
- ALTO_ABATIBLE: AA45=[135,148],AA50=[140,153],AA60=[169,186],AA70=[177,196],AA80=[184,206],AA90=[192,216],AA100=[201,226]
- ALTO_COMBINADO: AC45=[141,161],AC50=[147,166],AC60=[177,196],AC70=[184,206],AC80=[193,219],AC90=[201,229],AC100=[212,227]
- ALTO_COMBINADO_PLUS: ACP45=[133,154],ACP50=[137,162],ACP60=[160,188],ACP70=[177,197],ACP80=[184,199],ACP90=[192,213],ACP100=[203,228]
- ALTO_COMBINADO_PLUS_J: ACPJ45=[140,161],ACPJ50=[142,169],ACPJ60=[165,202],ACPJ70=[182,205],ACPJ80=[193,206],ACPJ90=[201,220],ACPJ100=[212,225]
- ALTILLO: L30=[91,96],L35=[95,98],L40=[98,102],L45=[101,105],L50=[104,109],L60=[110,131],L70=[113,134],L80=[116,137],L90=[119,140],L100=[122,143]
- ALTILLO_VITRINA: LV30=[96,101],LV35=[101,105],LV40=[104,110],LV45=[107,115],LV50=[114,121],LV60=[118,144],LV70=[121,147],LV80=[126,154],LV90=[129,157],LV100=[138,167]
- SOBREENCIMERA (h127147): S30D/I=[104,117],S35D/I=[110,126],S40D/I=[118,134],S45D/I=[124,142],S50D/I=[131,150],S60D/I=[145,166],S60=[175,202]
- SOBREENC_VITRINA: SV30D/I=[113,128],SV35D/I=[122,140],SV40D/I=[133,152],SV45D/I=[143,164],SV50D/I=[152,175],SV60D/I=[169,195],SV60=[192,223]
- SOBREENC_CAJON: SC30D/I=[141,155],SC35D/I=[148,165],SC40D/I=[158,174],SC45D/I=[166,184],SC50D/I=[174,193],SC60D/I=[191,212],SC60=[231,258]
- SOBREENC_VIT_CAJON: SVC30D/I=[150,165],SVC35D/I=[160,179],SVC40D/I=[172,192],SVC45D/I=[184,207],SVC50D/I=[196,219],SVC60D/I=[215,241],SVC60=[248,279]
- COLUMNA_DESPENSERO (h200220): CD30D/I=[179,189],CD35D/I=[190,201],CD40D/I=[202,213],CD45D/I=[213,225],CD50D/I=[224,237],CD60D/I=[248,261],CD60=[297,315],CD70=[317,335],CD80=[353,353] ⚠️ revisar (mismo valor en ambas columnas, posible error de imprenta),CD90=[358,376]
- COLUMNA_FRIGO: CF60D/I=[113,125],CF60=[131,144],CF60A=[123,135],CF60F=[143,155]
- COLUMNA_HORNO: CH60D/I=[202,218],CH60=[240,260],CHPC60D/I=[248,264],CHPC60=[285,306],CHGC60D/I=[300,316],CHGC60=[319,339],CHC60D/I=[404,418],CHC60=[424,442]
- COLUMNA_HORNO_MICRO: CHM60D/I=[194,211],CHM60=[236,254],CHMG60D/I=[240,257],CHMG60=[264,282],CHMC60D/I=[349,366],CHMC60=[373,391],CHMCG60D/I=[305,322],CHMCG60=[329,347]
- MEDIACOLUMNA: M30D/I=113,M35D/I=120,M40D/I=128,M45D/I=135,M50D/I=142,M60D/I=156,M60=186
- MEDIA_PUERTA_GAVETA: MPG30D/I=160,MPG35D/I=168,MPG40D/I=176,MPG45D/I=184,MPG50D/I=193,MPG60D/I=211,MPG60=241
- MEDIACOLUMNA_HORNO: MPH60D/I=117,MPH60=136,MPM60D/I=128,MPM60=152,MGHM60=118,MCHM60=151
- MEDIACOLUMNA_VITRINA: MV30D/I=122,MV35D/I=132,MV40D/I=143,MV45D/I=153,MV50D/I=163,MV60D/I=181,MV60=204
- MEDIACOL_VITRINA_GAVETA: MVG30D/I=166,MVG35D/I=176,MVG40D/I=186,MVG45D/I=197,MVG50D/I=209,MVG60D/I=229,MVG60=244
- BOTELLEROS (dual 7/9): BOA=[68,82],BOS=[109,123],BOC=[161,175]
- ALTILLOS_DECORATIVOS: LD30=42,LD35=45,LD40=47,LD45=50,LD50=53,LD60=58,LD70=64,LD80=70,LD90=75,LD100=81
- LATERALES_COLOR (h7090): LCA=[20,24],LCF=[31,37],LCB=[32,null],LCS=[33,36],LCM=[42,54],LCC=[81,88]
- COSTADOS_COLOR: CCA=[18,22],CCF=[30,35],CCB=[29,36],CCS=[31,35],CCM=[41,52],CCC=[85,93]
- REGLETA_COLOR (ancho 15): RA=[7,9],RM=[10,13],RS=[13,14],RC=[21,22]
- REGLETA_MELAMINA (ancho 10): RMA=[1,2],RMM=[2,3],RMS=[3,4],RMC=[4,5]
- COSTADOS_MELAMINA: CMCB=[19,20],CMCC=[27,28],CMBB=[8,null],CMBC=[15,null]
- BALDA_AEREA (h355060, 35/50/60): BAL30=[21,26,30],BAL40=[26,35,40],BAL50=[29,38,43],BAL60=[33,44,50],BAL90=[44,60,70],BAL100=[48,66,77],BAL120=[56,78,91],BAL140=[63,89,105],BAL160=[70,101,119],BAL180=[78,112,132],BAL200=[87,127,150],BAL220=[100,140,165],BAL240=[108,153,179]
- TECHO_COLOR (h355060): TEC100=[26,36,42],TEC120=[30,42,50],TEC140=[34,48,57],TEC160=[38,54,64],TEC180=[42,60,71],TEC200=[47,68,81],TEC220=[54,76,89],TEC240=[58,83,97], TEC260-360=null (igual que T1/T11-T13)
- ELEMENTOS_LINEALES (ent_med): COR=[53,27],POR=[36,19],ZOC=[31,16],PER=[3,2],PIN=[null,2],ZOCA=[28,16],ZOCAB=[34,18],PINA=[null,2],ANGZOC=[null,2],COST=[null,6],EMC1M/E=[85,50] (ENCM/E duplicado, ignorar),MOSE=[129,null],TANG/TLIN=[3,3],UENC=[null,3],COPM/E=[18,10],INT/EXT=[1,1],TAPAC=[null,1],TCAN=[null,1]

### T15 (páginas 85-90)
- PUERTAS: 14:[-,25,27,29,32,33,37] · 28:[-,37,37,37,40,43,47] · 40:[-,50,54,57,61,65,72] · 56:[-,50,54,57,61,65,72] · 70:[57,57,61,66,70,74,85] · 90:[69,69,74,79,85,90,100] · 127:[-,89,96,103,110,117,131] · 147:[-,107,116,124,132,141,158]
- VITRINA: 28:[39,39,40,41,45,50] · 40:[52,57,60,64,68,76] · 70:[58,64,70,76,82,93] · 90:[71,78,85,92,100,111] · 127:[93,103,113,123,133,149] · 147:[111,123,135,147,159,179]
- VITRINA_INGLESA: 70:[87,96,105,114,123,140] · 90:[107,117,128,138,150,167] · 127:[140,155,170,185,200,224] · 147:[167,185,203,221,239,269]
- REJILLA_CONFESIONARIO: 70:[60,67,72,77,84,97] · 90:[74,81,89,96,103,118] · 127:[96,107,118,128,138,159] · 147:[115,127,139,152,164,190]
- BAJO: B25D/I=90,B30D/I=91,B35D/I=96,B40D/I=102,B45D/I=106,B50D/I=111,B60D/I=123,B60=152,B70=162,B80=173,B90=182,B100=193
- BAJO_FREGADERO (dual): BF45D/I=[102,107],BF50D/I=[106,113],BF60D/I=[118,125],BF60=[146,153],BF70=[156,163],BF80=[165,173],BF90=[174,181],BF100=[183,192],BF120=[209,223]
- BAJO_RINCON_ESCUADRA: BRI95D/I=195,BRU95D/I=193
- BAJO_RINCON_CIEGO: BR90D/I=162,BR95D/I=167,BR100D/I=172,BR105D/I=177,BR110D/I=180
- BAJO_HORNO: BH60=76,BHC60=86,BHZ60=117,BHG60=120
- BAJO_TERMINAL: BT30D/I=107,BTS30D/I=116,BTZ30D/I=133,BTP33D/I=209
- BAJO_PUERTA_CAJON: BPC30D/I=138,BPC35D/I=144,BPC40D/I=151,BPC45D/I=159(de img:159? ver nota)=172 ⚠️revisar,BPC50D/I=179,BPC60D/I=244,BPC60=258,BPC70=271,BPC80=285,BPC90=299,BPC100=299 — **OJO: la fila BAJO_PUERTA_CAJON de T15 (imagen pg.86) hay que re-confirmar BPC45D/I y BPC100, posible desfase de fila**
- BAJO_5_CAJONES: BC30=280,BC35=292,BC40=303,BC45=317,BC50=330,BC60=352,BC70=372,BC80=380,BC90=473 ⚠️ revisar BC90 (salto grande vs BC80)
- BAJO_3CAJ_1GAV: BCG30=240,BCG35=248,BCG40=256,BCG45=267,BCG50=278,BCG60=297,BCG70=364,BCG80=368,BCG90=373
- BAJO_2GAV_1CAJ: BGC30=203,BGC35=206,BGC40=210,BGC45=218,BGC50=227,BGC60=243,BGC70=334,BGC80=338,BGC90=343
- BAJO_2CAJ_1GAV_1FRENTE: BCGF60=271,BCGF70=374,BCGF80=384,BCGF90=396
- BAJO_2GAV_1FRENTE: BGF60=214,BGF70=247,BGF80=296,BGF90=309,BGF120=333
- ALTO (h7090): A25D/I=[88,100],A30D/I=[89,102],A35D/I=[93,107],A40D/I=[98,113],A45D/I=[103,119],A50D/I=[108,125],A60D/I=[120,137],A60=[148,173],A70=[158,185],A80=[168,197],A90=[177,208],A100=[187,220]
- ALTO_VITRINA: AV30D/I=[90,104],AV35D/I=[96,111],AV40D/I=[103,119],AV45D/I=[109,127],AV50D/I=[116,135],AV60D/I=[128,149],AV60=[151,178],AV70=[164,193],AV80=[177,209],AV90=[190,225],AV100=[202,240]
- ALTO_CAMPANA: ASCE60D/I=[102,118],ASCE60=[130,147],ASCE90=[155,176],ASC60D/I=[99,113],ASC60=[125,142]
- ALTO_ESCURREPLATOS: AE45D/I=[109,129],AE50D/I=[115,136],AE60D/I=[127,149],AE60=[157,186],AE70=[166,199],AE80=[177,211],AE90=[187,224],AE100=[197,236]
- ALTO_RINCON_CIEGO: AR60D/I=[151,176],AR65D/I=[156,181]
- ALTO_MICROONDAS: AM60D/I=[85,108],AM60=[114,135],AMF60D/I=[112,128],AMF60=[139,157]
- ALTO_RINCON_ESCUADRA: ARI65D/I=[186,210],ARU65D/I=[183,208]
- ALTO_CALENTADOR: ACA45D/I=[95,110],ACA50D/I=[99,116],ACA60D/I=[110,125],ACA60=[138,162]
- ALTO_RINCON_CHAFLAN: ARC63D/I=[116,131],ARCV63D/I=[120,137]
- ALTO_CALDERA: ACC60D/I=[142,163],ACC60=[181,208]
- ALTO_DECORATIVO: AD40=[82,103],AD45=[87,109],AD50=[92,116],AD60=[103,129],AD70=[113,142],AD80=[123,156],AD90=[133,168],AD100=[143,183]
- ALTO_SOBREFRIGO: ASF60D/I=[103,117],ASF60=[130,145],ASF60A=[113,127],ASF60F=[133,147]
- ALTO_TERMINAL: AT30D/I=[89,96],ATP33D/I=[199,237]
- ALTO_ABATIBLE: AA45=[155,171],AA50=[160,177],AA60=[200,225],AA70=[210,237],AA80=[229,260],AA90=[229,260] ⚠️ revisar AA90 (igual que AA80, posible desfase),AA100=[239,272]
- ALTO_COMBINADO: AC45=[158,179],AC50=[163,185],AC60=[204,231],AC70=[213,243],AC80=[224,256],AC90=[233,267],AC100=[246,285]
- ALTO_COMBINADO_PLUS: ACP45=[137,161],ACP50=[140,170],ACP60=[173,209],ACP70=[177,197]⚠️revisar(salto pequeño vs ACP60),ACP80=[184,199]⚠️,ACP90=[192,213]⚠️,ACP100=[219,247] — **re-confirmar ACP70/80/90 de T15 contra papel: en la imagen aparecían iguales a T14**
- ALTO_COMBINADO_PLUS_J: ACPJ45=[144,168],ACPJ50=[145,177],ACPJ60=[178,223],ACPJ70=[182,205]⚠️,ACPJ80=[193,206]⚠️,ACPJ90=[201,220]⚠️,ACPJ100=[228,254] — mismo aviso que ACP (revisar 70/80/90)
- ALTILLO: L30=[107,111],L35=[114,115],L40=[115,119],L45=[119,123],L50=[123,128],L60=[130,132],L70=[137,165],L80=[144,172],L90=[151,179],L100=[158,186]
- ALTILLO_VITRINA: LV30=[109,112],LV35=[114,118],LV40=[118,123],LV45=[122,129],LV50=[126,136],LV60=[134,166],LV70=[141,173],LV80=[154,183],LV90=[157,190],LV100=[168,204]
- SOBREENCIMERA (h127147): S30D/I=[128,146],S35D/I=[136,156],S40D/I=[144,165],S45D/I=[151,174],S50D/I=[159,183],S60D/I=[174,201],S60=[220,256]
- SOBREENC_VITRINA: SV30D/I=[132,151],SV35D/I=[143,164],SV40D/I=[153,176],SV45D/I=[164,189],SV50D/I=[175,202],SV60D/I=[193,223],SV60=[228,265]
- SOBREENC_CAJON: SC30D/I=[170,189],SC35D/I=[180,200],SC40D/I=[190,211],SC45D/I=[200,223],SC50D/I=[210,234],SC60D/I=[230,257],SC60=[285,322]
- SOBREENC_VIT_CAJON: SVC30D/I=[175,193],SVC35D/I=[187,208],SVC40D/I=[200,223],SVC45D/I=[213,238],SVC50D/I=[226,253],SVC60D/I=[248,278],SVC60=[294,330]
- COLUMNA_DESPENSERO (h200220): CD30D/I=[221,234],CD35D/I=[233,249],CD40D/I=[247,263],CD45D/I=[260,276],CD50D/I=[273,290],CD60D/I=[300,318],CD60=[375,400],CD70=[395,421],CD80=[412,438],CD90=[436,461]
- COLUMNA_FRIGO: CF60D/I=[136,151],CF60=[163,179],CF60A=[146,161],CF60F=[166,181]
- COLUMNA_HORNO: CH60D/I=[247,267],CH60=[305,332],CHPC60D/I=[302,323],CHPC60=[358,385],CHGC60D/I=[363,383],CHGC60=[392,419],CHC60D/I=[471,488],CHC60=[500,525]
- COLUMNA_HORNO_MICRO: CHM60D/I=[240,259],CHM60=[296,314]⚠️revisar(en imagen CHM60D/I y CHM60G/I se solapan),CHMG60D/I=[296,314],CHMG60=[330,351],CHMC60D/I=[416,435],CHMC60=[450,471],CHMCG60D/I=[361,379],CHMCG60=[395,416]
- MEDIACOLUMNA: M30D/I=138,M35D/I=146,M40D/I=155,M45D/I=163,M50D/I=171,M60D/I=188,M60=233
- MEDIA_PUERTA_GAVETA: MPG30D/I=196,MPG35D/I=205,MPG40D/I=213,MPG45D/I=224,MPG50D/I=235,MPG60D/I=257,MPG60=302
- MEDIACOLUMNA_HORNO: MPH60D/I=141,MPH60=169,MPM60D/I=156,MPM60=193,MGHM60=136,MCHM60=169
- MEDIACOLUMNA_VITRINA: MV30D/I=142,MV35D/I=153,MV40D/I=165,MV45D/I=176,MV50D/I=187,MV60D/I=205,MV60=241
- MEDIACOL_VITRINA_GAVETA: MVG30D/I=197,MVG35D/I=208,MVG40D/I=218,MVG45D/I=231,MVG50D/I=245,MVG60D/I=267,MVG60=304
- BOTELLEROS (dual 7/9): BOA=[75,90],BOS=[121,137],BOC=[179,194]
- ALTILLOS_DECORATIVOS: LD30=46,LD35=50,LD40=53,LD45=55,LD50=59,LD60=65,LD70=71,LD80=78,LD90=84,LD100=90
- LATERALES_COLOR: LCA=[21,25],LCF=[31,36],LCB=[33,null],LCS=[34,38],LCM=[44,56],LCC=[84,91]
- COSTADOS_COLOR: CCA=[19,23],CCF=[32,39],CCB=[30,38],CCS=[32,36],CCM=[42,54],CCC=[89,97]
- REGLETA_COLOR: RA=[8,10],RM=[11,14],RS=[14,16],RC=[23,25]
- REGLETA_MELAMINA: RMA=[1,2],RMM=[2,3],RMS=[3,4],RMC=[4,5]
- COSTADOS_MELAMINA: CMCB=[19,20],CMCC=[27,28],CMBB=[8,null],CMBC=[15,null]
- BALDA_AEREA: BAL30=[23,29,33],BAL40=[29,39,44],BAL50=[32,42,48],BAL60=[36,48,56],BAL90=[48,67,79],BAL100=[54,74,88],BAL120=[61,88,102],BAL140=[70,100,117],BAL160=[79,112,132],BAL180=[88,125,148],BAL200=[96,144,168],BAL220=[111,158,184],BAL240=[120,170,199]
- TECHO_COLOR: TEC100=[29,40,47],TEC120=[33,47,55],TEC140=[38,54,64],TEC160=[43,61,72],TEC180=[47,68,80],TEC200=[52,78,91],TEC220=[60,85,100],TEC240=[65,92,108], TEC260-360=null
- ELEMENTOS_LINEALES: COR=[55,28],POR=[38,20],ZOC=[32,17],PER=[3,2],PIN=[null,2],ZOCA=[28,16],ZOCAB=[34,18],PINA=[null,2],ANGZOC=[null,2],COST=[null,8],EMC1M/E=[85,50],MOSE=[129,null],TANG/TLIN=[3,3],UENC=[null,3],COPM/E=[18,10],INT/EXT=[1,1],TAPAC=[null,1],TCAN=[null,1]
- Acabados (pie pág.90): JERTE CEREZO=T15, JERTE MAPLE=T15, JERTE MARINO=T15-10%, JERTE MARCO DE 7=T15+13%, BURDEOS MAPLE=T15+10%, TENERIFE MAPLE=T15+10%

### T16 (páginas 91-96) — transcrito parcialmente en esta sesión, faltan páginas 93-96 por re-confirmar con zoom (datos del resumen previo, sin re-lectura fresca esta vez)
- PUERTAS: 14:[-,15,16,17,18,21,25] · 28:[-,23,23,24,29,29,31] · 40:[-,27,29,31,33,35,39] · 56:[-,33,36,38,41,44,50] · 70:[36,37,40,44,47,50,57] · 90:[44,46,49,53,57,61,69] · 127:[-,59,64,70,75,80,91] · 147:[-,72,78,84,91,97,110]
- VITRINA: 28:[36,37,38,46,47,49]⚠️(PV45=46 rompe monotonía con PV40=38, revisar) · 40:[42,46,49,52,56,63] · 70:[58,62,64,67,69,76] · 90:[69,72,74,79,81,86] · 127:[83,86,90,95,98,105] · 147:[98,101,105,112,115,123]
- VITRINA_INGLESA: 70:[87,93,96,100,104,114] · 90:[104,108,111,119,122,129] · 127:[125,129,135,143,147,158] · 147:[147,152,158,168,173,185]
- REJILLA_CONFESIONARIO: 70:[44,49,53,57,62,72] · 90:[54,60,65,71,75,87] · 127:[71,79,86,93,101,116] · 147:[84,93,101,110,119,137]
- BAJO: B25D/I=66,B30D/I=68,B35D/I=71,B40D/I=75,B45D/I=79,B50D/I=83,B60D/I=92,B60=108,B70=116,B80=124,B90=132,B100=139
- BAJO_FREGADERO: BF45D/I=[75,80],BF50D/I=[79,84],BF60D/I=[88,94],BF60=[104,110],BF70=[111,117],BF80=[118,124],BF90=[124,131],BF100=[132,139],BF120=[146,158]
- BAJO_RINCON_ESCUADRA: BRI95D/I=146,BRU95D/I=144
- BAJO_RINCON_CIEGO: BR90D/I=116,BR95D/I=120,BR100D/I=123,BR105D/I=127,BR110D/I=132
- BAJO_HORNO: BH60=58,BHC60=68,BHZ60=95,BHG60=97
- BAJO_TERMINAL: BT30D/I=95,BTS30D/I=102,BTZ30D/I=118,BTP33D/I=144
- BAJO_PUERTA_CAJON: BPC30D/I=105,BPC35D/I=110,BPC40D/I=114,BPC45D/I=120,BPC50D/I=127,BPC60D/I=138,BPC60=183,BPC70=192,BPC80=202,BPC90=213,BPC100=226
- BAJO_5_CAJONES: BC30=218,BC35=226,BC40=232,BC45=243,BC50=259,BC60=279,BC70=342,BC80=362,BC90=370
- BAJO_3CAJ_1GAV: BCG30=186,BCG35=191,BCG40=196,BCG45=209,BCG50=219,BCG60=233,BCG70=281,BCG80=285,BCG90=290
- BAJO_2GAV_1CAJ: BGC30=155,BGC35=158,BGC40=162,BGC45=175,BGC50=180,BGC60=189,BGC70=267,BGC80=271,BGC90=276
- BAJO_2CAJ_1GAV_1FRENTE: BCGF60=209,BCGF70=276,BCGF80=286,BCGF90=298
- BAJO_2GAV_1FRENTE: BGF60=161,BGF70=217,BGF80=229,BGF90=242,BGF120=266
- (Resto de familias de T16 — ALTO*, SOBREENC*, COLUMNA*, MEDIACOLUMNA*, BOTELLEROS, ALTILLOS_DECORATIVOS, LATERALES/COSTADOS_COLOR, REGLETA*, BALDA_AEREA, TECHO_COLOR, COSTADOS_MELAMINA, ELEMENTOS_LINEALES, acabados): **datos disponibles en el resumen de la sesión anterior** (páginas 93-96 ya fueron leídas antes del compactado de contexto) — pendiente sólo de volcarlos al JSON, no de releer fotos. Si no aparecen en este documento al continuar, releer las imágenes de T16 págs. 93-96 una vez más (4 imágenes) para no perder precisión.

### T17 (páginas 97-102) — ✅ AHORA COMPLETA (ya no falta nada, las páginas 97-98 que antes faltaban llegaron en esta sesión)
- PUERTAS: 14:[-,13,14,15,16,18,21] · 28:[-,23,23,24,30,30,31] · 40:[-,27,29,32,34,36,40] · 56:[-,34,37,40,43,46,53] · 70:[37,37,41,45,48,52,61] · 90:[47,48,51,55,60,64,72] · 127:[-,60,67,73,79,86,98] · 147:[-,74,81,89,97,104,120]
- VITRINA: 28:[27,28,29,36,37,37]⚠️(PV45=36 rompe monotonía, revisar) · 40:[32,35,38,41,43,48] · 70:[40,43,47,51,55,62] · 90:[48,53,58,62,67,74] · 127:[62,69,75,82,88,97] · 147:[74,82,90,97,106,116]
- VITRINA_INGLESA: 70:[60,65,71,77,83,93] · 90:[72,80,87,93,101,111] · 127:[93,104,113,123,132,146] · 147:[111,123,135,146,159,174]
- REJILLA_CONFESIONARIO: 70:[41,46,49,53,58,67] · 90:[51,56,61,66,71,81] · 127:[65,73,80,86,93,107] · 147:[79,86,94,102,110,127]
- BAJO: B25D/I=71,B30D/I=72,B35D/I=77,B40D/I=81,B45D/I=85,B50D/I=89,B60D/I=100,B60=114,B70=123,B80=132,B90=141,B100=149
- BAJO_FREGADERO: BF45D/I=[81,86],BF50D/I=[85,91],BF60D/I=[95,102],BF60=[109,116],BF70=[117,124],BF80=[125,132],BF90=[132,140],BF100=[140,149],BF120=[153,167]
- BAJO_RINCON_ESCUADRA: BRI95D/I=156,BRU95D/I=155
- BAJO_RINCON_CIEGO: BR90D/I=123,BR95D/I=129,BR100D/I=131,BR105D/I=136,BR110D/I=141
- BAJO_HORNO: BH60=60,BHC60=70,BHZ60=102,BHG60=104
- BAJO_TERMINAL: BT30D/I=99,BTS30D/I=106,BTZ30D/I=123,BTP33D/I=150
- BAJO_PUERTA_CAJON: BPC30D/I=110,BPC35D/I=115,BPC40D/I=120,BPC45D/I=126,BPC50D/I=132,BPC60D/I=144,BPC60=190,BPC70=200,BPC80=209,BPC90=221,BPC100=234
- BAJO_5_CAJONES: BC30=222,BC35=228,BC40=233,BC45=243,BC50=257,BC60=274,BC70=341,BC80=354,BC90=363
- BAJO_3CAJ_1GAV: BCG30=191,BCG35=196,BCG40=200,BCG45=213,BCG50=222,BCG60=234,BCG70=282,BCG80=286,BCG90=291
- BAJO_2GAV_1CAJ: BGC30=163,BGC35=166,BGC40=169,BGC45=184,BGC50=188,BGC60=195,BGC70=276,BGC80=280,BGC90=285
- BAJO_2CAJ_1GAV_1FRENTE: BCGF60=209,BCGF70=277,BCGF80=287,BCGF90=299
- BAJO_2GAV_1FRENTE: BGF60=166,BGF70=227,BGF80=238,BGF90=251,BGF120=275
- ALTO (h7090): A25D/I=[68,79],A30D/I=[69,81],A35D/I=[74,85],A40D/I=[78,90],A45D/I=[82,95],A50D/I=[86,100],A60D/I=[96,110],A60=[111,132],A70=[119,140],A80=[126,150],A90=[136,160],A100=[144,171]
- ALTO_VITRINA: AV30D/I=[72,82],AV35D/I=[76,87],AV40D/I=[81,93],AV45D/I=[85,98],AV50D/I=[89,103],AV60D/I=[98,112],AV60=[115,134],AV70=[124,145],AV80=[133,156],AV90=[142,166],AV100=[151,177]
- ALTO_CAMPANA: ASCE60D/I=[83,95],ASCE60=[98,110],ASCE90=[120,135],ASC60D/I=[68,90],ASC60=[81,104]
- ALTO_ESCURREPLATOS: AE45D/I=[88,105],AE50D/I=[93,111],AE60D/I=[104,122],AE60=[119,146],AE70=[128,154],AE80=[136,164],AE90=[145,176],AE100=[154,187]
- ALTO_RINCON_CIEGO: AR60D/I=[131,152],AR65D/I=[118,139]⚠️revisar(menor que AR60D/I, raro)
- ALTO_RINCON_ESCUADRA: ARI65D/I=[148,169],ARU65D/I=[145,167]
- ALTO_CALENTADOR: ACA45D/I=[74,86],ACA50D/I=[78,91],ACA60D/I=[86,99],ACA60=[101,121]
- ALTO_RINCON_CHAFLAN: ARC63D/I=[95,108],ARCV63D/I=[97,110]
- ALTO_CALDERA: ACC60D/I=[108,119],ACC60=[130,139]
- ALTO_DECORATIVO: AD40=[94,121],AD45=[101,130],AD50=[107,139],AD60=[121,158],AD70=[135,177],AD80=[148,195],AD90=[162,214],AD100=[175,233]
- ALTO_SOBREFRIGO: ASF60D/I=[72,94],ASF60=[85,108],ASF60A=[82,104],ASF60F=[102,114]
- ALTO_TERMINAL: AT30D/I=[81,88],ATP33D/I=[140,173]
- ALTO_MICROONDAS: AM60D/I=[69,89],AM60=[86,104],AMF60D/I=[92,110],AMF60=[107,118]
- ALTO_ABATIBLE: AA45=[134,147],AA50=[138,152],AA60=[163,184],AA70=[171,192],AA80=[178,202],AA90=[188,212],AA100=[196,223]
- ALTO_COMBINADO: AC45=[141,152],AC50=[145,157],AC60=[171,187],AC70=[173,195],AC80=[180,204],AC90=[190,214],AC100=[198,226]
- ALTO_COMBINADO_PLUS: ACP45=[143,155],ACP50=[147,163],ACP60=[168,190],ACP70=[175,197],ACP80=[181,206],ACP90=[191,216],ACP100=[205,229]
- ALTO_COMBINADO_PLUS_J: ACPJ45=[150,162],ACPJ50=[152,170],ACPJ60=[173,204],ACPJ70=[180,205],ACPJ80=[190,208],ACPJ90=[200,219],ACPJ100=[209,236]
- ALTILLO: L30=[85,95],L35=[87,99],L40=[90,112],L45=[93,126],L50=[95,127],L60=[100,128],L70=[105,134],L80=[110,140],L90=[115,146],L100=[120,152]
- ALTILLO_VITRINA: LV30=[90,98],LV35=[93,101],LV40=[96,104],LV45=[100,109],LV50=[102,112],LV60=[108,129],LV70=[109,135],LV80=[113,140],LV90=[118,146],LV100=[122,151]
- SOBREENCIMERA (h127147): S30D/I=[100,114],S35D/I=[106,123],S40D/I=[114,131],S45D/I=[121,139],S50D/I=[128,148],S60D/I=[142,165],S60=[164,191]
- SOBREENC_VITRINA: SV30D/I=[102,116],SV35D/I=[109,124],SV40D/I=[117,132],SV45D/I=[124,141],SV50D/I=[132,149],SV60D/I=[142,162],SV60=[169,194]
- SOBREENC_CAJON: SC30D/I=[130,145],SC35D/I=[137,154],SC40D/I=[147,163],SC45D/I=[155,174],SC50D/I=[165,184],SC60D/I=[182,205],SC60=[214,241]
- SOBREENC_VIT_CAJON: SVC30D/I=[133,146],SVC35D/I=[140,156],SVC40D/I=[149,165],SVC45D/I=[158,175],SVC50D/I=[168,186],SVC60D/I=[183,202],SVC60=[239,244]⚠️revisar(salto raro vs SVC60D/I)
- COLUMNA_DESPENSERO (h200220): CD30D/I=[174,186],CD35D/I=[185,197],CD40D/I=[197,209],CD45D/I=[208,222],CD50D/I=[220,234],CD60D/I=[244,258],CD60=[281,302],CD70=[301,322],CD80=[318,340],CD90=[342,361]
- COLUMNA_FRIGO: CF60D/I=[116,127],CF60=[131,141],CF60A=[126,137],CF60F=[146,157]
- COLUMNA_HORNO: CH60D/I=[201,216],CH60=[229,253],CHPC60D/I=[244,260],CHPC60=[272,297],CHGC60D/I=[292,308],CHGC60=[306,330],CHC60D/I=[377,391],CHC60=[392,414]
- COLUMNA_HORNO_MICRO: CHM60D/I=[194,208],CHM60=[229,243],CHMG60D/I=[237,251],CHMG60=[256,270],CHMC60D/I=[327,341],CHMC60=[347,360],CHMCG60D/I=[302,316],CHMCG60=[321,335]
- MEDIACOLUMNA: M30D/I=110,M35D/I=117,M40D/I=125,M45D/I=131,M50D/I=140,M60D/I=155,M60=177
- MEDIA_PUERTA_GAVETA: MPG30D/I=147,MPG35D/I=154,MPG40D/I=161,MPG45D/I=173,MPG50D/I=180,MPG60D/I=195,MPG60=215
- MEDIACOLUMNA_HORNO: MPH60D/I=117,MPH60=131,MPM60D/I=128,MPM60=151,MGHM60=113,MCHM60=146
- MEDIACOLUMNA_VITRINA: MV30D/I=112,MV35D/I=120,MV40D/I=128,MV45D/I=135,MV50D/I=144,MV60D/I=155,MV60=181
- MEDIACOL_VITRINA_GAVETA: MVG30D/I=148,MVG35D/I=155,MVG40D/I=162,MVG45D/I=175,MVG50D/I=182,MVG60D/I=194,MVG60=218
- BOTELLEROS (dual 7/9): BOA=[71,85],BOS=[113,127],BOC=[166,180]
- ALTILLOS_DECORATIVOS: LD30=43,LD35=46,LD40=49,LD45=52,LD50=55,LD60=60,LD70=66,LD80=72,LD90=78,LD100=83
- LATERALES_COLOR: LCA=[20,25],LCF=[32,38],LCB=[33,null],LCS=[34,37],LCM=[44,55],LCC=[83,90]
- COSTADOS_COLOR: CCA=[19,23],CCF=[31,36],CCB=[30,37],CCS=[32,36],CCM=[42,54],CCC=[88,95]
- REGLETA_COLOR: RA=[8,10],RM=[11,13],RS=[13,15],RC=[22,24]
- REGLETA_MELAMINA: RMA=[1,2],RMM=[2,3],RMS=[3,4],RMC=[4,5]
- COSTADOS_MELAMINA: CMCB=[19,20],CMCC=[27,28],CMBB=[8,null],CMBC=[15,null]
- BALDA_AEREA: BAL30=[22,28,32],BAL40=[26,37,43],BAL50=[28,40,46],BAL60=[31,42,49],BAL90=[35,47,54],BAL100=[47,65,75],BAL120=[52,71,83],BAL140=[60,84,98],BAL160=[68,96,112],BAL180=[75,108,127],BAL200=[84,120,141],BAL220=[93,137,160],BAL240=[107,151,177]
- TECHO_COLOR: TEC100=[28,39,45],TEC120=[33,46,53],TEC140=[37,52,61],TEC160=[41,58,69],TEC180=[46,65,76],TEC200=[50,74,87],TEC220=[58,82,96],TEC240=[62,89,104], TEC260-360=null
- ELEMENTOS_LINEALES: COR=[54,28],POR=[37,19],ZOC=[32,17],PER=[3,2],PIN=[null,2],ZOCA=[28,16],ZOCAB=[34,18],PINA=[null,2],ANGZOC=[null,2],COST=[null,8],EMC1M/E=[85,50],MOSE=[null,129]⚠️revisar(en T13-T15 MOSE=[129,null]; en T17 imagen parece "MOSE...129" bajo columna única, igual semántica que "Mostrador solo Entero"→debería ser [129,null] salvo error de transcripción),TANG/TLIN=[3,3],UENC=[null,3],COPM/E=[18,10],INT/EXT=[1,1],TAPAC=[null,1],TCAN=[null,1]
- Acabados (pie pág.102): DUNA=T17, TUDOR BLANCO incremento 7%

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
