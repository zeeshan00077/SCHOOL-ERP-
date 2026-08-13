"""Phase 2B additions: student unique ID, student update+photo, ID card + bulk PDF, landscape voucher PDF."""
import base64
import mimetypes
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Optional

from db import (get_db, require_school_active, require_role, new_id, now_utc,
                iso, audit)
from pdf_service import voucher_pdf, id_cards_pdf
from routes_extras import fee_voucher as _voucher_payload

router = APIRouter(prefix="/api/school", tags=["phase2b"])
UPLOAD_ROOT = Path("/app/backend/uploads")


def _sid(u):
    if not u.get("school_id"):
        raise HTTPException(400, "No school_id")
    return u["school_id"]


from pymongo import ReturnDocument


async def next_student_id(db, school_id: str, prefix: str = "STU") -> str:
    year = now_utc().year
    key = f"{school_id}:{year}"
    doc = await db.counters.find_one_and_update(
        {"key": key},
        {"$inc": {"seq": 1}, "$setOnInsert": {"school_id": school_id, "year": year}},
        upsert=True, return_document=ReturnDocument.AFTER,
    )
    seq = doc.get("seq", 1) if doc else 1
    return f"{prefix}-{year}-{seq:05d}"


async def backfill_student_ids():
    db = get_db()
    schools = await db.schools.find({}, {"_id": 0, "id": 1}).to_list(1000)
    for s in schools:
        students = await db.students.find({"school_id": s["id"], "student_id": {"$in": [None, ""]}}, {"_id": 0}).sort("created_at", 1).to_list(5000)
        # also include those with no student_id field
        students += await db.students.find({"school_id": s["id"], "student_id": {"$exists": False}}, {"_id": 0}).sort("created_at", 1).to_list(5000)
        seen = set()
        for stu in students:
            if stu["id"] in seen:
                continue
            seen.add(stu["id"])
            sid_val = await next_student_id(db, s["id"])
            await db.students.update_one({"id": stu["id"]}, {"$set": {"student_id": sid_val}})


# ---------------- Student update + photo (existing create endpoint is preserved) ----------------
class StudentUpdateIn(BaseModel):
    name: Optional[str] = None
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    class_id: Optional[str] = None
    section_id: Optional[str] = None
    roll_number: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    cnic_bform: Optional[str] = None
    admission_date: Optional[str] = None
    academic_session: Optional[str] = None
    previous_school: Optional[str] = None
    emergency_contact: Optional[str] = None
    photo_url: Optional[str] = None
    status: Optional[str] = None


@router.put("/students/{sid_}")
async def update_student(sid_: str, inp: StudentUpdateIn, user=Depends(require_role("school_admin"))):
    db = get_db()
    exists = await db.students.find_one({"id": sid_, "school_id": _sid(user)})
    if not exists:
        raise HTTPException(404, "Not found")
    patch = {k: v for k, v in inp.model_dump().items() if v is not None}
    if patch:
        await db.students.update_one({"id": sid_}, {"$set": patch})
    await audit(db, actor=user, action="update_student", module="students", record_id=sid_, after=patch)
    return {"ok": True}


class PhotoIn(BaseModel):
    photo_url: str


@router.put("/students/{sid_}/photo")
async def set_photo(sid_: str, inp: PhotoIn, user=Depends(require_role("school_admin", "teacher", "receptionist"))):
    db = get_db()
    exists = await db.students.find_one({"id": sid_, "school_id": _sid(user)})
    if not exists:
        raise HTTPException(404, "Not found")
    await db.students.update_one({"id": sid_}, {"$set": {"photo_url": inp.photo_url}})
    await audit(db, actor=user, action="update_student_photo", module="students", record_id=sid_)
    return {"ok": True}


