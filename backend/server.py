"""Main FastAPI app — auth + startup + include routers."""
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent / ".env")

import os
import secrets
from datetime import datetime, timedelta
from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from db import (get_db, now_utc, iso, new_id, hash_password, verify_password,
                create_access_token, create_refresh_token, decode_token,
                set_auth_cookies, clear_auth_cookies, get_current_user, audit,
                compute_school_status)
from models import RegisterSchoolIn, LoginIn, ForgotIn, ResetIn
from seed import seed_all
from routes_super import router as super_router
from routes_school import router as school_router

app = FastAPI(title="Skoolzoom School ERP SaaS")
api = APIRouter(prefix="/api")


@app.on_event("startup")
async def startup():
    db = get_db()
    await db.users.create_index("email", unique=True)
    await db.password_reset_tokens.create_index("expires_at", expireAfterSeconds=0)
    await db.login_attempts.create_index("identifier")
    await db.schools.create_index("id", unique=True)
    await db.students.create_index([("school_id", 1), ("class_id", 1)])
    await db.attendance.create_index([("school_id", 1), ("date", 1)])
    await db.fee_invoices.create_index([("school_id", 1), ("student_id", 1)])
    await seed_all()


# ---------------- Auth ----------------
def _client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def _check_lockout(db, identifier: str):
    doc = await db.login_attempts.find_one({"identifier": identifier})
    if doc and doc.get("locked_until"):
        until = datetime.fromisoformat(doc["locked_until"])
        if until > now_utc():
            raise HTTPException(429, f"Too many failed attempts. Try again after {until.isoformat()}")


async def _bump_lockout(db, identifier: str):
    doc = await db.login_attempts.find_one({"identifier": identifier})
    attempts = (doc.get("attempts", 0) if doc else 0) + 1
    update = {"attempts": attempts, "identifier": identifier}
    if attempts >= 5:
        update["locked_until"] = iso(now_utc() + timedelta(minutes=15))
        update["attempts"] = 0
    await db.login_attempts.update_one({"identifier": identifier}, {"$set": update}, upsert=True)


async def _clear_lockout(db, identifier: str):
    await db.login_attempts.delete_one({"identifier": identifier})


@api.post("/auth/register-school")
async def register_school(inp: RegisterSchoolIn, response: Response, request: Request):
    db = get_db()
    email = inp.admin_email.lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(400, "Email already registered")
    trial_days = int(os.environ.get("TRIAL_DAYS", 7))
    school_id = new_id()
    now = now_utc()
    await db.schools.insert_one({
        "id": school_id, "name": inp.school_name, "city": inp.city,
        "address": inp.address, "phone": inp.admin_phone, "email": email,
        "admin_email": email, "admin_name": inp.admin_name,
        "logo_url": None, "website": None, "principal": inp.admin_name,
        "academic_session": f"{now.year}-{now.year+1}",
        "currency": "PKR", "timezone": "Asia/Karachi",
        "status": "active",
        "subscription_status": "trial",
        "subscription_expires_at": iso(now + timedelta(days=trial_days)),
        "current_plan_id": None,
        "is_demo": False, "created_at": iso(now),
    })
    user_id = new_id()
    await db.users.insert_one({
        "id": user_id, "email": email, "name": inp.admin_name, "phone": inp.admin_phone,
        "role": "school_admin", "school_id": school_id,
        "password_hash": hash_password(inp.password),
        "created_at": iso(now),
    })
    access = create_access_token(user_id, email, "school_admin", school_id)
    refresh = create_refresh_token(user_id)
    set_auth_cookies(response, access, refresh)
    await audit(db, actor={"id": user_id, "email": email, "role": "school_admin", "school_id": school_id},
                action="register_school", module="auth", school_id=school_id, record_id=school_id)
    return {
        "user": {"id": user_id, "email": email, "name": inp.admin_name,
                 "role": "school_admin", "school_id": school_id},
        "school_id": school_id,
        "access_token": access,
    }


