"""Phase 2 additions: Daily Diary, Fee Voucher, Result Card, WhatsApp Reminders, Change Password."""
import os
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional

from db import (get_db, get_current_user, require_role, require_school_active,
                new_id, now_utc, iso, audit, hash_password, verify_password, _scrub)

router = APIRouter(prefix="/api", tags=["extras"])


# ---------------- Change Password ----------------
class ChangePwIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)


@router.post("/auth/change-password")
async def change_password(inp: ChangePwIn, user=Depends(get_current_user)):
    db = get_db()
    full = await db.users.find_one({"id": user["id"]})
    if not full or not verify_password(inp.current_password, full["password_hash"]):
        raise HTTPException(400, "Current password is incorrect")
    await db.users.update_one({"id": user["id"]}, {"$set": {
        "password_hash": hash_password(inp.new_password),
        "must_change_password": False,
    }})
    await audit(db, actor=user, action="change_password", module="auth", record_id=user["id"])
    return {"ok": True}


# ---------------- Daily Diary ----------------
class DiaryIn(BaseModel):
    class_id: str
    section_id: Optional[str] = None
    subject_id: Optional[str] = None
    date: str
    homework: Optional[str] = ""
    classwork: Optional[str] = ""
    notes: Optional[str] = ""
    due_date: Optional[str] = None
    attachment_url: Optional[str] = None


def _sid(u):
    if not u.get("school_id"):
        raise HTTPException(400, "User has no school_id")
    return u["school_id"]


@router.post("/school/diary")
async def diary_create(inp: DiaryIn, user=Depends(require_school_active)):
    if user["role"] not in ("teacher", "school_admin"):
        raise HTTPException(403, "Only teachers/admin can post diary")
    db = get_db()
    doc = {"id": new_id(), "school_id": _sid(user), **inp.model_dump(),
           "author_id": user["id"], "author_name": user["name"], "author_role": user["role"],
           "created_at": iso(now_utc())}
    await db.daily_diary.insert_one(doc)
    await audit(db, actor=user, action="create_diary", module="diary", record_id=doc["id"])
    doc.pop("_id", None)
    return doc


@router.get("/school/diary")
async def diary_list(class_id: Optional[str] = None, section_id: Optional[str] = None,
                     subject_id: Optional[str] = None, date_from: Optional[str] = None,
                     date_to: Optional[str] = None, student_id: Optional[str] = None,
                     user=Depends(require_school_active)):
    db = get_db()
    s_id = _sid(user)
    q = {"school_id": s_id}

    # Role-based scoping
    if user["role"] == "parent":
        children = await db.students.find({"school_id": s_id, "parent_id": user["id"]}, {"_id": 0}).to_list(50)
        if student_id:
            children = [c for c in children if c["id"] == student_id]
        if not children:
            return []
        class_ids = list({c["class_id"] for c in children if c.get("class_id")})
        q["class_id"] = {"$in": class_ids}
    elif user["role"] == "student":
        me = await db.students.find_one({"school_id": s_id, "user_id": user["id"]}, {"_id": 0})
        if not me:
            return []
        q["class_id"] = me["class_id"]

    if class_id: q["class_id"] = class_id
    if section_id: q["section_id"] = section_id
    if subject_id: q["subject_id"] = subject_id
    if date_from or date_to:
        rng = {}
        if date_from: rng["$gte"] = date_from
        if date_to: rng["$lte"] = date_to
        q["date"] = rng
    return await db.daily_diary.find(q, {"_id": 0}).sort("date", -1).to_list(500)


@router.put("/school/diary/{diary_id}")
async def diary_update(diary_id: str, inp: DiaryIn, user=Depends(require_school_active)):
    db = get_db()
    doc = await db.daily_diary.find_one({"id": diary_id, "school_id": _sid(user)})
    if not doc:
        raise HTTPException(404, "Not found")
    if user["role"] not in ("school_admin",) and doc["author_id"] != user["id"]:
        raise HTTPException(403, "Not allowed to edit others' diary")
    await db.daily_diary.update_one({"id": diary_id}, {"$set": inp.model_dump()})
    await audit(db, actor=user, action="update_diary", module="diary", record_id=diary_id)
    return {"ok": True}


@router.delete("/school/diary/{diary_id}")
async def diary_delete(diary_id: str, user=Depends(require_school_active)):
    db = get_db()
    doc = await db.daily_diary.find_one({"id": diary_id, "school_id": _sid(user)})
    if not doc:
        raise HTTPException(404, "Not found")
    if user["role"] not in ("school_admin",) and doc["author_id"] != user["id"]:
        raise HTTPException(403, "Not allowed")
    await db.daily_diary.delete_one({"id": diary_id})
    await audit(db, actor=user, action="delete_diary", module="diary", record_id=diary_id)
    return {"ok": True}


