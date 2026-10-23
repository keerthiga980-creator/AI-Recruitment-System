import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "recruitment.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users table (Admin, HR, Candidate)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL, -- 'admin', 'hr', 'candidate'
        location TEXT DEFAULT '',
        created_at TEXT NOT NULL
    )
    """)

    # 2. Candidates table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT DEFAULT '',
        location TEXT DEFAULT '',
        education TEXT DEFAULT '',
        qualification TEXT DEFAULT '',
        skills TEXT DEFAULT '',
        experience TEXT DEFAULT '0-1 Years',
        role_title TEXT DEFAULT 'Job Seeker',
        resume_filename TEXT DEFAULT '',
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    # 3. Jobs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        company TEXT NOT NULL,
        location TEXT NOT NULL,
        job_type TEXT NOT NULL,
        experience TEXT NOT NULL,
        salary TEXT DEFAULT '',
        skills TEXT NOT NULL,
        description TEXT DEFAULT '',
        posted_by TEXT DEFAULT 'recruiter@techcorp.com',
        status TEXT DEFAULT 'Active',
        created_at TEXT NOT NULL
    )
    """)

    # 4. Applications table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        candidate_name TEXT NOT NULL,
        candidate_email TEXT NOT NULL,
        candidate_location TEXT DEFAULT '',
        match_score INTEGER NOT NULL DEFAULT 0,
        matching_skills TEXT DEFAULT '',
        missing_skills TEXT DEFAULT '',
        status TEXT DEFAULT 'Applied', -- 'Applied', 'Under Review', 'Shortlisted', 'Rejected'
        applied_at TEXT NOT NULL,
        FOREIGN KEY (job_id) REFERENCES jobs (id)
    )
    """)

    conn.commit()

    # Pre-seed default data if users table is empty
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]

    if user_count == 0:
        seed_data(cursor)
        conn.commit()

    conn.close()


def seed_data(cursor):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Seed demo users
    demo_users = [
        ("System Admin", "admin@airecruit.com", "admin123", "admin", "Coimbatore"),
        ("Sarah Jenkins", "recruiter@techcorp.com", "hr123", "hr", "Coimbatore"),
        ("Priya S", "priya@gmail.com", "candidate123", "candidate", "Coimbatore"),
        ("Arun K", "arun@gmail.com", "candidate123", "candidate", "Coimbatore"),
        ("Divya R", "divya@gmail.com", "candidate123", "candidate", "Tiruppur"),
        ("Karthik M", "karthik@gmail.com", "candidate123", "candidate", "Chennai"),
        ("Sneha P", "sneha@gmail.com", "candidate123", "candidate", "Coimbatore"),
        ("Rahul S", "rahul@gmail.com", "candidate123", "candidate", "Salem"),
        ("Keerthiga J", "keerthiga@gmail.com", "candidate123", "candidate", "Coimbatore")
    ]

    for name, email, password, role, loc in demo_users:
        cursor.execute("""
            INSERT INTO users (name, email, password, role, location, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, email, password, role, loc, now))

    # Seed candidates
    demo_candidates = [
        ("Priya S", "priya@gmail.com", "+91 98765 43210", "Coimbatore", "B.Tech Information Technology", "First Class with Distinction", "Python, SQL, Django, FastAPI, REST API", "1-3 Years", "Python Developer"),
        ("Arun K", "arun@gmail.com", "+91 98765 43211", "Coimbatore", "M.Sc Artificial Intelligence & Data Science", "First Class", "Python, Machine Learning, NLP, PyTorch, Deep Learning", "1-3 Years", "AI/ML Developer"),
        ("Divya R", "divya@gmail.com", "+91 98765 43212", "Tiruppur", "B.Sc Computer Science", "First Class", "SQL, Excel, Power BI, Python, Data Analytics", "0-1 Years", "Data Analyst"),
        ("Karthik M", "karthik@gmail.com", "+91 98765 43213", "Chennai", "B.E Computer Science & Engineering", "First Class", "Java, SQL, Spring Boot, Hibernate, MySQL", "2-4 Years", "Java Developer"),
        ("Sneha P", "sneha@gmail.com", "+91 98765 43214", "Coimbatore", "B.Sc Information Technology", "Distinction", "Python, Data Analytics, Excel, Tableau, Statistics", "0-1 Years", "Data Analyst"),
        ("Rahul S", "rahul@gmail.com", "+91 98765 43215", "Salem", "B.Tech Artificial Intelligence", "First Class", "Python, AI, Machine Learning, TensorFlow, Computer Vision", "1-2 Years", "AI Developer"),
        ("Keerthiga J", "keerthiga@gmail.com", "+91 98765 43216", "Coimbatore", "B.Sc Computer Science - AI", "Distinction", "SQL, Java, C, HTML, CSS, JavaScript, Python, AI", "Fresher", "Junior Software Developer")
    ]

    for name, email, phone, loc, edu, qual, skills, exp, role_title in demo_candidates:
        cursor.execute("""
            INSERT INTO candidates (name, email, phone, location, education, qualification, skills, experience, role_title, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, email, phone, loc, edu, qual, skills, exp, role_title, now))

    # Seed initial jobs
    demo_jobs = [
        ("Python Developer", "Tech Corp Solutions", "Coimbatore", "Full Time", "1-3 Years", "₹5 - ₹8 LPA", "Python, SQL, Django, FastAPI", "Looking for a backend developer skilled in Python and FastAPI to build scalable REST services.", "recruiter@techcorp.com"),
        ("AI/ML Engineer", "Innovate AI Labs", "Coimbatore", "Full Time", "1-3 Years", "₹7 - ₹12 LPA", "Python, Machine Learning, NLP, PyTorch, Deep Learning", "Seeking an AI engineer to develop intelligent automation and NLP models.", "recruiter@techcorp.com"),
        ("Data Analyst", "Apex Analytics", "Tiruppur", "Full Time", "0-2 Years", "₹4 - ₹6 LPA", "SQL, Excel, Power BI, Python, Data Analytics", "Analyze business metrics, build dashboards, and provide actionable business insights.", "recruiter@techcorp.com"),
        ("Java Backend Developer", "CloudSoft Technologies", "Chennai", "Full Time", "2-4 Years", "₹6 - ₹10 LPA", "Java, SQL, Spring Boot, Hibernate, MySQL", "Develop robust enterprise microservices using Java Spring Boot.", "recruiter@techcorp.com"),
        ("Junior Software Developer", "NextGen Infotech", "Chennai", "Full Time", "Fresher", "₹3.5 - ₹5 LPA", "Java, Python, SQL, HTML, CSS, JavaScript", "Entry level opening for freshers with good problem-solving and programming fundamentals.", "recruiter@techcorp.com"),
        ("AI Intern", "FutureTech AI", "Coimbatore", "Internship", "Fresher", "₹15,000 / month", "Python, AI, Machine Learning", "Hands-on internship working with cutting-edge computer vision and NLP models.", "recruiter@techcorp.com")
    ]

    for title, comp, loc, jtype, exp, sal, skills, desc, posted_by in demo_jobs:
        cursor.execute("""
            INSERT INTO jobs (title, company, location, job_type, experience, salary, skills, description, posted_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, comp, loc, jtype, exp, sal, skills, desc, posted_by, now))

    # Seed a few initial applications
    demo_apps = [
        (1, "Priya S", "priya@gmail.com", "Coimbatore", 94, "Python, SQL, Django, FastAPI", "", "Shortlisted"),
        (2, "Arun K", "arun@gmail.com", "Coimbatore", 92, "Python, Machine Learning, NLP, PyTorch", "", "Under Review"),
        (3, "Divya R", "divya@gmail.com", "Tiruppur", 88, "SQL, Excel, Power BI, Python", "", "Applied")
    ]

    for jid, cname, cmail, cloc, mscore, mskills, misskills, status in demo_apps:
        cursor.execute("""
            INSERT INTO applications (job_id, candidate_name, candidate_email, candidate_location, match_score, matching_skills, missing_skills, status, applied_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (jid, cname, cmail, cloc, mscore, mskills, misskills, status, now))
