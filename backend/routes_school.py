"""School-scoped routes — enforced tenant isolation via user['school_id']."""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from datetime import datetime, timedelta
from db import (get_db, require_role, require_school_active, get_current_user,
                now_utc, iso, new_id, audit, hash_password, compute_school_status)
from models import (SchoolUpdateIn, ClassIn, SectionIn, SubjectIn, StudentIn, TeacherIn,
                    AttendanceBulkIn, FeeStructureIn, FeeInvoiceIn, FeePaymentIn,
                    ExamIn, MarksBulkIn, TimetableEntryIn, NoticeIn, PaymentSubmitIn,
                    UserCreateIn)

router = APIRouter(prefix="/api/school", tags=["school"])

STAFF_ROLES = ["school_admin", "teacher", "accountant", "receptionist", "librarian"]


def sid(u):
    if not u.get("school_id"):
        raise HTTPException(400, "User has no school_id")
    return u["school_id"]


# ------------ School Info & Subscription ------------
@router.get("/me")
async def my_school(user=Depends(get_current_user)):
    if user["role"] == "super_admin":
        return {"role": "super_admin"}
    db = get_db()
    s = await db.schools.find_one({"id": sid(user)}, {"_id": 0})
    if not s:
        raise HTTPException(404, "School not found")
    s.update(compute_school_status(s))
    return s


@router.put("/settings")
async def update_settings(inp: SchoolUpdateIn, user=Depends(require_role("school_admin"))):
    db = get_db()
    patch = {k: v for k, v in inp.model_dump().items() if v is not None}
    await db.schools.update_one({"id": sid(user)}, {"$set": patch})
    await audit(db, actor=user, action="update_school", module="settings", record_id=sid(user), after=patch)
    return {"ok": True}


@router.get("/subscription")
async def subscription(user=Depends(get_current_user)):
    db = get_db()
    s = await db.schools.find_one({"id": sid(user)}, {"_id": 0})
    s.update(compute_school_status(s))
    payments = await db.payments.find({"school_id": sid(user)}, {"_id": 0}).sort("created_at", -1).to_list(100)
    plans = await db.subscription_plans.find({"is_active": True}, {"_id": 0}).to_list(100)
    return {"school": s, "payments": payments, "plans": plans}


@router.post("/payments")
async def submit_payment(inp: PaymentSubmitIn, user=Depends(require_role("school_admin"))):
    db = get_db()
    plan = await db.subscription_plans.find_one({"id": inp.plan_id})
    if not plan:
        raise HTTPException(404, "Plan not found")
    doc = {
        "id": new_id(),
        "school_id": sid(user),
        "submitted_by": user["id"],
        "plan_id": inp.plan_id,
        "amount": inp.amount,
        "method": inp.method,
        "reference_number": inp.reference_number,
        "payment_date": inp.payment_date,
        "proof_url": inp.proof_url,
        "notes": inp.notes,
        "status": "pending",
        "created_at": iso(now_utc()),
    }
    await db.payments.insert_one(doc)
    await audit(db, actor=user, action="submit_payment", module="payments", record_id=doc["id"], after=doc)
    doc.pop("_id", None)
    return doc