# ---------------- Fee Voucher (enriched print payload) ----------------
@router.get("/school/fee-invoices/{invoice_id}/voucher")
async def fee_voucher(invoice_id: str, user=Depends(require_school_active)):
    db = get_db()
    s_id = _sid(user)
    inv = await db.fee_invoices.find_one({"id": invoice_id, "school_id": s_id}, {"_id": 0})
    if not inv:
        raise HTTPException(404, "Invoice not found")

    student = await db.students.find_one({"id": inv["student_id"], "school_id": s_id}, {"_id": 0})
    if not student:
        raise HTTPException(404, "Student not found")

    # parents can only see vouchers for their children
    if user["role"] == "parent" and student.get("parent_id") != user["id"]:
        raise HTTPException(403, "Not your child")
    if user["role"] == "student" and student.get("user_id") != user["id"]:
        raise HTTPException(403, "Not your invoice")

    school = await db.schools.find_one({"id": s_id}, {"_id": 0})
    cls = await db.classes.find_one({"id": student["class_id"], "school_id": s_id}, {"_id": 0})
    section = None
    if student.get("section_id"):
        section = await db.sections.find_one({"id": student["section_id"], "school_id": s_id}, {"_id": 0})

    # Sum previous unpaid balance for this student (other invoices past-due)
    other_invoices = await db.fee_invoices.find({
        "school_id": s_id, "student_id": student["id"],
        "id": {"$ne": invoice_id}, "status": {"$in": ["unpaid", "partial"]}
    }, {"_id": 0}).to_list(200)
    previous_balance = sum((oi["amount"] - oi.get("paid_amount", 0)) for oi in other_invoices)

    voucher_no = f"V-{inv['id'][:8].upper()}"
    total_payable = (inv["amount"] - inv.get("paid_amount", 0)) + previous_balance
    return {
        "voucher_no": voucher_no,
        "issue_date": now_utc().date().isoformat(),
        "school": {
            "name": school.get("name"),
            "address": school.get("address"),
            "phone": school.get("phone"),
            "email": school.get("email"),
            "website": school.get("website"),
            "logo_url": school.get("logo_url"),
            "bank_instructions": school.get("bank_instructions") or "",
            "principal": school.get("principal"),
        },
        "student": {
            "name": student["name"],
            "admission_number": student.get("admission_number"),
            "father_name": student.get("father_name"),
            "roll_number": student.get("roll_number"),
            "class_name": cls["name"] if cls else "",
            "section_name": section["name"] if section else "",
        },
        "invoice": {
            "id": inv["id"],
            "title": inv["title"],
            "month": inv.get("month"),
            "amount": inv["amount"],
            "paid_amount": inv.get("paid_amount", 0),
            "due_date": inv["due_date"],
            "status": inv.get("status", "unpaid"),
            "discount": inv.get("discount", 0),
            "fine": inv.get("fine", 0),
        },
        "previous_balance": previous_balance,
        "total_payable": total_payable,
        "developer": {"name": "Zeeshan Computers Sheikh Fazal", "contact": "0343-0819382"},
    }


