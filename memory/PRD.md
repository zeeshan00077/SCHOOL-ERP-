# Skoolzoom — Multi-Tenant School ERP SaaS (PRD)

## Problem statement
Production-ready multi-tenant SaaS ERP for schools (Pakistan-first) with full trial/subscription lifecycle, tenant isolation, RBAC + granular custom roles, secure uploads, real PDF & XLSX generation, financial workflows with ledger, admissions pipeline, and official WhatsApp Business Cloud API integration. Developer branding: "Developed by Zeeshan Computers Sheikh Fazal · 0343-0819382".

## Architecture
FastAPI + Motor MongoDB · uuid string ids · React 19 + Router 7 + Tailwind + shadcn/ui + Recharts · xhtml2pdf for PDFs · openpyxl for XLSX · httpx for WhatsApp Cloud API · JWT (cookies + Bearer, bcrypt) · every /api/school/* enforces school_id server-side · audit logs · brute-force lockout · unique index on ledger(school_id, ref_type, ref_id) enforces idempotency at DB level.

## Phase 1–3 — SHIPPED
Full auth + tenants, super admin console, ERP CRUD, subscription + manual payment, EN/UR RTL, light/dark, Daily Diary, ID Cards front+back + bulk PDF, A4 landscape 3-copy Fee Voucher PDF, Result Card PDF, unique Student IDs, secure photo upload, Expenses + approval + ledger, Payroll + salary slip PDF, Cash/Bank accounts + Ledger, Reports summary + CSV, Admissions (public /apply → convert), system settings super-admin-only, parent dashboard scoping. 124/124 tests.

## Phase 4 (2026-02-13) — SHIPPED
- **Custom Role Builder** — permissions catalog (14 modules × up to 7 actions); CRUD /api/school/custom-roles; server-side sanitization strips unknown modules/actions and platform-level escalation attempts; cross-tenant enforcement; assign PUT /users/{uid}/custom-role rejects role from another school
- **Fee → Ledger auto-post** — pay_create writes ledger CREDIT idempotently; refund endpoint writes DEBIT reversal + reverses invoice paid_amount; unique DB index (school_id, ref_type, ref_id) enforces hard idempotency
- **Real WhatsApp Business Cloud API** — POST /reminders/send-now calls Graph API via httpx when WHATSAPP_ACCESS_TOKEN + WHATSAPP_PHONE_NUMBER_ID env vars set; when unset, returns integration_configured=false and NEVER falsely claims sent; reminder_logs store queued/sending/sent/delivered/read/failed with provider_message_id; POST /webhooks/whatsapp/status updates delivery state
- **XLSX exports** — openpyxl-generated Students/Fee Collection/Expenses/Payroll/Ledger .xlsx with branded header rows, column widths, totals rows; CSV exports untouched
- **Tests** — 144/144 pass (124 baseline + 20 Phase 4)

## Production hardening remaining
- WhatsApp webhook needs X-Hub-Signature-256 HMAC verification (needs WHATSAPP_APP_SECRET env)
- Retry with exponential backoff for WhatsApp 429/5xx
- Rotate all seeded demo passwords before go-live
- Move file uploads to Emergent object storage
- Rate-limit public /api/public/admission-enquiries
- HTML-escape user-provided strings before xhtml2pdf interpolation

## Remaining ERP modules from original scope
Front Desk (visitors/calls/appointments), full Admissions workflow (documents, admission fee), Syllabus tracking, PTM scheduling, Complaints/Tickets, Tasks, Download Center, POS (school store/uniform), Inventory, Library (books/issue/return/fine), Transport (routes/vehicles/drivers), full HR (leaves/departments/documents), Certificates generator, Attendance %/late report, Defaulter list PDF, Payroll expense report, Online payment gateway (Stripe/JazzCash), Biometric attendance, LMS (courses/lessons/quizzes), PWA/mobile shell, AI features.
