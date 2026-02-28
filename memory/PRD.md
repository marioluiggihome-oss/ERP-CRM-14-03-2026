# LUIGGI HOME - Kitchen Budget ERP/CRM

## Original Problem Statement
Replicate a kitchen budgeting ERP/CRM application named **LUIGGI HOME** with focus on:
1. User-guided product catalog creation from master PDF (TARIFA-COMPLETA.pdf)
2. Digitalizador (draft digitizer) with image analysis, PDF export, cost/margin calculation
3. Armarios (wardrobes) component with AI-powered design
4. User roles & permissions (Admin, Gerente, Director Comercial)

## User's Preferred Language
Spanish (es)

## Core Architecture
- **Frontend:** React + Shadcn/UI
- **Backend:** FastAPI (server.py)
- **Database:** MongoDB (test_database)
- **AI Integration:** Google Gemini via emergentintegrations

## Current Statistics (Feb 2026)
- **Total Products:** 6,754
- **Programs:** 
  - ESTÁNDAR: 4,092 productos
  - GOLA: 2,518 productos
  - ALUMINIO: 144 productos
- **Categories:** 19+ unique categories

## Completed Tasks

### Feb 28, 2026 - Bug Fixes & Data Import ✅

#### Bug Fixes
1. **Product Library Rendering Bug (P0)** - FIXED
   - Root cause: 182 products had `null` IDs causing React rendering issues
   - Fix: Assigned unique UUIDs to all products with missing IDs
   
2. **Category Filtering Bug (P0)** - FIXED
   - Root cause: Outdated filtering logic filtering by category name
   - Fix: Categories now come directly from filtered products by program
   
3. **Duplicate Categories Bug (P0)** - FIXED
   - Unified `SOBREMODULOS` → `SOBREMÓDULOS`
   - Unified `Puertas` → `PUERTAS`

#### Data Import - Pages 301-400
- **Processed:** 100 pages from PDF `301-400.pdf`
- **Products imported:** 1,481 new products
- **Categories covered:** ALTOS GOLA, BAJOS GOLA, SEMICOLUMNAS GOLA, COLUMNAS GOLA

### Previous Sessions
- Icons for Foldable Doors (HK-TOP, HS, HL, HF) implemented
- Digitalizador Analyzer Search implemented
- Armarios Draggable Accessories implemented
- Massive data import from multiple PDFs (pages 95-300)

## Pending Tasks

### P1 - User Verification Pending
- [ ] Verify Digitalizador Analyzer Search functionality
- [ ] Verify Armarios Draggable Accessories functionality

### P2 - Next Tasks
- [ ] Continue product catalog import (pages 401+) when user provides more PDFs
- [ ] Client-Sales Rep Assignment

### P3 - Technical Debt
- [ ] Refactor `/app/backend/server.py` (monolithic)
- [ ] Refactor `/app/frontend/src/components/BudgetTable.jsx` (>1900 lines)
- [ ] Refactor Digitalizador.jsx and Armarios.jsx

## Key Files
- `/app/backend/server.py` - Main backend API
- `/app/frontend/src/components/BudgetTable.jsx` - Product library & budget
- `/app/frontend/src/components/Digitalizador.jsx` - Draft digitizer
- `/app/frontend/src/components/Armarios.jsx` - Wardrobe designer
- `/app/frontend/src/components/CabinetIcon.jsx` - Cabinet icons (HK, HS, HL, HF)
- `/app/import_pages_301_400.py` - Data ingestion script for pages 301-400

## Import Scripts
- `/app/import_catalog_batch.py` - Original batch import script
- `/app/import_pages_301_400.py` - Script for pages 301-400 (uses Gemini 2.5 Flash)

## Test Credentials
- **User:** MARIO
- **Password:** MARIO

## 3rd Party Integrations
- **Google Gemini:** Via emergentintegrations (Emergent LLM Key)
- **SendGrid:** Email sending (requires API key)
- **jspdf/html2canvas:** Client-side PDF generation
