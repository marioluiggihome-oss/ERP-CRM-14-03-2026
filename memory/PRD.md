# LUIGGI HOME - Kitchen Budget ERP/CRM

## Original Problem Statement
Replicate a kitchen budgeting ERP/CRM application named **LUIGGI HOME** with focus on:
1. User-guided product catalog creation from master PDF (TARIFA-COMPLETA.pdf)
2. Digitalizador (draft digitizer) with image analysis, PDF export, cost/margin calculation
3. Armarios (wardrobes) component with AI-powered design
4. User roles & permissions (Admin, Gerente, Director Comercial)
5. Email registration and Two-Factor Authentication (2FA)

## User's Preferred Language
Spanish (es)

## Core Architecture
- **Frontend:** React + Shadcn/UI
- **Backend:** FastAPI (server.py + modular routers)
- **Database:** MongoDB (test_database)
- **AI Integration:** Google Gemini via emergentintegrations
- **Authentication:** JWT + TOTP (pyotp, qrcode)

## Current Statistics (Mar 2026)
- **Total Products:** 7,148
- **Programs:** 
  - ESTÁNDAR: 4,092 productos
  - GOLA: 2,518 productos
  - ALUMINIO: 144 productos
- **Categories:** 19+ unique categories

## Completed Tasks

### Mar 7, 2026 - Permission Fix & Authentication Enhancement ✅

#### Bug Fixes
1. **Armarios Permission Bug (P0)** - FIXED
   - Root cause: Armarios module was rendered without checking `canAccessArmarios` permission
   - Fix: Added permission check `(state.currentUser?.isAdmin || state.currentUser?.canAccessArmarios)` in App.js
   - Files modified: `/app/frontend/src/App.js` (line 598-600)

2. **DateTime Comparison Bug in Auth** - FIXED
   - Root cause: MongoDB stores dates without timezone, causing comparison errors
   - Fix: Added timezone normalization before comparison
   - Files modified: `/app/backend/routes/auth_advanced.py`

#### New Features Implemented
1. **Email Registration System** - COMPLETE
   - User registration with email/password
   - Email verification with 6-digit code
   - Password strength validation
   - Backend: `/api/auth/register`, `/api/auth/verify-email`, `/api/auth/resend-verification`
   - Frontend: `RegisterForm.jsx` integrated into `Login.jsx`

2. **Two-Factor Authentication (2FA)** - COMPLETE
   - TOTP-based 2FA using pyotp
   - QR code generation for authenticator apps
   - 8 backup codes for recovery
   - Backend: `/api/auth/2fa/enable`, `/api/auth/2fa/verify`, `/api/auth/2fa/disable`
   - Frontend: `TwoFactorSetup.jsx` component ready for integration

3. **Enhanced Login Flow** - COMPLETE
   - Login supports email or username
   - 2FA code prompt when enabled
   - Backup code support for account recovery
   - Backend: `/api/auth/login-email`

### Previous Sessions (Feb-Mar 2026)
- Backend refactoring: Extracted routes to `/app/backend/routes/`
- Pydantic models centralized: `/app/backend/models/schemas.py` (880+ lines)
- Data audit: Corrected pricing errors in 7,148-item catalog
- IA Lab button visibility fix
- Icons for Foldable Doors (HK-TOP, HS, HL, HF) implemented
- Digitalizador Analyzer Search implemented
- Armarios Draggable Accessories implemented

## Pending Tasks

### P1 - User Verification Pending
- [ ] Verify Digitalizador Analyzer Search functionality
- [ ] Verify Armarios Draggable Accessories functionality
- [ ] Investigate product catalog issues from DOCX file (categories like "BAJOS 640 FONDO 58")

### P2 - Next Tasks
- [ ] Add 2FA configuration option in user settings/profile
- [ ] Continue product catalog import (pages 401+) when user provides more PDFs
- [ ] Client-Sales Rep Assignment
- [ ] Implement "Gerente" (Manager) role with specific permissions

### P3 - Technical Debt / Refactoring
- [ ] Complete refactoring `/app/backend/server.py` (still ~5,800 lines)
- [ ] Decompose `/app/frontend/src/components/BudgetTable.jsx` (>1900 lines)
- [ ] Decompose `/app/frontend/src/components/Armarios.jsx` (>3300 lines)

## Key Files

### Backend
- `/app/backend/server.py` - Main backend API (refactoring in progress)
- `/app/backend/routes/auth_advanced.py` - Email registration & 2FA endpoints
- `/app/backend/routes/auth.py` - Traditional authentication
- `/app/backend/routes/ia_lab.py` - AI analysis endpoints
- `/app/backend/models/schemas.py` - Centralized Pydantic models

### Frontend
- `/app/frontend/src/App.js` - Main app with permission-based navigation
- `/app/frontend/src/components/Login.jsx` - Login with email/2FA support
- `/app/frontend/src/components/RegisterForm.jsx` - Email registration form
- `/app/frontend/src/components/TwoFactorSetup.jsx` - 2FA setup component
- `/app/frontend/src/components/BudgetTable.jsx` - Product library & budget
- `/app/frontend/src/components/Digitalizador.jsx` - Draft digitizer
- `/app/frontend/src/components/Armarios.jsx` - Wardrobe designer

## Test Credentials
- **Admin User:** MARIO / MARIO
- **Test Email User:** nuevo_usuario@example.com / Test1234

## 3rd Party Integrations
- **Google Gemini:** Via emergentintegrations (Emergent LLM Key)
- **SendGrid:** Email sending (requires API key - not configured in preview)
- **pyotp/qrcode:** TOTP-based 2FA
- **jspdf/html2canvas:** Client-side PDF generation
- **recharts:** Data visualization

## API Endpoints - Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/auth/register | POST | Register new user with email |
| /api/auth/verify-email | POST | Verify email with 6-digit code |
| /api/auth/resend-verification | POST | Resend verification code |
| /api/auth/login-email | POST | Login with email (supports 2FA) |
| /api/auth/2fa/enable | POST | Enable 2FA, returns QR code |
| /api/auth/2fa/verify | POST | Verify 2FA setup |
| /api/auth/2fa/disable | POST | Disable 2FA |
| /api/auth/forgot-password | POST | Request password reset |
| /api/auth/reset-password | POST | Reset password with code |

## Test Reports
- Latest: `/app/test_reports/iteration_21.json` - All auth features PASS
