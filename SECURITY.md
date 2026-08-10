# Política de Seguridad

## Reportar una vulnerabilidad

Si descubres una vulnerabilidad de seguridad en este proyecto, por favor **NO abras un issue público**.

En su lugar, reporta la vulnerabilidad de forma privada:

1. Ve a la pestaña **Security** del repositorio en GitHub.
2. Selecciona **Report a vulnerability**.
3. Describe el problema con el máximo detalle posible.

## 🕐 Tiempos de respuesta

| Acción | Tiempo estimado |
|--------|----------------|
| Confirmación de recepción | 48 horas |
| Evaluación inicial | 5 días hábiles |
| Resolución o parche | 30 días (según severidad) |

## 🔐 Buenas prácticas

### Para desarrolladores

- **Nunca** subas credenciales, API keys, tokens o contraseñas al repositorio.
- Usa siempre variables de entorno (`.env`) para información sensible.
- Verifica que `.env` esté en `.gitignore` antes de hacer commit.
- Usa secretos de GitHub para CI/CD, nunca hardcodea valores.
- Revisa los logs antes de compartirlos: pueden contener datos sensibles.

### Para usuarios

- Cambia las contraseñas por defecto tras la instalación.
- Mantén el sistema actualizado con las últimas versiones.
- Usa HTTPS en producción.
- Configura correctamente los permisos de la base de datos.

## 📋 Alcance

Esta política cubre:

- El código del repositorio principal.
- Las pipelines de CI/CD.
- Las dependencias gestionadas por Dependabot.

No cubre:

- Vulnerabilidades en dependencias de terceros (reporta al mantenedor de la librería).
- Problemas de configuración del entorno de despliegue.

## 🔄 Actualizaciones de seguridad

Las actualizaciones de dependencias se gestionan automáticamente mediante [Dependabot](https://docs.github.com/en/code-security/dependabot), configurado en `.github/dependabot.yml`.

Las alertas de seguridad se revisan semanalmente y se priorizan según su severidad (CRITICAL > HIGH > MEDIUM > LOW).
