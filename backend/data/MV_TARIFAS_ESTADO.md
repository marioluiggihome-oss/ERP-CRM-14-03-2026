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

## Nota sobre el error "solicitud demasiado grande"
La conversación acumuló >100 imágenes; el request supera el límite. Solución: **sesión nueva** (el repo conserva todo).
