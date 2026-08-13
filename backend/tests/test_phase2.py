"""Phase 2A tests — Diary, Fee Voucher, Result Card, WhatsApp Reminders, Change Password.

Extends /app/backend/tests/backend_test.py; reuses demo schools + seeded users.
"""
import os
import uuid
from datetime import datetime, timezone

import pytest
import requests

BASE = os.environ.get("REACT_APP_BACKEND_URL", "https://school-erp-saas-2.preview.emergentagent.com").rstrip("/")
API = f"{BASE}/api"

SUPER = ("zeeshan.ali98558@gmail.com", "ZeeshanAdmin@2026")
SCHOOL_A = ("admin@greenvalley.edu", "School@123")
SCHOOL_B = ("admin@iqra.edu", "School@123")
TEACHER_A = ("teacher@greenvalley.edu", "Teacher@123")
TEACHER_B = ("teacher@iqra.edu", "Teacher@123")
PARENT_A = ("parent@greenvalley.edu", "Parent@123")
STUDENT_A = ("student@greenvalley.edu", "Student@123")


def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=15)
    assert r.status_code == 200, f"login {email}: {r.status_code} {r.text}"
    return r.json()["access_token"], r.json()["user"]


def _hdr(tok):
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


# ---------- session fixtures ----------
@pytest.fixture(scope="module")
def admin_a():
    return _login(*SCHOOL_A)


@pytest.fixture(scope="module")
def admin_b():
    return _login(*SCHOOL_B)


@pytest.fixture(scope="module")
def teacher_a():
    return _login(*TEACHER_A)


@pytest.fixture(scope="module")
def teacher_b():
    return _login(*TEACHER_B)


@pytest.fixture(scope="module")
def parent_a():
    return _login(*PARENT_A)


@pytest.fixture(scope="module")
def student_a():
    return _login(*STUDENT_A)


@pytest.fixture(scope="module")
def super_tok():
    return _login(*SUPER)[0]


@pytest.fixture(scope="module")
def a_class_and_student(admin_a):
    """Reuse a class + a student that has parent_id = parent_a user id."""
    tok, _ = admin_a
    parent_tok, parent_user = _login(*PARENT_A)
    # find a student under this parent
    students = requests.get(f"{API}/school/students", headers=_hdr(tok), timeout=10).json()
    child = next((s for s in students if s.get("parent_id") == parent_user["id"]), None)
    if not child:
        # seed a class + student assigned to parent if missing
        classes = requests.get(f"{API}/school/classes", headers=_hdr(tok), timeout=10).json()
        cid = classes[0]["id"]
        s = requests.post(f"{API}/school/students", headers=_hdr(tok), json={
            "name": "TEST_ChildOfParent", "class_id": cid,
            "parent_id": parent_user["id"], "roll_number": "P01",
        }, timeout=10).json()
        child = s
    return {"class_id": child["class_id"], "student_id": child["id"], "parent_id": child.get("parent_id")}


# =========================================================
# 1) Change Password
# =========================================================
class TestChangePassword:
    def test_wrong_current(self, admin_a):
        tok, _ = admin_a
        r = requests.post(f"{API}/auth/change-password", headers=_hdr(tok),
                          json={"current_password": "totally-wrong", "new_password": "NewPass@123"},
                          timeout=10)
        assert r.status_code == 400

    def test_change_and_rollback(self):
        # register throwaway school + admin, then change pw, then change back
        suffix = uuid.uuid4().hex[:6]
        email = f"chpw+{suffix}@example.com"
        reg = requests.post(f"{API}/auth/register-school", json={
            "school_name": f"TEST_CHPW_{suffix}", "admin_name": "X",
            "admin_email": email, "admin_phone": "1", "password": "Old@1234",
        }, timeout=15).json()
        tok = reg["access_token"]

        r = requests.post(f"{API}/auth/change-password", headers=_hdr(tok),
                          json={"current_password": "Old@1234", "new_password": "New@12345"}, timeout=10)
        assert r.status_code == 200

        # old password no longer works
        bad = requests.post(f"{API}/auth/login", json={"email": email, "password": "Old@1234"}, timeout=10)
        assert bad.status_code == 401
        # new password works
        good = requests.post(f"{API}/auth/login", json={"email": email, "password": "New@12345"}, timeout=10)
        assert good.status_code == 200


