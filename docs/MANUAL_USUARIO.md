# MANUAL DE USO - LUIGGI HOME
## Sistema de Presupuestación y Gestión de Cocinas

---

## ÍNDICE

1. [Introducción](#introducción)
2. [Tipos de Usuario y Permisos](#tipos-de-usuario-y-permisos)
3. [Módulo de Presupuestos](#módulo-de-presupuestos)
4. [Módulo CRM](#módulo-crm)
5. [Portal de Fábrica](#portal-de-fábrica)
6. [Informes y Despiece](#informes-y-despiece)
7. [Administración](#administración)

---

## 1. INTRODUCCIÓN

LUIGGI HOME es un sistema ERP/CRM especializado para empresas de mobiliario de cocina. Permite:

- Crear presupuestos con productos de diferentes bibliotecas (ZC, MV)
- Gestionar clientes y oportunidades comerciales
- Generar informes de despiece para fabricación
- Controlar el proceso de fabricación con seguimiento visual
- Exportar documentos en PDF y Excel

---

## 2. TIPOS DE USUARIO Y PERMISOS

### 2.1 ADMINISTRADOR
**Acceso completo al sistema**

| Módulo | Acceso |
|--------|--------|
| Presupuesto | ✅ |
| CRM | ✅ |
| IA Lab | ✅ |
| Archivo | ✅ |
| Digitalizador | ✅ |
| Fábrica | ✅ (si tiene permiso) |
| Montajes | ✅ |
| Panel Maestro | ✅ |

**Puede:**
- Crear y editar usuarios
- Configurar tarifas y productos
- Exportar datos
- Gestionar backups

---

### 2.2 DIRECTOR COMERCIAL / GERENTE
**Supervisión comercial y estratégica**

| Módulo | Acceso |
|--------|--------|
| Presupuesto | ✅ |
| CRM | ✅ |
| Archivo | ✅ |
| Panel Maestro | ✅ (limitado) |

**Puede:**
- Ver todas las oportunidades del CRM
- Asignar comerciales a clientes
- Ver informes de ventas
- Gestionar su red comercial

---

### 2.3 REPRESENTANTE / COMERCIAL
**Gestión de ventas y clientes**

| Módulo | Acceso |
|--------|--------|
| Presupuesto | ✅ |
| CRM | ✅ (solo sus clientes) |
| Archivo | ✅ |
| Mis Tiendas | ✅ |

**Puede:**
- Crear presupuestos
- Gestionar sus propios clientes
- Ver y editar oportunidades asignadas
- Acceder a tiendas vinculadas

---

### 2.4 TIENDA / PUNTO DE VENTA
**Uso básico de presupuestos**

| Módulo | Acceso |
|--------|--------|
| Presupuesto | ✅ |
| Archivo | ❌ |
| CRM | ❌ |
| Panel Maestro | ❌ |

**Puede:**
- Crear presupuestos para clientes
- Ver catálogo de productos
- Imprimir presupuestos

**No puede:**
- Acceder al CRM
- Ver costos de fábrica
- Exportar datos

---

### 2.5 USUARIO DE FÁBRICA
**⚠️ ACCESO EXCLUSIVO A FABRICACIÓN**

| Módulo | Acceso |
|--------|--------|
| Portal de Fábrica | ✅ |
| Presupuesto | ❌ |
| CRM | ❌ |
| Archivo | ❌ |
| Panel Maestro | ❌ |

**Puede:**
- Ver órdenes de fabricación
- Marcar muebles como fabricados
- Ver despiece de órdenes
- Imprimir listas de corte
- Establecer fechas de entrega

**No puede:**
- Ver presupuestos ni precios
- Acceder a información de clientes
- Modificar productos ni tarifas

---

### 2.6 MONTADOR / INSTALADOR
**Gestión de montajes**

| Módulo | Acceso |
|--------|--------|
| Agenda de Montajes | ✅ |
| Presupuesto | ❌ |

**Puede:**
- Ver agenda de montajes asignados
- Actualizar estado de instalaciones

---

## 3. MÓDULO DE PRESUPUESTOS

### 3.1 Crear un Presupuesto

1. Acceder a **PRESUPUESTO** en el menú lateral
2. Seleccionar la **tarifa/biblioteca** (ZC o MV)
3. Hacer clic en productos para añadirlos
4. Ajustar cantidades si es necesario
5. Guardar el presupuesto con datos del cliente

### 3.2 Selección de Productos

**Categorías disponibles:**
- **BAJOS**: Muebles de cocina parte inferior
- **ALTOS**: Muebles de pared
- **COLUMNAS**: Muebles de altura completa
- **SEMICOLUMNAS**: Columnas de media altura
- **SOBREMÓDULOS**: Módulos superiores adicionales
- **ESPECIALES**: Rinconeras, fregaderos, etc.

### 3.3 Opciones de Mueble

- **Dimensiones**: Ancho, alto, fondo personalizables
- **Mano**: Derecha (D) o Izquierda (I) según bisagras
- **Material casco**: Melamina, MDF, etc.
- **Acabado puerta**: Según catálogo de acabados

### 3.4 Guardar y Exportar

- **Guardar**: Guarda en base de datos para futuras ediciones
- **PDF**: Genera documento para imprimir/enviar al cliente
- **Excel**: Exporta líneas del presupuesto

---

## 4. MÓDULO CRM

### 4.1 Gestión de Clientes

**Datos del cliente:**
- Nombre y empresa
- **Código interno**: Generado automáticamente por el sistema
- **Código externo**: Código del programa de gestión externo
- Contacto: email, teléfono
- Dirección completa
- NIF/CIF

**Estados del cliente:**
- Potencial
- Activo
- Inactivo

### 4.2 Oportunidades de Venta

**Pipeline de ventas:**
1. **Lead**: Contacto inicial
2. **Cualificado**: Interés confirmado
3. **Presupuesto**: Presupuesto enviado
4. **Negociación**: En proceso de cierre
5. **Ganado/Perdido**: Resultado final

### 4.3 Seguimiento

- Registrar llamadas y visitas
- Programar recordatorios
- Adjuntar documentos
- Notas y comentarios

---

## 5. PORTAL DE FÁBRICA

### 5.1 Dashboard

Muestra en tiempo real:
- **Órdenes activas**: Total en proceso
- **En producción**: Actualmente fabricándose
- **Listas**: Preparadas para entregar
- **Entregas esta semana**: Planificadas próximos 7 días
- **Piezas en producción**: Contador total

### 5.2 Órdenes de Fabricación

**Estados de orden:**
| Estado | Color | Descripción |
|--------|-------|-------------|
| Borrador | Gris | Recién creada, no confirmada |
| Confirmada | Azul | Aprobada para producción |
| En Producción | Ámbar | Fabricándose |
| Lista | Verde | Completada, pendiente entrega |
| Entregada | Verde oscuro | Finalizada |
| Cancelada | Rojo | Anulada |

**Prioridades:**
- Baja
- Normal
- Alta
- **Urgente**

### 5.3 Resumen por Categoría

Cada orden muestra cantidad de muebles por tipo:
- 🔵 **Altos**
- 🟡 **Bajos**
- 🟣 **Columnas**
- 🔷 **Semicolumnas**
- 🔵 **Sobremódulos**
- 🔴 **Especiales**

### 5.4 Barra de Progreso de Fabricación

**Colores:**
- 🔴 **Rojo**: Sin empezar (0% fabricado)
- 🔵 **Azul**: En proceso (parcialmente fabricado)
- 🟢 **Verde**: Fabricado (100% completado)

### 5.5 Marcar Muebles como Fabricados

Cada mueble tiene 3 botones:
- ⬜ **Pendiente**: No se ha empezado
- ▶️ **En proceso**: Se está fabricando
- ✓ **Fabricado**: Completado

### 5.6 Importar Órdenes

**Dos métodos:**
1. **Importar Pedido**: Desde presupuestos guardados en el sistema
2. **Importar PDF**: Analiza PDF con IA para detectar muebles

### 5.7 Documentos para Fábrica

Usuarios de fábrica pueden imprimir:
- Lista de corte por material
- Orden de montaje
- Bandas y traseras
- Resumen de herrajes

---

## 6. INFORMES Y DESPIECE

### 6.1 Acceder al Despiece

1. Crear un presupuesto con muebles
2. Hacer clic en botón **DESPIECE**
3. Se abre modal con cálculos automáticos

### 6.2 Pestañas del Despiece

| Pestaña | Contenido |
|---------|-----------|
| **Orden Montaje** | Lista completa de piezas por mueble |
| **Lista Corte** | Agrupado por material para seccionadora |
| **Bandas y Traseras** | Canto en metros lineales, áreas |
| **Casco, Puerta y Herraje** | Dimensiones y herrajes estimados |

### 6.3 Cálculos Automáticos

**Se calculan:**
- Dimensiones de cada pieza (largo × ancho × grosor)
- Puertas con tolerancias correctas:
  - Alto: -2mm del alto del mueble
  - Ancho: -3mm del ancho correspondiente
- Canto necesario en metros lineales
- Área total en m²
- Herrajes estimados (bisagras, tiradores, soportes)

### 6.4 Exportar Informes

- **PDF A4**: Para imprimir
- **CSV**: Para hojas de cálculo
- **XML**: Para sistemas externos

---

## 7. ADMINISTRACIÓN

### 7.1 Panel Maestro (MASTER)

**Pestañas disponibles:**
- **RED DISTRIBUCIÓN**: Gestión de usuarios
- **TARIFAS**: Configuración de bibliotecas
- **PARÁMETROS**: Ajustes generales
- **BACKUPS**: Copias de seguridad
- **PANEL DIRECTOR**: Exportaciones

### 7.2 Gestión de Usuarios

**Crear usuario:**
1. Ir a RED DISTRIBUCIÓN
2. Clic en "+ NUEVO"
3. Completar datos
4. Asignar permisos en "Capacidades Técnicas"
5. Guardar

**Permisos disponibles:**
- IA Lab
- Ver Costo
- Informes
- CRM
- Digitalizador
- **FÁBRICA** (acceso al portal)
- Montajes
- Inventario
- Personalizar interfaz

**Usuario SOLO Fábrica:**
Activar este checkbox para usuarios que:
- Solo deben ver el Portal de Fábrica
- No necesitan acceso a presupuestos ni clientes

### 7.3 Exportar Datos

Desde **PANEL DIRECTOR**:
- **Artículos**: Catálogo de productos
- **Presup.**: Todos los presupuestos
- **CRM**: Clientes y oportunidades
- **Usuarios**: Lista de usuarios

Los archivos se descargan en formato Excel (.xlsx)

---

## GLOSARIO

| Término | Definición |
|---------|------------|
| **Tarifa** | Biblioteca de productos (ZC, MV) |
| **Montada** | Mueble ensamblado completo |
| **Despiece** | Lista de corte de tableros |
| **Casco** | Estructura/cuerpo del mueble |
| **Canto** | Banda de acabado para cantos |
| **OF** | Orden de Fabricación |
| **D/I** | Derecha/Izquierda (mano del mueble) |
| **2P** | 2 Puertas |

---

## SOPORTE

Para asistencia técnica contactar con:
- **Email**: soporte@luiggihome.es
- **Teléfono**: (ver panel de administración)

---

*Versión del manual: 1.0*
*Última actualización: Marzo 2026*
