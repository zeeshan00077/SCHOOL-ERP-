# Skoolzoom — Multi-Tenant School ERP SaaS (PRD)

## Problem statement
Production-ready multi-tenant SaaS ERP for schools (Pakistan-first) with full trial/subscription lifecycle, tenant isolation, and role-based access. Developer branding: "Developed by Zeeshan Computers Sheikh Fazal · 0343-0819382".

## Locked choices
- JWT auth (cookies + Bearer, 8h access / 30d refresh, bcrypt)
- Manual payment verification only (Phase 1) — Bank Transfer / JazzCash / Easypaisa
- Full English + Urdu (RTL) from day 1 with Nastaliq font
- Demo data: 2 seeded schools
- Super admin: zeeshan.ali98558@gmail.com

## Architecture
- FastAPI + Motor MongoDB (uuid string ids in `id` field)
- React 19 + Router 7 + Tailwind + shadcn/ui + Recharts + lucide-react + sonner
- Multi-tenant: every /api/school/* dependency injects school_id from JWT and enforces server-side; super_admin bypasses
- Role scoping: parents/students only see their own children/self across students, invoices, exams, marks, results, attendance, timetable, diary, voucher, result-card
- Audit logs (scrubbed of Mongo _id) on every mutation
- Brute-force lockout keyed on email (X-Forwarded-For handled)

## Phase 1 — SHIPPED (2026-02-13)
Landing, school registration+7d trial, JWT auth (+lockout/refresh/forgot/reset), Super Admin console (schools/plans/payments/audit), School ERP (dashboard/students/teachers/parents/classes+sections/subjects/attendance/fees+invoices+payments/exams+marks+results/timetable/notices/users/settings), Subscription page with manual payment, EN/UR RTL, light/dark, developer branding, tenant isolation verified.

## Phase 2A — SHIPPED (2026-02-13)
- **Daily Diary/Homework** — teacher CRUD, parent/student read-only scoped to own children/class
- **Printable Fee Voucher** — 3-copy A4 (School/Bank/Parent) with configurable bank_instructions
- **Printable Result Card** — A4 with school logo, subject-wise marks, totals, grade, position, attendance summary, signatures
- **WhatsApp Reminders architecture** — config/due-soon preview/queue endpoint. Returns `integration_configured=false` and NEVER falsely claims sent when env vars unset
- **Change Password** endpoint + page
- **Login demo credentials hidden** behind "Show" toggle
- **Role scoping fix** — students/fee-invoices/exams/marks/results/attendance/timetable now correctly filter for parent/student roles

## Backlog
- **P2B**: Front desk, admissions, syllabus, PTM, complaints, tasks, download center
- **P3**: POS, Inventory, Library, Transport
- **P4**: HR/Payroll, advanced accounting, PDF exports for all reports
- **P5**: Real WhatsApp/SMS/Email integrations, Stripe/Razorpay, PWA, biometric attendance, AI features
- Per-school idempotent demo seeding
- Confirm business rule for trial+plan stacking on payment approval

## Production hardening remaining
- Rotate all seeded passwords via /app/change-password before go-live
- Rebind CORS to specific origins (not *) in backend/.env
- Add file upload storage (S3-compatible or Emergent object storage) for logos/proofs/attachments
- Wire real WhatsApp Business API by setting WHATSAPP_ACCESS_TOKEN + WHATSAPP_PHONE_NUMBER_ID env vars