# ------------ Dashboard ------------
@router.get("/dashboard")
async def dashboard(user=Depends(require_school_active)):
    db = get_db()
    s_id = sid(user)
    total_students = await db.students.count_documents({"school_id": s_id})
    total_teachers = await db.teachers.count_documents({"school_id": s_id})
    total_parents = await db.users.count_documents({"school_id": s_id, "role": "parent"})
    today = now_utc().date().isoformat()
    att = await db.attendance.find({"school_id": s_id, "date": today}, {"_id": 0}).to_list(10000)
    present = sum(1 for a in att if a["status"] == "present")
    absent = sum(1 for a in att if a["status"] == "absent")
    payments_today = await db.fee_payments.find({"school_id": s_id, "paid_on": today}, {"_id": 0}).to_list(10000)
    fee_today = sum(p["amount"] for p in payments_today)
    invoices = await db.fee_invoices.find({"school_id": s_id}, {"_id": 0}).to_list(20000)
    pending_fees = sum((i["amount"] - i.get("paid_amount", 0)) for i in invoices if i.get("status") != "paid")
    notices = await db.notices.find({"school_id": s_id}, {"_id": 0}).sort("created_at", -1).limit(5).to_list(5)
    # attendance trend last 7 days
    trend = []
    for i in range(6, -1, -1):
        d = (now_utc() - timedelta(days=i)).date().isoformat()
        day_att = await db.attendance.find({"school_id": s_id, "date": d}, {"_id": 0}).to_list(10000)
        p = sum(1 for a in day_att if a["status"] == "present")
        trend.append({"date": d, "present": p, "total": len(day_att)})
    # fee collection last 6 months
    fee_series = []
    for i in range(5, -1, -1):
        month = (now_utc().replace(day=1) - timedelta(days=i * 30)).strftime("%Y-%m")
        month_pays = [p for p in await db.fee_payments.find({"school_id": s_id}, {"_id": 0}).to_list(20000)
                      if p.get("paid_on", "").startswith(month)]
        fee_series.append({"month": month, "amount": sum(p["amount"] for p in month_pays)})
    return {
        "total_students": total_students, "total_teachers": total_teachers, "total_parents": total_parents,
        "present_today": present, "absent_today": absent,
        "fee_collection_today": fee_today, "pending_fees": pending_fees,
        "notices": notices, "attendance_trend": trend, "fee_series": fee_series,
    }


# ------------ Classes / Sections / Subjects ------------
@router.get("/classes")
async def list_classes(user=Depends(require_school_active)):
    db = get_db()
    classes = await db.classes.find({"school_id": sid(user)}, {"_id": 0}).sort("order", 1).to_list(500)
    for c in classes:
        c["sections"] = await db.sections.find({"school_id": sid(user), "class_id": c["id"]}, {"_id": 0}).to_list(50)
    return classes


@router.post("/classes")
async def create_class(inp: ClassIn, user=Depends(require_role("school_admin"))):
    db = get_db()
    doc = {"id": new_id(), "school_id": sid(user), **inp.model_dump(), "created_at": iso(now_utc())}
    await db.classes.insert_one(doc)
    await audit(db, actor=user, action="create_class", module="classes", record_id=doc["id"])
    doc.pop("_id", None)
    return doc


@router.delete("/classes/{class_id}")
async def del_class(class_id: str, user=Depends(require_role("school_admin"))):
    db = get_db()
    await db.classes.delete_one({"id": class_id, "school_id": sid(user)})
    await audit(db, actor=user, action="delete_class", module="classes", record_id=class_id)
    return {"ok": True}


@router.post("/sections")
async def create_section(inp: SectionIn, user=Depends(require_role("school_admin"))):
    db = get_db()
    cls = await db.classes.find_one({"id": inp.class_id, "school_id": sid(user)})
    if not cls:
        raise HTTPException(404, "Class not found")
    doc = {"id": new_id(), "school_id": sid(user), **inp.model_dump()}
    await db.sections.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.get("/subjects")
async def list_subjects(user=Depends(require_school_active)):
    db = get_db()
    return await db.subjects.find({"school_id": sid(user)}, {"_id": 0}).to_list(500)


@router.post("/subjects")
async def create_subject(inp: SubjectIn, user=Depends(require_role("school_admin"))):
    db = get_db()
    doc = {"id": new_id(), "school_id": sid(user), **inp.model_dump()}
    await db.subjects.insert_one(doc)
    doc.pop("_id", None)
    return doc


async def _role_scope(db, user):
    """Return (student_ids, class_ids) accessible to a parent/student user.
    None => no restriction (admin/teacher/accountant see full school scope).
    """
    role = user["role"]
    if role == "parent":
        kids = await db.students.find({"school_id": user["school_id"], "parent_id": user["id"]}, {"_id": 0}).to_list(50)
        return ([k["id"] for k in kids], list({k["class_id"] for k in kids if k.get("class_id")}))
    if role == "student":
        me = await db.students.find_one({"school_id": user["school_id"], "user_id": user["id"]}, {"_id": 0})
        if me:
            return ([me["id"]], [me["class_id"]] if me.get("class_id") else [])
        return ([], [])
    return (None, None)


