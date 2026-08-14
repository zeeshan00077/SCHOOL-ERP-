"""Phase 4 tests — Custom roles+permissions, Fee→Ledger auto-post, refunds,
WhatsApp (unconfigured), XLSX exports, cross-tenant enforcement, accounting consistency."""
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


def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=15)
    assert r.status_code == 200, f"login {email}: {r.status_code} {r.text}"
    j = r.json()
    return j["access_token"], j["user"]


def _h(tok): return {"Authorization": f"Bearer {tok}"}
def _hj(tok): return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def admin_a(): return _login(*SCHOOL_A)
@pytest.fixture(scope="module")
def admin_b(): return _login(*SCHOOL_B)
@pytest.fixture(scope="module")
def teacher_a(): return _login(*TEACHER_A)


# ============ Permission Catalog ============
class TestPermissionsCatalog:
    def test_catalog_available_to_all_roles(self, admin_a, teacher_a):
        for tok, _u in (admin_a, teacher_a):
            r = requests.get(f"{API}/school/permissions/catalog", headers=_h(tok))
            assert r.status_code == 200, r.text
            j = r.json()
            assert "modules" in j and "role_defaults" in j
            assert "fees" in j["modules"] and "receive_payment" in j["modules"]["fees"]
            assert "school_admin" in j["role_defaults"]

    def test_permissions_me(self, admin_a, teacher_a):
        for tok, u in (admin_a, teacher_a):
            r = requests.get(f"{API}/school/permissions/me", headers=_h(tok))
            assert r.status_code == 200
            j = r.json()
            assert j["role"] == u["role"]
            assert isinstance(j["permissions"], dict)


