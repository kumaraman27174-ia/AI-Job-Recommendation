from flask import Flask, render_template, request, redirect, session, url_for, flash
import os
from werkzeug.utils import secure_filename

from db import get_db
from services.resume_parser import extract_text, extract_skills, detect_domain
from scraper.sarkari_scraper import get_sarkari_jobs
from providers.adzuna_api import get_adzuna_jobs
from providers.indeed_api import get_indeed_jobs
from services.ai_matcher import match_jobs_advanced, normalize_jobs, split_private_and_internship_jobs

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def ensure_profile_columns():
    """Add new dashboard columns automatically if old database.sql was already imported."""
    db = get_db()
    cursor = db.cursor()
    columns = {
        "age": "INT",
        "phone": "VARCHAR(20)",
        "gender": "VARCHAR(20)",
        "location": "VARCHAR(100)",
        "hobby": "TEXT",
        "preferred_job_type": "VARCHAR(50)",
        "experience_level": "VARCHAR(50)",
        "skills_text": "TEXT"
    }
    for col, col_type in columns.items():
        try:
            cursor.execute(f"ALTER TABLE profile ADD COLUMN {col} {col_type}")
            db.commit()
        except Exception:
            db.rollback()


def get_registered_user_count():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        result = cursor.fetchone()
        return result[0] if result else 0
    except Exception:
        return 0


@app.route("/")
def home():
    user_count = get_registered_user_count()
    return render_template("index.html", user_count=user_count)


# ================= AUTH =================

@app.route("/signup", methods=["POST"])
def signup():
    email = request.form["email"]
    password = request.form["password"]

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    if cursor.fetchone():
        flash("Already registered")
        return redirect("/")

    cursor.execute("INSERT INTO users (email,password) VALUES (%s,%s)", (email,password))
    db.commit()
    return redirect("/")


@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s",(email,password))
    user = cursor.fetchone()

    if not user:
        flash("Wrong credentials")
        return redirect("/")

    session["user"] = email
    return redirect("/dashboard")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully")
    return redirect("/")


# ================= DASHBOARD =================

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    ensure_profile_columns()

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM profile WHERE email=%s",(session["user"],))
    profile = cursor.fetchone()
    is_update = True if profile else False

    return render_template("dashboard.html", profile=profile, is_update=is_update)


# ================= PROFILE =================

@app.route("/profile", methods=["POST"])
def profile():
    if "user" not in session:
        return redirect("/")

    ensure_profile_columns()

    email = session["user"]

    name = request.form["name"]
    age = request.form["age"]
    qualification = request.form["qualification"]
    phone = request.form["phone"]
    gender = request.form["gender"]
    location = request.form["location"]
    hobby = request.form.get("hobby", "")
    preferred_job_type = request.form.get("preferred_job_type", "")
    experience_level = request.form.get("experience_level", "")
    skills_text = request.form.get("skills_text", "")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM profile WHERE email=%s", (email,))
    old_profile = cursor.fetchone()

    file = request.files.get("resume")
    resume_path = old_profile["resume"] if old_profile and old_profile.get("resume") else None

    if file and file.filename:
        if resume_path and os.path.exists(resume_path):
            try:
                os.remove(resume_path)
            except Exception:
                pass

        filename = secure_filename(file.filename)
        resume_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(resume_path)
    elif not resume_path:
        flash("Please upload resume")
        return redirect("/dashboard")

    text = extract_text(resume_path)
    resume_skills = extract_skills(text)
    manual_skills = [s.strip() for s in skills_text.split(",") if s.strip()]
    skills = list(dict.fromkeys(resume_skills + manual_skills))
    domain = detect_domain(skills, qualification)

    session["skills"] = skills
    session["domain"] = domain

    cursor = db.cursor()
    cursor.execute("DELETE FROM profile WHERE email=%s", (email,))
    cursor.execute("""
        INSERT INTO profile(
            email, name, age, qualification, phone, gender, location, hobby,
            preferred_job_type, experience_level, skills_text, resume
        )
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        email, name, age, qualification, phone, gender, location, hobby,
        preferred_job_type, experience_level, skills_text, resume_path
    ))
    db.commit()

    return redirect("/jobs")


# ================= JOBS =================

@app.route("/jobs")
def jobs():
    skills = session.get("skills", [])
    domain = session.get("domain", "General")

    sarkari = normalize_jobs(get_sarkari_jobs(),"Govt")

    # Fetch private jobs + internships from both APIs
    adzuna_jobs = normalize_jobs(get_adzuna_jobs(domain), "Adzuna")
    jsearch_jobs = normalize_jobs(get_indeed_jobs(domain), "JSearch")

    # Extra internship searches so internship section gets better results
    adzuna_internships = normalize_jobs(get_adzuna_jobs(domain + " internship"), "Adzuna")
    jsearch_internships = normalize_jobs(get_indeed_jobs(domain + " internship"), "JSearch")

    all_api_jobs = adzuna_jobs + jsearch_jobs + adzuna_internships + jsearch_internships
    private, internships = split_private_and_internship_jobs(all_api_jobs)

    govt_jobs = match_jobs_advanced(skills, sarkari, "Government")
    private_jobs = match_jobs_advanced(skills, private, domain)
    internship_jobs = match_jobs_advanced(skills, internships, domain)

    return render_template(
        "jobs.html",
        govt_jobs=govt_jobs,
        private_jobs=private_jobs,
        internship_jobs=internship_jobs,
        domain=domain,
        preferred_job_type="Government / Private / Internship",
        username=session.get("user")
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
