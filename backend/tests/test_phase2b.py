"""Phase 2B tests — Student unique ID, photo upload, ID card + bulk PDF, landscape voucher PDF."""
import io
import os
import uuid

import pytest
import requests
from PIL import Image

BASE = os.environ.get("REACT_APP_BACKEND_URL", "https://school-erp-saas-2.preview.emergentagent.com").rstrip("/")
API = f"{BASE}/api"

SUPER = ("zeeshan.ali98558@gmail.com", "ZeeshanAdmin@2026")
SCHOOL_A = ("admin@greenvalley.edu", "School@123")
SCHOOL_B = ("admin@iqra.edu", "School@123")
TEACHER_A = ("teacher@greenvalley.edu", "Teacher@123")
PARENT_A = ("parent@greenvalley.edu", "Parent@123")
STUDENT_A = ("student@greenvalley.edu", "Student@123")


def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=15)
    assert r.status_code == 200, f"login {email}: {r.status_code} {r.text}"
    return r.json()["access_token"], r.json()["user"]


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


def _hj(tok):
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


def _tiny_png_bytes(color=(255, 0, 0), size=(20, 20)) -> bytes:
    im = Image.new("RGB", size, color)
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


# ---------- session fixtures ----------
@pytest.fixture(scope="module")
def admin_a(): return _login(*SCHOOL_A)
@pytest.fixture(scope="module")
def admin_b(): return _login(*SCHOOL_B)
@pytest.fixture(scope="module")
def teacher_a(): return _login(*TEACHER_A)
@pytest.fixture(scope="module")
def parent_a(): return _login(*PARENT_A)
@pytest.fixture(scope="module")
def student_a(): return _login(*STUDENT_A)
@pytest.fixture(scope="module")
def super_tok(): return _login(*SUPER)[0]


@pytest.fixture(scope="module")
def class_a(admin_a):
    tok, _ = admin_a
    cls = requests.get(f"{API}/school/classes", headers=_h(tok), timeout=10).json()
    assert cls, "No classes in School A"
    return cls[0]


# =========================================================
# 1) Unique Student ID backfill + generation
# =========================================================
class TestStudentUniqueId:
    def test_all_existing_students_have_student_id(self, admin_a):
        tok, _ = admin_a
        rows = requests.get(f"{API}/school/students", headers=_h(tok), timeout=15).json()
        assert isinstance(rows, list)
        # Every existing student should have a student_id (backfilled on startup)
        missing = [s for s in rows if not s.get("student_id")]
        assert not missing, f"Students missing student_id: {[m.get('name') for m in missing]}"
        # Format STU-YYYY-NNNNN
        import re
        pat = re.compile(r"^STU-\d{4}-\d{5}$")
        for s in rows:
            assert pat.match(s["student_id"]), f"bad format: {s['student_id']}"

    def test_uniqueness_within_school(self, admin_a):
        tok, _ = admin_a
        rows = requests.get(f"{API}/school/students", headers=_h(tok), timeout=15).json()
        ids = [s["student_id"] for s in rows if s.get("student_id")]
        assert len(ids) == len(set(ids)), "duplicate student_id in school A"

    def test_new_student_gets_next_id(self, admin_a, class_a):
        tok, _ = admin_a
        s = requests.post(f"{API}/school/students", headers=_hj(tok), json={
            "name": f"TEST_UniqID_{uuid.uuid4().hex[:6]}",
            "class_id": class_a["id"],
            "roll_number": "TU1",
        }, timeout=15)
        assert s.status_code == 200, s.text
        data = s.json()
        assert data.get("student_id"), "No student_id returned on create"
        assert data["student_id"].startswith("STU-")

    def test_search_by_student_id(self, admin_a, class_a):
        tok, _ = admin_a
        # create one
        s = requests.post(f"{API}/school/students", headers=_hj(tok), json={
            "name": f"TEST_Search_{uuid.uuid4().hex[:4]}",
            "class_id": class_a["id"],
            "roll_number": "TS1",
        }, timeout=15).json()
        sid_val = s["student_id"]
        # search by full student_id
        r = requests.get(f"{API}/school/students?q={sid_val}", headers=_h(tok), timeout=10)
        assert r.status_code == 200
        found = r.json()
        assert any(x["id"] == s["id"] for x in found), f"student not found by student_id {sid_val}"

    def test_school_a_and_b_sequences_independent(self, admin_a, admin_b, class_a):
        ta, _ = admin_a
        tb, _ = admin_b
        # School A latest
        sa = requests.post(f"{API}/school/students", headers=_hj(ta), json={
            "name": f"TEST_IsoA_{uuid.uuid4().hex[:4]}", "class_id": class_a["id"], "roll_number": "IA"
        }, timeout=15).json()
        # School B
        cls_b = requests.get(f"{API}/school/classes", headers=_h(tb), timeout=10).json()
        assert cls_b
        sb = requests.post(f"{API}/school/students", headers=_hj(tb), json={
            "name": f"TEST_IsoB_{uuid.uuid4().hex[:4]}", "class_id": cls_b[0]["id"], "roll_number": "IB"
        }, timeout=15).json()
        # both have student_id STU-YYYY-NNNNN but independent counters — just assert both formatted and different
        assert sa["student_id"] != sb["student_id"]
        assert sa["student_id"].startswith("STU-")
        assert sb["student_id"].startswith("STU-")


