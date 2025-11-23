import os
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from . import crud, database, models

app = FastAPI()

# --- Static files setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")   # static folder is inside app/
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Ensure tables exist
models.Base.metadata.create_all(bind=database.engine)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(db: Session, token: str):
    if not token:
        return None
    return crud.get_auth_user_by_token(db, token)

# -------------------------------
# Home Page
# -------------------------------
@app.get("/", response_class=RedirectResponse)
async def root():
    return RedirectResponse(url="/home")

@app.get("/home", response_class=RedirectResponse)
async def home_redirect():
    return RedirectResponse(url="/index")

@app.get("/index")
async def index(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("session_token")
    user = get_current_user(db, token)
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

# -------------------------------
# Signup / Login
# -------------------------------
@app.get("/signup")
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request, "error": None})

@app.post("/signup")
async def signup(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        crud.create_auth_user(db, username, email, password)
        return RedirectResponse(url="/login", status_code=303)
    except Exception as e:
        return templates.TemplateResponse("signup.html", {"request": request, "error": str(e)})

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    auth_user = crud.get_auth_user_by_username(db, username)
    if not auth_user or not crud.verify_password(password, auth_user.password_hash):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    token = crud.create_session_for_user(db, auth_user)
    resp = RedirectResponse(url="/quiz", status_code=303)
    resp.set_cookie(key="session_token", value=token, httponly=True, samesite="Lax")
    return resp

# -------------------------------
# Quiz
# -------------------------------
@app.get("/quiz")
async def quiz_page(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("session_token")
    user = get_current_user(db, token)
    return templates.TemplateResponse("quiz.html", {"request": request, "user": user})

@app.post("/quiz")
async def quiz_submit(
    request: Request,
    name: str = Form(...),
    skill: str = Form(...),
    q1: str = Form(...),
    q2: str = Form(...),
    q3: str = Form(...),
    q4: str = Form(...),
    q5: str = Form(...),
    q6: str = Form(...),
    db: Session = Depends(get_db)
):
    token = request.cookies.get("session_token")
    user = get_current_user(db, token)

    likert_map = {
        "strongly_disagree": 1,
        "disagree": 2,
        "neutral": 3,
        "agree": 4,
        "strongly_agree": 5
    }

    answers = {
        "tech": likert_map.get(q1, 3),
        "art": likert_map.get(q2, 3),
        "data": likert_map.get(q3, 3),
        "comm": likert_map.get(q4, 3),
        "math": likert_map.get(q5, 3),
        "research": likert_map.get(q6, 3)
    }

    max_trait = max(answers, key=answers.get)
    personality_type = {
        "tech": "Tech Enthusiast",
        "art": "Creative Thinker",
        "data": "Analytical Mind",
        "comm": "Communicative Leader",
        "math": "Analytical Mind",
        "research": "Creative Thinker"
    }.get(max_trait, "Analytical Mind")

    if user:
        crud.update_profile(db, user, name=name, skills=skill, bio=f"Personality: {personality_type}")

    return RedirectResponse(url=f"/matches?personality_type={personality_type}", status_code=303)

# -------------------------------
# Matches
# -------------------------------
@app.get("/matches")
async def matches(request: Request, personality_type: str = "", db: Session = Depends(get_db)):
    token = request.cookies.get("session_token")
    user = get_current_user(db, token)
    skills = user.skills if user else ""
    matches = crud.find_career_matches(skills, personality_type)
    return templates.TemplateResponse("matches.html", {"request": request, "user": user, "matches": matches})


# -------------------------------
# Profile
# -------------------------------
@app.get("/profile")
async def profile_page(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("session_token")
    user = get_current_user(db, token)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("profile.html", {"request": request, "user": user})


@app.post("/profile")
async def profile_submit(
    request: Request,
    name: str = Form(...),
    skill: str = Form(...),
    q1: str = Form(...),
    q2: str = Form(...),
    q3: str = Form(...),
    q4: str = Form(...),
    q5: str = Form(...),
    q6: str = Form(...),
    db: Session = Depends(get_db)
):
    token = request.cookies.get("session_token")
    user = get_current_user(db, token)

    # Likert scale mapping
    likert_map = {
        "strongly_disagree": 1,
        "disagree": 2,
        "neutral": 3,
        "agree": 4,
        "strongly_agree": 5
    }

    answers = {
        "tech": likert_map.get(q1, 3),
        "art": likert_map.get(q2, 3),
        "data": likert_map.get(q3, 3),
        "comm": likert_map.get(q4, 3),
        "math": likert_map.get(q5, 3),
        "research": likert_map.get(q6, 3)
    }

    max_trait = max(answers, key=answers.get)
    personality_type = {
        "tech": "Tech Enthusiast",
        "art": "Creative Thinker",
        "data": "Analytical Mind",
        "comm": "Communicative Leader",
        "math": "Analytical Mind",
        "research": "Creative Thinker"
    }.get(max_trait, "Analytical Mind")

    # Save profile info if logged in
    if user:
        crud.update_profile(db, user, name=name, skills=skill, bio=f"Personality: {personality_type}")

    # Redirect to matches page with personality type
    return RedirectResponse(url=f"/matches?personality_type={personality_type}", status_code=303)