# ------------ Students ------------
@router.get("/students")
async def list_students(class_id: Optional[str] = None, q: Optional[str] = None,
                        user=Depends(require_school_active)):
    db = get_db()
    query = {"school_id": sid(user)}
    stu_ids, class_ids = await _role_scope(db, user)
    if stu_ids is not None:
        query["id"] = {"$in": stu_ids}
    if class_id:
        query["class_id"] = class_id
    if q:
        query["name"] = {"$regex": q, "$options": "i"}
    return await db.students.find(query, {"_id": 0}).sort("name", 1).to_list(5000)


@router.post("/students")
async def create_student(inp: StudentIn, user=Depends(require_role("school_admin"))):
    db = get_db()
    cls = await db.classes.find_one({"id": inp.class_id, "school_id": sid(user)})
    if not cls:
        raise HTTPException(404, "Class not found")
    data = inp.model_dump()
    parent_email = data.pop("parent_email", None)
    parent_name = data.pop("parent_name", None)
    parent_phone = data.pop("parent_phone", None)
    parent_id = None
    if parent_email:
        existing = await db.users.find_one({"email": parent_email.lower()})
        if existing:
            parent_id = existing["id"]
        else:
            parent_doc = {
                "id": new_id(), "email": parent_email.lower(), "name": parent_name or parent_email,
                "phone": parent_phone, "role": "parent", "school_id": sid(user),
                "password_hash": hash_password("Parent@123"),
                "created_at": iso(now_utc()),
            }
            await db.users.insert_one(parent_doc)
            parent_id = parent_doc["id"]
    admission = data.get("admission_number") or f"ADM-{int(now_utc().timestamp())}"
    doc = {
        "id": new_id(), "school_id": sid(user), **data,
        "admission_number": admission, "parent_id": parent_id,
        "status": "active", "created_at": iso(now_utc()),
    }
    await db.students.insert_one(doc)
    await audit(db, actor=user, action="create_student", module="students", record_id=doc["id"])
    doc.pop("_id", None)
    return doc


@router.get("/students/{sid_}")
async def get_student(sid_: str, user=Depends(require_school_active)):
    db = get_db()
    s = await db.students.find_one({"id": sid_, "school_id": sid(user)}, {"_id": 0})
    if not s:
        raise HTTPException(404, "Not found")
    if user["role"] == "parent" and s.get("parent_id") != user["id"]:
        raise HTTPException(404, "Not found")
    if user["role"] == "student" and s.get("user_id") != user["id"]:
        raise HTTPException(404, "Not found")
    return s


@router.delete("/students/{sid_}")
async def del_student(sid_: str, user=Depends(require_role("school_admin"))):
    db = get_db()
    await db.students.delete_one({"id": sid_, "school_id": sid(user)})
    await audit(db, actor=user, action="delete_student", module="students", record_id=sid_)
    return {"ok": True}


# ------------ Teachers ------------
@router.get("/teachers")
async def list_teachers(user=Depends(require_school_active)):
    db = get_db()
    return await db.teachers.find({"school_id": sid(user)}, {"_id": 0}).to_list(1000)


@router.post("/teachers")
async def create_teacher(inp: TeacherIn, user=Depends(require_role("school_admin"))):
    db = get_db()
    data = inp.model_dump()
    pwd = data.pop("password", None) or "Teacher@123"
    email = data["email"].lower()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(400, "Email already exists")
    user_doc = {
        "id": new_id(), "email": email, "name": data["name"], "phone": data.get("phone"),
        "role": "teacher", "school_id": sid(user),
        "password_hash": hash_password(pwd),
        "created_at": iso(now_utc()),
    }
    await db.users.insert_one(user_doc)
    doc = {"id": new_id(), "school_id": sid(user), "user_id": user_doc["id"], **data,
           "employee_id": f"EMP-{int(now_utc().timestamp())}", "status": "active",
           "created_at": iso(now_utc())}
    await db.teachers.insert_one(doc)
    await audit(db, actor=user, action="create_teacher", module="teachers", record_id=doc["id"])
    doc.pop("_id", None)
    return doc


