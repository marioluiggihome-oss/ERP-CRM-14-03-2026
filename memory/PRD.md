# LUIGGI HOME - Kitchen Budgeting ERP/CRM

## Estado del Proyecto: EN DESARROLLO ACTIVO

## Problema Original
Replicar una aplicación de presupuestos de cocina ERP/CRM llamada LUIGGI HOME con múltiples módulos, sistemas de precios y gestión de usuarios.

## Última Actualización: 15 Marzo 2026

---

## ✅ COMPLETADO EN ESTA SESIÓN (15 Marzo 2026)

### P0 - Mejoras UI/Datos
- ✅ **Botón CATÁLOGO MODELOS**: Solo visible para tarifa ZC (oculto en MV)
- ✅ **Variantes de altura COLUMNAS MV**: 68 productos con H200 y H220 (34 cada uno)

### P1 - Corte Viga por Biblioteca
- ✅ **UI configuración separada**: Campos "Corte Viga ZC (€)" y "Corte Viga MV (€)" en MÁRGENES
- ✅ **Backend**: Campo `libraryVigaCutIncrements` en SettingsModel
- ✅ **Cálculo de precios**: BudgetTable usa el valor correcto según biblioteca activa

### P1 - Exportación Catálogo por Biblioteca
- ✅ **Endpoint API**: `GET /api/products/export/library/{ZC|MV}` genera Excel
- ✅ **Botones UI**: En tab INVENTARIO - botones "ZC" y "MV" para descarga directa
- ✅ **Formato ZC**: Columnas REF, DESC, CATEGORÍA, SERIE, AN, AL, FO, Z1-Z12
- ✅ **Formato MV**: Columnas REF, DESC, CATEGORÍA, SERIE, AN, AL, FO, T1-T21

### Correcciones Adicionales
- ✅ **Digitalizador por Biblioteca**: Detecta muebles según la biblioteca activa (ZC o MV)
- ✅ **Barra de búsqueda duplicada**: Eliminada
- ✅ **Migración de usuarios**: Usuarios migrados de test_database a luiggi_home
- ✅ **Label "Nombre Público Tienda"**: Cambiado a "Nombre" en formulario de usuario

### 🆕 NUEVO: Agenda de Montajes
- ✅ **Componente**: `AgendaMontajes.jsx` - Gestión completa de montadores e instaladores
- ✅ **API Backend**: CRUD completo para montadores y montajes
  - `GET/POST /api/montadores` - Listar/crear montadores
  - `GET/PUT/DELETE /api/montadores/{id}` - Gestionar montador individual
  - `GET/POST /api/montajes` - Listar/crear montajes
  - `GET/PUT/DELETE /api/montajes/{id}` - Gestionar montaje individual
  - `GET /api/montadores/{id}/montajes` - Montajes por montador
- ✅ **Frontend API**: `montadoresAPI` y `montajesAPI` en api.js
- ✅ **Permisos de usuario**:
  - `canAccessMontajes` - Permiso para ver la agenda
  - `isMontador` - Rol de montador/instalador
- ✅ **Navegación**: Botón "MONTAJES" en el sidebar (icono de llave)
- ✅ **Funcionalidades**:
  - Gestión de montadores (nombre, empresa, teléfono, email, zona, especialidad, rating)
  - Programación de montajes (cliente, dirección, fecha, hora, duración, estado)
  - Estados: activo/inactivo/vacaciones para montadores
  - Estados: pendiente/en_curso/completado/cancelado para montajes
  - Valoración con estrellas (1-5)
  - Filtros por estado y búsqueda

---

## 🔴 PENDIENTE / BUGS CONOCIDOS

### P0 - CRÍTICO (PAUSADO POR USUARIO)
1. **Bug cálculo presupuesto despiece** - Items de despiece no se suman al total (PAUSADO)

### P2 - MEJORAS
2. **Logo perdido** - Usuario debe volver a subir el logo desde Panel Maestro
3. **Glitch visual barra lateral colapsada** - Recurrente
4. **Refactorización componentes grandes** - BudgetTable.jsx (~3069 líneas), SettingsModal.jsx (~4671 líneas)

### P3 - BLOQUEADOS
5. **Flujo registro email** - Requiere verificación de dominio en Resend

---

## ARQUITECTURA

### Backend (FastAPI)
```
/app/backend/
├── server.py                    # Servidor principal + endpoints montadores/montajes
├── models/schemas.py            # MontadorCreate, MontajeCreate, etc.
├── routes/
│   ├── libraries.py
│   └── ...
```

### Frontend (React)
```
/app/frontend/src/
├── App.js                       # Navegación a AgendaMontajes
├── components/
│   ├── AgendaMontajes.jsx       # NUEVO: Gestión de montadores
│   ├── BudgetTable.jsx
│   ├── SettingsModal.jsx        # Permisos canAccessMontajes, isMontador
│   └── ...
└── services/
    └── api.js                   # montadoresAPI, montajesAPI
```

### Base de Datos (MongoDB: luiggi_home)
```
Colecciones:
- products          # library: ZC/MV
- system_settings   # libraryVigaCutIncrements
- users             # canAccessMontajes, isMontador
- montadores        # NUEVA: montadores/instaladores
- montajes          # NUEVA: instalaciones programadas
```

---

## BIBLIOTECAS/TARIFAS

| Código | Sistema Precios | Productos |
|--------|-----------------|-----------|
| ZC | ZONAS (Z1-Z12) | ~4505 |
| MV | TARIFAS (T1-T21) | ~290 |

---

## CREDENCIALES TEST
- **Usuario**: MARIO / MARIO (Admin)
- **Otros**: ALBERTO, EDU

---

## PRÓXIMAS TAREAS

### Backlog
1. (P2 - PAUSADO) Fix cálculo total presupuesto despiece
2. (P2) Usuario debe volver a subir el logo
3. (P2) Fix glitch sidebar colapsado
4. (P3) Refactorización componentes grandes
5. (P3) Preview visual del catálogo antes de exportar

---

## HISTORIAL DE CAMBIOS

### 15 Marzo 2026 (Sesión completa)
- ✅ P0: Botón CATÁLOGO MODELOS solo visible en ZC
- ✅ P0: Variantes de altura COLUMNAS MV (H200, H220)
- ✅ P1: Corte Viga independiente por biblioteca (ZC/MV)
- ✅ P1: Exportación catálogo ZC/MV
- ✅ Digitalizador filtra por biblioteca activa
- ✅ Eliminada barra de búsqueda duplicada
- ✅ Migrados usuarios de test_database
- ✅ Label "Nombre Público Tienda" → "Nombre"
- ✅ **NUEVO: Agenda de Montajes completa**