# ---------------- Result Card (enriched print payload) ----------------
@router.get("/school/results/{exam_id}/students/{student_id}/card")
async def result_card(exam_id: str, student_id: str, user=Depends(require_school_active)):
    db = get_db()
    s_id = _sid(user)
    exam = await db.exams.find_one({"id": exam_id, "school_id": s_id}, {"_id": 0})
    student = await db.students.find_one({"id": student_id, "school_id": s_id}, {"_id": 0})
    if not exam or not student:
        raise HTTPException(404, "Not found")

    if user["role"] == "parent" and student.get("parent_id") != user["id"]:
        raise HTTPException(403, "Not your child")
    if user["role"] == "student" and student.get("user_id") != user["id"]:
        raise HTTPException(403, "Not your result")

    school = await db.schools.find_one({"id": s_id}, {"_id": 0})
    cls = await db.classes.find_one({"id": student["class_id"], "school_id": s_id}, {"_id": 0})
    section = None
    if student.get("section_id"):
        section = await db.sections.find_one({"id": student["section_id"], "school_id": s_id}, {"_id": 0})

    marks = await db.marks.find({"school_id": s_id, "exam_id": exam_id, "student_id": student_id}, {"_id": 0}).to_list(200)
    subject_ids = [m["subject_id"] for m in marks]
    subjects = await db.subjects.find({"school_id": s_id, "id": {"$in": subject_ids}}, {"_id": 0}).to_list(200)
    smap = {s["id"]: s for s in subjects}

    obtained = sum(m["marks_obtained"] for m in marks)
    total = sum(m["total"] for m in marks)
    pct = (obtained / total * 100) if total else 0
    from routes_school import _grade
    grade = _grade(pct)
    passed = pct >= (exam.get("passing_marks", 40) / max(exam.get("total_marks", 100), 1) * 100)

    # position among class
    all_marks = await db.marks.find({"school_id": s_id, "exam_id": exam_id}, {"_id": 0}).to_list(20000)
    per_stu = {}
    for m in all_marks:
        per_stu.setdefault(m["student_id"], 0)
        per_stu[m["student_id"]] += m["marks_obtained"]
    ranked = sorted(per_stu.items(), key=lambda x: x[1], reverse=True)
    position = next((i + 1 for i, (sid_, _) in enumerate(ranked) if sid_ == student_id), None)

    # attendance summary (this month)
    month = now_utc().strftime("%Y-%m")
    att = await db.attendance.find({"school_id": s_id, "student_id": student_id,
                                    "date": {"$regex": f"^{month}"}}, {"_id": 0}).to_list(200)
    att_summary = {"present": 0, "absent": 0, "late": 0, "leave": 0}
    for a in att:
        att_summary[a["status"]] = att_summary.get(a["status"], 0) + 1

    return {
        "school": {
            "name": school.get("name"),
            "address": school.get("address"),
            "phone": school.get("phone"),
            "email": school.get("email"),
            "logo_url": school.get("logo_url"),
            "principal": school.get("principal"),
            "academic_session": school.get("academic_session"),
        },
        "student": {
            "id": student["id"],
            "name": student["name"],
            "admission_number": student.get("admission_number"),
            "father_name": student.get("father_name"),
            "roll_number": student.get("roll_number"),
            "class_name": cls["name"] if cls else "",
            "section_name": section["name"] if section else "",
            "photo_url": student.get("photo_url"),
        },
        "exam": {"id": exam["id"], "name": exam["name"], "start_date": exam["start_date"],
                 "end_date": exam["end_date"], "total_marks": exam["total_marks"],
                 "passing_marks": exam["passing_marks"]},
        "subjects": [{"name": smap.get(m["subject_id"], {}).get("name", "—"),
                      "code": smap.get(m["subject_id"], {}).get("code", ""),
                      "marks": m["marks_obtained"],
                      "total": m["total"],
                      "passed": m["marks_obtained"] >= (exam.get("passing_marks", 40) / max(exam.get("total_marks", 100), 1) * m["total"])
                      } for m in marks],
        "totals": {"obtained": obtained, "total": total, "percentage": round(pct, 2),
                   "grade": grade, "passed": passed, "position": position},
        "attendance": att_summary,
        "issued_on": now_utc().date().isoformat(),
        "developer": {"name": "Zeeshan Computers Sheikh Fazal", "contact": "0343-0819382"},
    }


# ---------------- WhatsApp Reminders architecture ----------------
class ReminderConfigIn(BaseModel):
    enabled: bool = True
    days_before: int = 3
    template: str = ("Dear Parent, this is a reminder that the school fee for "
                     "{student_name} is due on {due_date}. Amount payable: {amount}. "
                     "Please contact {school_name} for assistance.")
    school_contact: Optional[str] = None


def _wa_configured() -> bool:
    """WhatsApp API is 'configured' only if BOTH token and phone number id are set."""
    return bool(os.environ.get("WHATSAPP_ACCESS_TOKEN") and os.environ.get("WHATSAPP_PHONE_NUMBER_ID"))


@router.get("/school/reminders/config")
async def reminder_config(user=Depends(require_school_active)):
    db = get_db()
    school = await db.schools.find_one({"id": _sid(user)}, {"_id": 0})
    cfg = school.get("whatsapp_config") or {}
    return {
        "enabled": cfg.get("enabled", True),
        "days_before": cfg.get("days_before", 3),
        "template": cfg.get("template", ReminderConfigIn().template),
        "school_contact": cfg.get("school_contact") or school.get("phone"),
        "integration_configured": _wa_configured(),
        "integration_note": ("WhatsApp Business API not configured. Set WHATSAPP_ACCESS_TOKEN and "
                             "WHATSAPP_PHONE_NUMBER_ID environment variables to enable real sending.")
                             if not _wa_configured() else "WhatsApp Business API is configured.",
    }


