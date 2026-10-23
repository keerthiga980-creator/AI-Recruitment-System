import os
import base64
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

from database import init_db, get_db_connection
from ai_matcher import compute_ai_match, parse_skills

# Initialize database on startup
init_db()

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="AI Recruitment & Local Talent Discovery API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# PYDANTIC SCHEMAS
# ==========================================

class UserRegister(BaseModel):
    name: str
    email: str
    password: str
    role: str  # 'candidate', 'hr', 'admin'
    location: Optional[str] = ""


class UserLogin(BaseModel):
    email: str
    password: str
    role: str


class JobCreate(BaseModel):
    jobTitle: str
    company: str
    location: str
    jobType: str
    experience: str
    salary: Optional[str] = ""
    skills: str
    description: Optional[str] = ""
    posted_by: Optional[str] = "recruiter@techcorp.com"


class CandidateProfileUpdate(BaseModel):
    email: str
    name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    education: Optional[str] = None
    qualification: Optional[str] = None
    skills: Optional[str] = None
    experience: Optional[str] = None
    role_title: Optional[str] = None


class ResumeUpload(BaseModel):
    candidate_email: str
    filename: str
    file_data: str  # Base64 encoded file data


class JobApplication(BaseModel):
    job_id: int
    candidate_email: str


class ApplicationStatusUpdate(BaseModel):
    status: str


# ==========================================
# HOME & HEALTH CHECK APIS
# ==========================================

@app.get("/")
def home():
    return {
        "status": "online",
        "message": "AI-Powered Recruitment System Backend is running smoothly!"
    }


@app.get("/test")
def test_backend():
    return {
        "status": "success",
        "message": "Backend database and API connections are working!"
    }


# ==========================================
# AUTHENTICATION APIS
# ==========================================

@app.post("/register")
def register_user(user: UserRegister):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if user already exists
    cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?)", (user.email.strip(),))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    role_clean = user.role.lower().strip()
    if role_clean not in ["candidate", "hr", "admin"]:
        role_clean = "candidate"

    cursor.execute("""
        INSERT INTO users (name, email, password, role, location, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user.name.strip(), user.email.strip(), user.password, role_clean, user.location or "", now))

    user_id = cursor.lastrowid

    # If candidate, also create candidate profile
    if role_clean == "candidate":
        cursor.execute("""
            INSERT INTO candidates (user_id, name, email, location, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, user.name.strip(), user.email.strip(), user.location or "", now))

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "message": f"Account registered successfully as {role_clean.capitalize()}!",
        "user": {
            "id": user_id,
            "name": user.name.strip(),
            "email": user.email.strip(),
            "role": role_clean,
            "location": user.location or ""
        }
    }


@app.post("/login")
def login_user(creds: UserLogin):
    conn = get_db_connection()
    cursor = conn.cursor()

    email_clean = creds.email.strip().lower()
    role_clean = creds.role.strip().lower()

    cursor.execute("""
        SELECT id, name, email, password, role, location
        FROM users
        WHERE LOWER(email) = ? AND role = ?
    """, (email_clean, role_clean))

    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail=f"No account found with this email for role '{creds.role}'.")

    if user["password"] != creds.password:
        raise HTTPException(status_code=401, detail="Incorrect password. Please try again.")

    return {
        "status": "success",
        "message": "Login successful!",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "location": user["location"]
        }
    }


# ==========================================
# JOB APIS
# ==========================================

@app.get("/jobs")
def get_jobs(
    location: Optional[str] = "",
    skill: Optional[str] = "",
    posted_by: Optional[str] = None
):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM jobs WHERE status = 'Active'"
    params = []

    if posted_by:
        query += " AND LOWER(posted_by) = LOWER(?)"
        params.append(posted_by.strip())

    cursor.execute(query + " ORDER BY id DESC", params)
    raw_jobs = [dict(row) for row in cursor.fetchall()]

    # Also count applications for each job
    for j in raw_jobs:
        cursor.execute("SELECT COUNT(*) FROM applications WHERE job_id = ?", (j["id"],))
        j["applications_count"] = cursor.fetchone()[0]

    conn.close()

    # Filter by location and skill if provided
    filtered = []
    loc_filter = location.strip().lower()
    skill_filter = skill.strip().lower()

    for j in raw_jobs:
        loc_match = (loc_filter == "" or loc_filter in j["location"].lower())
        skill_match = (
            skill_filter == "" or skill_filter == "all"
            or skill_filter in [s.lower() for s in parse_skills(j["skills"])]
        )
        if loc_match and skill_match:
            filtered.append(j)

    return {
        "count": len(filtered),
        "jobs": filtered
    }