@router.get("/parents")
async def list_parents(user=Depends(require_school_active)):
    db = get_db()
    parents = await db.users.find({"school_id": sid(user), "role": "parent"},
                                  {"_id": 0, "password_hash": 0}).to_list(2000)
    for p in parents:
        p["children"] = await db.students.find({"parent_id": p["id"], "school_id": sid(user)},
                                                {"_id": 0}).to_list(20)
    return parents


# ------------ Users ------------
@router.get("/users")
async def list_users(user=Depends(require_role("school_admin"))):
    db = get_db()
    return await db.users.find({"school_id": sid(user)}, {"_id": 0, "password_hash": 0}).to_list(2000)


@router.post("/users")
async def create_user(inp: UserCreateIn, user=Depends(require_role("school_admin"))):
    db = get_db()
    email = inp.email.lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(400, "Email already exists")
    doc = {"id": new_id(), "email": email, "name": inp.name, "phone": inp.phone,
           "role": inp.role, "school_id": sid(user),
           "password_hash": hash_password(inp.password), "created_at": iso(now_utc())}
    await db.users.insert_one(doc)
    await audit(db, actor=user, action="create_user", module="users", record_id=doc["id"])
    doc.pop("password_hash", None); doc.pop("_id", None)
    return doc


# ------------ Attendance ------------
@router.post("/attendance")
async def mark_attendance(inp: AttendanceBulkIn, user=Depends(require_school_active)):
    if user["role"] not in ("school_admin", "teacher"):
        raise HTTPException(403, "Only teachers/admin can mark attendance")
    db = get_db()
    # remove existing for this class/date/section then re-insert
    q = {"school_id": sid(user), "class_id": inp.class_id, "date": inp.date}
    if inp.section_id:
        q["section_id"] = inp.section_id
    await db.attendance.delete_many(q)
    docs = []
    for e in inp.entries:
        docs.append({"id": new_id(), "school_id": sid(user), "class_id": inp.class_id,
                     "section_id": inp.section_id, "date": inp.date,
                     "student_id": e.student_id, "status": e.status,
                     "marked_by": user["id"], "created_at": iso(now_utc())})
    if docs:
        await db.attendance.insert_many(docs)
    await audit(db, actor=user, action="mark_attendance", module="attendance",
                record_id=f"{inp.class_id}:{inp.date}", after={"count": len(docs)})
    return {"ok": True, "count": len(docs)}


@router.get("/attendance")
async def get_attendance(class_id: str, date: str, section_id: Optional[str] = None,
                         user=Depends(require_school_active)):
    db = get_db()
    q = {"school_id": sid(user), "class_id": class_id, "date": date}
    if section_id:
        q["section_id"] = section_id
    stu_ids, _ = await _role_scope(db, user)
    if stu_ids is not None:
        q["student_id"] = {"$in": stu_ids}
    return await db.attendance.find(q, {"_id": 0}).to_list(1000)


# ------------ Fees ------------
@router.get("/fee-structures")
async def fs_list(user=Depends(require_school_active)):
    db = get_db()
    return await db.fee_structures.find({"school_id": sid(user)}, {"_id": 0}).to_list(500)


@router.post("/fee-structures")
async def fs_create(inp: FeeStructureIn, user=Depends(require_role("school_admin"))):
    db = get_db()
    doc = {"id": new_id(), "school_id": sid(user), **inp.model_dump(), "created_at": iso(now_utc())}
    await db.fee_structures.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.get("/fee-invoices")
async def inv_list(student_id: Optional[str] = None, user=Depends(require_school_active)):
    db = get_db()
    q = {"school_id": sid(user)}
    if student_id:
        q["student_id"] = student_id
    invoices = await db.fee_invoices.find(q, {"_id": 0}).sort("due_date", -1).to_list(5000)
    return invoices


@router.post("/fee-invoices")
async def inv_create(inp: FeeInvoiceIn, user=Depends(require_role("school_admin", "accountant"))):
    db = get_db()
    stu = await db.students.find_one({"id": inp.student_id, "school_id": sid(user)})
    if not stu:
        raise HTTPException(404, "Student not found")
    doc = {"id": new_id(), "school_id": sid(user), **inp.model_dump(),
           "student_name": stu["name"], "paid_amount": 0, "status": "unpaid",
           "created_at": iso(now_utc())}
    await db.fee_invoices.insert_one(doc)
    await audit(db, actor=user, action="create_invoice", module="fees", record_id=doc["id"])
    doc.pop("_id", None)
    return doc