# ---------------- Landscape 3-copy Fee Voucher PDF ----------------
@router.get("/fee-invoices/{invoice_id}/voucher.pdf")
async def voucher_pdf_download(invoice_id: str, user=Depends(require_school_active)):
    v = await _voucher_payload(invoice_id, user)  # role/tenant checked inside
    pdf_bytes = voucher_pdf(v)
    return Response(content=pdf_bytes, media_type="application/pdf", headers={
        "Content-Disposition": f'inline; filename="voucher-{v["voucher_no"]}.pdf"'
    })


# ---------------- ID Cards ----------------
async def _enrich_student(db, s_id: str, stu: dict) -> dict:
    cls = await db.classes.find_one({"id": stu.get("class_id"), "school_id": s_id}, {"_id": 0}) if stu.get("class_id") else None
    section = None
    if stu.get("section_id"):
        section = await db.sections.find_one({"id": stu["section_id"], "school_id": s_id}, {"_id": 0})
    return {**stu, "class_name": cls["name"] if cls else "", "section_name": section["name"] if section else ""}


def _photo_data_uri(school_id: str, photo_url: Optional[str]) -> Optional[str]:
    """Convert /api/school/uploads/{file_id} URL to a data URI for embedding into PDF."""
    if not photo_url:
        return None
    fname = photo_url.rstrip("/").split("/")[-1]
    if "/" in fname or ".." in fname:
        return None
    p = UPLOAD_ROOT / school_id / fname
    if not p.exists():
        return None
    mime, _ = mimetypes.guess_type(str(p))
    b64 = base64.b64encode(p.read_bytes()).decode()
    return f"data:{mime or 'image/jpeg'};base64,{b64}"


@router.get("/id-cards/{student_id}")
async def id_card_data(student_id: str, user=Depends(require_school_active)):
    db = get_db()
    s_id = _sid(user)
    stu = await db.students.find_one({"id": student_id, "school_id": s_id}, {"_id": 0})
    if not stu:
        raise HTTPException(404, "Not found")
    # Role scoping — parent only own child, student only self
    if user["role"] == "parent" and stu.get("parent_id") != user["id"]:
        raise HTTPException(404, "Not found")
    if user["role"] == "student" and stu.get("user_id") != user["id"]:
        raise HTTPException(404, "Not found")
    stu = await _enrich_student(db, s_id, stu)
    school = await db.schools.find_one({"id": s_id}, {"_id": 0})
    return {
        "school": {k: school.get(k) for k in ["name","address","phone","email","website","logo_url","principal","academic_session","id_card_back_text"]},
        "student": stu,
        "session": school.get("academic_session"),
    }


class BulkCardsIn(BaseModel):
    student_ids: List[str] = []
    class_id: Optional[str] = None
    section_id: Optional[str] = None


@router.post("/id-cards/pdf")
async def id_cards_pdf_endpoint(inp: BulkCardsIn, user=Depends(require_role("school_admin", "teacher"))):
    db = get_db()
    s_id = _sid(user)
    q = {"school_id": s_id}
    if inp.student_ids:
        q["id"] = {"$in": inp.student_ids}
    elif inp.class_id:
        q["class_id"] = inp.class_id
        if inp.section_id:
            q["section_id"] = inp.section_id
    else:
        raise HTTPException(400, "Provide student_ids or class_id")
    students = await db.students.find(q, {"_id": 0}).sort("roll_number", 1).to_list(5000)
    if not students:
        raise HTTPException(404, "No students matched")
    students = [await _enrich_student(db, s_id, s) for s in students]
    school = await db.schools.find_one({"id": s_id}, {"_id": 0})
    photo_map = {s["id"]: _photo_data_uri(s_id, s.get("photo_url")) for s in students}
    pdf_bytes = id_cards_pdf(
        school=school,
        students=students,
        session=school.get("academic_session"),
        back_text=school.get("id_card_back_text"),
        photo_urls_by_id=photo_map,
    )
    await audit(db, actor=user, action="generate_id_cards_pdf", module="id_cards",
                after={"count": len(students)})
    return Response(content=pdf_bytes, media_type="application/pdf", headers={
        "Content-Disposition": f'attachment; filename="id-cards-{len(students)}.pdf"'
    })
