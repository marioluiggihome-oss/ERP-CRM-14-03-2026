# Informe de Auditoría Profunda del ERP/CRM

**Autor:** Manus AI  
**Fecha:** 14 de junio de 2026  
**Repositorio revisado:** [`https://github.com/marioluiggihome-oss/ERP-CRM-14-03-2026`](https://github.com/marioluiggihome-oss/ERP-CRM-14-03-2026)

## Resumen Ejecutivo General

Este informe presenta los resultados de una auditoría profunda del sistema ERP/CRM, cubriendo aspectos de seguridad de la API, lógica de negocio y consistencia de datos, así como la calidad y mantenibilidad del código. El sistema muestra una base funcional sólida, con implementaciones adecuadas en autenticación y modularización del backend. Sin embargo, se han identificado áreas críticas de mejora relacionadas con la validación de entrada, la transaccionalidad de la base de datos, la asincronía de tareas y la cobertura de pruebas, que son fundamentales para la robustez, seguridad y escalabilidad a largo plazo del sistema.

---

## 1. Auditoría de Seguridad y Permisos de la API (RBAC, JWT, Inyección)

### Resumen Ejecutivo

La implementación de JWT y el control de acceso basado en roles (RBAC) es generalmente robusta. El sistema maneja bien la autenticación y autorización a nivel de backend. Las principales áreas de mejora se centran en la validación exhaustiva de la entrada del usuario para prevenir inyecciones y en la seguridad del almacenamiento de tokens en el frontend.

### Hallazgos y Análisis

#### 1.1. Autenticación JWT

La implementación de JWT en `jwt_service.py` y `auth_routes.py` sigue buenas prácticas:

*   **Secreto JWT (`JWT_SECRET`)**: Se exige su configuración vía variable de entorno, crucial para la seguridad en producción [1].
*   **Algoritmo y Expiración**: Uso de `HS256` y tiempos de expiración razonables (24h acceso, 7d refresco) limitan el riesgo de tokens comprometidos.
*   **Validación de Tokens**: Las funciones `decode_token`, `verify_access_token` y `verify_refresh_token` manejan correctamente tokens expirados o inválidos (HTTP 401).
*   **Hashing de Contraseñas**: `auth_routes.py` usa `bcrypt`, un algoritmo fuerte. El fallback a SHA256 para compatibilidad con cuentas antiguas es una consideración práctica, pero se recomienda migrar todas a `bcrypt`.

#### 1.2. Control de Acceso Basado en Roles (RBAC)

El sistema utiliza dependencias de FastAPI (`Depends`) y roles en el payload del JWT con `require_auth` y `require_admin` en `jwt_service.py`:

*   **`require_auth`**: Asegura un token de acceso válido, lanzando 401 si no hay credenciales o el token es inválido.
*   **`require_admin`**: Extiende `require_auth` para verificar roles administrativos (`ADMIN_ROLE_FLAGS`), devolviendo 403 si el usuario no tiene permisos elevados.

Este enfoque es efectivo para proteger rutas, aunque los cambios de rol no se reflejan hasta la expiración/refresco del token.

#### 1.3. Posibles Vulnerabilidades de Inyección NoSQL

Las operaciones a MongoDB se realizan mediante `motor.motor_asyncio`, que parametriza las consultas, reduciendo el riesgo de inyección NoSQL directa. Sin embargo, la seguridad depende de la validación y sanitización de la entrada del usuario antes de construir consultas. Se observa una buena práctica en `auth_routes.py` con `re.escape(username)` para prevenir inyecciones regex.

**Puntos a revisar en detalle (sin acceso al código completo):**

*   **Validación de Esquemas**: Asegurar que todos los endpoints que reciben datos del usuario usen esquemas de validación (Pydantic) para definir estrictamente tipos y formatos, previniendo datos maliciosos.
*   **Construcción de Consultas Dinámicas**: Identificar y revisar puntos donde las consultas se construyen dinámicamente con entrada de usuario sin validación estricta.

#### 1.4. Gestión de Secretos y Configuración

`config.py` centraliza la configuración y carga variables de entorno, exigiendo `JWT_SECRET`. `CORS_ORIGINS` también se gestiona por variables de entorno.

**Áreas de mejora:**

*   **Rotación de Secretos**: Implementar una estrategia para la rotación periódica de `JWT_SECRET` y otras claves sensibles.
*   **Almacenamiento de Tokens en Frontend**: El `localStorage` es susceptible a XSS. Considerar `HttpOnly cookies` para tokens de acceso o refresh tokens más seguros.

### Conclusiones de Seguridad de la API

La API tiene una base de seguridad adecuada. Los puntos clave son la **validación exhaustiva de la entrada del usuario** y la **seguridad del almacenamiento de tokens en el frontend**.

### Recomendaciones de Seguridad de la API

1.  **Revisión de Endpoints Críticos**: Revisar manualmente endpoints sensibles para asegurar validación de entrada robusta.
2.  **Implementación de Pydantic**: Confirmar el uso de Pydantic en todos los modelos de solicitud y respuesta de FastAPI.
3.  **Evaluación de Almacenamiento de Tokens**: Investigar la migración a métodos más seguros como `HttpOnly cookies`.

---

## 2. Auditoría de Lógica de Negocio y Consistencia de Datos (MongoDB, Expedientes)

### Resumen Ejecutivo

La lógica de negocio es funcional y utiliza correctamente las capacidades atómicas de MongoDB para contadores. Sin embargo, la **falta de transaccionalidad** en procesos multi-paso y la **ejecución sincrónica de tareas pesadas** son puntos de debilidad que afectan la consistencia de datos y la experiencia del usuario.

### Hallazgos y Análisis

#### 2.1. Generación de Números de Expediente (`expedient.py`)

El sistema usa `system_counters` para la correlatividad de expedientes:

*   **Atomicidad**: `find_one_and_update` con `$inc` garantiza la atomicidad en la gestión de contadores [2].
*   **Flexibilidad de Formato**: Soporta formato legacy y segmentado por cliente (`EXP-AAAA-CLIENTE-NNN`).
*   **Manejo de Inicialización**: Crea automáticamente el contador si no existe.

**Observación Crítica:**
La función `get_next_expedient_number` es un endpoint `GET` que modifica el estado del servidor. Las operaciones que modifican el estado deberían ser `POST` o `PATCH` para cumplir con los estándares REST y evitar problemas con cachés o pre-fetchers.

#### 2.2. Confirmación de Pedidos y Órdenes de Fabricación (`orders.py`)

El endpoint `/orders/confirm` es crítico y realiza múltiples tareas:

1.  Procesa archivos adjuntos.
2.  Genera contenido HTML para email.
3.  Envía el email (con fallback de proveedor).
4.  Guarda el pedido en la base de datos.
5.  Crea automáticamente una orden de fabricación correlativa.

**Puntos Fuertes:**
*   **Resiliencia en Email**: Fallback (SendGrid -> Resend) asegura la entrega de notificaciones.
*   **Integración de Datos**: Creación automática de órdenes de fabricación reduce errores.
*   **Almacenamiento de Adjuntos**: Guardar adjuntos en base64 permite reconstruir el historial, aunque puede aumentar el tamaño de la DB.

**Áreas de Riesgo y Mejora:**
*   **Falta de Transaccionalidad**: Si una parte del proceso falla (ej. email enviado, pero DB falla), el sistema queda inconsistente. Se recomienda usar transacciones multi-documento de MongoDB para envolver las operaciones críticas.
*   **Carga de Trabajo en el Endpoint**: Tareas sincrónicas (procesamiento de archivos, envío de emails) pueden bloquear la respuesta al usuario. Mover el envío de emails y la generación de órdenes de fabricación a `BackgroundTasks` o una cola de tareas (Celery/RQ).
*   **Uso de `Form` para Datos Complejos**: Enviar ítems como cadena JSON en un campo `Form` es propenso a errores. Es más robusto usar un esquema Pydantic y `application/json`.

### Conclusiones de Lógica de Negocio

La lógica es funcional, pero la **falta de transaccionalidad** en procesos multi-paso y la **ejecución sincrónica de tareas pesadas** son debilidades que afectan la consistencia y el rendimiento.

### Recomendaciones de Lógica de Negocio

1.  **Migrar a Transacciones**: Implementar transacciones de MongoDB en el flujo de confirmación de pedidos.
2.  **Asincronía para Emails**: Utilizar `BackgroundTasks` de FastAPI para el envío de correos.
3.  **Refactorizar a JSON**: Cambiar el endpoint de confirmación de pedidos para aceptar JSON.

---

## 3. Auditoría de Calidad de Código y Mantenibilidad (Refactorización, Deuda Técnica)

### Resumen Ejecutivo

El código es funcional y está razonablemente organizado, pero existen oportunidades significativas de mejora en la reutilización de código del frontend, la descomposición de componentes, la cobertura de pruebas y la centralización de lógica en el backend.

### Hallazgos y Análisis

#### 3.1. Frontend (React/JavaScript)

##### Gestión de Peticiones API (`api.js`)

*   **Repetición de Código**: Duplicidad en la construcción de URLs y gestión de parámetros de consulta. Se recomienda una función auxiliar centralizada.
*   **Manejo Inconsistente de Errores**: Variedad en el manejo de excepciones. Se necesita una estrategia centralizada.
*   **Almacenamiento de Tokens**: El uso de `localStorage` es susceptible a XSS. (Reiterado del informe de seguridad).

##### Componentes React

Componentes grandes (más de 2.000 líneas) como `CRMActivities.jsx` y `CRMCalendar.jsx` sugieren la necesidad de **descomposición en componentes más pequeños y reutilizables**.

**Recomendaciones:**
*   Extraer lógica de negocio a custom hooks.
*   Separar la presentación de la lógica de estado.
*   Crear componentes de presentación reutilizables.

#### 3.2. Backend (FastAPI/Python)

##### Modularización de Rutas

El backend está bien estructurado en módulos por dominio, lo cual es una buena práctica. Sin embargo, algunos módulos como `orders.py` realizan múltiples tareas en un único endpoint, lo que podría beneficiarse de la descomposición en funciones auxiliares o servicios.

##### Gestión de Dependencias

El uso de `Depends` en FastAPI es correcto. Oportunidades de mejora incluyen extender `require_auth` para autorización basada en recursos y un manejador centralizado de errores para un logging y formato uniforme.

##### Deuda Técnica Identificada

1.  **Duplicación de Conexiones MongoDB**: Algunos archivos crean sus propias conexiones a MongoDB en lugar de usar la centralizada de `config.py`.
2.  **Falta de Validación con Pydantic**: Algunos endpoints aceptan `dict` genéricos sin validación de esquema.
3.  **Logging Inconsistente**: El logging es ad-hoc. Se necesita una estrategia centralizada.

#### 3.3. Patrones de Diseño

*   **Patrón de Servicio**: Bien utilizado en el backend para funcionalidades transversales.
*   **Patrón de Repositorio**: No explícito. Las consultas a MongoDB se realizan directamente. Un patrón de repositorio centralizaría la lógica de acceso a datos y mejoraría la testabilidad.

#### 3.4. Testing

**Brecha significativa**: No se han identificado archivos de prueba unitarias o de integración. Se recomienda implementar:

*   **Pruebas Unitarias**: Para funciones de servicio.
*   **Pruebas de Integración**: Para endpoints críticos.
*   **Pruebas E2E**: Para flujos completos del usuario.

### Conclusiones de Calidad de Código

El código es funcional, pero necesita mejoras en **reutilización de código**, **descomposición de componentes**, **testing** y **centralización de lógica**.

### Recomendaciones Prioritarias de Calidad de Código

| Prioridad | Recomendación | Impacto |
|-----------|---------------|--------|
| **Alta** | Implementar suite de pruebas (unitarias, integración, E2E) | Mejora significativa de confiabilidad |
| **Alta** | Centralizar manejo de errores en el backend | Mejora de observabilidad y debugging |
| **Media** | Refactorizar componentes React grandes | Mejora de mantenibilidad |
| **Media** | Implementar patrón de repositorio para acceso a datos | Mejora de testabilidad |
| **Baja** | Reducir repetición de código en `api.js` | Mejora de mantenibilidad |

---

## Referencias

[1] OWASP. (n.d.). *JWT Best Practices*. Recuperado de [https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_Cheat_Sheet.html)
[2] MongoDB. (n.d.). *Transactions*. Recuperado de [https://www.mongodb.com/docs/manual/core/transactions/](https://www.mongodb.com/docs/manual/core/transactions/)