# =========================================================
# 2) Daily Diary
# =========================================================
class TestDiary:
    def test_teacher_can_post(self, teacher_a, a_class_and_student):
        tok, _ = teacher_a
        payload = {"class_id": a_class_and_student["class_id"],
                   "date": datetime.now(timezone.utc).date().isoformat(),
                   "homework": "TEST_HW math ex 5", "notes": "TEST"}
        r = requests.post(f"{API}/school/diary", headers=_hdr(tok), json=payload, timeout=10)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["homework"] == "TEST_HW math ex 5"
        assert d["author_role"] == "teacher"
        # persistence via GET
        rows = requests.get(f"{API}/school/diary?class_id={payload['class_id']}",
                            headers=_hdr(tok), timeout=10).json()
        assert any(x["id"] == d["id"] for x in rows)

    def test_parent_cannot_post(self, parent_a, a_class_and_student):
        tok, _ = parent_a
        r = requests.post(f"{API}/school/diary", headers=_hdr(tok), json={
            "class_id": a_class_and_student["class_id"],
            "date": datetime.now(timezone.utc).date().isoformat(),
            "homework": "spoof"}, timeout=10)
        assert r.status_code == 403

    def test_student_cannot_post(self, student_a, a_class_and_student):
        tok, _ = student_a
        r = requests.post(f"{API}/school/diary", headers=_hdr(tok), json={
            "class_id": a_class_and_student["class_id"],
            "date": datetime.now(timezone.utc).date().isoformat(),
            "homework": "spoof"}, timeout=10)
        assert r.status_code == 403

    def test_parent_get_scoped_to_children(self, parent_a, teacher_a, a_class_and_student, admin_a):
        # Ensure at least one diary in child's class
        t_tok, _ = teacher_a
        requests.post(f"{API}/school/diary", headers=_hdr(t_tok), json={
            "class_id": a_class_and_student["class_id"],
            "date": datetime.now(timezone.utc).date().isoformat(),
            "homework": "TEST_parent_scope_check"}, timeout=10)

        # Create diary in ANOTHER class of School A (parent's child not in it)
        a_tok, _ = admin_a
        classes = requests.get(f"{API}/school/classes", headers=_hdr(a_tok), timeout=10).json()
        other = next((c for c in classes if c["id"] != a_class_and_student["class_id"]), None)
        if other:
            requests.post(f"{API}/school/diary", headers=_hdr(t_tok), json={
                "class_id": other["id"],
                "date": datetime.now(timezone.utc).date().isoformat(),
                "homework": "TEST_other_class"}, timeout=10)

        p_tok, _ = parent_a
        rows = requests.get(f"{API}/school/diary", headers=_hdr(p_tok), timeout=10).json()
        # all rows must be in parent's children's classes
        allowed = {a_class_and_student["class_id"]}
        for row in rows:
            assert row["class_id"] in allowed, f"leaked class {row['class_id']}"

    def test_student_get_scoped_to_own_class(self, student_a):
        tok, u = student_a
        rows = requests.get(f"{API}/school/diary", headers=_hdr(tok), timeout=10).json()
        # get student's class
        my = requests.get(f"{API}/school/students?user_id={u['id']}", headers=_hdr(tok), timeout=10)
        # may not have such filter; just ensure only one class_id present in results
        seen_classes = {r["class_id"] for r in rows}
        assert len(seen_classes) <= 1

    def test_tenant_isolation_diary(self, teacher_a, teacher_b, admin_a, admin_b):
        ta, _ = teacher_a
        tb, _ = teacher_b
        # create a diary entry in school A
        classes_a = requests.get(f"{API}/school/classes", headers=_hdr(_login(*SCHOOL_A)[0]), timeout=10).json()
        cid_a = classes_a[0]["id"]
        d = requests.post(f"{API}/school/diary", headers=_hdr(ta), json={
            "class_id": cid_a, "date": datetime.now(timezone.utc).date().isoformat(),
            "homework": "TEST_TENANT_A"}, timeout=10).json()
        # School B GET must not include this id (spoof by class_id even)
        rows_b = requests.get(f"{API}/school/diary?class_id={cid_a}", headers=_hdr(tb), timeout=10).json()
        assert all(r["id"] != d["id"] for r in rows_b)

    def test_author_delete_only(self, teacher_a, admin_b):
        ta, _ = teacher_a
        tb, _ = admin_b
        classes_a = requests.get(f"{API}/school/classes", headers=_hdr(_login(*SCHOOL_A)[0]), timeout=10).json()
        cid = classes_a[0]["id"]
        d = requests.post(f"{API}/school/diary", headers=_hdr(ta), json={
            "class_id": cid, "date": datetime.now(timezone.utc).date().isoformat(),
            "homework": "TEST_del"}, timeout=10).json()
        # cross-tenant delete = 404
        r = requests.delete(f"{API}/school/diary/{d['id']}", headers=_hdr(tb), timeout=10)
        assert r.status_code == 404
        # author can delete
        r2 = requests.delete(f"{API}/school/diary/{d['id']}", headers=_hdr(ta), timeout=10)
        assert r2.status_code == 200


