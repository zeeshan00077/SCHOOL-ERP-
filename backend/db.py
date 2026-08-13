"""Database, security, and helper utilities."""
import os
import bcrypt
import jwt
import uuid
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import Request, HTTPException, Depends

JWT_ALGO = "HS256"
ACCESS_TTL_MIN = 60 * 8  # 8 hours (long day at school)
REFRESH_TTL_DAYS = 30

_client = None
_db = None


def get_db():
    global _client, _db
    if _db is None:
        _client = AsyncIOMotorClient(os.environ["MONGO_URL"])
        _db = _client[os.environ["DB_NAME"]]
    return _db


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.isoformat()


def new_id() -> str:
    return str(uuid.uuid4())


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def _secret() -> str:
    return os.environ["JWT_SECRET"]


def create_access_token(user_id: str, email: str, role: str, school_id: str | None) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "school_id": school_id,
        "type": "access",
        "exp": now_utc() + timedelta(minutes=ACCESS_TTL_MIN),
    }
    return jwt.encode(payload, _secret(), algorithm=JWT_ALGO)


def create_refresh_token(user_id: str) -> str:
    payload = {"sub": user_id, "type": "refresh", "exp": now_utc() + timedelta(days=REFRESH_TTL_DAYS)}
    return jwt.encode(payload, _secret(), algorithm=JWT_ALGO)


def decode_token(token: str) -> dict:
    return jwt.decode(token, _secret(), algorithms=[JWT_ALGO])


def _extract_token(request: Request) -> str | None:
    tok = request.cookies.get("access_token")
    if tok:
        return tok
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None


async def get_current_user(request: Request) -> dict:
    token = _extract_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    db = get_db()
    user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_role(*roles):
    async def _dep(user: dict = Depends(get_current_user)):
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Forbidden — insufficient role")
        return user
    return _dep


async def require_school_active(user: dict = Depends(get_current_user)) -> dict:
    """Enforce that user's school subscription/trial is still valid for ERP access.
    Super admin bypasses this. School admin can still access billing pages even when
    expired (handled at route level via require_role only).
    """
    if user["role"] == "super_admin":
        return user
    db = get_db()
    school = await db.schools.find_one({"id": user["school_id"]}, {"_id": 0})
    if not school:
        raise HTTPException(status_code=403, detail="School not found")
    if school.get("status") in ("suspended", "cancelled"):
        raise HTTPException(status_code=402, detail="School access suspended")
    expiry = school.get("subscription_expires_at")
    if expiry:
        exp_dt = datetime.fromisoformat(expiry)
        if exp_dt < now_utc():
            raise HTTPException(status_code=402, detail="Subscription/trial expired — renewal required")
    return user


def compute_school_status(school: dict) -> dict:
    """Return computed subscription fields for a school doc."""
    exp = school.get("subscription_expires_at")
    now = now_utc()
    days_remaining = 0
    is_trial = school.get("subscription_status") == "trial"
    expired = False
    if exp:
        exp_dt = datetime.fromisoformat(exp)
        delta = exp_dt - now
        days_remaining = max(0, delta.days + (1 if delta.total_seconds() > 0 and delta.seconds > 0 else 0))
        if delta.total_seconds() <= 0:
            expired = True
    status = school.get("subscription_status", "trial")
    if expired and status in ("trial", "active"):
        status = "trial_expired" if is_trial else "expired"
    return {
        "subscription_status_effective": status,
        "days_remaining": days_remaining,
        "is_trial": is_trial,
        "expired": expired,
    }


def set_auth_cookies(response, access: str, refresh: str):
    common = dict(httponly=True, secure=True, samesite="none", path="/")
    response.set_cookie(key="access_token", value=access, max_age=ACCESS_TTL_MIN * 60, **common)
    response.set_cookie(key="refresh_token", value=refresh, max_age=REFRESH_TTL_DAYS * 86400, **common)


def clear_auth_cookies(response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")


def _scrub(v):
    """Recursively strip Mongo _id / ObjectId so audit rows stay JSON-serializable."""
    from bson import ObjectId
    if isinstance(v, dict):
        return {k: _scrub(val) for k, val in v.items() if k != "_id"}
    if isinstance(v, list):
        return [_scrub(x) for x in v]
    if isinstance(v, ObjectId):
        return str(v)
    return v


async def audit(db, *, actor: dict | None, action: str, module: str, school_id: str | None = None,
                record_id: str | None = None, before=None, after=None, ip: str | None = None):
    entry = {
        "id": new_id(),
        "actor_user_id": actor["id"] if actor else None,
        "actor_email": actor["email"] if actor else None,
        "actor_role": actor["role"] if actor else None,
        "school_id": school_id or (actor.get("school_id") if actor else None),
        "action": action,
        "module": module,
        "record_id": record_id,
        "before": _scrub(before),
        "after": _scrub(after),
        "ip": ip,
        "created_at": iso(now_utc()),
    }
    await db.audit_logs.insert_one(entry)
