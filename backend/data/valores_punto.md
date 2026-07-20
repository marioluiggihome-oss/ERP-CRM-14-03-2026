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
- **Grupo ACB**: coste = **netos tarifa −28%** (tarifa ACB × 0,72).
  - IMPORTANTE: el "−50% −28%" se aplica SOLO cuando se parte del precio
    PUBLICADO en el presupuestador de Cocina Desmontada, porque ese precio ya
    lleva el valor de punto ×2 (el −50% deshace el ×2 y el −28% es el descuento
    real). Sobre la tarifa neta (cascos.js) se aplica únicamente el −28%.
