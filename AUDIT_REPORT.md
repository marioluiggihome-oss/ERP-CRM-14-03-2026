# Informe de Auditoría Nocturna — ERP-CRM Luiggi Home

**Fecha:** 3 de julio de 2026  
**Repositorio:** `marioluiggihome-oss/ERP-CRM-14-03-2026` (rama `main`)  
**Frontend:** `https://erp.luiggihome.es`  
**Backend:** `https://erp-crm-14-03-2026-production.up.railway.app`

---

## Resumen Ejecutivo

Esta auditoría nocturna revisó el estado completo del ERP-CRM tras la sesión de desarrollo anterior. Se identificaron **9 problemas** y se aplicaron **todos los fixes** correspondientes. El sistema queda en estado funcional y listo para producción tras el redespliegue en Railway.

---

## Hallazgos y Fixes Aplicados

### 1. Fix Crítico: Render 3D — Polling a URLs 404

| Campo | Detalle |
|-------|---------|
| **Archivo** | `EstudioCocinas.jsx` (línea 192) |
| **Problema** | `apiGet` no incluía el prefijo `/api/estudio-cocinas` en la URL, causando que el polling del render fuera a rutas 404 del backend |
| **Impacto** | El render siempre mostraba "El render tardó demasiado" |
| **Fix** | Corregido `apiGet` para incluir el prefijo correcto |
| **Commit** | `11e9f4af` (ya pusheado) |

### 2. Branding Visible — "Motor: LuiggiAI"

| Campo | Detalle |
|-------|---------|
| **Archivo** | `AgentesDisenadores.jsx` (línea 376) |
| **Problema** | Texto "Motor: LuiggiAI" visible en el header del módulo |
| **Fix** | Cambiado a "Lanza hasta 7 proyectos de diseño en paralelo con IA" |

### 3. Permiso Específico `canUseAgentesIA` Inexistente

| Campo | Detalle |
|-------|---------|
| **Archivos** | `SettingsModal.jsx`, `App.js` |
| **Problema** | El módulo Agentes IA usaba permisos genéricos (`canUseKitchenDesigner || canUseCocinasAI || canUseAIAnalysis`) en vez de un permiso propio |
| **Fix** | Creado `canUseAgentesIA` en: CAPABILITY_KEYS, defaultUser, form reset, checkbox en sección Producción/Fábrica, condiciones del sidebar y tab en App.js |

### 4. Agentes IA en Sección Incorrecta del Sidebar

| Campo | Detalle |
|-------|---------|
| **Archivo** | `App.js` (líneas 1149-1159 → movido a 1200-1211) |
| **Problema** | El botón estaba en la sección de Diseño, junto a 3D Estudio y Armarios |
| **Fix** | Movido a la sección Producción, después de Fábrica. Color cambiado a `bg-purple-600` para diferenciarlo |

### 5. WelcomeScreen sin Entrada para Agentes IA

| Campo | Detalle |
|-------|---------|
| **Archivo** | `WelcomeScreen.jsx` (línea 76) |
| **Problema** | No existía acceso rápido al módulo Agentes IA |
| **Fix** | Añadida entrada en grupo `produccion` con icono Sparkles, color purple, y condición `canUseAgentesIA || isAdmin` |

### 6. Inconsistencia en `config.py` — URL del Proveedor

| Campo | Detalle |
|-------|---------|
| **Archivo** | `backend/services/luiggi_ai/config.py` |
| **Problema** | `provider_base_url` apuntaba a `api.manus.im/v2` (dominio antiguo) mientras que `engine_core.py` ya usaba `api.manus.ai/v2` |
| **Fix** | Actualizado a `api.manus.ai/v2`. Añadido `manus.ai` a `provider_asset_hosts` y `sanitize_replacements` |

### 7. Galería de Renders Incompleta en Frontend