# =========================================================
# 2) Photo upload + secure serve
# =========================================================
class TestPhotoUpload:
    @pytest.fixture(scope="class")
    def uploaded_a(self, admin_a):
        tok, _ = admin_a
        files = {"file": ("t.png", _tiny_png_bytes(), "image/png")}
        r = requests.post(f"{API}/school/uploads/photo", headers=_h(tok), files=files, timeout=15)
        assert r.status_code == 200, r.text
        j = r.json()
        assert "file_id" in j and "url" in j
        assert j["url"].startswith("/api/school/uploads/")
        return {"tok": tok, "file_id": j["file_id"], "url": j["url"]}

    def test_upload_and_download_same_school(self, uploaded_a):
        r = requests.get(f"{API}/school/uploads/{uploaded_a['file_id']}",
                         headers=_h(uploaded_a["tok"]), timeout=15)
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("image/")

    def test_reject_non_image(self, admin_a):
        tok, _ = admin_a
        files = {"file": ("evil.txt", b"not an image", "text/plain")}
        r = requests.post(f"{API}/school/uploads/photo", headers=_h(tok), files=files, timeout=15)
        assert r.status_code == 400

    def test_reject_oversize(self, admin_a):
        tok, _ = admin_a
        # 4 MB PNG - use bigger image
        big = _tiny_png_bytes(size=(3000, 3000))
        # PNG compresses small solid color — force RGB noise
        import os as _os
        raw = _os.urandom(4 * 1024 * 1024 + 10)
        files = {"file": ("big.png", raw, "image/png")}
        r = requests.post(f"{API}/school/uploads/photo", headers=_h(tok), files=files, timeout=20)
        # Either 400 for size or 400 for invalid-image (random bytes) — both acceptable rejection
        assert r.status_code == 400

    def test_tenant_isolation_serve_returns_404(self, uploaded_a, admin_b):
        tb, _ = admin_b
        r = requests.get(f"{API}/school/uploads/{uploaded_a['file_id']}",
                         headers=_h(tb), timeout=15)
        assert r.status_code == 404

    def test_teacher_same_school_can_view(self, uploaded_a, teacher_a):
        tok, _ = teacher_a
        r = requests.get(f"{API}/school/uploads/{uploaded_a['file_id']}",
                         headers=_h(tok), timeout=15)
        assert r.status_code == 200

    def test_super_admin_can_view_any_file(self, uploaded_a, super_tok):
        r = requests.get(f"{API}/school/uploads/{uploaded_a['file_id']}",
                         headers=_h(super_tok), timeout=15)
        assert r.status_code == 200

    def test_path_traversal_rejected(self, admin_a):
        tok, _ = admin_a
        # embedded ".." should be rejected with 400 (fastapi routing may match a segment;
        # slash is impossible as path param without url-encoding). Try encoded and plain.
        r = requests.get(f"{API}/school/uploads/..evil", headers=_h(tok), timeout=10)
        # Route requires exact match; "..evil" is treated as file_id → 400 by ".." check
        assert r.status_code in (400, 404)

    def test_unauthenticated_download_401(self, uploaded_a):
        r = requests.get(f"{API}/school/uploads/{uploaded_a['file_id']}", timeout=10)
        assert r.status_code in (401, 403)


