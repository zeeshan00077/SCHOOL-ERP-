"""Seed super admin, default subscription plan, and demo schools."""
import os
from datetime import timedelta
from db import get_db, hash_password, now_utc, iso, new_id


async def seed_all():
    db = get_db()
    await _seed_super_admin(db)
    await _seed_default_plan(db)
    await _seed_demo_schools(db)


async def _seed_super_admin(db):
    email = os.environ["SUPER_ADMIN_EMAIL"].lower()
    pw = os.environ["SUPER_ADMIN_PASSWORD"]
    name = os.environ.get("SUPER_ADMIN_NAME", "Super Admin")
    existing = await db.users.find_one({"email": email})
    if not existing:
        await db.users.insert_one({
            "id": new_id(), "email": email, "name": name, "role": "super_admin",
            "school_id": None, "password_hash": hash_password(pw),
            "created_at": iso(now_utc()),
        })


async def _seed_default_plan(db):
    if await db.subscription_plans.count_documents({}) == 0:
        await db.subscription_plans.insert_many([
            {"id": new_id(), "name": "Annual School Plan",
             "price": float(os.environ.get("DEFAULT_PLAN_PRICE", 25000)),
             "duration_days": 365, "max_students": 500, "max_teachers": 100,
             "modules": ["Students", "Teachers", "Attendance", "Fees", "Exams",
                         "Timetable", "Notices"],
             "is_active": True, "created_at": iso(now_utc())},
            {"id": new_id(), "name": "Enterprise Plan",
             "price": 75000.0, "duration_days": 365, "max_students": 5000,
             "max_teachers": 500, "modules": ["All Modules"],
             "is_active": True, "created_at": iso(now_utc())},
        ])


