# Skoolzoom — Multi-Tenant School ERP SaaS (PRD)

## Problem statement
Production-ready multi-tenant SaaS ERP for schools (Pakistan-first) with full trial/subscription lifecycle, tenant isolation, RBAC, secure uploads, real PDF generation, financial workflows and admissions pipeline. Developer branding: "Developed by Zeeshan Computers Sheikh Fazal · 0343-0819382".

## Architecture
FastAPI + Motor MongoDB · uuid string ids · React 19 + Router 7 + Tailwind + shadcn/ui + Recharts · xhtml2pdf (pisa) for PDFs · local file uploads at /app/backend/uploads/{school_id}/ · JWT (cookies + Bearer, bcrypt) · every /api/school/* enforces school_id server-side · role scoping for parent/student on every listable resource · audit logs on every mutation · brute-force lockout by email + X-Forwarded-For.

## Phase 1 (2026-02-13) — SHIPPED
Landing, school registration (7d trial), auth (login/logout/register/refresh/forgot/reset + lockout), Super Admin console, School ERP (students/teachers/parents/classes/attendance/fees/exams/timetable/notices/users/settings), Subscription manual payment, EN/UR RTL, light/dark.

## Phase 2A — SHIPPED
Daily Diary, Fee Voucher print, Result Card print, WhatsApp Reminders architecture (never fake-sends), Change Password, hidden demo credentials, legacy role scoping fixes.

## Phase 2B — SHIPPED
Unique Student ID (STU-YYYY-NNNNN per-school), secure photo upload, extended student fields, Student Profile, ID Card generator (front+back HTML + bulk PDF), configurable id_card_back_text, result card auto-photo, **A4 landscape 3-copy Fee Voucher** with real PDF, reusable pdf_service, receptionist role.

## Phase 3 (2026-02-13) — SHIPPED
- **System settings separation** — /api/system-settings super_admin-only; school admin cannot modify developer branding. /api/public/system-branding read-only surface.
- **Parent dashboard scoping** — role_scope='parent' returns children-only counts / attendance / pending_fees / notices.
- **Expense management** — CRUD + pending/approved/rejected + category filter + date range; approval creates ledger debit.
- **Payroll** — per-employee basic + allowances[] + deductions[]; monthly `process` computes net; `pay` marks paid + ledger; salary slip PDF via xhtml2pdf.
- **Accounts + Ledger** — cash/bank accounts, ledger entries for expenses and salaries.
- **Reports module** — summary (income/expenses/net/outstanding/method-split/category-split), students.csv, fee-collection.csv, presets (today/week/month/prev/year/custom).
- **Admissions** — public /api/public/admission-enquiries (no auth) creates ENQ-YYYY-NNNN, school admin/receptionist list/update/approve/reject, convert generates a real student with STU-YYYY-NNNNN and marks enquiry converted.
- **Result Card PDF** — /api/school/results/{exam_id}/students/{student_id}/card.pdf via reusable pdf_service.
- **Predefined roles expanded** — school_admin, teacher, accountant, receptionist, librarian, parent, student.
- **Public route** — /apply (unauthenticated admission enquiry form).
- **Tests** — 124/124 pass (89 baseline + 35 new).

## Phase 3 known-limitations / forward-work
- Fee payments do not yet auto-write ledger credit entries (only expenses/salaries write ledger)
- Payroll `process` is idempotent per month — no `?force=true` to re-compute after salary edits yet
- Public /api/public/admission-enquiries has Pydantic validation but no rate limit/CAPTCHA
- User-provided strings (school name, employee name) not HTML-escaped before xhtml2pdf interpolation — xhtml2pdf sanitises most, but harden later
- No fully-configurable custom-role builder UI yet (predefined roles only)
- Parent dashboard fee-collection chart shows empty pane instead of empty-state (cosmetic)

## Backlog (Phase 4+)
- Custom role builder + granular per-permission editor UI
- Full LMS, POS, Inventory, Library, Transport
- Real WhatsApp Business API delivery
- Move file storage to Emergent object storage
- Excel export (openpyxl) alongside CSV
- Pillow-resize photos before PDF embed
- More reports: attendance percentage, defaulter list PDF, payroll expense report, ledger P&L
- SMS/Email integrations, Stripe/Razorpay online payments
- PWA/mobile shell, biometric attendance, AI features
