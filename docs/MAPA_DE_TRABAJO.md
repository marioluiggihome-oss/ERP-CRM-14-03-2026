# Mapa de trabajo — LUIGGI HOME ERP

> Hoja de ruta para dar más valor a la aplicación. Enfoque acordado:
> **primero pulir (uso interno), luego productizar para vender a otras cocinas.**

## Las 4 palancas de valor
1. **Que la IA acierte de verdad** — subir el % de acierto del catálogo en el
   analizador de planos y el digitalizador. *Es el mayor diferenciador.*
2. **Flujo completo sin fricción** — Presupuesto → Pedido → Factura (y fábrica)
   con menos pasos.
3. **Control y márgenes** — rentabilidad por proyecto, ranking comercial, alertas.
4. **Productizar para vender** — multiempresa, altas self-service, cuotas (Stripe).

---

## Tareas pendientes (descubiertas durante el trabajo)

### 🔴 Estabilidad / build (prioridad máxima)
- [x] Render de Facturas/Mando (estaban en blanco).
- [x] Build del frontend fallaba por JSX roto en `BudgetTable.jsx` (2 `</div>`).
- [x] Build del frontend fallaba por bloque duplicado/corrupto en `DespieceCatalog.jsx`.
- [x] **Añadir CI (GitHub Action) que compile el frontend en cada PR** para que un
      error de sintaxis NUNCA llegue a producción ni rompa el deploy.
      → `.github/workflows/frontend-build.yml` (Node 18 + yarn, misma config que el
      deploy de Railway).

### 🟠 IA — acierto del catálogo (palanca 1)
- [x] Estabilidad: `temperature=0` en el análisis (resultados repetibles).
- [x] Volcado al presupuesto: usar el match confirmado del backend (código, medidas,
      puntos) en vez de re-buscar en el catálogo del frontend.
- [ ] **Emparejamiento por tipo + medida**: cuando no hay código exacto, buscar el
      producto del MISMO tipo (alto/bajo/columna) con el ancho más cercano, en vez de
      devolver "el primero que entre por dimensiones".
- [ ] **Tratar electrodomésticos/fregaderos aparte** (campana, horno, fregadero…):
      no son muebles del catálogo → no contarlos como "error", marcarlos como accesorio.
- [ ] **Mejorar el prompt** para que los códigos sugeridos cuadren con el formato real
      del catálogo ZC.
- [ ] **Cargar el catálogo ZC también en el frontend** (o devolver `zonePoints` desde el
      backend) para que la valoración por zona sea exacta tras el volcado.

### 🟡 Flujo presupuesto → factura (palanca 2)
- [ ] Botón "Convertir presupuesto en pedido" y "Pedido → Factura" con un clic.
- [ ] Enviar pedido a fábrica desde el presupuesto.

### 🟡 Control y márgenes (palanca 3)
- [ ] Margen/rentabilidad por proyecto (coste vs PVP).
- [ ] Mejoras en el Panel de Mando (ya existe base).

### 🟢 Productización (palanca 4 — fase 2)
- [ ] Multiempresa (multi-tenant).
- [ ] Alta de clientes self-service + planes de precio (Stripe).
- [ ] Onboarding y datos de demo.

### ⚙️ Configuración / despliegue
- [x] `GEMINI_API_KEY` (AIza…) en el backend + restringida a "solo API de Gemini".
- [x] `REACT_APP_BACKEND_URL` correcto en el frontend.
- [ ] Plantear unificar/limpiar los dos servicios de Railway si procede.
- [ ] Subir la nueva **tarifa ZC** al repo cuando esté lista.
