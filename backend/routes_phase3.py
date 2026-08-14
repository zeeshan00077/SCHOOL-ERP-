"""Phase 3: system settings separation, expenses, payroll, accounts+ledger,
reports, admissions, parent-scoped dashboard, result card PDF."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import timedelta
import csv, io, base64, mimetypes
from pathlib import Path

from db import (get_db, get_current_user, require_role, require_school_active,
                new_id, now_utc, iso, audit)
from routes_extras import result_card as _card_data
from pdf_service import html_to_pdf_bytes, DEV_BRAND

router = APIRouter(prefix="/api", tags=["phase3"])
UPLOAD_ROOT = Path("/app/backend/uploads")


def _sid(u):
    if not u.get("school_id"):
        raise HTTPException(400, "No school_id")
    return u["school_id"]


# ============ System Settings (Super Admin only) ============
class SystemSettingsIn(BaseModel):
    developer_name: Optional[str] = None
    developer_contact: Optional[str] = None
    developer_email: Optional[str] = None
    default_trial_days: Optional[int] = None
    default_currency: Optional[str] = None
    platform_name: Optional[str] = None
    maintenance_mode: Optional[bool] = None
    footer_note: Optional[str] = None


DEFAULT_SYSTEM = {
    "developer_name": "Zeeshan Computers Sheikh Fazal",
    "developer_contact": "0343-0819382",
    "developer_email": None,
    "default_trial_days": 7,
    "default_currency": "PKR",
    "platform_name": "Skoolzoom",
    "maintenance_mode": False,
    "footer_note": None,
}


@router.get("/system-settings")
async def get_system_settings(user=Depends(require_role("super_admin"))):
    db = get_db()
    doc = await db.system_settings.find_one({"key": "singleton"}, {"_id": 0})
    if not doc:
        doc = {"key": "singleton", **DEFAULT_SYSTEM}
        await db.system_settings.insert_one(dict(doc))
        doc.pop("_id", None)
    return doc


@router.put("/system-settings")
async def put_system_settings(inp: SystemSettingsIn, user=Depends(require_role("super_admin"))):
    db = get_db()
    patch = {k: v for k, v in inp.model_dump().items() if v is not None}
    await db.system_settings.update_one({"key": "singleton"}, {"$set": patch, "$setOnInsert": {"key": "singleton"}}, upsert=True)
    await audit(db, actor=user, action="update_system_settings", module="system", after=patch)
    return {"ok": True}


@router.get("/public/system-branding")
async def public_branding():
    """Read-only branding surface used by the frontend for footers."""
    db = get_db()
    doc = await db.system_settings.find_one({"key": "singleton"}, {"_id": 0}) or {}
    return {
        "developer_name": doc.get("developer_name", DEFAULT_SYSTEM["developer_name"]),
        "developer_contact": doc.get("developer_contact", DEFAULT_SYSTEM["developer_contact"]),
        "platform_name": doc.get("platform_name", DEFAULT_SYSTEM["platform_name"]),
        "footer_note": doc.get("footer_note"),
    }


# ============ Expenses ============
DEFAULT_EXPENSE_CATEGORIES = ["Electricity", "Gas", "Water", "Internet", "Stationery",
                              "Maintenance", "Transport", "Fuel", "Cleaning", "Salaries",
                              "Rent", "Furniture", "Repairs", "Events", "Other"]


class ExpenseIn(BaseModel):
    date: str
    category: str
    description: str
    amount: float
    payment_method: str = "cash"  # cash|bank|jazzcash|easypaisa|other
    account_id: Optional[str] = None
    paid_to: Optional[str] = None
    reference: Optional[str] = None
    proof_url: Optional[str] = None
    notes: Optional[str] = None


class ExpenseDecisionIn(BaseModel):
    remarks: Optional[str] = None


def _ledger_add(db, school_id, kind, amount, account_id, description, ref_type, ref_id, user):
    return db.ledger.insert_one({
        "id": new_id(), "school_id": school_id, "kind": kind,  # debit|credit
        "amount": amount, "account_id": account_id, "description": description,
        "ref_type": ref_type, "ref_id": ref_id, "actor_id": user["id"],
        "created_at": iso(now_utc()),
    })


@router.get("/school/expense-categories")
async def expense_categories(user=Depends(require_school_active)):
    return DEFAULT_EXPENSE_CATEGORIES


@router.get("/school/expenses")
async def list_expenses(status: Optional[str] = None, date_from: Optional[str] = None,
                        date_to: Optional[str] = None, category: Optional[str] = None,
                        user=Depends(require_school_active)):
    if user["role"] in ("parent", "student", "teacher"):
        raise HTTPException(403, "Not allowed")
    db = get_db()
    q = {"school_id": _sid(user)}
    if status: q["status"] = status
    if category: q["category"] = category
    if date_from or date_to:
        r = {}
        if date_from: r["$gte"] = date_from
        if date_to: r["$lte"] = date_to
        q["date"] = r
    return await db.expenses.find(q, {"_id": 0}).sort("date", -1).to_list(5000)


@router.post("/school/expenses")
async def create_expense(inp: ExpenseIn, user=Depends(require_role("school_admin", "accountant"))):
    db = get_db()
    doc = {
        "id": new_id(), "school_id": _sid(user), **inp.model_dump(),
        "status": "pending", "created_by": user["id"], "created_by_name": user["name"],
        "created_at": iso(now_utc()),
    }
    await db.expenses.insert_one(doc)
    await audit(db, actor=user, action="create_expense", module="expenses", record_id=doc["id"])
    doc.pop("_id", None)
    return doc


@router.post("/school/expenses/{eid}/approve")
async def approve_expense(eid: str, inp: ExpenseDecisionIn, user=Depends(require_role("school_admin"))):
    db = get_db()
    e = await db.expenses.find_one({"id": eid, "school_id": _sid(user)})
    if not e:
        raise HTTPException(404, "Not found")
    if e["status"] != "pending":
        raise HTTPException(400, f"Expense is {e['status']}")
    await db.expenses.update_one({"id": eid}, {"$set": {
        "status": "approved", "approved_by": user["id"], "approved_at": iso(now_utc()),
        "remarks": inp.remarks,
    }})
    await _ledger_add(db, _sid(user), "debit", e["amount"], e.get("account_id"),
                      f"Expense: {e['category']} — {e['description']}", "expense", eid, user)
    await audit(db, actor=user, action="approve_expense", module="expenses", record_id=eid)
    return {"ok": True}


@router.post("/school/expenses/{eid}/reject")
async def reject_expense(eid: str, inp: ExpenseDecisionIn, user=Depends(require_role("school_admin"))):
    db = get_db()
    r = await db.expenses.update_one({"id": eid, "school_id": _sid(user), "status": "pending"},
        {"$set": {"status": "rejected", "approved_by": user["id"], "approved_at": iso(now_utc()), "remarks": inp.remarks}})
    if r.matched_count == 0:
        raise HTTPException(400, "Not pending or not found")
    await audit(db, actor=user, action="reject_expense", module="expenses", record_id=eid)
    return {"ok": True}


# ============ Accounts / Ledger ============
class AccountIn(BaseModel):
    name: str
    kind: str = "cash"  # cash|bank
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    opening_balance: float = 0.0


@router.get("/school/accounts")
async def list_accounts(user=Depends(require_school_active)):
    if user["role"] in ("parent", "student", "teacher"):
        raise HTTPException(403, "Not allowed")
    db = get_db()
    return await db.accounts.find({"school_id": _sid(user)}, {"_id": 0}).to_list(100)


@router.post("/school/accounts")
async def create_account(inp: AccountIn, user=Depends(require_role("school_admin", "accountant"))):
    db = get_db()
    doc = {"id": new_id(), "school_id": _sid(user), **inp.model_dump(),
           "created_at": iso(now_utc())}
    await db.accounts.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.get("/school/ledger")
async def ledger(date_from: Optional[str] = None, date_to: Optional[str] = None,
                 user=Depends(require_role("school_admin", "accountant"))):
    db = get_db()
    q = {"school_id": _sid(user)}
    if date_from or date_to:
        r = {}
        if date_from: r["$gte"] = date_from
        if date_to: r["$lte"] = date_to + "T23:59:59"
        q["created_at"] = r
    return await db.ledger.find(q, {"_id": 0}).sort("created_at", -1).to_list(5000)


# ============ Payroll / Salaries ============
class SalaryProfileIn(BaseModel):
    basic_salary: float = 0
    allowances: List[dict] = []  # [{name, amount}]
    deductions: List[dict] = []
    salary_type: str = "monthly"  # monthly|daily|hourly
    bank_details: Optional[str] = None


@router.put("/school/employees/{teacher_id}/salary")
async def set_salary(teacher_id: str, inp: SalaryProfileIn, user=Depends(require_role("school_admin"))):
    db = get_db()
    t = await db.teachers.find_one({"id": teacher_id, "school_id": _sid(user)})
    if not t:
        raise HTTPException(404, "Employee not found")
    patch = inp.model_dump()
    # keep legacy salary field in sync
    patch["salary"] = inp.basic_salary + sum(a.get("amount", 0) for a in inp.allowances)
    await db.teachers.update_one({"id": teacher_id}, {"$set": patch})
    await audit(db, actor=user, action="set_salary", module="payroll", record_id=teacher_id, after=patch)
    return {"ok": True}


class PayrollProcessIn(BaseModel):
    month: str  # YYYY-MM


@router.post("/school/payroll/process")
async def process_payroll(inp: PayrollProcessIn, user=Depends(require_role("school_admin"))):
    db = get_db()
    s_id = _sid(user)
    existing = await db.payroll_runs.find_one({"school_id": s_id, "month": inp.month})
    if existing and existing.get("status") == "processed":
        return {"ok": True, "run_id": existing["id"], "already": True}
    teachers = await db.teachers.find({"school_id": s_id, "status": "active"}, {"_id": 0}).to_list(1000)
    entries = []
    total_net = 0
    for t in teachers:
        allowances = t.get("allowances") or []
        deductions = t.get("deductions") or []
        basic = float(t.get("basic_salary", t.get("salary", 0)) or 0)
        allow_total = sum(float(a.get("amount", 0)) for a in allowances)
        deduct_total = sum(float(d.get("amount", 0)) for d in deductions)
        net = basic + allow_total - deduct_total
        entries.append({"employee_id": t["id"], "employee_name": t["name"],
                        "designation": t.get("subject") or t.get("department"),
                        "basic": basic, "allowances": allowances, "deductions": deductions,
                        "allow_total": allow_total, "deduct_total": deduct_total,
                        "net": net, "status": "unpaid"})
        total_net += net
    run_id = new_id()
    doc = {"id": run_id, "school_id": s_id, "month": inp.month,
           "entries": entries, "total_net": total_net,
           "status": "processed", "processed_by": user["id"], "processed_at": iso(now_utc()),
           "created_at": iso(now_utc())}
    if existing:
        await db.payroll_runs.replace_one({"id": existing["id"]}, doc)
        run_id = existing["id"]; doc["id"] = run_id
    else:
        await db.payroll_runs.insert_one(doc)
    await audit(db, actor=user, action="process_payroll", module="payroll", record_id=run_id, after={"month": inp.month, "count": len(entries), "total": total_net})
    return {"ok": True, "run_id": run_id, "count": len(entries), "total_net": total_net}


class PayEmployeeIn(BaseModel):
    employee_id: str
    method: str = "cash"
    account_id: Optional[str] = None
    reference: Optional[str] = None
    paid_on: Optional[str] = None


@router.get("/school/payroll")
async def list_payroll(month: Optional[str] = None, user=Depends(require_role("school_admin", "accountant"))):
    db = get_db()
    q = {"school_id": _sid(user)}
    if month: q["month"] = month
    return await db.payroll_runs.find(q, {"_id": 0}).sort("month", -1).to_list(200)


@router.post("/school/payroll/{run_id}/pay")
async def pay_employee(run_id: str, inp: PayEmployeeIn, user=Depends(require_role("school_admin", "accountant"))):
    db = get_db()
    run = await db.payroll_runs.find_one({"id": run_id, "school_id": _sid(user)})
    if not run:
        raise HTTPException(404, "Run not found")
    updated = False
    for e in run["entries"]:
        if e["employee_id"] == inp.employee_id and e["status"] != "paid":
            e["status"] = "paid"
            e["paid_on"] = inp.paid_on or now_utc().date().isoformat()
            e["method"] = inp.method
            e["reference"] = inp.reference
            e["paid_by"] = user["id"]
            updated = True
            # ledger
            await _ledger_add(db, _sid(user), "debit", e["net"], inp.account_id,
                              f"Salary: {e['employee_name']} — {run['month']}",
                              "salary", f"{run_id}:{inp.employee_id}", user)
            break
    if not updated:
        raise HTTPException(400, "Not found or already paid")
    await db.payroll_runs.update_one({"id": run_id}, {"$set": {"entries": run["entries"]}})
    await audit(db, actor=user, action="pay_salary", module="payroll",
                record_id=f"{run_id}:{inp.employee_id}")
    return {"ok": True}


@router.get("/school/payroll/{run_id}/slip/{employee_id}.pdf")
async def salary_slip_pdf(run_id: str, employee_id: str, user=Depends(require_role("school_admin", "accountant"))):
    db = get_db()
    run = await db.payroll_runs.find_one({"id": run_id, "school_id": _sid(user)}, {"_id": 0})
    if not run:
        raise HTTPException(404, "Not found")
    entry = next((e for e in run["entries"] if e["employee_id"] == employee_id), None)
    if not entry:
        raise HTTPException(404, "Employee not in run")
    school = await db.schools.find_one({"id": _sid(user)}, {"_id": 0})
    rows_a = "".join(f"<tr><td>{a.get('name')}</td><td align='right'>{float(a.get('amount',0)):,.0f}</td></tr>" for a in entry.get("allowances", []))
    rows_d = "".join(f"<tr><td>{d.get('name')}</td><td align='right'>{float(d.get('amount',0)):,.0f}</td></tr>" for d in entry.get("deductions", []))
    html = f"""
    <html><head><style>
      @page {{ size:A4; margin:14mm; }}
      body {{ font-family:Helvetica,Arial,sans-serif; font-size:10pt; color:#111; }}
      h2 {{ margin:0; }} .hdr {{ border-bottom:2px solid #065F46; padding-bottom:6px; margin-bottom:10px; }}
      table {{ width:100%; border-collapse:collapse; margin-top:6px; }}
      td,th {{ border:1px solid #999; padding:4px 6px; }} th {{ background:#eef; }}
      .tot {{ background:#f5f5f5; font-weight:bold; }}
      .sign {{ margin-top:36px; display:flex; justify-content:space-between; font-size:9pt; }}
      .brand {{ text-align:center; color:#666; font-size:8pt; margin-top:20px; }}
    </style></head><body>
      <div class="hdr">
        <h2>{school.get('name')}</h2>
        <div style="font-size:9pt">{school.get('address') or ''}</div>
        <div style="font-size:9pt">{school.get('phone') or ''} · {school.get('email') or ''}</div>
        <div style="font-size:11pt; margin-top:4px"><b>SALARY SLIP · {run['month']}</b></div>
      </div>
      <table>
        <tr><td>Employee</td><td><b>{entry['employee_name']}</b></td><td>Designation</td><td>{entry.get('designation') or '—'}</td></tr>
        <tr><td>Employee ID</td><td>{entry['employee_id']}</td><td>Month</td><td>{run['month']}</td></tr>
      </table>
      <table>
        <tr><th colspan="2">Earnings</th></tr>
        <tr><td>Basic Salary</td><td align="right">{entry['basic']:,.0f}</td></tr>
        {rows_a}
        <tr class="tot"><td>Gross</td><td align="right">{entry['basic']+entry['allow_total']:,.0f}</td></tr>
      </table>
      <table>
        <tr><th colspan="2">Deductions</th></tr>
        {rows_d if rows_d else '<tr><td colspan=2><i>None</i></td></tr>'}
        <tr class="tot"><td>Total Deductions</td><td align="right">{entry['deduct_total']:,.0f}</td></tr>
      </table>
      <table>
        <tr class="tot"><td>Net Salary Payable</td><td align="right">PKR {entry['net']:,.0f}</td></tr>
        <tr><td>Payment Status</td><td>{entry.get('status','unpaid')}</td></tr>
        <tr><td>Paid On</td><td>{entry.get('paid_on') or '—'}</td></tr>
      </table>
      <div class="sign"><div>Accountant<br/>________________</div><div>Principal<br/>{school.get('principal') or '________________'}</div></div>
      <div class="brand">{DEV_BRAND}</div>
    </body></html>
    """
    pdf = html_to_pdf_bytes(html)
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="salary-{run["month"]}-{entry["employee_id"]}.pdf"'})


# ============ Result Card PDF ============
def _photo_uri(school_id, photo_url):
    if not photo_url:
        return None
    fname = photo_url.rstrip("/").split("/")[-1]
    if "/" in fname or ".." in fname:
        return None
    p = UPLOAD_ROOT / school_id / fname
    if not p.exists():
        return None
    mime, _ = mimetypes.guess_type(str(p))
    return f"data:{mime or 'image/jpeg'};base64,{base64.b64encode(p.read_bytes()).decode()}"


@router.get("/school/results/{exam_id}/students/{student_id}/card.pdf")
async def result_card_pdf(exam_id: str, student_id: str, user=Depends(require_school_active)):
    d = await _card_data(exam_id, student_id, user)
    school = d["school"]; stu = d["student"]; ex = d["exam"]; t = d["totals"]
    photo_src = _photo_uri(user["school_id"], stu.get("photo_url"))
    subj_rows = "".join(
        f"<tr><td>{s.get('name','—')}</td><td align='right'>{s.get('total')}</td>"
        f"<td align='right'>{s.get('marks')}</td>"
        f"<td align='right'>{(s['marks']/s['total']*100):.1f}%</td>"
        f"<td align='right'>{'Pass' if s.get('passed') else 'Fail'}</td></tr>"
        for s in d["subjects"]
    )
    att = d.get("attendance", {})
    html = f"""
    <html><head><style>
      @page {{ size:A4; margin:12mm; }}
      body {{ font-family:Helvetica,Arial,sans-serif; font-size:10pt; color:#111; }}
      .frame {{ border:2px solid #065F46; padding:10px; }}
      .hdr {{ border-bottom:2px solid #065F46; padding-bottom:6px; margin-bottom:8px; }}
      table {{ width:100%; border-collapse:collapse; }}
      td.info, th.info {{ padding:2px 4px; }}
      table.marks {{ margin-top:6px; }}
      table.marks th, table.marks td {{ border:1px solid #999; padding:4px 6px; }}
      table.marks th {{ background:#e6f4ee; }}
      .tot {{ background:#e6f4ee; font-weight:bold; }}
      .att {{ margin-top:6px; }}
      .att td {{ border:1px solid #ccc; padding:4px; text-align:center; }}
      .sign {{ margin-top:26px; display:flex; justify-content:space-between; font-size:9pt; }}
      .brand {{ text-align:center; color:#777; font-size:8pt; margin-top:8px; }}
    </style></head><body><div class="frame">
      <div class="hdr">
        <table><tr>
          <td class="info"><b style="font-size:14pt">{school.get('name')}</b><br/>
            <span style="font-size:8pt">{school.get('address') or ''}</span><br/>
            <span style="font-size:8pt">{school.get('phone') or ''} · {school.get('email') or ''}</span></td>
          <td class="info" align="right"><b style="font-size:11pt">RESULT CARD</b><br/>
            <span style="font-size:9pt">{ex['name']}</span><br/>
            <span style="font-size:8pt">Session {school.get('academic_session') or '—'}</span></td>
        </tr></table>
      </div>
      <table><tr>
        <td class="info" style="width:70%">
          <table style="font-size:9.5pt">
            <tr><td>Name:</td><td><b>{stu['name']}</b></td><td>Adm #:</td><td>{stu.get('admission_number','—')}</td></tr>
            <tr><td>Student ID:</td><td>{stu.get('student_id','—')}</td><td>Roll #:</td><td>{stu.get('roll_number','—')}</td></tr>
            <tr><td>Father:</td><td>{stu.get('father_name','—')}</td><td>Class:</td><td>{stu.get('class_name','')} {stu.get('section_name','')}</td></tr>
            <tr><td>Exam dates:</td><td>{ex.get('start_date')} – {ex.get('end_date')}</td><td>Position:</td><td><b>{t.get('position') or '—'}</b></td></tr>
          </table>
        </td>
        <td class="info" align="right" style="width:30%">
          {('<img src="'+photo_src+'" width="90" height="112"/>') if photo_src else '<div style="border:1px dashed #999;width:82px;height:100px;text-align:center;padding-top:40px;color:#999;font-size:8pt">Photo</div>'}
        </td>
      </tr></table>
      <table class="marks">
        <tr><th>Subject</th><th align="right">Total</th><th align="right">Obtained</th><th align="right">%</th><th align="right">Result</th></tr>
        {subj_rows if subj_rows else '<tr><td colspan=5 align="center"><i>No marks entered</i></td></tr>'}
        <tr class="tot"><td>Total</td><td align="right">{t.get('total')}</td><td align="right">{t.get('obtained')}</td><td align="right">{t.get('percentage')}%</td><td align="right">{'Passed · Grade '+t.get('grade','') if t.get('passed') else 'Failed · Grade '+t.get('grade','')}</td></tr>
      </table>
      <table class="att"><tr>
        <td>Present<br/><b>{att.get('present',0)}</b></td>
        <td>Absent<br/><b>{att.get('absent',0)}</b></td>
        <td>Late<br/><b>{att.get('late',0)}</b></td>
        <td>Leave<br/><b>{att.get('leave',0)}</b></td>
      </tr></table>
      <div class="sign"><div>Class Teacher<br/>_______________</div><div>Principal<br/>{school.get('principal') or '_______________'}</div></div>
      <div class="brand">{DEV_BRAND}</div>
    </div></body></html>
    """
    pdf = html_to_pdf_bytes(html)
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="result-{stu.get("student_id") or stu.get("id")}.pdf"'})


# ============ Reports ============
@router.get("/school/reports/summary")
async def reports_summary(date_from: str, date_to: str, user=Depends(require_role("school_admin", "accountant"))):
    db = get_db()
    s_id = _sid(user)
    payments = await db.fee_payments.find({"school_id": s_id, "paid_on": {"$gte": date_from, "$lte": date_to}}, {"_id": 0}).to_list(20000)
    fee_income = sum(p["amount"] for p in payments)
    by_method = {}
    for p in payments:
        by_method[p.get("method","cash")] = by_method.get(p.get("method","cash"), 0) + p["amount"]
    expenses = await db.expenses.find({"school_id": s_id, "date": {"$gte": date_from, "$lte": date_to}, "status": "approved"}, {"_id": 0}).to_list(20000)
    exp_total = sum(e["amount"] for e in expenses)
    exp_by_cat = {}
    for e in expenses:
        exp_by_cat[e["category"]] = exp_by_cat.get(e["category"], 0) + e["amount"]
    invoices = await db.fee_invoices.find({"school_id": s_id}, {"_id": 0}).to_list(20000)
    outstanding = sum((i["amount"] - i.get("paid_amount",0)) for i in invoices if i.get("status") != "paid")
    defaulters = [i for i in invoices if i.get("status") in ("unpaid","partial") and i.get("due_date","") < now_utc().date().isoformat()]
    return {
        "date_from": date_from, "date_to": date_to,
        "fee_income": fee_income, "fee_by_method": by_method, "fee_payments_count": len(payments),
        "expenses_total": exp_total, "expenses_by_category": exp_by_cat, "expenses_count": len(expenses),
        "net_balance": fee_income - exp_total,
        "outstanding": outstanding, "defaulters_count": len(defaulters),
    }


@router.get("/school/reports/students.csv")
async def students_csv(class_id: Optional[str] = None,
                       user=Depends(require_role("school_admin", "accountant"))):
    db = get_db()
    q = {"school_id": _sid(user)}
    if class_id: q["class_id"] = class_id
    students = await db.students.find(q, {"_id": 0}).sort("name", 1).to_list(20000)
    classes = {c["id"]: c["name"] for c in await db.classes.find({"school_id": _sid(user)}, {"_id": 0}).to_list(500)}
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Student ID", "Admission #", "Name", "Father", "Class", "Roll", "Gender", "DOB", "Phone", "Status"])
    for s in students:
        w.writerow([s.get("student_id",""), s.get("admission_number",""), s["name"],
                    s.get("father_name",""), classes.get(s.get("class_id"), ""),
                    s.get("roll_number",""), s.get("gender",""), s.get("dob",""),
                    s.get("phone",""), s.get("status","active")])
    return Response(content=buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="students.csv"'})


@router.get("/school/reports/fee-collection.csv")
async def fee_csv(date_from: str, date_to: str, user=Depends(require_role("school_admin", "accountant"))):
    db = get_db()
    payments = await db.fee_payments.find({"school_id": _sid(user), "paid_on": {"$gte": date_from, "$lte": date_to}}, {"_id": 0}).sort("paid_on", -1).to_list(20000)
    students = {s["id"]: s for s in await db.students.find({"school_id": _sid(user)}, {"_id": 0}).to_list(20000)}
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Receipt #", "Date", "Student", "Student ID", "Amount", "Method", "Reference"])
    for p in payments:
        st = students.get(p.get("student_id"), {})
        w.writerow([p.get("receipt_no",""), p.get("paid_on",""), st.get("name",""), st.get("student_id",""),
                    p["amount"], p.get("method",""), p.get("reference","")])
    return Response(content=buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="fee-collection.csv"'})


# ============ Admissions ============
class AdmissionEnquiryIn(BaseModel):
    school_id: str
    student_name: str
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    phone: str
    email: Optional[str] = None
    desired_class: Optional[str] = None
    previous_school: Optional[str] = None
    message: Optional[str] = None
    photo_url: Optional[str] = None


@router.post("/public/admission-enquiries")
async def submit_enquiry(inp: AdmissionEnquiryIn):
    db = get_db()
    school = await db.schools.find_one({"id": inp.school_id}, {"_id": 0})
    if not school:
        raise HTTPException(404, "School not found")
    from pymongo import ReturnDocument
    seq_doc = await db.counters.find_one_and_update(
        {"key": f"enq:{inp.school_id}"},
        {"$inc": {"seq": 1}, "$setOnInsert": {"school_id": inp.school_id}},
        upsert=True, return_document=ReturnDocument.AFTER,
    )
    seq = seq_doc.get("seq", 1) if seq_doc else 1
    enq_no = f"ENQ-{now_utc().year}-{seq:04d}"
    doc = {"id": new_id(), "school_id": inp.school_id, "enquiry_number": enq_no,
           **inp.model_dump(), "status": "new", "created_at": iso(now_utc())}
    await db.admission_enquiries.insert_one(doc)
    doc.pop("_id", None)
    return {"enquiry_number": enq_no, "id": doc["id"], "school_name": school.get("name")}


@router.get("/public/schools")
async def public_schools_list():
    db = get_db()
    schools = await db.schools.find({"status": "active"}, {"_id": 0, "id": 1, "name": 1, "city": 1}).to_list(500)
    return schools


@router.get("/school/admission-enquiries")
async def list_enquiries(status: Optional[str] = None,
                         user=Depends(require_role("school_admin", "receptionist"))):
    db = get_db()
    q = {"school_id": _sid(user)}
    if status: q["status"] = status
    return await db.admission_enquiries.find(q, {"_id": 0}).sort("created_at", -1).to_list(1000)


class EnquiryUpdateIn(BaseModel):
    status: Optional[str] = None  # new|contacted|follow_up|approved|rejected|converted
    notes: Optional[str] = None


@router.put("/school/admission-enquiries/{eid}")
async def update_enquiry(eid: str, inp: EnquiryUpdateIn, user=Depends(require_role("school_admin", "receptionist"))):
    db = get_db()
    patch = {k: v for k, v in inp.model_dump().items() if v is not None}
    r = await db.admission_enquiries.update_one({"id": eid, "school_id": _sid(user)}, {"$set": patch})
    if r.matched_count == 0:
        raise HTTPException(404, "Not found")
    await audit(db, actor=user, action="update_enquiry", module="admissions", record_id=eid, after=patch)
    return {"ok": True}


class ConvertEnquiryIn(BaseModel):
    class_id: str
    section_id: Optional[str] = None
    roll_number: Optional[str] = None


@router.post("/school/admission-enquiries/{eid}/convert")
async def convert_enquiry(eid: str, inp: ConvertEnquiryIn, user=Depends(require_role("school_admin", "receptionist"))):
    db = get_db()
    e = await db.admission_enquiries.find_one({"id": eid, "school_id": _sid(user)})
    if not e:
        raise HTTPException(404, "Not found")
    if e.get("status") == "converted":
        raise HTTPException(400, "Already converted")
    cls = await db.classes.find_one({"id": inp.class_id, "school_id": _sid(user)})
    if not cls:
        raise HTTPException(404, "Class not found")
    from routes_phase2b import next_student_id
    student_uid = await next_student_id(db, _sid(user))
    stu = {
        "id": new_id(), "school_id": _sid(user), "name": e["student_name"],
        "father_name": e.get("father_name"), "mother_name": e.get("mother_name"),
        "phone": e.get("phone"), "photo_url": e.get("photo_url"),
        "class_id": inp.class_id, "section_id": inp.section_id,
        "roll_number": inp.roll_number, "student_id": student_uid,
        "admission_number": f"ADM-{int(now_utc().timestamp())}",
        "previous_school": e.get("previous_school"),
        "status": "active", "created_at": iso(now_utc()),
    }
    await db.students.insert_one(stu)
    await db.admission_enquiries.update_one({"id": eid}, {"$set": {
        "status": "converted", "converted_student_id": stu["id"], "converted_at": iso(now_utc())}})
    await audit(db, actor=user, action="convert_enquiry", module="admissions", record_id=eid,
                after={"student_id": stu["id"], "student_uid": student_uid})
    stu.pop("_id", None)
    return stu
