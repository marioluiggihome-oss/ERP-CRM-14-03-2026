# Valores de punto configurados (referencia para cálculos)

Fuente: Ajustes → Precios (Panel Maestro). Actualizado 20/07/2026.

| Módulo | Campo | Valor | Nota |
|---|---|---|---|
| Cocina Desmontada (presupuestador de cascos) | `cascosPointValue` / `pointValueDesmontada` | **2,0 €/punto** | Venta = tarifa ACB × 2. La tarifa ACB (cascos en kit) está cargada en `frontend/src/data/cascos.js`. |
| Cocina Montada (despiece) | `pointValueDespiece` | 0,88 | Según backup settings. |
| Cocina Montada | `pointValueMontada` | 1,0 | Según backup settings. |
| MV (Muebles Valencia) | `pointValue` MV | 3,33 | Ver `mv_tarifas_oficiales.json` (`_meta.pointValue`). |

## Descuentos de compra de cascos (vigentes 20/07/2026)
- **Montakit**: −25% sobre su tarifa de cascos (columna del acabado que aplique).
- **Grupo ACB**: −50% y sobre el resultado −28% (factor 0,36) sobre la tarifa ACB
  publicada (la misma que está cargada como base en Cocina Desmontada).
