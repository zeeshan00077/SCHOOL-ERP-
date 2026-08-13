"""Super Admin routes — platform-wide control."""
from fastapi import APIRouter, Depends, HTTPException, Request
from datetime import datetime, timedelta
from typing import Optional
from db import get_db, require_role, now_utc, iso, new_id, audit, compute_school_status
from models import PlanIn, PaymentDecisionIn

router = APIRouter(prefix="/api/super-admin", tags=["super-admin"])


@router.get("/stats")
async def stats(user=Depends(require_role("super_admin"))):
    db = get_db()
    schools = await db.schools.find({}, {"_id": 0}).to_list(10000)
    total = len(schools)
    active = trial = expired_c = suspended = 0
    for s in schools:
        comp = compute_school_status(s)
        eff = comp["subscription_status_effective"]
        if eff == "active":
            active += 1
        elif eff == "trial":
            trial += 1
        elif eff in ("expired", "trial_expired"):
            expired_c += 1
        elif eff == "suspended":
            suspended += 1
    total_students = await db.students.count_documents({})
    total_teachers = await db.teachers.count_documents({})
    payments = await db.payments.find({}, {"_id": 0}).to_list(10000)
    revenue = sum(p["amount"] for p in payments if p["status"] == "approved")
    pending = sum(1 for p in payments if p["status"] == "pending")
    # revenue by month (last 6 months)
    by_month = {}
    for p in payments:
        if p["status"] != "approved":
            continue
        month = p.get("approved_at", p.get("created_at", ""))[:7]
        by_month[month] = by_month.get(month, 0) + p["amount"]
    revenue_series = [{"month": k, "amount": v} for k, v in sorted(by_month.items())][-6:]
    return {
        "total_schools": total, "active_schools": active, "trial_schools": trial,
        "expired_schools": expired_c, "suspended_schools": suspended,
        "total_students": total_students, "total_teachers": total_teachers,
        "revenue": revenue, "pending_payments": pending,
        "revenue_series": revenue_series,
    }


@router.get("/schools")
async def list_schools(q: Optional[str] = None, status: Optional[str] = None,
                      user=Depends(require_role("super_admin"))):
    db = get_db()
    query = {}
    if q:
        query["$or"] = [{"name": {"$regex": q, "$options": "i"}},
                        {"admin_email": {"$regex": q, "$options": "i"}}]
    schools = await db.schools.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    out = []
    for s in schools:
        s.update(compute_school_status(s))
        if status and s["subscription_status_effective"] != status:
            continue
        out.append(s)
    return out


@router.post("/schools/{school_id}/extend")
async def extend(school_id: str, days: int, user=Depends(require_role("super_admin"))):
    db = get_db()
    s = await db.schools.find_one({"id": school_id})
    if not s:
        raise HTTPException(404, "School not found")
    cur = s.get("subscription_expires_at")
    base = datetime.fromisoformat(cur) if cur else now_utc()
    if base < now_utc():
        base = now_utc()
    new_exp = base + timedelta(days=days)
    await db.schools.update_one({"id": school_id}, {"$set": {
        "subscription_expires_at": iso(new_exp),
        "subscription_status": "active",
    }})
    await audit(db, actor=user, action="extend_subscription", module="schools",
                school_id=school_id, record_id=school_id, after={"days": days})
    return {"ok": True, "new_expiry": iso(new_exp)}


@router.post("/schools/{school_id}/suspend")
async def suspend(school_id: str, user=Depends(require_role("super_admin"))):
    db = get_db()
    await db.schools.update_one({"id": school_id}, {"$set": {"subscription_status": "suspended", "status": "suspended"}})
    await audit(db, actor=user, action="suspend_school", module="schools", school_id=school_id, record_id=school_id)
    return {"ok": True}


@router.post("/schools/{school_id}/activate")
async def activate(school_id: str, user=Depends(require_role("super_admin"))):
    db = get_db()
    s = await db.schools.find_one({"id": school_id})
    if not s:
        raise HTTPException(404, "Not found")
    # if no expiry or expired, give 30 days grace
    exp = s.get("subscription_expires_at")
    if not exp or datetime.fromisoformat(exp) < now_utc():
        exp = iso(now_utc() + timedelta(days=30))
    await db.schools.update_one({"id": school_id}, {"$set": {
        "subscription_status": "active", "status": "active", "subscription_expires_at": exp
    }})
    await audit(db, actor=user, action="activate_school", module="schools", school_id=school_id, record_id=school_id)
    return {"ok": True}


