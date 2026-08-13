# Skoolzoom — Multi-Tenant School ERP SaaS (PRD)

## Problem statement
Production-ready multi-tenant SaaS ERP for schools (Pakistan-first) with tenant isolation, RBAC, subscription lifecycle, printable/PDF documents, and photo-driven records. Developer branding: "Developed by Zeeshan Computers Sheikh Fazal · 0343-0819382".

## Locked choices
- JWT auth (cookies + Bearer, bcrypt); manual payment verification; EN + Urdu (RTL); demo data
- Super admin owner: zeeshan.ali98558@gmail.com

## Architecture
- FastAPI + Motor MongoDB (uuid string ids)
- React 19 + Router 7 + Tailwind + shadcn/ui + Recharts + lucide-react + sonner
- xhtml2pdf (pisa) for server-side PDF generation (`/app/backend/pdf_service.py`)
- Local file uploads at `/app/backend/uploads/{school_id}/{uuid}.ext` served via authenticated endpoint
- Tenant isolation on every /api/school/*; role scoping for parents/students on students/invoices/exams/marks/results/attendance/timetable/diary/voucher/id-card
- Audit logs on every mutation (scrubbed of BSON _id)
- Brute-force lockout keyed on email + X-Forwarded-For

## Phase 1 — SHIPPED (2026-02-13)
Landing, school registration (7d trial), JWT auth (+lockout/refresh/forgot/reset), Super Admin console, School ERP (students/teachers/parents/classes/attendance/fees/exams/timetable/notices/users/settings), Subscription manual payment, EN/UR RTL, light/dark.

## Phase 2A — SHIPPED (2026-02-13)
Daily Diary, Fee Voucher print, Result Card print, WhatsApp Reminders architecture (never fake-sends), Change Password, hidden demo credentials, role scoping fixes.

## Phase 2B — SHIPPED (2026-02-13)
- **Unique Student ID** — `STU-YYYY-NNNNN` per-school sequence in `db.counters`; backfilled at startup; searchable via ?q= across id/name/adm/father/roll
- **Secure photo upload** — multipart POST /api/school/uploads/photo (MIME + 3MB validation, safe uuid filename); GET /api/school/uploads/{file_id} authenticated + tenant-scoped
- **Extended student fields** — cnic_bform, admission_date, academic_session, previous_school, emergency_contact, photo_url
- **Student profile page** with change photo, edit fields, generate/download ID card
- **ID Card generator** — HTML front+back preview at /print/id-card/:studentId + real PDF via POST /api/school/id-cards/pdf (bulk by student_ids OR whole class, one combined PDF)
- **Configurable back text** — school.id_card_back_text (editable in Settings)
- **Result Card auto-photo** — endpoint payload now includes student.photo_url
- **A4 LANDSCAPE Fee Voucher** — 3 copies (Student/Parent/Bank) on ONE page via /print/voucher and /api/school/fee-invoices/{id}/voucher.pdf
- **Reusable PDF service** — pdf_service.voucher_pdf() + id_cards_pdf() ready for future documents
- **Receptionist role** — can create students & set photos
- **Tests**: 89/89 pass (52 regression + 37 Phase 2B)

## Backlog / Phase 3 candidates
- Admissions module (online enquiry → application → approval → student creation)
- Front desk (visitors, calls, appointments)
- POS / Inventory / Library / Transport / HR-Payroll
- Real WhatsApp Business API wiring
- Move file storage to Emergent object storage
- PDFs for Result Card, Attendance report, Payroll slips
- Parent dashboard scoped aggregates (currently shows school-wide numbers)
- Pillow-resize student photos to 200×250 before embedding in PDFs