@router.post("/fee-payments")
async def pay_create(inp: FeePaymentIn, user=Depends(require_role("school_admin", "accountant"))):
    db = get_db()
    inv = await db.fee_invoices.find_one({"id": inp.invoice_id, "school_id": sid(user)})
    if not inv:
        raise HTTPException(404, "Invoice not found")
    new_paid = inv.get("paid_amount", 0) + inp.amount
    status = "paid" if new_paid >= inv["amount"] else "partial"
    receipt_no = f"RC-{int(now_utc().timestamp())}"
    doc = {"id": new_id(), "school_id": sid(user), "invoice_id": inp.invoice_id,
           "student_id": inv["student_id"], "amount": inp.amount, "method": inp.method,
           "reference": inp.reference, "paid_on": inp.paid_on or now_utc().date().isoformat(),
           "received_by": user["id"], "receipt_no": receipt_no, "created_at": iso(now_utc())}
    await db.fee_payments.insert_one(doc)
    await db.fee_invoices.update_one({"id": inp.invoice_id}, {"$set": {
        "paid_amount": new_paid, "status": status}})
    await audit(db, actor=user, action="record_payment", module="fees", record_id=doc["id"], after={"amount": inp.amount})
    doc.pop("_id", None)
    return doc


@router.get("/fee-payments")
async def pay_list(user=Depends(require_school_active)):
    db = get_db()
    q = {"school_id": sid(user)}
    stu_ids, _ = await _role_scope(db, user)
    if stu_ids is not None:
        q["student_id"] = {"$in": stu_ids}
    return await db.fee_payments.find(q, {"_id": 0}).sort("created_at", -1).to_list(5000)


# ------------ Exams & Results ------------
@router.get("/exams")
async def exams_list(user=Depends(require_school_active)):
    db = get_db()
    return await db.exams.find({"school_id": sid(user)}, {"_id": 0}).sort("start_date", -1).to_list(500)


@router.post("/exams")
async def exams_create(inp: ExamIn, user=Depends(require_role("school_admin", "teacher"))):
    db = get_db()
    doc = {"id": new_id(), "school_id": sid(user), **inp.model_dump(), "created_at": iso(now_utc())}
    await db.exams.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.post("/marks")
async def marks_bulk(inp: MarksBulkIn, user=Depends(require_role("school_admin", "teacher"))):
    db = get_db()
    exam = await db.exams.find_one({"id": inp.exam_id, "school_id": sid(user)})
    if not exam:
        raise HTTPException(404, "Exam not found")
    await db.marks.delete_many({"school_id": sid(user), "exam_id": inp.exam_id, "subject_id": inp.subject_id})
    docs = []
    for m in inp.marks:
        docs.append({"id": new_id(), "school_id": sid(user), "exam_id": inp.exam_id,
                     "subject_id": inp.subject_id, "student_id": m["student_id"],
                     "marks_obtained": float(m["marks_obtained"]), "total": exam["total_marks"],
                     "created_at": iso(now_utc())})
    if docs:
        await db.marks.insert_many(docs)
    return {"ok": True, "count": len(docs)}


@router.get("/marks")
async def marks_list(exam_id: str, user=Depends(require_school_active)):
    db = get_db()
    return await db.marks.find({"school_id": sid(user), "exam_id": exam_id}, {"_id": 0}).to_list(10000)


