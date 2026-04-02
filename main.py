from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from db import get_db, init_db
from models import extract_skills_from_jd

app = FastAPI()
templates = Jinja2Templates(directory="templates")

init_db()

def normalize_skill(skill):
    return skill.strip().title()

def get_job_id(topic_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT job_id FROM topics WHERE id=?", (topic_id,))
    result = cur.fetchone()
    return result[0] if result else None

def skill_exists(cur, job_id, skill):
    cur.execute(
        "SELECT 1 FROM topics WHERE job_id=? AND LOWER(topic)=LOWER(?)",
        (job_id, skill)
    )
    return cur.fetchone() is not None

@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cur.fetchone()
    if not user:
        return HTMLResponse("<h3>Invalid credentials</h3>")

    return RedirectResponse(url=f"/dashboard/{user[0]}", status_code=303)

@app.get("/logout")
def logout():
    return RedirectResponse(url="/", status_code=303)

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
def register(username: str = Form(...), password: str = Form(...)):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    if cur.fetchone():
        return HTMLResponse("<h3>User already exists</h3>")

    cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()

    return RedirectResponse(url="/", status_code=303)

@app.get("/dashboard/{user_id}", response_class=HTMLResponse)
def dashboard(request: Request, user_id: int):
    conn = get_db()
    cur = conn.cursor()

    jobs_with_progress = []

    cur.execute("SELECT id, company, role FROM jobs WHERE user_id=?", (user_id,))
    jobs = cur.fetchall()

    for j in jobs:
        job_id = j[0]

        cur.execute("""
        SELECT COUNT(*), SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END)
        FROM topics WHERE job_id=?
        """, (job_id,))
        total, completed = cur.fetchone()

        total = total or 0
        completed = completed or 0
        progress = int((completed / total) * 100) if total > 0 else 0

        jobs_with_progress.append((j[0], j[1], j[2], progress))

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user_id": user_id,
        "jobs": jobs_with_progress
    })


@app.post("/add-job/{user_id}")
def add_job(user_id: int, company: str = Form(...), role: str = Form(...), jd: str = Form(...)):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO jobs (user_id, company, role, jd) VALUES (?, ?, ?, ?)",
        (user_id, company, role, jd)
    )
    conn.commit()

    return RedirectResponse(url=f"/dashboard/{user_id}", status_code=303)

@app.get("/job/{job_id}", response_class=HTMLResponse)
def job_detail(request: Request, job_id: int):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT company, role, jd, user_id FROM jobs WHERE id=?", (job_id,))
    job = cur.fetchone()

    if not job:
        return HTMLResponse("Job not found")

    company, role, jd, user_id = job

    skills = extract_skills_from_jd(jd)

    cur.execute("SELECT id, topic, status, priority FROM topics WHERE job_id=?", (job_id,))
    topics = cur.fetchall()

    if not topics:
        for s in skills:
            clean = normalize_skill(s)
            if not skill_exists(cur, job_id, clean):
                cur.execute(
                    "INSERT INTO topics (job_id, topic) VALUES (?, ?)",
                    (job_id, clean)
                )
        conn.commit()

        cur.execute("SELECT id, topic, status, priority FROM topics WHERE job_id=?", (job_id,))
        topics = cur.fetchall()

    total = len(topics)
    completed = sum(1 for t in topics if t[2] == "completed")
    progress = int((completed / total) * 100) if total > 0 else 0

    return templates.TemplateResponse("job_detail.html", {
        "request": request,
        "job_id": job_id,
        "user_id": user_id,
        "company": company,
        "role": role,
        "jd": jd,
        "topics": topics,
        "progress": progress,
        "completed": completed,
        "total": total,
        "matched": [],
        "missing": []
    })


@app.post("/add-skill/{job_id}")
def add_skill(job_id: int, skill: str = Form(...)):
    conn = get_db()
    cur = conn.cursor()

    clean = normalize_skill(skill)

    if not skill_exists(cur, job_id, clean):
        cur.execute("INSERT INTO topics (job_id, topic) VALUES (?, ?)", (job_id, clean))
        conn.commit()

    return RedirectResponse(url=f"/job/{job_id}", status_code=303)


@app.post("/update-skill/{topic_id}")
def update_skill(topic_id: int, skill: str = Form(...)):
    conn = get_db()
    cur = conn.cursor()

    job_id = get_job_id(topic_id)
    clean = normalize_skill(skill)

    if not skill_exists(cur, job_id, clean):
        cur.execute("UPDATE topics SET topic=? WHERE id=?", (clean, topic_id))
        conn.commit()

    return RedirectResponse(url=f"/job/{job_id}", status_code=303)


@app.post("/delete-skill/{topic_id}")
def delete_skill(topic_id: int):
    conn = get_db()
    cur = conn.cursor()

    job_id = get_job_id(topic_id)

    cur.execute("DELETE FROM topics WHERE id=?", (topic_id,))
    conn.commit()

    return RedirectResponse(url=f"/job/{job_id}", status_code=303)


@app.post("/update-status/{topic_id}")
def update_status(topic_id: int, status: str = Form(...)):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("UPDATE topics SET status=? WHERE id=?", (status, topic_id))
    conn.commit()

    return RedirectResponse(url=f"/job/{get_job_id(topic_id)}", status_code=303)


@app.post("/update-priority/{topic_id}")
def update_priority(topic_id: int, priority: str = Form(...)):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("UPDATE topics SET priority=? WHERE id=?", (priority, topic_id))
    conn.commit()

    return RedirectResponse(url=f"/job/{get_job_id(topic_id)}", status_code=303)


@app.post("/match/{job_id}", response_class=HTMLResponse)
def match(request: Request, job_id: int, resume: str = Form(...)):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT company, role, jd, user_id FROM jobs WHERE id=?", (job_id,))
    company, role, jd, user_id = cur.fetchone()

    cur.execute("SELECT id, topic, status, priority FROM topics WHERE job_id=?", (job_id,))
    topics = cur.fetchall()

    jd_skills = [t[1].lower() for t in topics]
    resume_skills = [s.strip().lower() for s in resume.split(",")]

    matched = [s for s in jd_skills if s in resume_skills]
    missing = [s for s in jd_skills if s not in resume_skills]

    total = len(topics)
    completed = sum(1 for t in topics if t[2] == "completed")
    progress = int((completed / total) * 100) if total > 0 else 0

    return templates.TemplateResponse("job_detail.html", {
        "request": request,
        "job_id": job_id,
        "user_id": user_id,
        "company": company,
        "role": role,
        "jd": jd,
        "topics": topics,
        "progress": progress,
        "completed": completed,
        "total": total,
        "matched": matched,
        "missing": missing
    })