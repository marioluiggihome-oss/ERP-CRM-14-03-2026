# LUIGGI HOME - Kitchen Budget ERP/CRM

## Original Problem Statement
Replicate a kitchen budgeting ERP/CRM application named **LUIGGI HOME**.

## User's Preferred Language
Spanish (es)

## Current Statistics (Mar 2026)
- **Total Products:** 7,148
- **Series Normalizadas:** 2,428 productos actualizados

## Completed Tasks - Session Mar 7, 2026

### 🔐 Permisos por Módulo (Sin bypass Admin)
Todos los módulos requieren su permiso específico activo:
- **CRM** → `canAccessCRM`
- **IA Lab** → `canUseAIAnalysis`
- **Digitalizador** → `canUseDigitalizador`
- **Armarios** → `canAccessArmarios`

### 👥 Roles CRM - Director Comercial y Gerente
- **Director Comercial** (`isDirectorComercial`) y **Gerente** (`isGerente`) siempre ven TODO el CRM
- Los **Comerciales** solo ven los clientes que tienen asignados
- Los datos se acumulan aunque no haya comercial asignado
- Al asignar comercial, ve toda la información histórica

**Archivos modificados:**
- `CRMDashboard.jsx`, `CRMContacts.jsx`, `CRMPipeline.jsx`, `CRMCalendar.jsx`
- `SettingsModal.jsx` - Nuevo checkbox para Director Comercial
- `/app/backend/models/schemas.py` - Nuevo campo `isDirectorComercial`

### 📐 Filtros de Librería
- Programa, Categoría, Serie
- 🚪 Tipo de Apertura (HK, HF, HL, HS)
- 📐 Medidas (Ancho, Alto, Fondo con ±5mm tolerancia)

### 🗂️ Series Normalizadas
- ALTOS→ALTO, BAJOS→BAJO, ESTANDAR→ESTÁNDAR
- 2,428 productos corregidos

### 📧 Emails Modernizados
- Plantilla profesional con diseño LUIGGI HOME
- Notificación al admin en nuevos registros

## ⚠️ PROBLEMA CONOCIDO: SendGrid

**Error:** HTTP 403 Forbidden al enviar emails

**Causa:** La API key de SendGrid no tiene permisos suficientes o el dominio remitente (`noreply@luiggihome.com`) no está verificado.

**Solución requerida por el usuario:**
1. Acceder a la cuenta de SendGrid
2. Verificar el dominio `luiggihome.com` en Sender Authentication
3. O usar un remitente ya verificado (Single Sender Verification)
4. Verificar que la API key tenga permisos de "Mail Send"

## Pending Tasks

### P0 - Inmediato
- [ ] ⚠️ **Configurar SendGrid** - El usuario debe verificar dominio/remitente en su cuenta SendGrid

### P1 - Próximas Tareas
- [ ] Botón para ocultar/mostrar el catálogo lateral (ya existe `isCatalogOpen` pero puede mejorarse el icono)
- [ ] Revisar productos HS que ya no son Servo-Drive
- [ ] Panel 2FA en perfil de usuario

### P2 - Technical Debt
- [ ] Refactoring `server.py`, `BudgetTable.jsx`, `Armarios.jsx`

## Roles del Sistema

| Rol | Permisos CRM | Permisos Generales |
|-----|--------------|-------------------|
| Gerente | Ve TODO | Acceso total |
| Director Comercial | Ve TODO | Según permisos |
| Admin | Ve TODO | Acceso total |
| Responsable Delegación | Ve su delegación | Según permisos |
| Comercial | Solo sus clientes | Según permisos |
| Tienda | Solo sus datos | Limitado |

## Test Credentials
- **Admin User:** MARIO / MARIO

## Key Files Modified This Session
- `/app/frontend/src/components/CRM*.jsx` - Lógica Director Comercial
- `/app/frontend/src/components/SettingsModal.jsx` - Nuevo rol
- `/app/frontend/src/components/Digitalizador.jsx` - Opción CRM condicional
- `/app/backend/models/schemas.py` - Campo isDirectorComercial