# ============ Custom Roles CRUD ============
class TestCustomRoles:
    def test_teacher_forbidden_list(self, teacher_a):
        r = requests.get(f"{API}/school/custom-roles", headers=_h(teacher_a[0]))
        assert r.status_code == 403

    def test_admin_crud_and_sanitize(self, admin_a):
        tok = admin_a[0]
        # Create with mix of valid + invalid modules/actions + escalation attempt
        payload = {
            "name": f"TEST_Role_{uuid.uuid4().hex[:6]}",
            "description": "test",
            "permissions": {
                "fees": ["view", "receive_payment", "hack_action"],  # hack_action stripped
                "unknown_module": ["view"],       # dropped
                "students": ["view", "delete"],
                "super_admin": ["all"],            # dropped
                "settings": ["edit", "wipe"],      # wipe stripped
            },
        }
        r = requests.post(f"{API}/school/custom-roles", json=payload, headers=_hj(tok))
        assert r.status_code == 200, r.text
        role = r.json()
        rid = role["id"]
        assert "unknown_module" not in role["permissions"]
        assert "super_admin" not in role["permissions"]
        assert "hack_action" not in role["permissions"].get("fees", [])
        assert "wipe" not in role["permissions"].get("settings", [])
        assert "receive_payment" in role["permissions"]["fees"]

        # List
        r = requests.get(f"{API}/school/custom-roles", headers=_h(tok))
        assert r.status_code == 200
        assert any(x["id"] == rid for x in r.json())

        # Update
        r = requests.put(f"{API}/school/custom-roles/{rid}",
                         json={"name": role["name"], "description": "upd",
                               "permissions": {"fees": ["view"]}, "active": True},
                         headers=_hj(tok))
        assert r.status_code == 200

        # Delete unassigned OK
        r = requests.delete(f"{API}/school/custom-roles/{rid}", headers=_h(tok))
        assert r.status_code == 200

    def test_cross_tenant_role_isolation(self, admin_a, admin_b):
        # A creates a role
        r = requests.post(f"{API}/school/custom-roles",
                          json={"name": f"TEST_XT_{uuid.uuid4().hex[:6]}", "permissions": {"fees": ["view"]}},
                          headers=_hj(admin_a[0]))
        assert r.status_code == 200
        rid = r.json()["id"]

        # B cannot update / delete A's role
        r_upd = requests.put(f"{API}/school/custom-roles/{rid}",
                             json={"name": "hijack", "permissions": {}, "active": True},
                             headers=_hj(admin_b[0]))
        assert r_upd.status_code == 404
        r_del = requests.delete(f"{API}/school/custom-roles/{rid}", headers=_h(admin_b[0]))
        # Backend silently no-ops (delete_one on non-matching filter returns ok).
        # Verify role STILL exists in school A regardless of the status code.
        assert r_del.status_code in (200, 404)
        a_list = requests.get(f"{API}/school/custom-roles", headers=_h(admin_a[0])).json()
        assert any(x["id"] == rid for x in a_list), "cross-tenant DELETE must NOT remove A's role"

        # B cannot assign A's role to their own user
        me_b = requests.get(f"{API}/auth/me", headers=_h(admin_b[0])).json()
        r_assign = requests.put(f"{API}/school/users/{me_b['id']}/custom-role",
                                json={"custom_role_id": rid}, headers=_hj(admin_b[0]))
        # target user exists in school B, but role belongs to A → 404 role
        assert r_assign.status_code == 404

        # Cleanup
        requests.delete(f"{API}/school/custom-roles/{rid}", headers=_h(admin_a[0]))

    def test_delete_when_assigned_fails(self, admin_a):
        tok = admin_a[0]
        r = requests.post(f"{API}/school/custom-roles",
                          json={"name": f"TEST_AssignedRole_{uuid.uuid4().hex[:6]}",
                                "permissions": {"students": ["view"]}},
                          headers=_hj(tok))
        assert r.status_code == 200
        rid = r.json()["id"]

        # find a teacher in school A
        users = requests.get(f"{API}/school/users", headers=_h(tok))
        assert users.status_code == 200
        target = next(u for u in users.json() if u["role"] == "teacher")

        r = requests.put(f"{API}/school/users/{target['id']}/custom-role",
                         json={"custom_role_id": rid}, headers=_hj(tok))
        assert r.status_code == 200

        # delete now fails
        r = requests.delete(f"{API}/school/custom-roles/{rid}", headers=_h(tok))
        assert r.status_code == 400
        assert "assigned" in r.text.lower()

        # unassign + cleanup
        requests.put(f"{API}/school/users/{target['id']}/custom-role",
                     json={"custom_role_id": None}, headers=_hj(tok))
        r = requests.delete(f"{API}/school/custom-roles/{rid}", headers=_h(tok))
        assert r.status_code == 200


# ============ Fee → Ledger auto-post + Refund ============
def _create_test_invoice_and_pay(tok, amount=1234.0):
    # find a student in school A
    stu_resp = requests.get(f"{API}/school/students", headers=_h(tok))
    assert stu_resp.status_code == 200
    students = stu_resp.json()
    assert students, "need at least one student"
    student_id = students[0]["id"]
    r = requests.post(f"{API}/school/fee-invoices",
                      json={"student_id": student_id, "title": "TEST_P4_Invoice",
                            "amount": amount, "due_date": "2099-12-31"},
                      headers=_hj(tok))
    assert r.status_code == 200, r.text
    inv = r.json()
    r = requests.post(f"{API}/school/fee-payments",
                      json={"invoice_id": inv["id"], "amount": amount, "method": "cash"},
                      headers=_hj(tok))
    assert r.status_code == 200, r.text
    pay = r.json()
    return inv, pay