@router.get("/results/{exam_id}")
async def results(exam_id: str, user=Depends(require_school_active)):
    db = get_db()
    exam = await db.exams.find_one({"id": exam_id, "school_id": sid(user)}, {"_id": 0})
    if not exam:
        raise HTTPException(404, "Exam not found")
    marks = await db.marks.find({"school_id": sid(user), "exam_id": exam_id}, {"_id": 0}).to_list(20000)
    students = await db.students.find({"school_id": sid(user), "class_id": exam["class_id"]}, {"_id": 0}).to_list(2000)
    subjects_ids = list({m["subject_id"] for m in marks})
    subjects = await db.subjects.find({"school_id": sid(user), "id": {"$in": subjects_ids}}, {"_id": 0}).to_list(200)
    subj_map = {s["id"]: s for s in subjects}
    per_student = {}
    for m in marks:
        per_student.setdefault(m["student_id"], []).append(m)
    rows = []
    for stu in students:
        stu_marks = per_student.get(stu["id"], [])
        obtained = sum(m["marks_obtained"] for m in stu_marks)
        total = sum(m["total"] for m in stu_marks)
        pct = (obtained / total * 100) if total else 0
        grade = _grade(pct)
        rows.append({"student_id": stu["id"], "student_name": stu["name"],
                     "roll_number": stu.get("roll_number"),
                     "subjects": [{"subject_id": m["subject_id"],
                                   "subject_name": subj_map.get(m["subject_id"], {}).get("name", ""),
                                   "marks": m["marks_obtained"], "total": m["total"]} for m in stu_marks],
                     "obtained": obtained, "total": total, "percentage": round(pct, 2), "grade": grade})
    rows.sort(key=lambda r: r["obtained"], reverse=True)
    for i, r in enumerate(rows):
        r["position"] = i + 1
    # Apply role scoping — parents see only their kids' rows, students only their own row.
    stu_ids, _ = await _role_scope(db, user)
    if stu_ids is not None:
        rows = [r for r in rows if r["student_id"] in stu_ids]
    return {"exam": exam, "results": rows}


def _grade(p):
    if p >= 80: return "A+"
    if p >= 70: return "A"
    if p >= 60: return "B"
    if p >= 50: return "C"
    if p >= 40: return "D"
    return "F"


# ------------ Timetable ------------
@router.get("/timetable")
async def tt_list(class_id: Optional[str] = None, teacher_id: Optional[str] = None,
                  user=Depends(require_school_active)):
    db = get_db()
    q = {"school_id": sid(user)}
    if class_id: q["class_id"] = class_id
    if teacher_id: q["teacher_id"] = teacher_id
    _, class_ids = await _role_scope(db, user)
    if class_ids is not None:
        if class_id and class_id not in class_ids:
            return []
        q["class_id"] = {"$in": class_ids}
    return await db.timetable.find(q, {"_id": 0}).to_list(5000)


@router.post("/timetable")
async def tt_create(inp: TimetableEntryIn, user=Depends(require_role("school_admin"))):
    db = get_db()
    # check conflicts
    if inp.teacher_id:
        conflict = await db.timetable.find_one({"school_id": sid(user), "teacher_id": inp.teacher_id,
                                                "day": inp.day, "period": inp.period})
        if conflict:
            raise HTTPException(400, "Teacher already booked for this period")
    doc = {"id": new_id(), "school_id": sid(user), **inp.model_dump()}
    await db.timetable.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.delete("/timetable/{entry_id}")
async def tt_del(entry_id: str, user=Depends(require_role("school_admin"))):
    db = get_db()
    await db.timetable.delete_one({"id": entry_id, "school_id": sid(user)})
    return {"ok": True}


# ------------ Notices ------------
@router.get("/notices")
async def notices_list(user=Depends(require_school_active)):
    db = get_db()
    return await db.notices.find({"school_id": sid(user)}, {"_id": 0}).sort("created_at", -1).to_list(200)


@router.post("/notices")
async def notice_create(inp: NoticeIn, user=Depends(require_role("school_admin", "teacher"))):
    db = get_db()
    doc = {"id": new_id(), "school_id": sid(user), **inp.model_dump(),
           "created_by": user["id"], "created_by_name": user["name"],
           "created_at": iso(now_utc())}
    await db.notices.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.delete("/notices/{notice_id}")
async def notice_del(notice_id: str, user=Depends(require_role("school_admin"))):
    db = get_db()
    await db.notices.delete_one({"id": notice_id, "school_id": sid(user)})
    return {"ok": True}


# ------------ Audit (school scope) ------------
@router.get("/audit-logs")
async def school_audit(user=Depends(require_role("school_admin"))):
    db = get_db()
    from db import _scrub
    docs = await db.audit_logs.find({"school_id": sid(user)}, {"_id": 0}).sort("created_at", -1).to_list(500)
    return [_scrub(d) for d in docs]