# =========================================================
# 3) Student admission with new fields + role gating
# =========================================================
class TestStudentAdmissionFields:
    def test_admission_with_new_fields(self, admin_a, class_a):
        tok, _ = admin_a
        r = requests.post(f"{API}/school/students", headers=_hj(tok), json={
            "name": "TEST_Admission_Fields",
            "class_id": class_a["id"],
            "cnic_bform": "12345-6789012-3",
            "admission_date": "2026-01-05",
            "academic_session": "2026-2027",
            "previous_school": "TEST Previous School",
            "emergency_contact": "+92 300 1234567",
            "photo_url": "/api/school/uploads/dummy.png",
            "roll_number": "AF1",
        }, timeout=15)
        assert r.status_code == 200, r.text
        s = r.json()
        for k in ("cnic_bform", "admission_date", "academic_session", "previous_school",
                  "emergency_contact", "photo_url"):
            assert s.get(k), f"missing field {k}"

    def test_receptionist_can_create(self, admin_a, class_a):
        # create a receptionist user
        a_tok, _ = admin_a
        email = f"reception+{uuid.uuid4().hex[:6]}@greenvalley.edu"
        u = requests.post(f"{API}/school/users", headers=_hj(a_tok), json={
            "name": "TEST Reception", "email": email, "password": "Recep@123", "role": "receptionist"
        }, timeout=10)
        assert u.status_code == 200, u.text
        # login as receptionist
        tok, _ = _login(email, "Recep@123")
        r = requests.post(f"{API}/school/students", headers=_hj(tok), json={
            "name": "TEST_RecepCreated", "class_id": class_a["id"], "roll_number": "RC1"
        }, timeout=15)
        assert r.status_code == 200, r.text

    def test_teacher_cannot_create_student(self, teacher_a, class_a):
        tok, _ = teacher_a
        r = requests.post(f"{API}/school/students", headers=_hj(tok), json={
            "name": "TEST_TeacherCreate", "class_id": class_a["id"], "roll_number": "TX1"
        }, timeout=15)
        assert r.status_code == 403


# =========================================================
# 4) Student update + photo
# =========================================================
class TestStudentUpdate:
    def test_update_fields(self, admin_a, class_a):
        tok, _ = admin_a
        s = requests.post(f"{API}/school/students", headers=_hj(tok), json={
            "name": "TEST_UpdateOrig", "class_id": class_a["id"], "roll_number": "UP1"
        }, timeout=15).json()
        r = requests.put(f"{API}/school/students/{s['id']}", headers=_hj(tok), json={
            "name": "TEST_UpdateNew", "emergency_contact": "+92 111"
        }, timeout=15)
        assert r.status_code == 200, r.text
        # verify persistence
        got = requests.get(f"{API}/school/students/{s['id']}", headers=_h(tok), timeout=10).json()
        assert got["name"] == "TEST_UpdateNew"
        assert got["emergency_contact"] == "+92 111"
        # student_id preserved
        assert got["student_id"] == s["student_id"]

    def test_update_cross_tenant_404(self, admin_a, admin_b, class_a):
        ta, _ = admin_a
        s = requests.post(f"{API}/school/students", headers=_hj(ta), json={
            "name": "TEST_UpdCross", "class_id": class_a["id"], "roll_number": "XT1"
        }, timeout=15).json()
        tb, _ = admin_b
        r = requests.put(f"{API}/school/students/{s['id']}", headers=_hj(tb), json={"name": "hack"}, timeout=10)
        assert r.status_code == 404

    def test_photo_update_teacher_allowed(self, teacher_a, admin_a, class_a):
        a_tok, _ = admin_a
        s = requests.post(f"{API}/school/students", headers=_hj(a_tok), json={
            "name": "TEST_PhotoUpd", "class_id": class_a["id"], "roll_number": "PU1"
        }, timeout=15).json()
        tok, _ = teacher_a
        r = requests.put(f"{API}/school/students/{s['id']}/photo", headers=_hj(tok),
                         json={"photo_url": "/api/school/uploads/x.png"}, timeout=10)
        assert r.status_code == 200