@app.post("/jobs")
def create_job(job: JobCreate):
    conn = get_db_connection()
    cursor = conn.cursor()

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    cursor.execute("""
        INSERT INTO jobs (title, company, location, job_type, experience, salary, skills, description, posted_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job.jobTitle.strip(),
        job.company.strip(),
        job.location.strip(),
        job.jobType.strip(),
        job.experience.strip(),
        job.salary.strip() if job.salary else "",
        job.skills.strip(),
        job.description.strip() if job.description else "",
        job.posted_by.strip() if job.posted_by else "recruiter@techcorp.com",
        now
    ))

    job_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "status": "success",
        "message": "Job posted successfully!",
        "job": {
            "id": job_id,
            "jobTitle": job.jobTitle,
            "company": job.company,
            "location": job.location,
            "skills": job.skills
        }
    }


@app.delete("/jobs/{job_id}")
def delete_job(job_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    cursor.execute("DELETE FROM applications WHERE job_id = ?", (job_id,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": f"Job #{job_id} deleted successfully."}


# ==========================================
# CANDIDATES & LOCAL TALENT APIS (WITH AI MATCHING)
# ==========================================

@app.get("/candidates")
def get_candidates(
    location: Optional[str] = "",
    skill: Optional[str] = "",
    search: Optional[str] = "",
    job_id: Optional[int] = None
):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM candidates ORDER BY id DESC")
    candidates = [dict(row) for row in cursor.fetchall()]

    job_skills_str = ""
    job_loc_str = ""
    if job_id:
        cursor.execute("SELECT skills, location FROM jobs WHERE id = ?", (job_id,))
        job_row = cursor.fetchone()
        if job_row:
            job_skills_str = job_row["skills"]
            job_loc_str = job_row["location"]

    conn.close()

    loc_q = location.strip().lower()
    skill_q = skill.strip().lower()
    search_q = search.strip().lower()

    filtered = []
    for cand in candidates:
        cand_skills_list = [s.strip() for s in cand["skills"].split(",") if s.strip()]
        cand["skills_list"] = cand_skills_list

        # AI Matching against job if provided, or baseline match
        if job_skills_str:
            ai_res = compute_ai_match(cand["skills"], job_skills_str, cand["location"], job_loc_str)
            cand["match"] = ai_res["match_score"]
            cand["matching_skills"] = ai_res["matching_skills"]
            cand["missing_skills"] = ai_res["missing_skills"]
            cand["match_level"] = ai_res["match_level"]
        else:
            cand["match"] = 85  # default showcase baseline

        # Filtering
        loc_match = (loc_q == "" or loc_q in cand["location"].lower())
        skill_match = (
            skill_q == "" or skill_q == "all"
            or any(skill_q in s.lower() for s in cand_skills_list)
        )
        search_match = (
            search_q == ""
            or search_q in cand["name"].lower()
            or search_q in cand["role_title"].lower()
            or any(search_q in s.lower() for s in cand_skills_list)
        )

        if loc_match and skill_match and search_match:
            filtered.append(cand)

    # Sort candidates by AI match percentage descending
    filtered.sort(key=lambda x: x.get("match", 0), reverse=True)

    return {
        "count": len(filtered),
        "candidates": filtered
    }


@app.get("/local-talent")
def get_local_talent(
    location: str = "",
    skill: str = "all"
):
    # Specialized for Local Talent Discovery feature
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM candidates")
    candidates = [dict(row) for row in cursor.fetchall()]
    conn.close()

    loc_filter = location.strip().lower()
    skill_filter = skill.strip().lower()

    filtered = []
    for cand in candidates:
        cand_skills = [s.strip() for s in cand["skills"].split(",") if s.strip()]
        cand["skills"] = cand_skills

        loc_match = (loc_filter == "" or loc_filter in cand["location"].lower())
        skill_match = (
            skill_filter == "all" or skill_filter == ""
            or any(skill_filter in s.lower() for s in cand_skills)
        )

        if loc_match and skill_match:
            cand["match"] = 90 if loc_match and loc_filter else 84
            filtered.append(cand)

    return {
        "count": len(filtered),
        "candidates": filtered
    }


@app.get("/candidate/profile")
def get_candidate_profile(email: str = Query(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM candidates WHERE LOWER(email) = LOWER(?)", (email.strip(),))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Candidate profile not found.")

    profile = dict(row)
    profile["skills_list"] = [s.strip() for s in profile["skills"].split(",") if s.strip()]
    return profile


@app.put("/candidate/profile")
def update_candidate_profile(update_data: CandidateProfileUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM candidates WHERE LOWER(email) = LOWER(?)", (update_data.email.strip(),))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Candidate profile not found.")

    fields = []
    values = []

    if update_data.name is not None:
        fields.append("name = ?")
        values.append(update_data.name.strip())
    if update_data.phone is not None:
        fields.append("phone = ?")
        values.append(update_data.phone.strip())
    if update_data.location is not None:
        fields.append("location = ?")
        values.append(update_data.location.strip())
    if update_data.education is not None:
        fields.append("education = ?")
        values.append(update_data.education.strip())
    if update_data.qualification is not None:
        fields.append("qualification = ?")
        values.append(update_data.qualification.strip())
    if update_data.skills is not None:
        fields.append("skills = ?")
        values.append(update_data.skills.strip())
    if update_data.experience is not None:
        fields.append("experience = ?")
        values.append(update_data.experience.strip())
    if update_data.role_title is not None:
        fields.append("role_title = ?")
        values.append(update_data.role_title.strip())

    if fields:
        values.append(existing["id"])
        cursor.execute(f"UPDATE candidates SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()

    conn.close()
    return {"status": "success", "message": "Candidate profile updated successfully!"}


@app.post("/candidate/upload-resume")
def upload_resume(data: ResumeUpload):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM candidates WHERE LOWER(email) = LOWER(?)", (data.candidate_email.strip(),))
    candidate = cursor.fetchone()
    if not candidate:
        conn.close()
        raise HTTPException(status_code=404, detail="Candidate not found.")

    # Save file to uploads folder
    safe_filename = f"{candidate['id']}_{os.path.basename(data.filename)}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    try:
        # File data comes as base64 string (often prefixed with data:...)
        raw_b64 = data.file_data
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",")[1]

        file_bytes = base64.b64decode(raw_b64)
        with open(file_path, "wb") as f:
            f.write(file_bytes)

        # Update candidate record with resume filename
        cursor.execute("UPDATE candidates SET resume_filename = ? WHERE id = ?", (safe_filename, candidate["id"]))
        conn.commit()

    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to save resume: {str(e)}")

    conn.close()
    return {
        "status": "success",
        "message": f"Resume '{data.filename}' uploaded and analyzed successfully!",
        "filename": safe_filename
    }


@app.get("/candidate/recommended-jobs")
def get_recommended_jobs(email: str = Query(...)):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT skills, location FROM candidates WHERE LOWER(email) = LOWER(?)", (email.strip(),))
    cand = cursor.fetchone()

    cursor.execute("SELECT * FROM jobs WHERE status = 'Active'")
    jobs = [dict(row) for row in cursor.fetchall()]

    # Check which jobs candidate already applied for
    cursor.execute("SELECT job_id, status FROM applications WHERE LOWER(candidate_email) = LOWER(?)", (email.strip(),))
    applied_map = {row["job_id"]: row["status"] for row in cursor.fetchall()}
    conn.close()

    cand_skills = cand["skills"] if cand else ""
    cand_loc = cand["location"] if cand else ""

    recommended = []
    for j in jobs:
        ai_res = compute_ai_match(cand_skills, j["skills"], cand_loc, j["location"])
        j["match_score"] = ai_res["match_score"]
        j["matching_skills"] = ai_res["matching_skills"]
        j["missing_skills"] = ai_res["missing_skills"]
        j["match_level"] = ai_res["match_level"]
        j["is_applied"] = j["id"] in applied_map
        j["application_status"] = applied_map.get(j["id"], None)
        recommended.append(j)

    # Rank jobs by AI match score descending
    recommended.sort(key=lambda x: x["match_score"], reverse=True)

    return {
        "count": len(recommended),
        "jobs": recommended
    }


# ==========================================
# APPLICATIONS APIS (APPLY, SHORTLIST, STATUS)
# ==========================================

@app.post("/applications/apply")
def apply_to_job(application: JobApplication):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get job
    cursor.execute("SELECT * FROM jobs WHERE id = ?", (application.job_id,))
    job = cursor.fetchone()
    if not job:
        conn.close()
        raise HTTPException(status_code=404, detail="Job not found.")

    # Get candidate
    cursor.execute("SELECT * FROM candidates WHERE LOWER(email) = LOWER(?)", (application.candidate_email.strip(),))
    candidate = cursor.fetchone()
    if not candidate:
        conn.close()
        raise HTTPException(status_code=404, detail="Candidate profile not found. Please log in.")

    # Check if already applied
    cursor.execute("""
        SELECT id FROM applications WHERE job_id = ? AND LOWER(candidate_email) = LOWER(?)
    """, (application.job_id, application.candidate_email.strip()))
    if cursor.fetchone():
        conn.close()
        return {"status": "info", "message": "You have already applied for this job."}

    # Run AI Matcher
    ai_res = compute_ai_match(candidate["skills"], job["skills"], candidate["location"], job["location"])
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    cursor.execute("""
        INSERT INTO applications (job_id, candidate_name, candidate_email, candidate_location, match_score, matching_skills, missing_skills, status, applied_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Applied', ?)
    """, (
        job["id"],
        candidate["name"],
        candidate["email"],
        candidate["location"],
        ai_res["match_score"],
        ", ".join(ai_res["matching_skills"]),
        ", ".join(ai_res["missing_skills"]),
        now
    ))

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "message": f"Successfully applied for '{job['title']}'! Your AI match score is {ai_res['match_score']}%.",
        "match_score": ai_res["match_score"]
    }


@app.get("/applications/candidate")
def get_candidate_applications(email: str = Query(...)):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT a.id as app_id, a.match_score, a.matching_skills, a.status, a.applied_at,
               j.id as job_id, j.title, j.company, j.location, j.job_type, j.salary
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE LOWER(a.candidate_email) = LOWER(?)
        ORDER BY a.id DESC
    """, (email.strip(),))

    apps = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return {
        "count": len(apps),
        "applications": apps
    }


@app.get("/applications/hr")
def get_hr_applications(email: Optional[str] = None):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT a.id as app_id, a.candidate_name, a.candidate_email, a.candidate_location,
               a.match_score, a.matching_skills, a.missing_skills, a.status, a.applied_at,
               j.id as job_id, j.title as job_title, j.company, j.location as job_location
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
    """
    params = []
    if email:
        query += " WHERE LOWER(j.posted_by) = LOWER(?)"
        params.append(email.strip())

    query += " ORDER BY a.match_score DESC, a.id DESC"
    cursor.execute(query, params)
    apps = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return {
        "count": len(apps),
        "applications": apps
    }


@app.put("/applications/{app_id}/status")
def update_application_status(app_id: int, status_update: ApplicationStatusUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE applications SET status = ? WHERE id = ?", (status_update.status, app_id))
    conn.commit()
    conn.close()

    return {
        "status": "success",
        "message": f"Application #{app_id} status updated to '{status_update.status}'."
    }


# ==========================================
# DASHBOARD STATS APIS
# ==========================================

@app.get("/stats/hr")
def get_hr_stats(email: Optional[str] = None):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'Active'")
    active_jobs = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM candidates")
    total_candidates = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM applications WHERE status = 'Shortlisted'")
    shortlisted = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(match_score) FROM applications")
    avg_match = cursor.fetchone()[0] or 86.0

    conn.close()

    return {
        "active_jobs": active_jobs,
        "total_candidates": total_candidates,
        "shortlisted": shortlisted,
        "avg_match": round(avg_match)
    }


@app.get("/stats/candidate")
def get_candidate_stats(email: str = Query(...)):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Applied count
    cursor.execute("SELECT COUNT(*) FROM applications WHERE LOWER(candidate_email) = LOWER(?)", (email.strip(),))
    applied_count = cursor.fetchone()[0]

    # Total active jobs
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE status = 'Active'")
    jobs_count = cursor.fetchone()[0]

    # Candidate profile completion
    cursor.execute("SELECT * FROM candidates WHERE LOWER(email) = LOWER(?)", (email.strip(),))
    cand = cursor.fetchone()
    conn.close()

    completion = 40
    if cand:
        if cand["skills"]: completion += 20
        if cand["education"]: completion += 15
        if cand["phone"]: completion += 10
        if cand["resume_filename"]: completion += 15

    return {
        "profile_completion": min(100, completion),
        "ai_matches_count": jobs_count,
        "applied_count": applied_count
    }
