"""Secure file upload + serve for student photos (and future asset types).

- Files live under /app/backend/uploads/{school_id}/{uuid}.{ext}
- Upload is authenticated; caller's school_id enforces tenancy
- Download is authenticated; user must belong to same school (super_admin bypasses)
- MIME + extension + max-size validation via Pillow (photos only for now)
"""
import os
from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from PIL import Image
import io

from db import get_db, get_current_user, require_school_active, new_id, now_utc, iso, audit

router = APIRouter(prefix="/api/school", tags=["uploads"])

UPLOAD_DIR = Path("/app/backend/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_PHOTO_MIME = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}
MAX_PHOTO_BYTES = 3 * 1024 * 1024  # 3 MB


def _validate_image(raw: bytes) -> str:
    if len(raw) > MAX_PHOTO_BYTES:
        raise HTTPException(400, "Photo exceeds 3 MB size limit")
    try:
        im = Image.open(io.BytesIO(raw))
        im.verify()
    except Exception:
        raise HTTPException(400, "Uploaded file is not a valid image")
    fmt = (im.format or "").lower()
    mime = f"image/{fmt}"
    if mime not in ALLOWED_PHOTO_MIME:
        raise HTTPException(400, f"Unsupported image format: {fmt}")
    return "." + ("jpg" if fmt == "jpeg" else fmt)


@router.post("/uploads/photo")
async def upload_photo(file: UploadFile = File(...), user=Depends(require_school_active)):
    if user["role"] not in ("school_admin", "teacher", "receptionist", "accountant"):
        raise HTTPException(403, "Not allowed to upload photos")
    if not user.get("school_id"):
        raise HTTPException(400, "No school context")
    raw = await file.read()
    ext = _validate_image(raw)

    school_dir = UPLOAD_DIR / user["school_id"]
    school_dir.mkdir(parents=True, exist_ok=True)
    file_id = uuid4().hex + ext
    dest = school_dir / file_id
    with open(dest, "wb") as f:
        f.write(raw)

    db = get_db()
    rec = {"id": new_id(), "school_id": user["school_id"], "file_id": file_id,
           "size": len(raw), "content_type": file.content_type,
           "uploaded_by": user["id"], "created_at": iso(now_utc())}
    await db.uploads.insert_one(rec)
    await audit(db, actor=user, action="upload_photo", module="uploads", record_id=file_id)
    # URL served by our own authenticated endpoint
    return {"file_id": file_id, "url": f"/api/school/uploads/{file_id}"}


@router.get("/uploads/{file_id}")
async def serve_upload(file_id: str, user=Depends(get_current_user)):
    # Basic path safety
    if "/" in file_id or ".." in file_id:
        raise HTTPException(400, "Invalid file id")
    # Super admin can access any file; find owning school
    db = get_db()
    rec = await db.uploads.find_one({"file_id": file_id}, {"_id": 0})
    if not rec:
        raise HTTPException(404, "Not found")
    if user["role"] != "super_admin" and rec["school_id"] != user.get("school_id"):
        raise HTTPException(404, "Not found")
    path = UPLOAD_DIR / rec["school_id"] / file_id
    if not path.exists():
        raise HTTPException(404, "File missing on disk")
    return FileResponse(str(path), media_type=rec.get("content_type") or "image/jpeg")
