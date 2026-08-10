# ERP-CRM

Sistema integral ERP/CRM para gestión empresarial con módulos de ventas, inventario, facturación, proyectos y renderizado 3D con IA.

## 📋 Tabla de contenidos

- [Descripción](#descripción)
- [Arquitectura](#arquitectura)
- [Módulos principales](#módulos-principales)
- [Tech Stack](#tech-stack)
- [Requisitos previos](#requisitos-previos)
- [Instalación](#instalación)
- [Variables de entorno](#variables-de-entorno)
- [Uso](#uso)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Testing](#testing)
- [Contribuir](#contribuir)
- [Licencia](#licencia)

## Descripción

Plataforma ERP/CRM que combina gestión comercial tradicional con herramientas de IA para renderizado 3D de productos. El sistema permite gestionar clientes, inventario, facturación, proyectos y catálogo de productos con un frontend interactivo y un backend en Python.

## Arquitectura

El proyecto sigue una arquitectura cliente-servidor con separación de responsabilidades:

- **Frontend**: Aplicación JavaScript con interfaz de usuario para gestión de módulos ERP/CRM.
- **Backend**: API en Python que expone endpoints para operaciones de negocio, persistencia de datos y integración con motores de IA.
- **Motor de IA**: Servicio integrado para generación de renders 3D de productos a partir de parámetros de configuración.
- **Docker**: Contenedores para despliegue consistente entre entornos de desarrollo y producción.

## Módulos principales

| Módulo | Descripción |
|---------|-------------|
| **CRM** | Gestión de clientes, contactos y oportunidades de venta |
| **Inventario** | Control de stock, productos y almacenes |
| **Facturación** | Emisión de facturas, proformas y gestión de impuestos |
| **Proyectos** | Seguimiento de proyectos y tareas asociadas |
| **Render 3D** | Generación de renders de productos mediante IA |
| **Digitalizador** | Herramienta de digitalización de catálogo |

## Tech Stack

- **Frontend**: JavaScript, HTML, CSS
- **Backend**: Python
- **IA/Renderizado**: Motor de renderizado 3D con IA (`ai_engine.py`, `render_3d.py`)
- **Despliegue**: Docker, Docker Compose
- **CI/CD**: GitHub Actions
- **Dependencias**: Dependabot para actualizaciones automáticas

## Requisitos previos

- Node.js 18+ y npm
- Python 3.10+
- Docker y Docker Compose (opcional, para despliegue con contenedores)
- pip (gestor de paquetes de Python)

## Instalación

### Opción 1: Local

```bash
# Clonar el repositorio
git clone https://github.com/marioluiggihome-oss/ERP-CRM-14-03-2026.git
cd ERP-CRM-14-03-2026

# Instalar dependencias del frontend
npm install

# Instalar dependencias del backend
pip install -r requirements.txt
# o si están en backend/
pip install -r backend/requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones

# Iniciar el frontend
npm start

# Iniciar el backend (en otra terminal)
python app.py
# o
python backend/app.py
```

### Opción 2: Docker

```bash
# Clonar y construir
git clone https://github.com/marioluiggihome-oss/ERP-CRM-14-03-2026.git
cd ERP-CRM-14-03-2026

docker-compose up --build
```

## Variables de entorno

Crea un archivo `.env` basado en `.env.example` con las siguientes variables:

```env
# Base de datos
DB_HOST=localhost
DB_PORT=5432
DB_NAME=erp_crm
DB_USER=tu_usuario
DB_PASSWORD=tu_password

# API de IA (para renderizado 3D)
AI_API_KEY=tu_api_key
AI_PROVIDER=openai

# Configuración del servidor
PORT=5000
FLASK_ENV=development
SECRET_KEY=tu_secret_key
```

> ⚠️ **Importante**: Nunca subas el archivo `.env` al repositorio. Ya está incluido en `.gitignore`.

## Uso

1. Accede al frontend en `http://localhost:3000` (o el puerto configurado).
2. La API del backend está disponible en `http://localhost:5000`.
3. Para generar renders 3D, navega al módulo de Digitalizador y configura los parámetros del producto.

## Estructura del proyecto

```
ERP-CRM-14-03-2026/
├── frontend/          # Código del frontend (JavaScript)
├── backend/           # API en Python
│   ├── app.py         # Punto de entrada del servidor
│   ├── ai_engine.py   # Motor de IA para renders
│   └── render_3d.py   # Lógica de renderizado 3D
├── .github/
│   ├── workflows/     # Pipelines de CI/CD
│   └── dependabot.yml # Configuración de Dependabot
├── Dockerfile         # Imagen de la aplicación
├── docker-compose.yml # Orquestación de contenedores
├── LICENSE            # Licencia MIT
└── README.md          # Este archivo
```

## Testing

```bash
# Tests del frontend
npm test

# Tests del backend
pytest
# o si los tests están en una carpeta específica
pytest tests/
```

Los tests se ejecutan automáticamente en cada push y pull request mediante GitHub Actions.

## Contribuir

Las contribuciones son bienvenidas. Por favor, lee [CONTRIBUTING.md](CONTRIBUTING.md) para conocer el proceso de desarrollo y las normas de estilo.

## Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.