async def _seed_demo_schools(db):
    if await db.schools.count_documents({}) > 0:
        return
    trial_days = int(os.environ.get("TRIAL_DAYS", 7))
    demos = [
        {
            "name": "Green Valley Public School",
            "admin_email": "admin@greenvalley.edu",
            "admin_name": "Ahmed Khan",
            "days_ago": 0,  # fresh trial
            "city": "Lahore",
            "logo_hue": "emerald",
            "teacher_email": "teacher@greenvalley.edu",
            "teacher_name": "Fatima Riaz",
            "parent_email": "parent@greenvalley.edu",
            "parent_name": "Muhammad Aslam",
            "student_email": "student@greenvalley.edu",
            "student_name": "Ali Aslam",
        },
        {
            "name": "Iqra Model Academy",
            "admin_email": "admin@iqra.edu",
            "admin_name": "Sadia Malik",
            "days_ago": 4,  # trial ending soon
            "city": "Karachi",
            "logo_hue": "amber",
            "teacher_email": "teacher@iqra.edu",
            "teacher_name": "Zubair Ahmad",
        },
    ]
    for d in demos:
        registered_at = now_utc() - timedelta(days=d["days_ago"])
        trial_expiry = registered_at + timedelta(days=trial_days)
        school_id = new_id()
        await db.schools.insert_one({
            "id": school_id, "name": d["name"], "city": d["city"],
            "admin_email": d["admin_email"], "admin_name": d["admin_name"],
            "logo_url": None, "address": f"{d['city']}, Pakistan",
            "phone": "+92-300-0000000", "email": d["admin_email"],
            "website": None, "principal": d["admin_name"],
            "academic_session": "2025-2026", "currency": "PKR",
            "timezone": "Asia/Karachi",
            "status": "active",
            "subscription_status": "trial",
            "subscription_expires_at": iso(trial_expiry),
            "current_plan_id": None,
            "is_demo": True, "created_at": iso(registered_at),
        })
        # school admin
        admin_id = new_id()
        await db.users.insert_one({
            "id": admin_id, "email": d["admin_email"], "name": d["admin_name"],
            "role": "school_admin", "school_id": school_id,
            "password_hash": hash_password("School@123"),
            "phone": "+92-300-1111111", "created_at": iso(registered_at),
        })
        # teacher
        teacher_user_id = new_id()
        await db.users.insert_one({
            "id": teacher_user_id, "email": d["teacher_email"], "name": d["teacher_name"],
            "role": "teacher", "school_id": school_id,
            "password_hash": hash_password("Teacher@123"),
            "created_at": iso(registered_at),
        })
        teacher_id = new_id()
        await db.teachers.insert_one({
            "id": teacher_id, "school_id": school_id, "user_id": teacher_user_id,
            "employee_id": f"EMP-{int(registered_at.timestamp())}",
            "name": d["teacher_name"], "email": d["teacher_email"],
            "phone": "+92-300-2222222", "qualification": "M.A. Education",
            "subject": "Mathematics", "department": "Academics",
            "salary": 45000, "status": "active",
            "created_at": iso(registered_at),
        })
        # classes
        class_ids = {}
        for i, cname in enumerate(["Class 6", "Class 7", "Class 8"]):
            cid = new_id()
            await db.classes.insert_one({"id": cid, "school_id": school_id, "name": cname,
                                         "order": i, "created_at": iso(registered_at)})
            class_ids[cname] = cid
            for sec in ["A", "B"]:
                await db.sections.insert_one({"id": new_id(), "school_id": school_id,
                                              "class_id": cid, "name": sec})
        # subjects
        subj_ids = {}
        for sname in ["English", "Urdu", "Mathematics", "Science", "Islamic Studies"]:
            sid_ = new_id()
            await db.subjects.insert_one({"id": sid_, "school_id": school_id, "name": sname,
                                          "code": sname[:3].upper()})
            subj_ids[sname] = sid_
        # parent + student for school A only
        if d.get("parent_email"):
            parent_id = new_id()
            await db.users.insert_one({
                "id": parent_id, "email": d["parent_email"], "name": d["parent_name"],
                "role": "parent", "school_id": school_id,
                "password_hash": hash_password("Parent@123"),
                "created_at": iso(registered_at),
            })
            # student user account
            student_user_id = new_id()
            await db.users.insert_one({
                "id": student_user_id, "email": d["student_email"], "name": d["student_name"],
                "role": "student", "school_id": school_id,
                "password_hash": hash_password("Student@123"),
                "created_at": iso(registered_at),
            })
            student_id = new_id()
            await db.students.insert_one({
                "id": student_id, "school_id": school_id, "name": d["student_name"],
                "admission_number": "ADM-1001", "father_name": d["parent_name"],
                "mother_name": "Ayesha Aslam", "dob": "2012-05-15", "gender": "male",
                "class_id": class_ids["Class 7"], "roll_number": "01",
                "phone": "+92-300-3333333", "address": "Lahore",
                "parent_id": parent_id, "user_id": student_user_id,
                "status": "active", "created_at": iso(registered_at),
            })
        # sprinkle 12 more students in Green Valley, 8 in Iqra
        n_more = 12 if d["name"].startswith("Green") else 8
        first_names = ["Bilal", "Sara", "Umair", "Hira", "Fahad", "Nida", "Kamran",
                       "Zainab", "Hasan", "Iqra", "Owais", "Rida", "Talha", "Amna"]
        for i in range(n_more):
            fname = first_names[i % len(first_names)]
            cname = list(class_ids.keys())[i % 3]
            await db.students.insert_one({
                "id": new_id(), "school_id": school_id, "name": f"{fname} Ahmed",
                "admission_number": f"ADM-{2000+i}", "father_name": "Ahmed Khan",
                "class_id": class_ids[cname], "roll_number": f"{i+2:02d}",
                "gender": "male" if i % 2 == 0 else "female",
                "status": "active", "created_at": iso(registered_at),
            })
        # fee structure
        for cname, cid in class_ids.items():
            await db.fee_structures.insert_one({"id": new_id(), "school_id": school_id,
                                                "class_id": cid, "name": "Monthly Tuition",
                                                "amount": 3500 if "6" in cname else (4000 if "7" in cname else 4500),
                                                "frequency": "monthly",
                                                "created_at": iso(registered_at)})
        # a notice
        await db.notices.insert_one({"id": new_id(), "school_id": school_id,
                                     "title": "Welcome to the new session!",
                                     "body": "Classes resume on Monday. Please ensure uniforms and books are ready.",
                                     "audience": "all",
                                     "created_by": admin_id, "created_by_name": d["admin_name"],
                                     "created_at": iso(registered_at)})
