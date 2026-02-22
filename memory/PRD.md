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
- **Database:** MongoDB
- **AI Integration:** Google Gemini via emergentintegrations

## Catalog Import Progress

### Completed Pages
| Pages | Date | Products Added | Category |
|-------|------|----------------|----------|
| 230-234 | Previous session | 30 | Various |
| 235-239 | Dec 2025 | 19 | COLUMNAS HORNO+MICRO 220cm |

### Current Statistics
- **Total Products:** 19 (fresh environment)
- **Last Page Processed:** 239
- **Next Page:** 240

### Products from Pages 235-239
All products are PROGRAMA ESTANDAR - COLUMNAS - ALTO 220cm FONDO 58cm:
- 22HM1P1PABL600, 22HM4CB1P600, 22HM4CL1P600, 22HM4CB2P600
- 22HM4CL2P600, 22HM1G2CB1P600, 22HM1G2CL1P600, 22HM1G2CB2P600
- 22HM1G2CL2P600, 22HM1G1CB1P600, 22HM1G1CL1P600, 22HM1G1CB2P600
- 22HM1G1CL2P600, 22HM1GB1P600, 22HM1GL1P600, 22HM1GB2P600
- 22HM1GL2P600, 22HM2G1CB1P600, 22HM2G1CB2P600

⚠️ **Pending:** 22HM2G1CL1P600 (empty price cells in source image)

## Completed Tasks (Dec 2025)

### Icons for Foldable Doors ✅
- Updated `CabinetIcon.jsx` with improved visual representations for:
  - **HK-TOP:** Hinged door opening upward (red)
  - **HS (Servo-Drive):** Motorized lift system with servo symbol (green)
  - **HL (Lift):** Vertical lift door mechanism (violet)
  - **HF (Free-Fold):** Bi-fold door with central hinge (cyan)
- Icons now visually represent the door mechanism instead of just text labels
- Tested and verified in both library view and budget view

## Pending Tasks

### P0 - High Priority
- [ ] Continue meticulous data import for pages 95-234 (Resume at page 152)
- [ ] Implement Digitalizador Analyzer Catalog Search
- [ ] Implement Draggable Accessories in Armarios

### P1 - Medium Priority
- [ ] Replace "Servo Drive" text (waiting for replacement text)
- [ ] Verify data export integrity
- [ ] Test multi-page PDF export in Digitalizador

### P2 - Lower Priority
- [ ] Client-Sales Rep Assignment
- [ ] Special "Casco" series with zero-cost logic
- [ ] CRM and Order Management workflow

### P3 - Technical Debt
- [ ] Refactor server.py (>6500 lines)
- [ ] Refactor Digitalizador.jsx (>1200 lines)
- [ ] Refactor Armarios.jsx (>2000 lines)
- [ ] Consolidate data ingestion scripts

## Key Files
- `/app/backend/server.py` - Main backend
- `/app/frontend/src/components/Digitalizador.jsx`
- `/app/frontend/src/components/Armarios.jsx`
- `/app/frontend/src/components/BudgetTable.jsx`
- `/app/frontend/src/components/SettingsModal.jsx`
- `/app/process_pages_235_239.py` - Latest import script

## Test Credentials
- **User:** MARIO
- **Password:** MARIO