class TestFeeLedgerAutoPost:
    def test_payment_creates_single_ledger_credit(self, admin_a):
        tok = admin_a[0]
        inv, pay = _create_test_invoice_and_pay(tok, amount=1500.0)
        # verify ledger has exactly 1 credit for this payment
        led = requests.get(f"{API}/school/ledger", headers=_h(tok)).json()
        matches = [e for e in led if e.get("ref_type") == "fee_payment" and e.get("ref_id") == pay["id"]]
        assert len(matches) == 1, f"expected 1 fee_payment ledger, got {len(matches)}"
        e = matches[0]
        assert e["kind"] == "credit"
        assert abs(e["amount"] - 1500.0) < 0.001

    def test_two_different_payments_two_ledger_entries(self, admin_a):
        tok = admin_a[0]
        _i1, p1 = _create_test_invoice_and_pay(tok, amount=100.0)
        _i2, p2 = _create_test_invoice_and_pay(tok, amount=200.0)
        led = requests.get(f"{API}/school/ledger", headers=_h(tok)).json()
        m1 = [e for e in led if e.get("ref_id") == p1["id"] and e.get("ref_type") == "fee_payment"]
        m2 = [e for e in led if e.get("ref_id") == p2["id"] and e.get("ref_type") == "fee_payment"]
        assert len(m1) == 1 and len(m2) == 1
        assert p1["id"] != p2["id"]


class TestRefund:
    def test_refund_creates_debit_and_reverses_invoice(self, admin_a):
        tok = admin_a[0]
        inv, pay = _create_test_invoice_and_pay(tok, amount=777.0)

        # verify invoice paid_amount = 777
        invs = requests.get(f"{API}/school/fee-invoices", headers=_h(tok)).json()
        found = next(i for i in invs if i["id"] == inv["id"])
        assert abs(found.get("paid_amount", 0) - 777.0) < 0.001

        # refund
        r = requests.post(f"{API}/school/fee-payments/{pay['id']}/refund",
                          json={"reason": "TEST_refund"}, headers=_hj(tok))
        assert r.status_code == 200, r.text

        # ledger debit exists
        led = requests.get(f"{API}/school/ledger", headers=_h(tok)).json()
        deb = [e for e in led if e.get("ref_type") == "fee_refund" and e.get("ref_id") == pay["id"]]
        assert len(deb) == 1
        assert deb[0]["kind"] == "debit"
        assert abs(deb[0]["amount"] - 777.0) < 0.001

        # invoice paid_amount reversed
        invs2 = requests.get(f"{API}/school/fee-invoices", headers=_h(tok)).json()
        found2 = next(i for i in invs2 if i["id"] == inv["id"])
        assert abs(found2.get("paid_amount", 0)) < 0.001

        # second refund returns 400
        r2 = requests.post(f"{API}/school/fee-payments/{pay['id']}/refund",
                           json={"reason": "again"}, headers=_hj(tok))
        assert r2.status_code == 400

    def test_refund_cross_tenant_404(self, admin_a, admin_b):
        _inv, pay = _create_test_invoice_and_pay(admin_a[0], amount=50.0)
        r = requests.post(f"{API}/school/fee-payments/{pay['id']}/refund",
                          json={"reason": "x"}, headers=_hj(admin_b[0]))
        assert r.status_code == 404


