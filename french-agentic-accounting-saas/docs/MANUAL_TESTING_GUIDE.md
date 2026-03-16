# DouCompta V4.0 - Manual Testing Guide

## Prerequisites
- Docker Desktop running
- `cd infrastructure && docker-compose up -d` (all services)
- `cd frontend-web && npm run dev` (frontend at http://localhost:3000)
- Login with test credentials or dev mock token

---

## 1. Comptabilite (Accounting) - /accounting

### 1.1 PCG Seed
1. Navigate to `/accounting`
2. Open browser console, run: `fetch('http://localhost:8019/api/v1/accounting/pcg-accounts/seed', {method:'POST', headers:{'Authorization':'Bearer dev_mock_token_local'}}).then(r=>r.json()).then(console.log)`
3. **Expected**: `{seeded: N}` where N > 50

### 1.2 Journal Entries List
1. Navigate to `/accounting`
2. Verify "Ecritures" tab is active
3. Filter by journal code (ACH, VTE, BNQ)
4. Filter by status (Brouillon, Valide)
5. Change fiscal year
6. **Expected**: Table loads, filters work, pagination appears

### 1.3 Generate Entry from Expense
1. Create an expense first via `/expenses`
2. Go to `/accounting`
3. Use API: POST `/api/v1/accounting/generate` with `{expense_id: "<id>"}`
4. **Expected**: New journal entry appears with 2-3 lines (expense + TVA + supplier)

### 1.4 Entry Detail & Validation
1. Click on an entry number in the list
2. **Expected**: Detail page shows lines table with debit/credit
3. Click "Valider" on a draft entry
4. **Expected**: Status changes to "Valide", green success message

### 1.5 Trial Balance
1. Click "Balance des comptes" tab
2. Select fiscal year
3. **Expected**: Table of accounts with debit/credit totals, balance column

### 1.6 FEC Export
1. Click "Export FEC" button or navigate to `/accounting/fec`
2. Enter SIREN (9 digits) and select year
3. Click "Telecharger le FEC"
4. **Expected**: .txt file downloads with tab-separated values, 18 columns

---

## 2. Dossiers Clients - /dossiers

### 2.1 Create Dossier
1. Navigate to `/dossiers`
2. Click "Nouveau dossier"
3. Fill: Name="Test SARL", SIREN="123456789", Legal form="SARL", TVA regime="Reel normal"
4. Click "Creer"
5. **Expected**: Dossier appears in the grid

### 2.2 Dossier Detail
1. Click on a dossier card
2. **Expected**: Overview tab with general info, recent activity
3. Click "Documents" tab - verify empty state
4. Click "Historique" tab - verify "Dossier cree" event

### 2.3 Search & Filter
1. Type in search box (name or SIREN)
2. Filter by status
3. **Expected**: Results filter in real-time

---

## 3. Notifications - Header Bell

### 3.1 Notification Bell
1. Look at header - bell icon should be visible
2. Click bell icon
3. **Expected**: Dropdown opens with notification list (may be empty)
4. If notifications exist, click checkmark to mark read
5. Click "Tout marquer lu"
6. **Expected**: Badge count updates

---

## 4. Banque (Banking) - /banking

### 4.1 Create Bank Account
1. Navigate to `/banking`
2. Click "Ajouter un compte"
3. Fill: Name="Compte courant", Bank="BNP Paribas", IBAN="FR7612345678901234567890123"
4. Click "Creer"
5. **Expected**: Account card appears with balance 0.00 EUR

### 4.2 Upload Statement
1. Prepare a CSV file with columns: date;libelle;montant
2. Upload via API: POST `/api/v1/banking/accounts/{id}/upload-statement`
3. **Expected**: Transactions imported, count returned

### 4.3 Reconciliation
1. Navigate to `/banking/reconciliation?account={id}`
2. **Expected**: Two-panel view - bank transactions left, journal entries right
3. Click "Rapprochement auto"
4. **Expected**: Matching transactions turn green, summary stats update
5. Select an unmatched transaction, then click "Associer" on an entry
6. **Expected**: Manual match created

### 4.4 Transactions List
1. Navigate to `/banking/transactions?account={id}`
2. Filter by status
3. **Expected**: Table with date, label, amount, reconciliation status

---

## 5. Fiscalite (Tax) - /tax

### 5.1 Compute CA3 Declaration
1. Navigate to `/tax`
2. Click "Nouvelle declaration"
3. Select type "TVA mensuelle (CA3)"
4. Set period (e.g., 2025-01-01 to 2025-01-31)
5. Click "Calculer"
6. **Expected**: TVA collectee and deductible breakdown, net amount

### 5.2 Declaration Detail
1. Click "Voir la declaration" after computation
2. **Expected**: Summary cards (amount, due date, type), CA3 detail table
3. Click "Valider" on a computed declaration
4. **Expected**: Status changes to "Validee"

### 5.3 Tax Calendar
1. Click "Echeancier" tab
2. **Expected**: List of upcoming deadlines with status badges

### 5.4 Penalty Alerts
1. Click "Alertes" tab
2. **Expected**: Green "all clear" or red warning cards with penalty estimates

---

## 6. Analyse Financiere - /analysis

### 6.1 SIG (Soldes Intermediaires de Gestion)
1. Navigate to `/analysis`
2. Select fiscal year
3. **Expected**: SIG waterfall from CA to Resultat net

### 6.2 Ratios
1. Click "Ratios" tab
2. **Expected**: 9 ratio cards (BFR, liquidite, endettement, etc.)

### 6.3 Score
1. Click "Score" tab
2. **Expected**: Score gauge (0-100), category label, component breakdown, recommendations

### 6.4 Previsions
1. Click "Previsions" tab
2. **Expected**: Forecast table with date, predicted value, confidence bands

---

## 7. Facturation Electronique - /invoices

### 7.1 Create Invoice
1. Navigate to `/invoices`
2. Click "Nouvelle facture"
3. Fill recipient, date, add line items
4. Click "Creer la facture"
5. **Expected**: Invoice created with Factur-X XML, redirects to list

### 7.2 Invoice List
1. Navigate to `/invoices`
2. Filter by type (Emises/Recues)
3. **Expected**: Table with invoice number, client, date, TTC amount, status

---

## 8. Paie & Social - /payroll

### 8.1 Charge Allocation
1. Navigate to `/payroll`
2. Enter: Gross=3000, Net=2300, Employer charges=1200, URSSAF=400, Retirement=200
3. Click "Ventiler les charges"
4. **Expected**: 6-line journal entry with PCG accounts (641, 645, 421, 431, 437)
5. Verify total debit == total credit

---

## 9. Documents - /documents

### 9.1 Classify Document
1. Navigate to `/documents`
2. Paste text: "FACTURE N° F-2025-001 Total TTC TVA"
3. Enter filename: "facture.pdf"
4. Click "Classifier"
5. **Expected**: Result shows "facture" with confidence and route "Facturation"

### 9.2 Different Document Types
1. Try: "Bulletin de salaire Brut Net URSSAF" -> bulletin_paie
2. Try: "Releve de compte IBAN solde" -> releve_bancaire
3. Try: "Random text xyz" -> autre (0% confidence)

---

## 10. Agents Autonomes - /agents

### 10.1 Agent Dashboard
1. Navigate to `/agents`
2. **Expected**: Status cards (total, active, executions, error rate)
3. List of 5 agents (RELANCA, A2A_FISCAL, A2A_BANK, COMPTAA, BANKA)

### 10.2 Toggle Agent
1. Click "Desactiver" on an active agent
2. **Expected**: Status changes to "Inactif", button changes to "Activer"
3. Click "Activer" to re-enable
4. **Expected**: Status back to "Actif"

---

## 11. Administration SaaS - /admin/saas

### 11.1 Dashboard
1. Navigate to `/admin/saas`
2. **Expected**: 4 cards (Tenants, Abonnements, Services, Utilisation)
3. Development notice banner visible

---

## User Journeys

### Journey A: Accountant Daily Workflow
1. Login -> Dashboard
2. Check notifications (bell icon)
3. Review pending expenses in `/approvals`
4. Approve expenses -> auto-generates journal entries
5. Go to `/accounting` -> verify entries created
6. Run trial balance check
7. Export FEC if needed

### Journey B: Tax Declaration Flow
1. Go to `/accounting` -> verify all entries validated
2. Navigate to `/tax` -> "Nouvelle declaration"
3. Compute CA3 for the month
4. Review collected vs deductible TVA
5. Validate declaration
6. Check `/tax` calendar for next deadlines

### Journey C: Bank Reconciliation
1. Upload bank statement at `/banking`
2. Go to reconciliation view
3. Run auto-reconciliation
4. Manually match remaining items
5. Verify match rate in summary

### Journey D: Client Dossier Management
1. Create client dossier at `/dossiers`
2. Upload relevant documents
3. View timeline for activity history
4. Check financial analysis for the client

### Journey E: New Invoice Flow
1. Go to `/invoices/new`
2. Create invoice with line items
3. Verify Factur-X XML generated
4. Track invoice status in list
