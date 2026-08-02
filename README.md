# ERP-CRM Luiggi Home

Sistema de gestión profesional para empresas de cocinas y muebles a medida. Integra presupuestación, CRM, catálogo de productos, renders 3D con IA, gestión de pedidos, facturación y rentabilidad en una única plataforma web.

---

## Descripción general

ERP-CRM Luiggi Home es una aplicación full-stack diseñada específicamente para el sector del mueble de cocina. Permite a los equipos de venta presupuestar cocinas montadas y desmontadas (cascos ACB), gestionar clientes y oportunidades comerciales, generar renders fotorrealistas con IA, controlar pedidos a proveedor y analizar la rentabilidad por proyecto.

La plataforma está en producción en [erp.luiggihome.es](https://erp.luiggihome.es) y da servicio a múltiples usuarios con distintos niveles de acceso (master, gerente, comercial, carpintero, montador, tienda).

---

## Arquitectura

```
erp-repo/
├── backend/          # API REST en Python (FastAPI)
│   ├── routes/       # Endpoints por módulo (auth, CRM, pedidos, cascos, IA…)
│   ├── services/     # Lógica de negocio (IA, Stripe, email, backup, JWT…)
│   ├── models/       # Modelos Pydantic (User, Client, Project, Product…)
│   └── main.py       # Punto de entrada FastAPI
├── frontend/         # SPA en React (Create React App)
│   └── src/
│       ├── components/  # ~60 componentes (CRM, Cascos, AIRenderStudio…)
│       └── App.js       # Router principal y gestión de estado global
└── .github/
    └── workflows/    # CI: build frontend + syntax check backend
```

**Stack tecnológico:**

| Capa | Tecnología |
|------|-----------|
| Frontend | React 18, Tailwind CSS, Lucide Icons |
| Backend | Python 3.11, FastAPI, Motor (async MongoDB) |
| Base de datos | MongoDB Atlas |
| Hosting | Railway (backend + frontend como servicios separados) |
| IA — Renders | Google Gemini imagen, Manus AI |
| IA — Visión/texto | Google Gemini Pro |
| Pagos | Stripe (suscripciones carpinteros) |
| Email | SMTP / SendGrid |
| Almacenamiento | Google Drive (backups automáticos) |

---

## Módulos principales

### Presupuestación
- **Cocina Montada** — presupuestador por puntos con catálogos MV, GTV y acabados personalizados.
- **Cocina Desmontada (Cascos)** — catálogo ACB con equivalencias, importación desde proforma Alvic (PDF), rentabilidad MV/Alvic.
- **Armarios** — presupuestador de armarios y vestidores a medida.

### CRM
Gestión completa del ciclo de venta: contactos, pipeline de oportunidades, calendario de visitas, parte diario, postventa y marketing por email.

### Estudio 3D (AIRenderStudio)
Generación de renders fotorrealistas por voz o texto. Soporta 4 motores de IA seleccionables: Gemini estándar, Manus, Gemini premium (prompt ultra-fotorrealista) y Gemini Flash.

### Pedidos y facturación
Control de pedidos de venta y compra, vinculación con expedientes, exportación a PDF y gestión de facturas.

### Rentabilidad
Análisis de margen por proyecto: coste de producción, valor de venta, rentabilidad por líneas de documento.

### Portal Carpintero
Acceso independiente para carpinteros externos con sus propios catálogos, usuarios y presupuestos.

---

## Variables de entorno requeridas

### Backend
- `MONGODB_URL` — Cadena de conexión MongoDB Atlas
- `JWT_SECRET` y `JWT_REFRESH_SECRET` — Claves de firma JWT
- `GEMINI_API_KEY` — Google Gemini (renders + visión)
- `REPLICATE_API_TOKEN` — Opcional, Flux Schnell renders
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` — Email
- `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` — Pagos
- `GOOGLE_DRIVE_FOLDER_ID`, `GOOGLE_SERVICE_ACCOUNT_JSON` — Backups Drive
- `BACKEND_URL`, `FRONTEND_URL`, `ENVIRONMENT`

### Frontend
- `REACT_APP_BACKEND_URL` — URL del backend en Railway

---

## Instalación local

### Requisitos previos
- Python 3.11+
- Node.js 18+
- MongoDB Atlas (o instancia local)

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8080
```

### Frontend

```bash
cd frontend
yarn install
yarn start
```

---

## CI/CD

| Workflow | Trigger | Qué comprueba |
|----------|---------|---------------|
| `frontend-build.yml` | Push a `main`, PR con cambios en `frontend/` | Compila el frontend con `yarn build` |
| `backend-check.yml` | Push a `main`, PR con cambios en `backend/` | Sintaxis Python con `compileall` + AST parse |

---

## Despliegue en Railway

- **exciting-emotion** — backend FastAPI (puerto 8080)
- **ERP-CRM-14-03-2026** — frontend React (build estático)

Los deploys se disparan automáticamente en cada push a `main`.

---

## Licencia

Copyright © 2024-2026 Luiggi Home. Todos los derechos reservados.

Este software es propietario y confidencial. Queda prohibida su copia, distribución, modificación o uso sin autorización expresa y por escrito del titular. Véase el archivo [LICENSE](./LICENSE) para más detalles.