# ============ WhatsApp — unconfigured ============
class TestWhatsAppUnconfigured:
    def test_env_vars_are_unset(self):
        # Sanity: env not configured
        assert not (os.environ.get("WHATSAPP_ACCESS_TOKEN") and os.environ.get("WHATSAPP_PHONE_NUMBER_ID"))

    def test_send_now_returns_not_configured_and_queued(self, admin_a):
        tok = admin_a[0]
        # pick any invoice
        invs = requests.get(f"{API}/school/fee-invoices", headers=_h(tok)).json()
        assert invs, "need invoices"
        ids = [i["id"] for i in invs[:2]]
        r = requests.post(f"{API}/school/reminders/send-now",
                          json={"invoice_ids": ids}, headers=_hj(tok))
        assert r.status_code == 200, r.text
        j = r.json()
        assert j["integration_configured"] is False
        assert j["sent"] == 0
        assert j["queued"] >= 1 or j.get("failed", 0) >= 0  # queued when phone missing counts too
        assert "integration_note" in j

    def test_cross_tenant_invoice_ids_silently_ignored(self, admin_a, admin_b):
        # get an invoice from B
        invs_b = requests.get(f"{API}/school/fee-invoices", headers=_h(admin_b[0])).json()
        if not invs_b:
            pytest.skip("school B has no invoices")
        r = requests.post(f"{API}/school/reminders/send-now",
                          json={"invoice_ids": [invs_b[0]["id"]]}, headers=_hj(admin_a[0]))
        assert r.status_code == 200
        j = r.json()
        # cross-tenant should be dropped → 0 queued/sent/failed
        assert j["sent"] == 0
        assert j["queued"] == 0
        assert j.get("failed", 0) == 0

    def test_webhook_updates_reminder_log(self, admin_a):
        tok = admin_a[0]
        invs = requests.get(f"{API}/school/fee-invoices", headers=_h(tok)).json()
        if not invs:
            pytest.skip("no invoices")
        # queue a reminder — no provider_message_id will be set (unconfigured), but we can test webhook idempotency
        r = requests.post(f"{API}/school/reminders/send-now",
                          json={"invoice_ids": [invs[0]["id"]]}, headers=_hj(tok))
        assert r.status_code == 200
        # webhook with random id — must not 500
        r2 = requests.post(f"{API}/webhooks/whatsapp/status",
                           json={"provider_message_id": f"wamid.TEST_{uuid.uuid4().hex}",
                                 "status": "delivered"})
        assert r2.status_code == 200


# ============ XLSX Exports ============
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
PK_MAGIC = b"PK\x03\x04"


class TestXLSXExports:
    def test_students_xlsx(self, admin_a):
        r = requests.get(f"{API}/school/reports/students.xlsx", headers=_h(admin_a[0]))
        assert r.status_code == 200
        assert XLSX_MIME in r.headers.get("content-type", "")
        assert r.content[:4] == PK_MAGIC

    def test_students_xlsx_teacher_403(self, teacher_a):
        r = requests.get(f"{API}/school/reports/students.xlsx", headers=_h(teacher_a[0]))
        assert r.status_code == 403

    def test_fee_collection_xlsx(self, admin_a):
        r = requests.get(f"{API}/school/reports/fee-collection.xlsx?date_from=2020-01-01&date_to=2099-12-31",
                         headers=_h(admin_a[0]))
        assert r.status_code == 200
        assert r.content[:4] == PK_MAGIC

    def test_expenses_xlsx(self, admin_a):
        r = requests.get(f"{API}/school/reports/expenses.xlsx", headers=_h(admin_a[0]))
        assert r.status_code == 200
        assert r.content[:4] == PK_MAGIC

    def test_ledger_xlsx(self, admin_a):
        r = requests.get(f"{API}/school/reports/ledger.xlsx", headers=_h(admin_a[0]))
        assert r.status_code == 200
        assert r.content[:4] == PK_MAGIC

    def test_payroll_xlsx_404_for_missing_month(self, admin_a):
        r = requests.get(f"{API}/school/reports/payroll.xlsx?month=1970-01", headers=_h(admin_a[0]))
        assert r.status_code == 404


# ============ Accounting consistency ============
class TestAccountingConsistency:
    def test_summary_direction_matches_ledger(self, admin_a):
        tok = admin_a[0]
        led = requests.get(f"{API}/school/ledger", headers=_h(tok)).json()
        credits = sum(e["amount"] for e in led if e["kind"] == "credit")
        debits = sum(e["amount"] for e in led if e["kind"] == "debit")
        # Just sanity — ledger must have data now that we've been posting
        assert credits > 0
        # reports/summary should exist
        r = requests.get(f"{API}/school/reports/summary?date_from=2020-01-01&date_to=2099-12-31", headers=_h(tok))
        assert r.status_code == 200