@api.post("/auth/login")
async def login(inp: LoginIn, response: Response, request: Request):
    db = get_db()
    email = inp.email.lower()
    ip = _client_ip(request)
    # Key lockout primarily on email so ingress IP rotation cannot bypass it,
    # while still tracking client IP for audit.
    identifier = email
    await _check_lockout(db, identifier)
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(inp.password, user["password_hash"]):
        await _bump_lockout(db, identifier)
        raise HTTPException(401, "Invalid email or password")
    await _clear_lockout(db, identifier)
    access = create_access_token(user["id"], user["email"], user["role"], user.get("school_id"))
    refresh = create_refresh_token(user["id"])
    set_auth_cookies(response, access, refresh)
    return {
        "user": {"id": user["id"], "email": user["email"], "name": user["name"],
                 "role": user["role"], "school_id": user.get("school_id")},
        "access_token": access,
    }


@api.post("/auth/logout")
async def logout(response: Response):
    clear_auth_cookies(response)
    return {"ok": True}


@api.get("/auth/me")
async def me(user=Depends(get_current_user)):
    return {"id": user["id"], "email": user["email"], "name": user["name"],
            "role": user["role"], "school_id": user.get("school_id"),
            "phone": user.get("phone")}


@api.post("/auth/refresh")
async def refresh(request: Request, response: Response):
    tok = request.cookies.get("refresh_token")
    if not tok:
        raise HTTPException(401, "No refresh token")
    try:
        payload = decode_token(tok)
    except Exception:
        raise HTTPException(401, "Invalid refresh")
    if payload.get("type") != "refresh":
        raise HTTPException(401, "Invalid token")
    db = get_db()
    u = await db.users.find_one({"id": payload["sub"]})
    if not u:
        raise HTTPException(401, "User not found")
    access = create_access_token(u["id"], u["email"], u["role"], u.get("school_id"))
    response.set_cookie("access_token", access, httponly=True, secure=True,
                        samesite="none", path="/", max_age=8 * 3600)
    return {"access_token": access}


@api.post("/auth/forgot-password")
async def forgot(inp: ForgotIn):
    db = get_db()
    user = await db.users.find_one({"email": inp.email.lower()})
    if user:
        token = secrets.token_urlsafe(32)
        await db.password_reset_tokens.insert_one({
            "id": new_id(), "token": token, "user_id": user["id"],
            "expires_at": now_utc() + timedelta(hours=1), "used": False,
            "created_at": iso(now_utc()),
        })
        print(f"[PASSWORD RESET] {inp.email} -> token={token}")
    # do not leak whether email exists
    return {"ok": True, "message": "If this email is registered, a reset link has been generated (check server logs in demo)."}


@api.post("/auth/reset-password")
async def reset(inp: ResetIn):
    db = get_db()
    rec = await db.password_reset_tokens.find_one({"token": inp.token, "used": False})
    if not rec:
        raise HTTPException(400, "Invalid or expired token")
    exp = rec["expires_at"]
    if isinstance(exp, str):
        exp = datetime.fromisoformat(exp)
    if exp < now_utc():
        raise HTTPException(400, "Token expired")
    await db.users.update_one({"id": rec["user_id"]},
                              {"$set": {"password_hash": hash_password(inp.new_password)}})
    await db.password_reset_tokens.update_one({"id": rec["id"]}, {"$set": {"used": True}})
    return {"ok": True}


# ---------------- Public info ----------------
@api.get("/public/plans")
async def public_plans():
    db = get_db()
    return await db.subscription_plans.find({"is_active": True}, {"_id": 0}).to_list(20)


@api.get("/health")
async def health():
    return {"status": "ok", "time": iso(now_utc())}


app.include_router(api)
app.include_router(super_router)
app.include_router(school_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=[o.strip() for o in os.environ.get("CORS_ORIGINS", "*").split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)