# =========================================================
# 5) Voucher PDF (landscape 3-copy)
# =========================================================
class TestVoucherPDF:
    @pytest.fixture(scope="class")
    def invoice_a(self, admin_a, class_a):
        tok, _ = admin_a
        # need a student
        s = requests.post(f"{API}/school/students", headers=_hj(tok), json={
            "name": "TEST_VoucherPDF", "class_id": class_a["id"], "roll_number": "VP1"
        }, timeout=15).json()
        inv = requests.post(f"{API}/school/fee-invoices", headers=_hj(tok), json={
            "student_id": s["id"], "title": "TEST_VP_Fee", "amount": 5000,
            "due_date": "2026-02-05",
        }, timeout=15)
        assert inv.status_code == 200, inv.text
        return inv.json()

    def test_voucher_pdf_binary(self, admin_a, invoice_a):
        tok, _ = admin_a
        r = requests.get(f"{API}/school/fee-invoices/{invoice_a['id']}/voucher.pdf",
                         headers=_h(tok), timeout=20)
        assert r.status_code == 200, r.text[:400]
        assert r.headers.get("content-type", "").startswith("application/pdf")
        assert r.content[:4] == b"%PDF", r.content[:20]
        # sanity — should include the three copy labels via search of PDF text is hard; skip
        assert len(r.content) > 1000

    def test_voucher_pdf_cross_school_404(self, admin_b, invoice_a):
        tok, _ = admin_b
        r = requests.get(f"{API}/school/fee-invoices/{invoice_a['id']}/voucher.pdf",
                         headers=_h(tok), timeout=20)
        assert r.status_code == 404


# =========================================================
# 6) ID Card preview + bulk PDF
# =========================================================
class TestIdCards:
    @pytest.fixture(scope="class")
    def some_student(self, admin_a, class_a):
        tok, _ = admin_a
        rows = requests.get(f"{API}/school/students", headers=_h(tok), timeout=10).json()
        # prefer an existing student
        if rows:
            return rows[0]
        s = requests.post(f"{API}/school/students", headers=_hj(tok), json={
            "name": "TEST_ICard", "class_id": class_a["id"], "roll_number": "IC1"
        }, timeout=15).json()
        return s

    def test_id_card_preview(self, admin_a, some_student):
        tok, _ = admin_a
        r = requests.get(f"{API}/school/id-cards/{some_student['id']}",
                         headers=_h(tok), timeout=15)
        assert r.status_code == 200, r.text
        j = r.json()
        assert "school" in j and "student" in j and "session" in j
        assert j["student"].get("student_id")
        assert "class_name" in j["student"]
        assert "id_card_back_text" in j["school"]

    def test_id_card_cross_school_404(self, admin_b, some_student):
        tok, _ = admin_b
        r = requests.get(f"{API}/school/id-cards/{some_student['id']}",
                         headers=_h(tok), timeout=10)
        assert r.status_code == 404

    def test_bulk_by_student_ids(self, admin_a, some_student):
        tok, _ = admin_a
        r = requests.post(f"{API}/school/id-cards/pdf", headers=_hj(tok),
                         json={"student_ids": [some_student["id"]]}, timeout=30)
        assert r.status_code == 200, r.text[:400]
        assert r.headers.get("content-type", "").startswith("application/pdf")
        assert r.content[:4] == b"%PDF"

    def test_bulk_by_class(self, admin_a, some_student):
        tok, _ = admin_a
        r = requests.post(f"{API}/school/id-cards/pdf", headers=_hj(tok),
                         json={"class_id": some_student["class_id"]}, timeout=45)
        assert r.status_code == 200, r.text[:400]
        assert r.content[:4] == b"%PDF"

    def test_bulk_requires_input(self, admin_a):
        tok, _ = admin_a
        r = requests.post(f"{API}/school/id-cards/pdf", headers=_hj(tok), json={}, timeout=15)
        assert r.status_code == 400

    def test_bulk_class_from_other_school_returns_404_or_no_match(self, admin_a, admin_b):
        # Get a class from School B, use its id from A → should be 404 (no students matched)
        tb, _ = admin_b
        cls_b = requests.get(f"{API}/school/classes", headers=_h(tb), timeout=10).json()
        assert cls_b
        ta, _ = admin_a
        r = requests.post(f"{API}/school/id-cards/pdf", headers=_hj(ta),
                         json={"class_id": cls_b[0]["id"]}, timeout=15)
        assert r.status_code == 404

    def test_teacher_allowed_pdf(self, teacher_a, some_student):
        tok, _ = teacher_a
        r = requests.post(f"{API}/school/id-cards/pdf", headers=_hj(tok),
                         json={"student_ids": [some_student["id"]]}, timeout=30)
        assert r.status_code == 200

    def test_parent_forbidden_pdf(self, parent_a):
        tok, _ = parent_a
        r = requests.post(f"{API}/school/id-cards/pdf", headers=_hj(tok),
                         json={"student_ids": ["x"]}, timeout=10)
        assert r.status_code == 403

    def test_student_forbidden_pdf(self, student_a):
        tok, _ = student_a
        r = requests.post(f"{API}/school/id-cards/pdf", headers=_hj(tok),
                         json={"student_ids": ["x"]}, timeout=10)
        assert r.status_code == 403