# ---------- Plans ----------
@router.get("/plans")
async def list_plans(user=Depends(require_role("super_admin"))):
    db = get_db()
    return await db.subscription_plans.find({}, {"_id": 0}).to_list(100)


@router.post("/plans")
async def create_plan(inp: PlanIn, user=Depends(require_role("super_admin"))):
    db = get_db()
    doc = {"id": new_id(), **inp.model_dump(), "created_at": iso(now_utc())}
    await db.subscription_plans.insert_one(doc)
    await audit(db, actor=user, action="create_plan", module="plans", record_id=doc["id"], after=inp.model_dump())
    doc.pop("_id", None)
    return doc


@router.put("/plans/{plan_id}")
async def update_plan(plan_id: str, inp: PlanIn, user=Depends(require_role("super_admin"))):
    db = get_db()
    r = await db.subscription_plans.update_one({"id": plan_id}, {"$set": inp.model_dump()})
    if r.matched_count == 0:
        raise HTTPException(404, "Plan not found")
    await audit(db, actor=user, action="update_plan", module="plans", record_id=plan_id, after=inp.model_dump())
    return {"ok": True}


@router.delete("/plans/{plan_id}")
async def delete_plan(plan_id: str, user=Depends(require_role("super_admin"))):
    db = get_db()
    await db.subscription_plans.delete_one({"id": plan_id})
    await audit(db, actor=user, action="delete_plan", module="plans", record_id=plan_id)
    return {"ok": True}


# ---------- Payments ----------
@router.get("/payments")
async def list_payments(status: Optional[str] = None, user=Depends(require_role("super_admin"))):
    db = get_db()
    q = {}
    if status:
        q["status"] = status
    return await db.payments.find(q, {"_id": 0}).sort("created_at", -1).to_list(1000)


@router.post("/payments/{payment_id}/approve")
async def approve_payment(payment_id: str, inp: PaymentDecisionIn, user=Depends(require_role("super_admin"))):
    db = get_db()
    p = await db.payments.find_one({"id": payment_id})
    if not p:
        raise HTTPException(404, "Payment not found")
    if p["status"] != "pending":
        raise HTTPException(400, f"Payment already {p['status']}")
    plan = await db.subscription_plans.find_one({"id": p["plan_id"]})
    duration = plan["duration_days"] if plan else 365
    school = await db.schools.find_one({"id": p["school_id"]})
    # start from max(now, current expiry) so extensions stack
    cur = school.get("subscription_expires_at") if school else None
    base = datetime.fromisoformat(cur) if cur else now_utc()
    if base < now_utc():
        base = now_utc()
    new_exp = base + timedelta(days=duration)
    await db.payments.update_one({"id": payment_id}, {"$set": {
        "status": "approved", "approved_by": user["id"],
        "approved_at": iso(now_utc()), "remarks": inp.remarks,
    }})
    await db.schools.update_one({"id": p["school_id"]}, {"$set": {
        "subscription_status": "active", "status": "active",
        "subscription_expires_at": iso(new_exp),
        "current_plan_id": p["plan_id"],
    }})
    await audit(db, actor=user, action="approve_payment", module="payments",
                school_id=p["school_id"], record_id=payment_id, after={"expires_at": iso(new_exp)})
    return {"ok": True, "new_expiry": iso(new_exp)}


@router.post("/payments/{payment_id}/reject")
async def reject_payment(payment_id: str, inp: PaymentDecisionIn, user=Depends(require_role("super_admin"))):
    db = get_db()
    r = await db.payments.update_one({"id": payment_id, "status": "pending"}, {"$set": {
        "status": "rejected", "approved_by": user["id"],
        "approved_at": iso(now_utc()), "remarks": inp.remarks,
    }})
    if r.matched_count == 0:
        raise HTTPException(400, "Not pending")
    await audit(db, actor=user, action="reject_payment", module="payments", record_id=payment_id)
    return {"ok": True}


@router.get("/audit-logs")
async def audit_logs(limit: int = 200, user=Depends(require_role("super_admin"))):
    db = get_db()
    from db import _scrub
    docs = await db.audit_logs.find({}, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return [_scrub(d) for d in docs]
