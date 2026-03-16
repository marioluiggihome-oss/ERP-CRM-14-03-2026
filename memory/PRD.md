# LUIGGI HOME - Kitchen Budgeting ERP/CRM

## Estado: EN DESARROLLO ACTIVO
## Última Actualización: 15 Marzo 2026

---

## ✅ COMPLETADO EN ESTA SESIÓN

### 1. Precios MV TARIFA 1 - CORREGIDOS Y AUDITADOS
- ✅ **383 productos MV** con precios T1 verificados
- ✅ Precios extraídos directamente de las imágenes de tarifas del usuario
- ✅ Campos actualizados: `T1`, `points`, `tariffPrices`

**Verificación de precios TARIFA 1:**
| Código | T1 Esperado | T1 Actual | Estado |
|--------|-------------|-----------|--------|
| A100 | 68 | 68 | ✅ |
| A25D/I | 36 | 36 | ✅ |
| A30D/I | 37 | 37 | ✅ |
| A60D/I | 46 | 46 | ✅ |
| B25D/I | 54 | 54 | ✅ |
| B60 | 72 | 72 | ✅ |
| B80 | 80 | 80 | ✅ |
| B100 | 90 | 90 | ✅ |

### 2. Precios TARIFA 2 - AGREGADOS
- ✅ Campo `tariffPrices.T2` actualizado para todos los productos
- ✅ Precios extraídos de las 5 imágenes de TARIFA 2

### 3. Error Guardar Casco - SOLUCIONADO
- ✅ Insertados 7 materiales en la BD (4 ZC, 3 MV)

### 4. Analizador de Planos IA
- ✅ Filtrado por biblioteca activa (ZC/MV)
- ✅ Indicador visual de catálogo

---

## PRECIOS TARIFA 1 (MV) - REFERENCIA

### ALTOS (sin variante altura en T1)
| Código | T1 |
|--------|-----|
| A25D/I | 36 |
| A30D/I | 37 |
| A40D/I | 39 |
| A50D/I | 51 |
| A60D/I | 46 |
| A70 | 55 |
| A80 | 48 |
| A90 | 59 |
| A100 | 68 |

### BAJOS
| Código | T1 |
|--------|-----|
| B25D/I | 54 |
| B30D/I | 56 |
| B40D/I | 62 |
| B60 | 72 |
| B80 | 80 |
| B100 | 90 |

### ALTILLOS (con variantes H70/H90)
| Código | H70 | H90 |
|--------|-----|-----|
| L30 | 81 | 104 |
| L60 | 105 | 127 |
| L100 | 131 | 147 |

---

## 📋 PENDIENTE

### P1 - Alta
- [ ] Casco por defecto por sección/biblioteca
- [ ] Restaurar logo empresa

### P2 - Media  
- [ ] Refactorización BudgetTable.jsx
- [ ] Bug "Despiece" (PAUSADO)

### P3 - Baja
- [ ] Refactorización SettingsModal.jsx, server.py
- [ ] Glitch sidebar colapsado

---

## CREDENCIALES
- **Usuario:** MARIO
- **Contraseña:** MARIO

## BASE DE DATOS
- **DB:** luiggi_home
- **Productos ZC:** 4542
- **Productos MV:** 383 (todos con precios T1 y T2)
- **Materiales:** 7 (4 ZC, 3 MV)
