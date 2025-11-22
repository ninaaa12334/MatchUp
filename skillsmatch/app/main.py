
from pathlib import Path

from fastapi import FastAPI, Request, Depends, Form, Query
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from . import crud, models, schemas, database

ROOT_DIR = Path(__file__).resolve().parent.parent  # Changed: .parent.parent to point to project root (skillsmatch/)

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="CareerMatch • Student Career Explorer")

# Mount static and template directories using absolute paths
app.mount("/static", StaticFiles(directory=str(ROOT_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(ROOT_DIR / "templates"))


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("session")
    user = crud.get_auth_user_by_token(db, token) if token else None
    return user


@app.get('/signup', response_class=HTMLResponse)
async def signup_get(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        return RedirectResponse('/profile', status_code=303)
    return templates.TemplateResponse('signup.html', {'request': request, 'user': user})


@app.post('/signup')
async def signup_post(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    existing = crud.get_auth_user_by_username(db, username)
    if existing:
        # simple behavior: redirect to login if exists
        return RedirectResponse('/login', status_code=303)
    try:
        auth = crud.create_auth_user(db, username, email, password)
        token = crud.create_session_for_user(db, auth)
        response = RedirectResponse('/profile', status_code=303)  # Changed to /profile
        response.set_cookie('session', token, httponly=True)
        return response
    except Exception as e:
        # Avoid crashing on DB errors (e.g., duplicate email). Show friendly message.
        return templates.TemplateResponse('signup.html', {"request": request, "error": str(e), 'user': None})


@app.get('/login', response_class=HTMLResponse)
async def login_get(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        return RedirectResponse('/profile', status_code=303)
    return templates.TemplateResponse('login.html', {'request': request, 'user': user})


@app.post('/login')
async def login_post(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = crud.get_auth_user_by_username(db, username)
    if not user or not crud.verify_password(password, user.password_hash):
        return RedirectResponse('/login', status_code=303)
    token = crud.create_session_for_user(db, user)
    response = RedirectResponse('/profile', status_code=303)
    response.set_cookie('session', token, httponly=True)
    return response


@app.get('/logout')
async def logout(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get('session')
    if token:
        user = crud.get_auth_user_by_token(db, token)
        if user:
            user.session_token = None
            db.add(user)
            db.commit()
    resp = RedirectResponse('/', status_code=303)
    resp.delete_cookie('session')
    return resp


@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    total_users = len(crud.get_users(db))
    return templates.TemplateResponse("index.html", {
        "request": request,
        "total_users": total_users,
        "user": user
    })


@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, db: Session = Depends(get_db)):
    # if logged in, prefill with profile
    user = get_current_user(request, db)
    return templates.TemplateResponse("profile.html", {"request": request, "user": user})


@app.post("/profile")
async def save_profile(
    request: Request,
    name: str = Form(...),
    skill: str = Form(...),
    bio: str = Form(None),
    quiz1: str = Form("no"),
    quiz2: str = Form("no"),
    quiz3: str = Form("no"),
    quiz4: str = Form("no"),
    db: Session = Depends(get_db)
):
    # Compute a simple personality type from the quiz
    score_tech = (1 if quiz1 == 'yes' else 0)
    score_creative = (1 if quiz2 == 'yes' else 0)
    score_analytical = (1 if quiz3 == 'yes' else 0)
    score_communicative = (1 if quiz4 == 'yes' else 0)

    max_score = max(score_tech, score_creative, score_analytical, score_communicative)
    if max_score == 0:
        personality_type = "Balanced"
    elif score_tech == max_score:
        personality_type = "Tech Enthusiast"
    elif score_creative == max_score:
        personality_type = "Creative Thinker"
    elif score_analytical == max_score:
        personality_type = "Analytical Mind"
    else:
        personality_type = "Communicative Leader"

    # If logged-in, attach profile to their account; otherwise keep legacy user table
    token = request.cookies.get("session")
    if token:
        auth = crud.get_auth_user_by_token(db, token)
        if auth:
            crud.update_profile(db, auth, name=name, skills=skill, bio=bio or "Exploring careers!")
    else:
        user = schemas.UserCreate(name=name, skill=skill, bio=bio or "Exploring careers!")
        crud.create_user(db, user)

    return RedirectResponse(f"/matches?personality_type={personality_type}", status_code=303)


@app.get("/matches", response_class=HTMLResponse)
async def matches_page(
    request: Request,
    q: str = Query(None),
    personality_type: str = Query(None),
    db: Session = Depends(get_db)
):
    # Prefer profile from logged-in user, otherwise use legacy users table
    user = get_current_user(request, db)
    if not user:
        users = crud.get_users(db)
        if not users:
            return RedirectResponse("/profile")
        user = users[-1]  # Legacy fallback; encourage login for better experience

    # Use provided personality_type if present, otherwise default to Balanced
    p_type = personality_type or "Balanced"

    # Use skills from profile structure
    skills_text = getattr(user, 'skills', None) or getattr(user, 'skill', '')
    raw_matches = crud.find_career_matches(skills_text, p_type)

    if q:
        ql = q.lower()
        raw_matches = [
            m for m in raw_matches
            if ql in m["career"].lower() or ql in m["university"].lower() or ql in m["details"].lower()
        ]

    matches = raw_matches[:12]

    context = {
        "request": request,
        "user": user,
        "matches": matches,
        "search_query": q,
        "personality_type": p_type
    }

    # Handle HTMX partial request for search results
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse("partials/results.html", context)
    else:
        return templates.TemplateResponse("matches.html", context)
