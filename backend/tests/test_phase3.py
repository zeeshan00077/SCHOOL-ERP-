"""Phase 3 tests — system settings, parent-dashboard scoping, expenses, accounts+ledger,
payroll, reports, admissions (public + convert), result card PDF, cross-tenant enforcement."""
import os
import time
import uuid

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


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


def _hj(tok):
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


# ---------- session fixtures ----------
@pytest.fixture(scope="module")
def admin_a(): return _login(*SCHOOL_A)
@pytest.fixture(scope="module")
def admin_b(): return _login(*SCHOOL_B)
@pytest.fixture(scope="module")
def teacher_a(): return _login(*TEACHER_A)
@pytest.fixture(scope="module")
def teacher_b(): return _login(*TEACHER_B)
@pytest.fixture(scope="module")
def parent_a(): return _login(*PARENT_A)
@pytest.fixture(scope="module")
def student_a(): return _login(*STUDENT_A)
@pytest.fixture(scope="module")
def super_tok(): return _login(*SUPER)[0]


# =========================================================
# 1. System settings separation
# =========================================================
class TestSystemSettings:
    def test_get_requires_super_admin_school_admin_403(self, admin_a):
        tok, _ = admin_a
        r = requests.get(f"{API}/system-settings", headers=_h(tok), timeout=10)
        assert r.status_code == 403

    def test_get_teacher_403(self, teacher_a):
        tok, _ = teacher_a
        r = requests.get(f"{API}/system-settings", headers=_h(tok), timeout=10)
        assert r.status_code == 403

    def test_super_admin_can_get(self, super_tok):
        r = requests.get(f"{API}/system-settings", headers=_h(super_tok), timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert "developer_name" in d
        assert "platform_name" in d

    def test_super_admin_can_put(self, super_tok):
        # keep original
        cur = requests.get(f"{API}/system-settings", headers=_h(super_tok), timeout=10).json()
        orig_note = cur.get("footer_note")
        new_note = f"TEST_footer_{uuid.uuid4().hex[:6]}"
        r = requests.put(f"{API}/system-settings", headers=_hj(super_tok),
                         json={"footer_note": new_note}, timeout=10)
        assert r.status_code == 200
        after = requests.get(f"{API}/system-settings", headers=_h(super_tok), timeout=10).json()
        assert after["footer_note"] == new_note
        # restore
        requests.put(f"{API}/system-settings", headers=_hj(super_tok),
                     json={"footer_note": orig_note or ""}, timeout=10)

    def test_put_school_admin_403(self, admin_a):
        tok, _ = admin_a
        r = requests.put(f"{API}/system-settings", headers=_hj(tok),
                         json={"footer_note": "hack"}, timeout=10)
        assert r.status_code == 403

    def test_public_branding_no_auth(self):
        r = requests.get(f"{API}/public/system-branding", timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert "developer_name" in d
        assert "platform_name" in d


# =========================================================
# 2. Parent dashboard scoping
# =========================================================
class TestParentDashboard:
    def test_parent_dashboard_scoped(self, parent_a):
        tok, _ = parent_a
        r = requests.get(f"{API}/school/dashboard", headers=_h(tok), timeout=10)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("role_scope") == "parent", f"role_scope missing: {d}"
        # only child count expected (>=1 typically 1)
        assert d.get("total_students", 99) <= 5, f"parent sees {d.get('total_students')} students"
        assert d.get("total_teachers", 99) == 0
        assert d.get("total_parents", 99) == 0
        # notices filtered — should be list <=5
        assert isinstance(d.get("notices", []), list)

    def test_school_admin_dashboard_wide(self, admin_a):
        tok, _ = admin_a
        r = requests.get(f"{API}/school/dashboard", headers=_h(tok), timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert "role_scope" not in d or d.get("role_scope") != "parent"
        assert d.get("total_students", 0) >= 1


# =========================================================
# 3. Expenses (RBAC, tenant, filters, approval → ledger)
# =========================================================
@pytest.fixture(scope="module")
def expense_a(admin_a):
    tok, _ = admin_a
    payload = {"date": "2026-01-05", "category": "Electricity",
               "description": "TEST_exp_" + uuid.uuid4().hex[:6],
               "amount": 1234.0, "payment_method": "cash"}
    r = requests.post(f"{API}/school/expenses", headers=_hj(tok), json=payload, timeout=10)
    assert r.status_code == 200, r.text
    return r.json()


class TestExpenses:
    def test_create_by_admin(self, expense_a):
        assert expense_a["status"] == "pending"
        assert expense_a["amount"] == 1234.0
        assert "id" in expense_a

    def test_teacher_forbidden(self, teacher_a):
        tok, _ = teacher_a
        r = requests.post(f"{API}/school/expenses", headers=_hj(tok),
                          json={"date": "2026-01-01", "category": "Other",
                                "description": "x", "amount": 10}, timeout=10)
        assert r.status_code == 403

    def test_parent_forbidden(self, parent_a):
        tok, _ = parent_a
        r = requests.get(f"{API}/school/expenses", headers=_h(tok), timeout=10)
        assert r.status_code == 403

    def test_list_filters(self, admin_a, expense_a):
        tok, _ = admin_a
        r = requests.get(f"{API}/school/expenses?status=pending", headers=_h(tok), timeout=10)
        assert r.status_code == 200
        ids = {e["id"] for e in r.json()}
        assert expense_a["id"] in ids

        r = requests.get(f"{API}/school/expenses?category=Electricity", headers=_h(tok), timeout=10)
        assert r.status_code == 200
        assert all(e["category"] == "Electricity" for e in r.json())

        r = requests.get(f"{API}/school/expenses?date_from=2026-01-01&date_to=2026-01-31",
                         headers=_h(tok), timeout=10)
        assert r.status_code == 200

    def test_cross_tenant_invisible(self, admin_b, expense_a):
        tok, _ = admin_b
        r = requests.get(f"{API}/school/expenses", headers=_h(tok), timeout=10)
        assert r.status_code == 200
        ids = {e["id"] for e in r.json()}
        assert expense_a["id"] not in ids

    def test_cross_tenant_approve_404(self, admin_b, expense_a):
        tok, _ = admin_b
        r = requests.post(f"{API}/school/expenses/{expense_a['id']}/approve",
                          headers=_hj(tok), json={}, timeout=10)
        assert r.status_code == 404

    def test_approve_creates_ledger(self, admin_a, expense_a):
        tok, _ = admin_a
        r = requests.post(f"{API}/school/expenses/{expense_a['id']}/approve",
                          headers=_hj(tok), json={"remarks": "ok"}, timeout=10)
        assert r.status_code == 200
        # Verify ledger has an entry for this expense
        led = requests.get(f"{API}/school/ledger", headers=_h(tok), timeout=10)
        assert led.status_code == 200
        matches = [e for e in led.json() if e.get("ref_type") == "expense"
                   and e.get("ref_id") == expense_a["id"]]
        assert len(matches) == 1
        assert matches[0]["kind"] == "debit"
        assert matches[0]["amount"] == 1234.0

    def test_double_approve_fails(self, admin_a, expense_a):
        tok, _ = admin_a
        r = requests.post(f"{API}/school/expenses/{expense_a['id']}/approve",
                          headers=_hj(tok), json={}, timeout=10)
        assert r.status_code == 400


# =========================================================
# 4. Accounts + Ledger
# =========================================================
class TestAccounts:
    def test_create_and_list(self, admin_a):
        tok, _ = admin_a
        name = "TEST_acct_" + uuid.uuid4().hex[:6]
        r = requests.post(f"{API}/school/accounts", headers=_hj(tok),
                          json={"name": name, "kind": "cash", "opening_balance": 100.0}, timeout=10)
        assert r.status_code == 200
        acc = r.json()
        assert acc["name"] == name
        lst = requests.get(f"{API}/school/accounts", headers=_h(tok), timeout=10)
        assert lst.status_code == 200
        assert any(a["id"] == acc["id"] for a in lst.json())

    def test_ledger_tenant_scoped(self, admin_a, admin_b):
        toka, _ = admin_a
        tokb, _ = admin_b
        la = requests.get(f"{API}/school/ledger", headers=_h(toka), timeout=10).json()
        lb = requests.get(f"{API}/school/ledger", headers=_h(tokb), timeout=10).json()
        a_ids = {e["id"] for e in la}
        b_ids = {e["id"] for e in lb}
        assert a_ids.isdisjoint(b_ids)


# =========================================================
# 5. Payroll
# =========================================================
@pytest.fixture(scope="module")
def teacher_a_id(admin_a):
    tok, _ = admin_a
    r = requests.get(f"{API}/school/teachers", headers=_h(tok), timeout=10)
    assert r.status_code == 200
    ts = r.json()
    assert len(ts) >= 1
    return ts[0]["id"]


@pytest.fixture(scope="module")
def teacher_b_id(admin_b):
    tok, _ = admin_b
    r = requests.get(f"{API}/school/teachers", headers=_h(tok), timeout=10)
    assert r.status_code == 200
    ts = r.json()
    return ts[0]["id"] if ts else None


class TestPayroll:
    def test_set_salary(self, admin_a, teacher_a_id):
        tok, _ = admin_a
        payload = {"basic_salary": 40000,
                   "allowances": [{"name": "House", "amount": 5000}, {"name": "Transport", "amount": 2000}],
                   "deductions": [{"name": "Tax", "amount": 1000}]}
        r = requests.put(f"{API}/school/employees/{teacher_a_id}/salary",
                         headers=_hj(tok), json=payload, timeout=10)
        assert r.status_code == 200

    def test_cross_tenant_salary_404(self, admin_a, teacher_b_id):
        if not teacher_b_id:
            pytest.skip("no teacher in school B")
        tok, _ = admin_a
        r = requests.put(f"{API}/school/employees/{teacher_b_id}/salary",
                         headers=_hj(tok), json={"basic_salary": 1}, timeout=10)
        assert r.status_code == 404

    def test_process_and_pay_and_slip(self, admin_a, teacher_a_id):
        tok, _ = admin_a
        # Use unique month per run to avoid interference w/ prior "already paid" state
        month = f"2099-{(int(time.time()) % 12) + 1:02d}"
        r = requests.post(f"{API}/school/payroll/process", headers=_hj(tok),
                          json={"month": month}, timeout=15)
        assert r.status_code == 200, r.text
        run_id = r.json()["run_id"]

        # Fetch run and find our teacher entry
        runs = requests.get(f"{API}/school/payroll?month={month}", headers=_h(tok), timeout=10).json()
        assert len(runs) >= 1
        run = next(x for x in runs if x["id"] == run_id)
        entry = next(e for e in run["entries"] if e["employee_id"] == teacher_a_id)
        # net = 40000 + 5000 + 2000 - 1000 = 46000
        assert entry["net"] == 46000

        # Pay
        r = requests.post(f"{API}/school/payroll/{run_id}/pay", headers=_hj(tok),
                          json={"employee_id": teacher_a_id, "method": "cash"}, timeout=10)
        assert r.status_code == 200

        # Ledger entry present
        led = requests.get(f"{API}/school/ledger", headers=_h(tok), timeout=10).json()
        salary_entries = [e for e in led if e.get("ref_type") == "salary"
                          and str(e.get("ref_id", "")).startswith(run_id)]
        assert len(salary_entries) >= 1
        assert salary_entries[0]["amount"] == 46000

        # Salary slip PDF
        r = requests.get(f"{API}/school/payroll/{run_id}/slip/{teacher_a_id}.pdf",
                         headers=_h(tok), timeout=15)
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("application/pdf")
        assert r.content[:5] == b"%PDF-"

        # Cross-tenant slip 404
        tokb, _ = _login(*SCHOOL_B)
        r = requests.get(f"{API}/school/payroll/{run_id}/slip/{teacher_a_id}.pdf",
                         headers=_h(tokb), timeout=10)
        assert r.status_code == 404

    def test_pay_double_400(self, admin_a, teacher_a_id):
        tok, _ = admin_a
        # find the latest run with paid entries for this teacher
        runs = requests.get(f"{API}/school/payroll", headers=_h(tok), timeout=10).json()
        target = None
        for r in runs:
            if any(e["employee_id"] == teacher_a_id and e.get("status") == "paid" for e in r.get("entries", [])):
                target = r; break
        if not target:
            pytest.skip("no paid entry found to double-pay")
        r = requests.post(f"{API}/school/payroll/{target['id']}/pay", headers=_hj(tok),
                          json={"employee_id": teacher_a_id, "method": "cash"}, timeout=10)
        assert r.status_code == 400


# =========================================================
# 6. Reports
# =========================================================
class TestReports:
    def test_summary_admin(self, admin_a):
        tok, _ = admin_a
        r = requests.get(f"{API}/school/reports/summary?date_from=2026-01-01&date_to=2026-12-31",
                         headers=_h(tok), timeout=15)
        assert r.status_code == 200
        d = r.json()
        for k in ["fee_income", "expenses_total", "net_balance", "outstanding",
                  "fee_by_method", "expenses_by_category", "defaulters_count"]:
            assert k in d, f"missing {k}"

    def test_summary_teacher_403(self, teacher_a):
        tok, _ = teacher_a
        r = requests.get(f"{API}/school/reports/summary?date_from=2026-01-01&date_to=2026-12-31",
                         headers=_h(tok), timeout=10)
        assert r.status_code == 403

    def test_students_csv(self, admin_a):
        tok, _ = admin_a
        r = requests.get(f"{API}/school/reports/students.csv", headers=_h(tok), timeout=15)
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("text/csv")
        assert "Student ID" in r.text.splitlines()[0]

    def test_fee_csv(self, admin_a):
        tok, _ = admin_a
        r = requests.get(f"{API}/school/reports/fee-collection.csv?date_from=2026-01-01&date_to=2026-12-31",
                         headers=_h(tok), timeout=15)
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("text/csv")


# =========================================================
# 7. Admissions
# =========================================================
@pytest.fixture(scope="module")
def school_a_id(admin_a):
    return admin_a[1]["school_id"]


class TestAdmissions:
    def test_public_schools(self):
        r = requests.get(f"{API}/public/schools", timeout=10)
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) >= 1

    def test_public_enquiry_no_auth(self, school_a_id):
        payload = {"school_id": school_a_id,
                   "student_name": "TEST_Enq_" + uuid.uuid4().hex[:6],
                   "father_name": "TEST_Father",
                   "phone": "03001234567",
                   "desired_class": "5"}
        r = requests.post(f"{API}/public/admission-enquiries", json=payload, timeout=10)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["enquiry_number"].startswith("ENQ-")
        assert "id" in d
        assert d["school_name"]

    def test_public_enquiry_invalid_school_404(self):
        r = requests.post(f"{API}/public/admission-enquiries",
                          json={"school_id": "no-such-id", "student_name": "X", "phone": "1"},
                          timeout=10)
        assert r.status_code == 404

    def test_list_teacher_403(self, teacher_a):
        tok, _ = teacher_a
        r = requests.get(f"{API}/school/admission-enquiries", headers=_h(tok), timeout=10)
        assert r.status_code == 403

    def test_list_admin_tenant_scoped(self, admin_a, admin_b, school_a_id):
        toka, _ = admin_a
        tokb, _ = admin_b
        # Create one in A
        r = requests.post(f"{API}/public/admission-enquiries",
                          json={"school_id": school_a_id, "student_name": "TEST_ScopedEnq",
                                "phone": "0300"}, timeout=10)
        eid_num = r.json()["enquiry_number"]

        la = requests.get(f"{API}/school/admission-enquiries", headers=_h(toka), timeout=10)
        lb = requests.get(f"{API}/school/admission-enquiries", headers=_h(tokb), timeout=10)
        assert la.status_code == 200 and lb.status_code == 200
        assert any(e.get("enquiry_number") == eid_num for e in la.json())
        assert not any(e.get("enquiry_number") == eid_num for e in lb.json())

    def test_convert_creates_student(self, admin_a, school_a_id):
        tok, _ = admin_a
        # get a class
        cls = requests.get(f"{API}/school/classes", headers=_h(tok), timeout=10).json()
        assert len(cls) >= 1
        class_id = cls[0]["id"]

        # Create enquiry
        r = requests.post(f"{API}/public/admission-enquiries",
                          json={"school_id": school_a_id,
                                "student_name": "TEST_ConvertMe_" + uuid.uuid4().hex[:4],
                                "father_name": "TEST_Dad", "phone": "0300"},
                          timeout=10)
        eid = r.json()["id"]

        r = requests.post(f"{API}/school/admission-enquiries/{eid}/convert",
                          headers=_hj(tok), json={"class_id": class_id, "roll_number": "99"}, timeout=15)
        assert r.status_code == 200, r.text
        stu = r.json()
        assert stu["student_id"].startswith("STU-")
        assert stu["name"].startswith("TEST_ConvertMe_")

        # Second convert should 400
        r2 = requests.post(f"{API}/school/admission-enquiries/{eid}/convert",
                           headers=_hj(tok), json={"class_id": class_id}, timeout=10)
        assert r2.status_code == 400

    def test_cross_tenant_convert_404(self, admin_b, school_a_id):
        tokb, _ = admin_b
        # Create enquiry against school A
        r = requests.post(f"{API}/public/admission-enquiries",
                          json={"school_id": school_a_id, "student_name": "TEST_XConvert",
                                "phone": "0300"}, timeout=10)
        eid = r.json()["id"]
        # School B classes
        cls = requests.get(f"{API}/school/classes", headers=_h(tokb), timeout=10).json()
        cid = cls[0]["id"] if cls else "x"
        r = requests.post(f"{API}/school/admission-enquiries/{eid}/convert",
                          headers=_hj(tokb), json={"class_id": cid}, timeout=10)
        assert r.status_code == 404


# =========================================================
# 8. Result Card PDF
# =========================================================
class TestResultCardPDF:
    def _find_exam_and_student(self, tok):
        exams = requests.get(f"{API}/school/exams", headers=_h(tok), timeout=10).json()
        students = requests.get(f"{API}/school/students", headers=_h(tok), timeout=10).json()
        return (exams[0]["id"] if exams else None,
                students[0]["id"] if students else None)

    def test_admin_pdf_ok(self, admin_a):
        tok, _ = admin_a
        eid, sid = self._find_exam_and_student(tok)
        if not eid or not sid:
            pytest.skip("no exam or student to card")
        r = requests.get(f"{API}/school/results/{eid}/students/{sid}/card.pdf",
                         headers=_h(tok), timeout=20)
        assert r.status_code == 200, r.text[:200]
        assert r.headers.get("content-type", "").startswith("application/pdf")
        assert r.content[:5] == b"%PDF-"

    def test_cross_tenant_pdf_404(self, admin_a, admin_b):
        toka, _ = admin_a
        tokb, _ = admin_b
        eid, sid = self._find_exam_and_student(toka)
        if not eid or not sid:
            pytest.skip("no data")
        r = requests.get(f"{API}/school/results/{eid}/students/{sid}/card.pdf",
                         headers=_h(tokb), timeout=15)
        assert r.status_code in (403, 404)
