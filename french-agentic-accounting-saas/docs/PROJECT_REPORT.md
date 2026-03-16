# Project: Dou Expense & Audit AI – France Edition

---

## Completed

- **User registration and login** – Signup, login, logout, token refresh, and `/me`; AuthContext with persisted session; login and signup pages with validation.
- **Dashboard UI** – Layout with real metrics (awaiting approval, this month spend, VAT recoverable), recent expenses table, expense trends chart (6 months by category), quick submit and pending approvals sidebar; skeleton loading to avoid flashes.
- **Expense lifecycle** – Create, edit, list, detail, delete; submit for approval; approve/reject with notes; list and pending-approvals APIs; New Expense and Approvals pages wired to backend.
- **Receipt upload and file service** – Upload via Next.js proxy to file service (8005); receipt status and download; backend pipeline with storage and optional encryption.
- **Backend API integration** – Frontend `api.ts` clients for auth, expenses, file, policy, anomaly, audit, report, admin, RAG, monitoring; auth token and refresh handling.
- **Local run with Docker** – `infrastructure/docker-compose.yml`: Postgres (pgvector), auth (8001), file-service (8005), expense (8002); frontend runs locally with `npm run dev`.
- **Backend services** – Auth (JWT, roles/permissions, dev mock token); expense (CRUD, submit/approve/reject, notification calls); audit (trail model, report generation); security RBAC and audit logger; notification service (email for approval requests/approved/rejected).

---

## In Progress

- **Audit Co-pilot** – UI page and chat-style interface exist; RAG/agentic backend services exist; full conversation flow and integration with audit data still being wired.
- **Notification system** – Backend `EmailNotificationService` exists and is called on expense submit/approve/reject; SMTP is optional and in-app list API is missing. Frontend Notifications page uses static/dummy data; no notifications API in `api.ts` and no real-time or in-app list.
- **Role-based access control** – Backend: roles/permissions, signup assigns Employee role, audit routes use `require_audit_permission`, security RBACRefiner. Frontend: user has `roles`/`permissions` but no route or UI gating by role; Users page uses dummy data; full RBAC enforcement in the UI is not done.

---

## Pending

- **Activity logs with timestamp tracking** – Backend has `AuditTrailService` and `/api/v1/audit/trail/{entity_type}/{entity_id}`; `/api/v1/audit/logs` returns empty placeholder data. No dedicated “Activity log” UI listing actions with timestamps.
- **Deployment for frontend and backend** – Docker Compose and Kubernetes manifests exist; GitHub Actions workflows (backend-ci, frontend-ci, deploy) are disabled; no automated build/deploy or production deployment setup.
