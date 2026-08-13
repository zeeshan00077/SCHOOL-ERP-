"""Pydantic input/output models."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import date


class RegisterSchoolIn(BaseModel):
    school_name: str
    admin_name: str
    admin_email: EmailStr
    admin_phone: str
    password: str = Field(min_length=6)
    city: Optional[str] = None
    address: Optional[str] = None


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class ForgotIn(BaseModel):
    email: EmailStr


class ResetIn(BaseModel):
    token: str
    new_password: str = Field(min_length=6)


class SchoolUpdateIn(BaseModel):
    name: Optional[str] = None
    logo_url: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    principal: Optional[str] = None
    academic_session: Optional[str] = None
    currency: Optional[str] = None
    timezone: Optional[str] = None


class PlanIn(BaseModel):
    name: str
    price: float
    duration_days: int = 365
    max_students: int = 500
    max_teachers: int = 100
    modules: List[str] = []
    is_active: bool = True


class PaymentSubmitIn(BaseModel):
    plan_id: str
    method: str  # bank_transfer | jazzcash | easypaisa | other
    amount: float
    reference_number: str
    payment_date: str  # ISO
    proof_url: Optional[str] = None
    notes: Optional[str] = None


class PaymentDecisionIn(BaseModel):
    remarks: Optional[str] = None


class ClassIn(BaseModel):
    name: str
    order: int = 0


class SectionIn(BaseModel):
    class_id: str
    name: str


class SubjectIn(BaseModel):
    name: str
    code: Optional[str] = None
    class_id: Optional[str] = None


class StudentIn(BaseModel):
    name: str
    admission_number: Optional[str] = None
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    class_id: str
    section_id: Optional[str] = None
    roll_number: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    parent_email: Optional[EmailStr] = None
    parent_name: Optional[str] = None
    parent_phone: Optional[str] = None


class TeacherIn(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    qualification: Optional[str] = None
    subject: Optional[str] = None
    department: Optional[str] = None
    salary: Optional[float] = None
    joining_date: Optional[str] = None
    password: Optional[str] = None


class AttendanceEntry(BaseModel):
    student_id: str
    status: str  # present|absent|late|leave|half


class AttendanceBulkIn(BaseModel):
    class_id: str
    section_id: Optional[str] = None
    date: str  # YYYY-MM-DD
    entries: List[AttendanceEntry]


class FeeStructureIn(BaseModel):
    class_id: str
    name: str
    amount: float
    frequency: str = "monthly"  # monthly|one_time|annual


class FeeInvoiceIn(BaseModel):
    student_id: str
    structure_id: Optional[str] = None
    title: str
    amount: float
    due_date: str
    month: Optional[str] = None  # e.g., "2026-02"


class FeePaymentIn(BaseModel):
    invoice_id: str
    amount: float
    method: str = "cash"
    reference: Optional[str] = None
    paid_on: Optional[str] = None


class ExamIn(BaseModel):
    name: str
    class_id: str
    start_date: str
    end_date: str
    total_marks: int = 100
    passing_marks: int = 40


class MarksBulkIn(BaseModel):
    exam_id: str
    subject_id: str
    marks: List[dict]  # [{student_id, marks_obtained}]


class TimetableEntryIn(BaseModel):
    class_id: str
    section_id: Optional[str] = None
    day: str  # mon|tue|wed|thu|fri|sat
    period: int
    start_time: str  # HH:MM
    end_time: str
    subject_id: Optional[str] = None
    teacher_id: Optional[str] = None
    room: Optional[str] = None


class NoticeIn(BaseModel):
    title: str
    body: str
    audience: str = "all"  # all|teachers|students|parents|class
    class_id: Optional[str] = None
    expires_at: Optional[str] = None


class UserCreateIn(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6)
    role: str  # school_admin|teacher|parent|student|accountant|receptionist|librarian
    phone: Optional[str] = None
