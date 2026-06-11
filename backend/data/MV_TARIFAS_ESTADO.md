# Tarifas MV — Estado del proyecto (resumen de páginas)

> Última actualización: cierre de jornada. Continúa mañana.
> Fuente: escaneos CamScanner del catálogo MV (Muebles Valencia). Cada tarifa = 6 páginas.
> Datos crudos en `mv_tarifas_oficiales.json`. **Nada conectado aún al presupuestador.**

## Mapa del catálogo
- **Tarifas de precio (columnas de puntos T1…T21): páginas 1–126** (cada tarifa, 6 páginas).
- **Glosario / dibujos de cada mueble + accesorios: páginas 127 en adelante.**
- Valor del punto MV ≈ **3,33 €/punto**. Cada tarifa es **independiente** (no multiplicador).

## Estructura de cada tarifa (6 páginas)
1. Puertas / Vitrina / Vitrina inglesa / Rejilla
2. Bajos (todas las familias de bajo)
3. Altos (todas las familias de alto)
4. Alto abatible / combinado / combinado plus / altillo / sobreencimera
5. Columnas / mediacolumnas / botelleros / altillos decorativos
6. Laterales/Costados color / regletas / balda aérea / techo color / elementos lineales (+ acabados de esa tarifa)

## Estado por tarifa

| Tarifa | Páginas | Estado |
|--------|---------|--------|
| T1  | 1–6     | ✅ COMPLETA y **volcada al JSON** |
| T2  | 7–12    | ✅ COMPLETA y **volcada al JSON** |
| T3  | 13–18   | ✅ recibida (pendiente de volcar) |
| T4  | 19–24   | ✅ recibida (pendiente) |
| T5  | 25–30   | ✅ recibida (pág. 25 leída por OCR; verificar puertas/vitrina/rejilla) |
| T6  | 31–36   | ✅ recibida (pendiente) |
| T7  | 37–42   | ✅ recibida (pendiente) |
| T8  | 43–48   | ⚠️ FALTAN **46, 47** (tengo 43,44,45,48) |
| T9  | 49–54   | ✅ recibida (pendiente) |
| T10 | 55–60   | ⚠️ FALTAN **57,58,59,60** (tengo 55,56) |
| T11 | 61–66   | ❌ SIN RECIBIR |
| T12 | 67–72   | ❌ SIN RECIBIR |
| T13 | 73–78   | ❌ SIN RECIBIR |
| T14 | 79–84   | ❌ SIN RECIBIR |
| T15 | 85–90   | ❌ SIN RECIBIR |
| T16 | 91–96   | ❌ SIN RECIBIR |
| T17 | 97–102  | ❌ SIN RECIBIR |
| T18 | 103–108 | ❌ SIN RECIBIR |
| T19 | 109–114 | ⚠️ FALTAN **109, 111, 112** (tengo 110,113,114) |
| T20 | 115–120 | ✅ recibida (pendiente) |
| T21 | 121–126 | ✅ recibida (pendiente) |
| Glosario | 127–138 | ✅ recibido (descripciones + dibujos + accesorios) |

## Páginas que faltan (lista para reenviar)
- **T8:** 46, 47
- **T10:** 57, 58, 59, 60
- **T11:** 61, 62, 63, 64, 65, 66
- **T12:** 67, 68, 69, 70, 71, 72
- **T13:** 73, 74, 75, 76, 77, 78
- **T14:** 79, 80, 81, 82, 83, 84
- **T15:** 85, 86, 87, 88, 89, 90
- **T16:** 91, 92, 93, 94, 95, 96
- **T17:** 97, 98, 99, 100, 101, 102
- **T18:** 103, 104, 105, 106, 107, 108
- **T19:** 109, 111, 112

**Total tarifa: 126 págs · Recibidas: 69 · Faltan: 57.**

## Hallazgos de revisión (confirmados)
- Las tarifas son columnas independientes y crecientes (T1 < T2 < … < T21).
- TECHO COLOR sólo llega a TEC240 (TEC260–360 en blanco) y se repite en varias tarifas.
- REGLETA MELAMINA es constante en todas las tarifas.
- BALDA AÉREA aparece desde la T4.
- Acabados por tarifa registrados (SYNCRO, VIGO, AR PLUS, FERIA, REINA, POLILAMINADO, ZENIT, LUXE, TOKIO, FENIX, TEXT…) e incrementos (CONTRACARA +5%, DIFUMINADO +20%, METALIZADO +23%).
- Acabados con **puntos por tirador**: EDER TEXT = T7 +8 ptos/tirador, ZELAN TEXT = T7 +7 ptos/tirador.

## Pendientes de trabajo (para continuar)
1. **Volcar T3–T21** al JSON (vía OCR + verificación cruzada Tn entre Tn-1 y Tn+1).
2. **PDF de verificación** por tarifa para cotejar contra el papel antes de tocar precios.
3. **Corregir el catálogo MV** en BD (afecta a Presupuestador 1 y 2 a la vez) + quitar duplicados fantasma (p.ej. "A100" con precio de otra tarifa).
4. **Arreglar Presupuestador 1**: selector de tarifa, fallback silencioso a T1, nombres "TARIFA n" vs "Tn", pointValue por defecto, código muerto `tariffPrices`.
5. **Presupuestador 2 — iconos/dibujos por mueble** (encargo del usuario): asociar cada familia/código a su icono. Decidir: dibujos recortados del catálogo vs iconos de línea limpios.
