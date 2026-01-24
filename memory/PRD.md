# LUIGGI HOME - ERP/CRM para Presupuestos de Cocinas

## Última Actualización: 25/01/2026

---

## RESUMEN DEL SISTEMA

LUIGGI HOME es un ERP/CRM completo para la gestión de presupuestos de cocinas y armarios, incluyendo:
- Gestión de usuarios con roles (Admin, Comercial, Tienda, Colaborador Comercial)
- Presupuestador técnico con cálculo automático de precios
- Módulo de Armarios con diseñador visual y despiece
- CRM completo con calendario, contactos y oportunidades
- Digitalizador de borradores con IA
- Importador de catálogo IA
- Sistema de backups automáticos

---

## ESTADO ACTUAL - 25/01/2026

### ✅ COMPLETADO HOY

| # | Funcionalidad | Descripción |
|---|--------------|-------------|
| 1 | **Importación masiva de productos** | 1,027 productos importados desde tarifa técnica |
| 2 | **BAJOS GOLA** | 291 productos BAJO GOLA importados |
| 3 | **ALTOS GOLA** | 465 productos ALTO GOLA importados |
| 4 | **COLUMNAS GOLA** | 107 productos COLUMNA GOLA importados |
| 5 | **ALTOS estándar** | 123 productos ALTO importados |
| 6 | **COLUMNAS estándar** | 24 productos COLUMNA importados |
| 7 | **COLUMNAS DESPENSERO** | 16 productos importados |
| 8 | **Colores FINSA 2025** | 150+ colores del catálogo oficial organizados en 14 categorías |
| 9 | **Trasera 8mm** | Corregido en Armarios y Muebles de cocina |
| 10 | **Decimales reducidos** | Tableros ahora con 2 decimales |
| 11 | **Guardar/Cargar Armarios** | API completa + Frontend para gestión de proyectos |
| 12 | **Modal Proyectos** | Lista de proyectos guardados con precio, fecha, cliente |
| 13 | **Botón ACTUALIZAR** | El botón cambia a "ACTUALIZAR" cuando hay proyecto cargado |

---

## CATÁLOGO DE PRODUCTOS

**Total: 1,027 productos**

| Categoría | Cantidad |
|-----------|----------|
| ALTO GOLA | 465 |
| BAJO GOLA | 291 |
| ALTO | 123 |
| COLUMNA GOLA | 107 |
| COLUMNA | 24 |
| COLUMNA DESPENSERO | 16 |
| BAJO | 1 |

---

## MÓDULO ARMARIOS

### Funcionalidades Implementadas:
1. **Diseñador Visual** - Vista previa del armario con módulos
2. **Configuración de Dimensiones** - Ancho, alto, fondo
3. **Selector de Módulos** - 1-8 módulos configurables
4. **Tipo de Puerta** - Corredera, Abatible, Plegable
5. **Colores FINSA 2025** - 150+ colores en 14 categorías
6. **Accesorios por Módulo** - Baldas, cajones, barras, zapatero, pantalonero, etc.
7. **Despiece Privado** - Lista numerada de todos los componentes
8. **Cálculo de Tableros** - m² de tablero 18mm y 8mm necesarios
9. **Guardar/Cargar Proyectos** - Persistencia en base de datos
10. **Exportar PDF** - Impresión del diseño

### Categorías de Colores FINSA 2025:
- Blancos (8 colores)
- Grises (14 colores)
- Cremas y Beiges (14 colores)
- Verdes (11 colores)
- Azules (11 colores)
- Rojos y Cálidos (10 colores)
- Maderas Claras (14 colores)
- Maderas Medias (15 colores)
- Maderas Oscuras (13 colores)
- Nogales (12 colores)
- Cerezos (6 colores)
- Metalizados (8 colores)
- Piedras/Cementos (12 colores)
- Textiles (10 colores)

---

## API ENDPOINTS

### Armarios
- `POST /api/armarios/projects` - Crear proyecto
- `GET /api/armarios/projects` - Listar proyectos
- `GET /api/armarios/projects/{id}` - Obtener proyecto
- `PUT /api/armarios/projects/{id}` - Actualizar proyecto
- `DELETE /api/armarios/projects/{id}` - Eliminar proyecto

### Productos
- `GET /api/products` - Listar productos
- `POST /api/products` - Crear producto
- `PUT /api/products/{id}` - Actualizar producto

### Despiece
- `POST /api/despiece/calculate` - Calcular despiece (trasera 8mm)

---

## ARQUITECTURA

```
/app
├── backend/
│   ├── server.py (~3800 líneas)
│   ├── import_gola_products.py
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── Armarios.jsx (~2300 líneas)
│       │   ├── BudgetTable.jsx
│       │   ├── CRMContacts.jsx
│       │   ├── DespieceModal.jsx
│       │   └── SettingsModal.jsx
│       └── services/
│           ├── api.js
│           └── pdfGenerator.js
└── memory/
    └── PRD.md
```

---

## PRÓXIMAS TAREAS

### P1 - Alta Prioridad
- [ ] Mejorar exportación PDF de Armarios con formato profesional

### P2 - Media Prioridad
- [ ] Auto-etiquetar CRM cuando se guarde proyecto de Armarios/Cocina
- [ ] Campo `catalogOrder` para ordenar productos como en PDF
- [ ] Reorganizar UI "expediente" para nuevos módulos

### P3 - Baja Prioridad
- [ ] Refactorizar `server.py` (>3800 líneas)
- [ ] Refactorizar `SettingsModal.jsx` (>2500 líneas)
- [ ] Notificaciones automáticas CRM por email
- [ ] Recordatorios calendario

---

## CREDENCIALES DE PRUEBA

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| MARIO | MARIO | Admin |
| TIENDSA | TIENDSA | Tienda |
| PRESCRIPTOR1 | PRESCRIPTOR1 | Colaborador Comercial |

---

## INTEGRACIONES

- **Google Gemini Vision** - Digitalizador de borradores, Importador catálogo, IA Lab
- **SendGrid** - Envío de backups por email
- **jsPDF** - Generación de PDF en frontend
- **MongoDB** - Base de datos principal