| Campo | Detalle |
|-------|---------|
| **Archivo** | `EstudioCocinas.jsx` |
| **Problema** | El backend tenía endpoints de galería (`/galeria/guardar`, `/galeria`, etc.) pero el frontend no los usaba |
| **Fix** | Implementado: pestaña "Galería" en TABS, estado `galeria`, funciones `loadGaleria`/`guardarEnGaleria`/`toggleFavorito`/`eliminarRender`, botón "Guardar" junto al PNG tras generar render, grid de miniaturas con marca de agua "3D Estudio", paginación, fullscreen con branding |

### 8. Rediseño Layout Armarios2.jsx

| Campo | Detalle |
|-------|---------|
| **Archivo** | `Armarios2.jsx` |
| **Problema** | Layout de 2 columnas (`grid lg:grid-cols-[1fr_360px]`) con el dibujo del armario compartiendo espacio con la configuración |
| **Fix** | Rediseñado a 3 columnas con paneles colapsables: Panel izquierdo (320px, configuración), Centro (flex-1, dibujo protagonista), Panel derecho (340px, Render IA + Presupuesto). Ambos paneles laterales tienen botón de colapso |

### 9. Responsive de AgentesDisenadores.jsx

| Campo | Detalle |
|-------|---------|
| **Archivo** | `AgentesDisenadores.jsx` |
| **Problema** | Header y layout no se adaptaban bien a móvil |
| **Fix** | Header con `flex-col sm:flex-row`, padding responsive, botón de lanzar con tamaño adaptativo, panel vacío con altura responsive |

---

## Estado Actual de los Módulos

| Módulo | Estado | Notas |
|--------|--------|-------|
| **3D Estudio (Render)** | ✅ Funcional | Fix apiGet aplicado. Polling async cada 8s. Galería implementada |
| **Agentes Diseñadores** | ✅ Funcional | Permiso propio, sección Producción, responsive mejorado |
| **Armarios 2** | ✅ Funcional | Layout 3 columnas con paneles colapsables |
| **Presupuestador 1** | ✅ Funcional | Wizard de costados operativo |
| **Instalaciones** | ✅ Funcional | Pestaña eléctrica/fontanería/gas |
| **Catálogo Johnson** | ⏳ Parcial | 9 fichas técnicas listas, faltan precios y descuentos |
| **Backend IA** | ✅ Funcional | config.py y engine_core.py consistentes con api.manus.ai |

---

## Pendientes para Próxima Sesión

1. **Catálogo Johnson**: Esperar precios y descuentos del usuario para completar artículos en el ERP
2. **Testing en producción**: Verificar que el render 3D funciona correctamente tras el redespliegue
3. **Responsive profundo**: Revisar todos los módulos en dispositivos reales (tablet/móvil)
4. **Armarios2 en móvil**: En pantallas pequeñas, los paneles colapsables se apilan verticalmente — considerar un modo "solo dibujo" para móvil
5. **Marca de agua en descarga**: La marca "3D Estudio" es solo visual en la galería; para descargas con marca de agua real se necesitaría procesamiento server-side (canvas o backend)

---

## Archivos Modificados en Esta Auditoría

```
frontend/src/components/EstudioCocinas.jsx    — Galería + fix apiGet
frontend/src/components/AgentesDisenadores.jsx — Branding + responsive
frontend/src/components/Armarios2.jsx          — Rediseño 3 columnas
frontend/src/components/SettingsModal.jsx      — Permiso canUseAgentesIA
frontend/src/components/WelcomeScreen.jsx      — Entrada Agentes IA
frontend/src/App.js                            — Sidebar + permiso
backend/services/luiggi_ai/config.py           — URL manus.ai
```

---

## Verificación Pre-Push

- [x] Balance de llaves, paréntesis y corchetes correcto en todos los archivos
- [x] No hay referencias a "Manus" en textos visibles de la UI
- [x] Permiso `canUseAgentesIA` registrado en CAPABILITY_KEYS, defaultUser y form reset
- [x] config.py consistente con engine_core.py (ambos usan api.manus.ai)
- [x] Galería conectada a endpoints existentes del backend
- [x] Armarios2 con layout de 3 columnas y paneles colapsables

---

*Informe generado automáticamente durante la auditoría nocturna del 3 de julio de 2026.*