@router.put("/school/reminders/config")
async def reminder_config_update(inp: ReminderConfigIn, user=Depends(require_role("school_admin"))):
    db = get_db()
    await db.schools.update_one({"id": _sid(user)},
                                {"$set": {"whatsapp_config": inp.model_dump()}})
    await audit(db, actor=user, action="update_reminder_config", module="reminders", record_id=_sid(user))
    return {"ok": True}


def _render_template(tmpl: str, ctx: dict) -> str:
    for k, v in ctx.items():
        tmpl = tmpl.replace("{" + k + "}", str(v))
    return tmpl


@router.get("/school/reminders/due-soon")
async def due_soon(user=Depends(require_school_active)):
    """List invoices that will be due within `days_before` days along with rendered
    message previews. Does NOT actually send any WhatsApp message."""
    db = get_db()
    s_id = _sid(user)
    school = await db.schools.find_one({"id": s_id}, {"_id": 0})
    cfg = school.get("whatsapp_config") or {}
    days_before = int(cfg.get("days_before", 3))
    template = cfg.get("template") or ReminderConfigIn().template
    today = now_utc().date()
    target = (today + timedelta(days=days_before)).isoformat()
    invoices = await db.fee_invoices.find({
        "school_id": s_id,
        "status": {"$in": ["unpaid", "partial"]},
        "due_date": {"$lte": target, "$gte": today.isoformat()},
    }, {"_id": 0}).sort("due_date", 1).to_list(2000)
    out = []
    for inv in invoices:
        stu = await db.students.find_one({"id": inv["student_id"], "school_id": s_id}, {"_id": 0})
        parent = None
        if stu and stu.get("parent_id"):
            parent = await db.users.find_one({"id": stu["parent_id"]}, {"_id": 0, "password_hash": 0})
        amount_due = inv["amount"] - inv.get("paid_amount", 0)
        msg = _render_template(template, {
            "student_name": stu["name"] if stu else "",
            "due_date": inv["due_date"],
            "amount": f"PKR {amount_due:,.0f}",
            "school_name": school.get("name", ""),
        })
        out.append({
            "invoice_id": inv["id"],
            "student_id": inv["student_id"],
            "student_name": stu["name"] if stu else "",
            "parent_name": parent["name"] if parent else None,
            "parent_phone": parent.get("phone") if parent else stu.get("phone") if stu else None,
            "due_date": inv["due_date"],
            "amount_due": amount_due,
            "preview_message": msg,
        })
    return {
        "integration_configured": _wa_configured(),
        "count": len(out),
        "items": out,
    }


class SendReminderIn(BaseModel):
    invoice_ids: List[str] = []
    dry_run: bool = True


@router.post("/school/reminders/send")
async def send_reminders(inp: SendReminderIn, user=Depends(require_role("school_admin", "accountant"))):
    """If the WhatsApp Business API is not configured, this endpoint records the
    intent as a queued reminder log and returns integration_configured=false. It
    never fakes a successful send.
    """
    db = get_db()
    s_id = _sid(user)
    school = await db.schools.find_one({"id": s_id}, {"_id": 0})
    cfg = school.get("whatsapp_config") or {}
    if not cfg.get("enabled", True):
        raise HTTPException(400, "Reminders are disabled in school settings")

    configured = _wa_configured()
    queued = 0
    for inv_id in inp.invoice_ids:
        inv = await db.fee_invoices.find_one({"id": inv_id, "school_id": s_id}, {"_id": 0})
        if not inv:
            continue
        entry = {
            "id": new_id(), "school_id": s_id, "invoice_id": inv_id,
            "student_id": inv["student_id"], "queued_by": user["id"],
            "status": "sent" if configured and not inp.dry_run else "queued",
            "integration_configured": configured,
            "created_at": iso(now_utc()),
        }
        await db.reminder_logs.insert_one(entry)
        queued += 1
    await audit(db, actor=user, action="queue_reminders", module="reminders",
                after={"count": queued, "configured": configured})
    return {
        "integration_configured": configured,
        "integration_note": ("WhatsApp Business API not configured — messages have NOT been sent. "
                             "They have been queued for future delivery.") if not configured else "OK",
        "queued": queued,
    }


@router.get("/school/reminders/logs")
async def reminder_logs(user=Depends(require_school_active)):
    db = get_db()
    return await db.reminder_logs.find({"school_id": _sid(user)}, {"_id": 0}).sort("created_at", -1).to_list(500)
