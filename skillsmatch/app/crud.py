from sqlalchemy.orm import Session
from . import models
from passlib.context import CryptContext
import secrets

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_user(db: Session, user_data):
    db_user = models.User(**user_data.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_users(db: Session):
    return db.query(models.User).all()


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


### Auth helpers (AuthUser table)
def create_auth_user(db: Session, username: str, email: str, password: str):
    hashed = pwd_context.hash(password)
    auth = models.AuthUser(username=username, email=email, password_hash=hashed)
    db.add(auth)
    db.commit()
    db.refresh(auth)
    return auth


def get_auth_user_by_username(db: Session, username: str):
    return db.query(models.AuthUser).filter(models.AuthUser.username == username).first()


def verify_password(plain, hashed):
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False


def create_session_for_user(db: Session, user: models.AuthUser):
    token = secrets.token_urlsafe(32)
    user.session_token = token
    db.add(user)
    db.commit()
    return token


def get_auth_user_by_token(db: Session, token: str):
    if not token:
        return None
    return db.query(models.AuthUser).filter(models.AuthUser.session_token == token).first()


def update_profile(db: Session, user: models.AuthUser, name: str = None, skills: str = None, favorite_subject: str = None, bio: str = None):
    if name is not None:
        user.name = name
    if skills is not None:
        user.skills = skills
    if favorite_subject is not None:
        user.favorite_subject = favorite_subject
    if bio is not None:
        user.bio = bio
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# Hardcoded career/university data (based on common high-demand fields)
CAREERS = [
    {"career": "Software Engineer", "requirements": "programming, math, problem-solving", "universities": "MIT, Stanford, Carnegie Mellon", "fit_types": ["Tech Enthusiast", "Analytical Mind"]},
    {"career": "Data Scientist", "requirements": "programming, statistics, data analysis", "universities": "UC Berkeley, Harvard, Stanford", "fit_types": ["Analytical Mind", "Tech Enthusiast"]},
    {"career": "UX/UI Designer", "requirements": "design, creativity, user research", "universities": "Pratt Institute, USC, Carnegie Mellon", "fit_types": ["Creative Thinker"]},
    {"career": "Graphic Designer", "requirements": "design, art, software tools", "universities": "Pratt Institute, Rhode Island School of Design", "fit_types": ["Creative Thinker"]},
    {"career": "Digital Marketer", "requirements": "marketing, communication, analytics", "universities": "NYU, UPenn (Wharton), USC", "fit_types": ["Communicative Leader"]},
    {"career": "SEO Specialist", "requirements": "marketing, writing, data", "universities": "NYU, Boston University", "fit_types": ["Communicative Leader", "Analytical Mind"]},
    {"career": "Biologist/Research Scientist", "requirements": "science, biology, lab work", "universities": "Harvard, Stanford, MIT", "fit_types": ["Analytical Mind"]},
    {"career": "Environmental Scientist", "requirements": "science, ecology, data", "universities": "Yale, UC Berkeley", "fit_types": ["Analytical Mind"]},
    {"career": "Product Manager", "requirements": "business, communication, tech", "universities": "Stanford, UPenn", "fit_types": ["Communicative Leader", "Tech Enthusiast"]},
    {"career": "Web Developer", "requirements": "programming, design, frontend", "universities": "MIT, University of Washington", "fit_types": ["Tech Enthusiast", "Creative Thinker"]},
    {"career": "AI Specialist", "requirements": "programming, machine learning, math", "universities": "Carnegie Mellon, Stanford", "fit_types": ["Tech Enthusiast", "Analytical Mind"]},
    {"career": "Content Creator", "requirements": "marketing, design, writing", "universities": "USC, NYU", "fit_types": ["Creative Thinker", "Communicative Leader"]}
]


def find_career_matches(skills_str: str, personality_type: str):
    if not skills_str:
        my_skills = set()
    else:
        my_skills = {s.strip().lower() for s in skills_str.split(",") if s.strip()}

    matches = []
    for career in CAREERS:
        req_skills = {r.strip().lower() for r in career["requirements"].split(",")}
        complementary_score = len(req_skills - my_skills)  # Skills they need to learn/grow
        type_fit = 5 if personality_type in career.get("fit_types", []) else 0  # Bonus for quiz fit

        # Always include matches; score will reflect fit
        matches.append({
            "career": career["career"],
            "university": career["universities"],
            "score": complementary_score + type_fit,
            "details": (f"Build on your skills by learning {', '.join(sorted(req_skills - my_skills))}" if req_skills - my_skills else "You already have all the key skills—great fit!")
        })

    return sorted(matches, key=lambda x: x["score"], reverse=True)


def find_complementary_matches(db: Session, skills_str: str, q: str = None):
    matches = find_career_matches(skills_str, "")
    if q:
        ql = q.lower()
        matches = [m for m in matches if ql in m["career"].lower() or ql in m["university"].lower() or ql in m["details"].lower()]
    return matches