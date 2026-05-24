# Credenciales de Prueba - LUIGGI HOME ERP

## Admin Principal (MASTER)
- **Email/Usuario**: `mario@luiggihome.es`
- **Contraseña**: `Mario2025*`
- **Roles**: Admin, isPrimaryAdmin, DirectorComercial
- **Permisos**: Acceso completo a todo el sistema

## Usuarios Comerciales (Solo en producción Railway)
Los 9 usuarios comerciales (MIGUEL, JOSEMANUEL, etc.) existen únicamente en la BD de producción Railway, NO en la BD de preview (MongoDB Atlas).

## Backend URLs
- Preview: definido en `/app/frontend/.env` (REACT_APP_BACKEND_URL)
- Producción: `erp.luiggihome.es` (Railway)

## Endpoints clave
- `POST /api/auth/login` - Login (devuelve `tokens.access_token`)
- `GET /api/users` - Listado de usuarios (requiere JWT)
- `GET /api/settings` - Configuración global (requiere JWT)
- `GET /api/crm/contacts` - Contactos CRM con aislamiento JWT
- `GET /api/digitalizador/history` - Auditoría Digitalizador IA