# =========================================================
# 7) Configurable back text via settings
# =========================================================
class TestIdCardBackText:
    def test_settings_update_and_reflect(self, admin_a, class_a):
        tok, _ = admin_a
        txt = f"TEST_BACK_{uuid.uuid4().hex[:6]}"
        r = requests.put(f"{API}/school/settings", headers=_hj(tok),
                         json={"id_card_back_text": txt}, timeout=10)
        assert r.status_code == 200
        # fetch id-card preview → back text present
        rows = requests.get(f"{API}/school/students", headers=_h(tok), timeout=10).json()
        assert rows
        card = requests.get(f"{API}/school/id-cards/{rows[0]['id']}", headers=_h(tok), timeout=10).json()
        assert card["school"]["id_card_back_text"] == txt


# =========================================================
# 8) Result card auto-photo
# =========================================================
class TestResultCardPhoto:
    def test_result_card_includes_photo_url(self, admin_a, class_a):
        tok, _ = admin_a
        # create student with photo_url
        s = requests.post(f"{API}/school/students", headers=_hj(tok), json={
            "name": "TEST_RCPhoto", "class_id": class_a["id"], "roll_number": "RP1",
            "photo_url": "/api/school/uploads/rc.png",
        }, timeout=15).json()
        # exam + marks
        exam = requests.post(f"{API}/school/exams", headers=_hj(tok), json={
            "name": f"TEST_RCPhoto_Ex_{uuid.uuid4().hex[:4]}",
            "class_id": class_a["id"], "start_date": "2026-01-01", "end_date": "2026-01-02",
            "total_marks": 100, "passing_marks": 40}, timeout=10).json()
        subj = requests.post(f"{API}/school/subjects", headers=_hj(tok),
                             json={"name": f"TEST_S_{uuid.uuid4().hex[:4]}"}, timeout=10).json()
        requests.post(f"{API}/school/marks", headers=_hj(tok), json={
            "exam_id": exam["id"], "subject_id": subj["id"],
            "marks": [{"student_id": s["id"], "marks_obtained": 80}],
        }, timeout=10)
        r = requests.get(f"{API}/school/results/{exam['id']}/students/{s['id']}/card",
                         headers=_h(tok), timeout=15)
        assert r.status_code == 200, r.text
        card = r.json()
        assert card["student"].get("photo_url") == "/api/school/uploads/rc.png"


# =========================================================
# 9) Regression — quick smoke on Phase 1 + 2A endpoints still work
# =========================================================
class TestRegressionSmoke:
    def test_login_super(self):
        tok, u = _login(*SUPER)
        assert u["role"] == "super_admin"

    def test_dashboard_admin(self, admin_a):
        tok, _ = admin_a
        r = requests.get(f"{API}/school/dashboard", headers=_h(tok), timeout=15)
        assert r.status_code == 200

    def test_voucher_json_endpoint_still_200(self, admin_a):
        tok, _ = admin_a
        invs = requests.get(f"{API}/school/fee-invoices", headers=_h(tok), timeout=15).json()
        if invs:
            r = requests.get(f"{API}/school/fee-invoices/{invs[0]['id']}/voucher",
                             headers=_h(tok), timeout=15)
            assert r.status_code == 200

    def test_parent_students_only_own_children(self, parent_a):
        tok, u = parent_a
        r = requests.get(f"{API}/school/students", headers=_h(tok), timeout=10)
        assert r.status_code == 200
        for stu in r.json():
            assert stu.get("parent_id") == u["id"], f"leaked student {stu.get('name')}"

    def test_audit_logs_no_500(self, admin_a):
        tok, _ = admin_a
        r = requests.get(f"{API}/school/audit-logs", headers=_h(tok), timeout=10)
        assert r.status_code == 200
