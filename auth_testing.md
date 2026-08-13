# Auth Testing Playbook — Skoolzoom

## Verify MongoDB
```
mongosh
use skoolzoom_db
db.users.find({role: "super_admin"}).pretty()
db.schools.find({}).pretty()
```
Check: bcrypt hash starts with `$2b$`, unique index on `users.email`, TTL on `password_reset_tokens.expires_at`.

## Login (Super Admin)
```
API=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)
curl -c /tmp/c.txt -X POST "$API/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"zeeshan.ali98558@gmail.com","password":"ZeeshanAdmin@2026"}'
curl -b /tmp/c.txt "$API/api/auth/me"
```

## Tenant Isolation Test
1. Login as `admin@greenvalley.edu` — should see only Green Valley students.
2. Login as `admin@iqra.edu` — should see only Iqra students.
3. Try `GET /api/students/{green_valley_student_id}` with Iqra token — must return 404.

## Trial Flow
- Register a new school via `POST /api/auth/register-school`.
- `GET /api/school/subscription` should return `status="trial"`, `days_remaining=7`.

## Payment Approval
- Login as school admin, submit `POST /api/school/payments` with proof.
- Login as super admin, approve via `POST /api/super-admin/payments/{id}/approve`.
- School subscription becomes `active`, expiry = now + 365d.
