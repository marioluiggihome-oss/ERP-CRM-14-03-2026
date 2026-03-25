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

### 5.7 Informe de Producción PDF

**Nueva funcionalidad (Marzo 2026)**

Genera un PDF completo del informe de producción que incluye:
- Logo corporativo de la empresa
- Información del pedido (número, cliente, fecha, prioridad)
- Lista de muebles a fabricar con dimensiones
- Despiece detallado de cada mueble:
  - Laterales (izquierdo y derecho)
  - Tapas (superior e inferior)
  - Trasera
  - Estantes
- Resumen de materiales (total piezas y área m²)
- Timestamp de generación

**Cómo descargar:**
1. Ir a Portal de Fábrica
2. Hacer clic en una orden para expandirla
3. Presionar botón azul **"Informe PDF"**
4. El archivo se descarga automáticamente

### 5.8 Documentos para Fábrica

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

### 6.5 Optimizador de Tableros

**Nueva funcionalidad estilo OpenCutList**

El optimizador de tableros minimiza el desperdicio de material calculando la mejor disposición de piezas en los tableros.

**Acceder al Optimizador:**
1. Abrir el modal de DESPIECE
2. Hacer clic en el botón **"Optimizar Tableros"** (color verde)
3. Se abre el panel de optimización

**Configuración del Tablero:**
| Opción | Descripción |
|--------|-------------|
| **Tamaño estándar** | 2440x1220mm (8x4 pies), 2440x1830mm, 2750x1830mm, 3050x1525mm |
| **Personalizado** | Definir dimensiones específicas |
| **Kerf (ancho de corte)** | 0mm (sin corte), 3mm (sierra fina), 4mm (estándar), 5mm (gruesa) |

**Panel de Piezas:**
- Las piezas se cargan automáticamente desde el despiece
- Puedes añadir/eliminar piezas manualmente
- Cada pieza muestra: nombre, dimensiones (ancho x alto), cantidad
- Colores distintivos para cada pieza

**Resultado de Optimización:**
| Métrica | Descripción |
|---------|-------------|
| **Tableros** | Cantidad de tableros necesarios |
| **Eficiencia** | Porcentaje de material aprovechado |
| **m² Usados** | Área total ocupada por piezas |
| **m² Desperdicio** | Área restante sin utilizar |
| **Estado** | ✓ Todo colocado / ⚠️ Piezas sin colocar |

**Visualización:**
- Los tableros se muestran con las piezas colocadas en posición óptima
- Cada pieza tiene un color distintivo para fácil identificación
- Se muestran las dimensiones de cada pieza sobre el diagrama
- Grid de referencia cada 100mm

**Exportar PDF:**
- Genera documento con diagrama de todos los tableros
- Incluye lista de piezas por tablero
- Resumen final con estadísticas de eficiencia

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

## 8. MIS PEDIDOS

### 8.1 Historial de Pedidos Confirmados

Accede a todos los pedidos confirmados en el sistema.

**Información mostrada:**
- Número de expediente
- Cliente
- Fecha de confirmación
- Estado de fabricación
- Importe total
- Número de artículos

### 8.2 Estados de Fabricación

| Estado | Icono | Descripción |
|--------|-------|-------------|
| Confirmado | ✓ | Pedido confirmado, pendiente producción |
| Pendiente | ⏱ | En cola de fabricación |
| En Producción | 🏭 | Fabricándose actualmente |
| Listo | 📦 | Preparado para envío |
| Enviado | 🚚 | En tránsito |
| Entregado | ✅ | Instalado en cliente |

### 8.3 Enviar Copia del Pedido

**Nueva funcionalidad (Marzo 2026)**

Permite reenviar una copia del pedido confirmado incluyendo:
- Resumen del pedido
- Lista de artículos
- Especificaciones de acabados
- Archivos adjuntos del cliente (planos, fotos, etc.)

**Cómo enviar:**
1. Ir a **Mis Pedidos** en el menú lateral
2. Localizar el pedido deseado
3. Hacer clic en el icono de avión (📤) azul
4. En el modal que aparece:
   - Introducir email de destino
   - Opcionalmente, añadir un mensaje
   - Marcar/desmarcar "Incluir archivos adjuntos"
5. Presionar **"Enviar Copia"**

**Nota:** Los archivos adjuntos solo se envían si fueron incluidos al confirmar el pedido original.

---

## 9. DASHBOARD FÁBRICA

### 9.1 Acceso

El Dashboard Fábrica está disponible para:
- Administradores
- Directores de Fábrica
- Usuarios con permiso específico

Acceder desde: **Panel Maestro > Dashboard Fábrica**

### 9.2 KPIs Principales

| Indicador | Descripción |
|-----------|-------------|
| **Órdenes Fabricación** | Total de OF en el período |
| **Pedidos Confirmados** | Nuevos pedidos confirmados |
| **Presupuestos** | Presupuestos guardados |
| **Ventas €** | Valor total de pedidos |
| **Presupuestos €** | Valor total presupuestado |
| **Piezas Producción** | Muebles en fabricación |
| **Tasa Conversión** | % presupuestos convertidos |

### 9.3 Gráficos

- **Tendencia Mensual**: Comparativa pedidos vs presupuestos (barras)
- **Estado de Producción**: Distribución por estado (circular)

### 9.4 Selector de Período

Filtrar datos por:
- Semana
- Mes
- Trimestre
- Año
- Todo el histórico

---

## 10. TELEMETRÍA IA

### 10.1 Reconocimiento Óptico de Catálogos

Permite importar fichas de productos de catálogos en papel o PDF usando inteligencia artificial.

**Librerías soportadas:**
- **ZC**: Zonas Z1-Z12
- **MV**: Tarifas T1-T21 (detección automática)

### 10.2 Proceso de Importación

1. Acceder a **Panel Maestro > Telemetría IA**
2. Seleccionar módulo (Montada o Despiece)
3. Seleccionar librería (ZC o MV)
4. Cargar imágenes de fichas (JPG, PNG, PDF)
5. Presionar **"Digitalizar"**
6. Esperar a que la IA procese las imágenes
7. Revisar el log de resultados

### 10.3 Detección Automática de Tarifas (MV)

Para la librería MV, la IA detecta automáticamente la tarifa (T1-T21) desde el encabezado de cada imagen. No es necesario seleccionar manualmente.

### 10.4 Sistema de Cola en Segundo Plano

La importación de catálogos grandes se procesa en segundo plano para evitar timeouts. El progreso se muestra en tiempo real en el panel de log.

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

*Versión del manual: 2.0*
*Última actualización: Marzo 2026*