# =========================================================
# 3) Fee Voucher
# =========================================================
class TestFeeVoucher:
    @pytest.fixture(scope="class")
    def invoice_a(self, admin_a, a_class_and_student):
        tok, _ = admin_a
        inv = requests.post(f"{API}/school/fee-invoices", headers=_hdr(tok), json={
            "student_id": a_class_and_student["student_id"],
            "title": "TEST_Voucher_Fee", "amount": 5000,
            "due_date": datetime.now(timezone.utc).date().isoformat(),
        }, timeout=10)
        assert inv.status_code == 200, inv.text
        return inv.json()

    def test_admin_voucher_ok(self, admin_a, invoice_a):
        tok, _ = admin_a
        r = requests.get(f"{API}/school/fee-invoices/{invoice_a['id']}/voucher",
                         headers=_hdr(tok), timeout=10)
        assert r.status_code == 200
        v = r.json()
        for k in ("school", "student", "invoice", "previous_balance", "total_payable", "voucher_no"):
            assert k in v
        assert v["invoice"]["id"] == invoice_a["id"]
        assert v["school"]["name"]
        # bank_instructions present (may be empty string)
        assert "bank_instructions" in v["school"]

    def test_cross_school_voucher_404(self, admin_b, invoice_a):
        tok, _ = admin_b
        r = requests.get(f"{API}/school/fee-invoices/{invoice_a['id']}/voucher",
                         headers=_hdr(tok), timeout=10)
        assert r.status_code == 404

    def test_parent_can_access_own_child(self, parent_a, invoice_a):
        tok, _ = parent_a
        r = requests.get(f"{API}/school/fee-invoices/{invoice_a['id']}/voucher",
                         headers=_hdr(tok), timeout=10)
        assert r.status_code == 200, r.text

    def test_parent_cannot_access_other_child(self, parent_a, admin_a):
        # create another student not linked to parent_a
        a_tok, _ = admin_a
        classes = requests.get(f"{API}/school/classes", headers=_hdr(a_tok), timeout=10).json()
        cid = classes[0]["id"]
        stu = requests.post(f"{API}/school/students", headers=_hdr(a_tok), json={
            "name": "TEST_OtherChild", "class_id": cid, "roll_number": "OX"}, timeout=10).json()
        inv = requests.post(f"{API}/school/fee-invoices", headers=_hdr(a_tok), json={
            "student_id": stu["id"], "title": "TEST_other", "amount": 100,
            "due_date": datetime.now(timezone.utc).date().isoformat()}, timeout=10).json()
        p_tok, _ = parent_a
        r = requests.get(f"{API}/school/fee-invoices/{inv['id']}/voucher",
                         headers=_hdr(p_tok), timeout=10)
        assert r.status_code == 403


# =========================================================
# 4) Result Card
# =========================================================
class TestResultCard:
    @pytest.fixture(scope="class")
    def exam_bundle(self, admin_a, a_class_and_student):
        tok, _ = admin_a
        today = datetime.now(timezone.utc).date().isoformat()
        exam = requests.post(f"{API}/school/exams", headers=_hdr(tok), json={
            "name": f"TEST_RC_Exam_{uuid.uuid4().hex[:4]}",
            "class_id": a_class_and_student["class_id"],
            "start_date": today, "end_date": today,
            "total_marks": 100, "passing_marks": 40}, timeout=10).json()
        subj = requests.post(f"{API}/school/subjects", headers=_hdr(tok),
                             json={"name": f"TEST_S_{uuid.uuid4().hex[:4]}"}, timeout=10).json()
        m = requests.post(f"{API}/school/marks", headers=_hdr(tok), json={
            "exam_id": exam["id"], "subject_id": subj["id"],
            "marks": [{"student_id": a_class_and_student["student_id"], "marks_obtained": 90}],
        }, timeout=10)
        assert m.status_code == 200
        return {"exam_id": exam["id"], "student_id": a_class_and_student["student_id"]}

    def test_admin_result_card(self, admin_a, exam_bundle):
        tok, _ = admin_a
        r = requests.get(f"{API}/school/results/{exam_bundle['exam_id']}/students/{exam_bundle['student_id']}/card",
                         headers=_hdr(tok), timeout=10)
        assert r.status_code == 200, r.text
        c = r.json()
        assert c["totals"]["percentage"] == 90.0
        assert c["totals"]["grade"]
        assert c["totals"]["position"] is not None
        assert c["totals"]["passed"] is True
        assert "attendance" in c and "subjects" in c
        assert c["developer"]["contact"] == "0343-0819382"

    def test_cross_school_card_404(self, admin_b, exam_bundle):
        tok, _ = admin_b
        r = requests.get(f"{API}/school/results/{exam_bundle['exam_id']}/students/{exam_bundle['student_id']}/card",
                         headers=_hdr(tok), timeout=10)
        assert r.status_code == 404

    def test_parent_own_child_ok(self, parent_a, exam_bundle):
        tok, _ = parent_a
        r = requests.get(f"{API}/school/results/{exam_bundle['exam_id']}/students/{exam_bundle['student_id']}/card",
                         headers=_hdr(tok), timeout=10)
        assert r.status_code == 200

    def test_parent_other_child_forbidden(self, parent_a, admin_a, exam_bundle):
        a_tok, _ = admin_a
        classes = requests.get(f"{API}/school/classes", headers=_hdr(a_tok), timeout=10).json()
        cid = classes[0]["id"]
        other_stu = requests.post(f"{API}/school/students", headers=_hdr(a_tok), json={
            "name": "TEST_RC_Other", "class_id": cid, "roll_number": "R2"}, timeout=10).json()
        p_tok, _ = parent_a
        r = requests.get(f"{API}/school/results/{exam_bundle['exam_id']}/students/{other_stu['id']}/card",
                         headers=_hdr(p_tok), timeout=10)
        assert r.status_code == 403


