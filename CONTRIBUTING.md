# Contribuir a ERP-CRM

¡Gracias por tu interés en contribuir! Este documento describe el proceso para participar en el desarrollo.

## 🚀 Proceso de desarrollo

### 1. Preparar el entorno

```bash
# Fork y clonar el repositorio
git clone https://github.com/tu-usuario/ERP-CRM-14-03-2026.git
cd ERP-CRM-14-03-2026

# Crear una rama para tu feature/fix
git checkout -b feature/nombre-descriptivo
# o
git checkout -b fix/descripcion-del-bug
```

### 2. Desarrollar

- Sigue las convenciones de código existentes.
- Escribe tests para las nuevas funcionalidades.
- Mantén los commits atómicos y con mensajes descriptivos.

### 3. Convención de commits

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

```
<tipo>: <descripción>

[opcional cuerpo]
[opcional footer]
```

**Tipos:**
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Cambios en documentación
- `style`: Formato, puntos y coma, etc. (sin cambios de código)
- `refactor`: Refactorización de código
- `test`: Añadir o corregir tests
- `chore`: Tareas de mantenimiento, dependencias
- `ci`: Cambios en CI/CD

**Ejemplos:**
```
feat: añadir exportación de facturas a PDF
fix: corregir cálculo de IVA en proformas
docs: actualizar README con instrucciones de Docker
```

### 4. Antes de hacer commit

```bash
# Frontend
npm run lint
npm test

# Backend
pytest
```

### 5. Enviar cambios

```bash
git add .
git commit -m "feat: descripción del cambio"
git push origin feature/nombre-descriptivo
```

Abre un Pull Request en GitHub con:
- Descripción clara de los cambios
- Referencia a issues relacionados (ej. `Closes #12`)
- Screenshots si hay cambios visuales

## 📝 Normas de estilo

### JavaScript (Frontend)
- Usa 2 espacios para indentación.
- Nombres de variables en camelCase.
- Nombres de clases y componentes en PascalCase.
- Evita `var`, usa `let` y `const`.

### Python (Backend)
- Sigue [PEP 8](https://peps.python.org/pep-0008/).
- Usa 4 espacios para indentación.
- Nombres de funciones y variables en snake_case.
- Nombres de clases en PascalCase.
- Docstrings para funciones públicas.

## 🧪 Testing

- Todo código nuevo debe incluir tests.
- Mínimo 80% de cobertura para funcionalidades críticas.
- Los tests deben ser independientes y reproducibles.

## 🔒 Seguridad

- Nunca subas credenciales, API keys o archivos `.env`.
- Reporta vulnerabilidades de forma privada (ver [SECURITY.md](SECURITY.md)).
- Revisa que no haya información sensible antes de hacer commit.

## ❓ ¿Dudas?

Abre un issue con la etiqueta `question` o contacta con el equipo de mantenimiento.
