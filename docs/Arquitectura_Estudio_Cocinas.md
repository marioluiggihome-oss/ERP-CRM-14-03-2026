# Auditoría y Arquitectura Unificada: Estudio de Cocinas

## 1. Auditoría del Estado Actual

Tras analizar el repositorio del ERP, se han identificado múltiples módulos y componentes que tratan de resolver partes del mismo problema (diseño de cocinas y renderizado con IA), pero de forma dispersa:

### Backend (Rutas y Servicios)
- `cocinasai.py`: Generación de renders a partir de planos/alzados usando `services.llm_vision` (Gemini).
- `kitchen_projects.py`: Gestión completa de proyectos 3D, wizard, medidas, muebles y llamadas a `luiggi_ai` (render y render-compose).
- `ai_engine.py`: Router del motor IA "LuiggiAI" que envuelve llamadas a un proveedor externo (Manus) para render, análisis y transcripción.
- `estudio_cocinas.py` (Nuevo): El router que acabamos de crear con render, edición, planos 2D y presentación.

### Frontend (Componentes)
- `CocinasIA.jsx`: Interfaz simple para generar renders desde planos.
- `KitchenDesigner3D.jsx`: Interfaz masiva (2000+ líneas) con gestión de proyectos, wizard de medidas, catálogo de puertas (ACB) y colores (Alvic), y generación de renders.
- `AIRenderStudio.jsx`: Interfaz tipo chat/estudio para generar renders por voz o texto, o seleccionando materiales.

**Problema Principal:** Hay duplicidad de esfuerzos. Tres componentes frontend distintos llamando a tres routers backend distintos para hacer tareas muy similares (renderizado de cocinas).

---

## 2. Propuesta de Arquitectura Unificada

Para simplificar el mantenimiento y mejorar la experiencia del usuario, propongo unificar todo bajo un único gran módulo llamado **Estudio de Cocinas**.

### El Nuevo Módulo: `EstudioCocinas`

Este módulo consolidará las funcionalidades de los tres componentes anteriores en una interfaz por pestañas (Tabs), manteniendo todo el código organizado.

#### Pestañas (Tabs) del Frontend:
1. **Proyectos (KitchenDesigner3D refactorizado):** Gestión de clientes, medidas, wizard de diseño y catálogo de materiales.
2. **Render Studio (AIRenderStudio refactorizado):** Generación de renders por IA (texto, voz, planos).
3. **Planos 2D:** Generación automática de planos técnicos acotados basados en las medidas del proyecto.
4. **Presentaciones:** Generación de fichas técnicas y presentaciones comerciales HTML para clientes.

#### Backend Unificado:
- Se mantendrá `kitchen_projects.py` para el CRUD de la base de datos.
- Se mantendrá `ai_engine.py` como el core de IA (abstracción del proveedor).
- Se potenciará `estudio_cocinas.py` para manejar las nuevas capacidades exclusivas (Planos 2D con matplotlib, Fichas Markdown, Presentaciones HTML).

---

## 3. Plan de Implementación

1. **Backend:** Ya hemos creado `estudio_cocinas.py` con los endpoints necesarios (`/plano`, `/ficha`, `/presentacion`).
2. **Frontend:** Crearemos un nuevo componente `EstudioCocinas.jsx` que actuará como contenedor (Wrapper) de los componentes existentes y añadirá las nuevas pestañas de Planos y Presentaciones.
3. **Integración:** Actualizaremos `App.js` para registrar esta nueva vista principal, ocultando las antiguas (`CocinasIA`, `AIRenderStudio`) bajo este nuevo paraguas para no romper el código existente, pero mejorando la UX.
