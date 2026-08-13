# Skoolzoom — Multi-Tenant School ERP SaaS (PRD)

## Problem statement
Build a production-ready multi-tenant SaaS ERP for schools (Pakistan-first, internationally extensible), covering front desk, admissions, students, teachers, parents, attendance, timetable, exams, fees, accounts, transport, library, HR, LMS, communication — with 7-day free trial, annual subscription plans, super-admin platform control, and tenant isolation. Developer branding: "Developed by Zeeshan Computers Sheikh Fazal · 0343-0819382".

## User choices (locked)
- Auth: JWT (email/password, access + refresh, cookies + Bearer)
- Payments: Manual verification only for Phase 1 (Bank Transfer / JazzCash / Easypaisa)
- Language: English + Urdu with full RTL toggle from day 1
- Demo data: 2 demo schools auto-seeded
- Super admin email: zeeshan.ali98558@gmail.com

## Architecture
- FastAPI + Motor (MongoDB) + Pydantic; UUID string ids in `id` field (no ObjectId leakage)
- React 19 + React Router 7 + Tailwind + shadcn/ui + Recharts + lucide-react + sonner
- Multi-tenant: every school-scoped collection has `school_id`; every /api/school/* dependency injects `user['school_id']` and enforces server-side; super_admin bypasses
- Audit logs on every mutation (create/update/delete/approve/extend)
- 8h access tokens, 30d refresh; brute-force lockout keyed on email (X-Forwarded-For for audit)

## Phase 1 — IMPLEMENTED (2026-02-13)
- Public landing (hero, modules bento, pricing, footer, dev branding, EN/UR RTL, light/dark)
- School registration (7-day trial auto-started)
- Login / Logout / Forgot / Reset password (JWT, bcrypt)
- Super Admin console: dashboard stats, schools list + extend/suspend/activate, plans CRUD, payment approvals, audit logs
- School Admin app: dashboard (7-day attendance chart, 6-mo fee series), students, teachers, parents, classes + sections, subjects, attendance grid marking, fee invoices + payments + receipts, exams + marks entry + results (grade/position), timetable grid + conflict detection, notices, users & roles, school settings
- Subscription page: manual payment submission (bank transfer/JazzCash/Easypaisa)
- Trial + subscription enforcement (402 on expired; super_admin bypasses)
- Role-based sidebar (users/settings hidden from non-admins)
- Tenant isolation verified: School A ≠ School B queries (13 vs 8 students)
- Demo seed: Green Valley Public School (Lahore) + Iqra Model Academy (Karachi) with classes, sections, subjects, teachers, students, notices

## Deferred (backlog)
- P2 — Front desk, admissions, daily diary/homework, syllabus, PTM, complaints, tasks, download center
- P3 — POS, Inventory, Library, Transport
- P4 — HR/Payroll, advanced accounting, advanced reports/exports
- P5 — SMS/WhatsApp/Email integrations, real online payment gateways (Stripe/Razorpay), PWA/mobile shell, biometric attendance, AI features

## Credentials (see /app/memory/test_credentials.md)
Super admin, both school admins, teacher, parent, student all seeded.