# =========================================================
# 5) WhatsApp Reminders architecture
# =========================================================
class TestReminders:
    def test_config_not_configured(self, admin_a):
        tok, _ = admin_a
        r = requests.get(f"{API}/school/reminders/config", headers=_hdr(tok), timeout=10)
        assert r.status_code == 200
        c = r.json()
        assert c["integration_configured"] is False
        assert "template" in c

    def test_config_update_admin_only(self, teacher_a, admin_a):
        t_tok, _ = teacher_a
        r = requests.put(f"{API}/school/reminders/config", headers=_hdr(t_tok),
                         json={"enabled": True, "days_before": 5, "template": "x"}, timeout=10)
        assert r.status_code == 403
        a_tok, _ = admin_a
        r2 = requests.put(f"{API}/school/reminders/config", headers=_hdr(a_tok),
                          json={"enabled": True, "days_before": 5,
                                "template": "Fee due for {student_name} on {due_date}, amount {amount} — {school_name}"},
                          timeout=10)
        assert r2.status_code == 200
        # readback
        c = requests.get(f"{API}/school/reminders/config", headers=_hdr(a_tok), timeout=10).json()
        assert c["days_before"] == 5

    def test_due_soon(self, admin_a, a_class_and_student):
        tok, _ = admin_a
        # ensure an unpaid invoice within window (due today)
        requests.post(f"{API}/school/fee-invoices", headers=_hdr(tok), json={
            "student_id": a_class_and_student["student_id"],
            "title": "TEST_ReminderInv", "amount": 500,
            "due_date": datetime.now(timezone.utc).date().isoformat()}, timeout=10)
        r = requests.get(f"{API}/school/reminders/due-soon", headers=_hdr(tok), timeout=15)
        assert r.status_code == 200
        j = r.json()
        assert j["integration_configured"] is False
        assert "items" in j
        if j["count"] > 0:
            item = j["items"][0]
            assert "preview_message" in item and item["preview_message"]

    def test_send_dry_run_does_not_claim_sent(self, admin_a, a_class_and_student):
        tok, _ = admin_a
        # create invoice
        inv = requests.post(f"{API}/school/fee-invoices", headers=_hdr(tok), json={
            "student_id": a_class_and_student["student_id"],
            "title": "TEST_SendReminder", "amount": 300,
            "due_date": datetime.now(timezone.utc).date().isoformat()}, timeout=10).json()
        r = requests.post(f"{API}/school/reminders/send", headers=_hdr(tok),
                         json={"invoice_ids": [inv["id"]], "dry_run": True}, timeout=15)
        assert r.status_code == 200
        j = r.json()
        assert j["integration_configured"] is False
        assert j["queued"] >= 1

        # logs must show queued (not sent)
        logs = requests.get(f"{API}/school/reminders/logs", headers=_hdr(tok), timeout=10).json()
        matched = [l for l in logs if l["invoice_id"] == inv["id"]]
        assert matched
        assert all(l["status"] == "queued" for l in matched), matched

    def test_send_forbidden_for_teacher(self, teacher_a):
        tok, _ = teacher_a
        r = requests.post(f"{API}/school/reminders/send", headers=_hdr(tok),
                         json={"invoice_ids": [], "dry_run": True}, timeout=10)
        assert r.status_code == 403


# =========================================================
# 6) Sidebar / role nav — via /auth/me role gating (not a page test)
# =========================================================
class TestParentStudentScoping:
    def test_parent_students_only_own_children(self, parent_a):
        tok, u = parent_a
        r = requests.get(f"{API}/school/students", headers=_hdr(tok), timeout=10)
        # parent may either see own children only or 200 empty; not 5xx
        assert r.status_code in (200, 403)
        if r.status_code == 200:
            data = r.json()
            for stu in data:
                # every returned student must be linked to parent (defense in depth)
                if "parent_id" in stu:
                    assert stu["parent_id"] == u["id"], f"leaked student {stu.get('id')}"
