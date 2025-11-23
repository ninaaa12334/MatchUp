from sqlalchemy.orm import Session
from . import models
from passlib.context import CryptContext
import secrets

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_auth_user(db: Session, username: str, email: str, password: str):
    hashed_pw = pwd_context.hash(password)
    user = models.AuthUser(username=username, email=email, password_hash=hashed_pw)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)





def get_auth_user_by_username(db: Session, username: str):
    return db.query(models.AuthUser).filter(models.AuthUser.username == username).first()



def create_session_for_user(db: Session, user: models.AuthUser):
    token = secrets.token_hex(16)
    user.session_token = token
    db.commit()
    return token

def get_auth_user_by_token(db: Session, token: str):
    return db.query(models.AuthUser).filter(models.AuthUser.session_token == token).first()

def update_profile(db: Session, user: models.AuthUser, name: str, skills: str, bio: str):
    user.name = name
    user.skills = skills
    user.bio = bio
    db.commit()
    db.refresh(user)
    return user


# Enhanced career/university data with images
CAREERS = [
    {"career": "Software Engineer", "requirements": "programming, math, problem-solving", "universities": "MIT, Stanford, Carnegie Mellon", "fit_types": ["Tech Enthusiast", "Analytical Mind"], "image": "static/img/software_engineer.jpg"},
    {"career": "Data Scientist", "requirements": "programming, statistics, data analysis", "universities": "UC Berkeley, Harvard, Stanford", "fit_types": ["Analytical Mind", "Tech Enthusiast"], "image": "static/img/data_scientist.jpg"},
    {"career": "UX/UI Designer", "requirements": "design, creativity, user research", "universities": "Pratt Institute, USC, Carnegie Mellon", "fit_types": ["Creative Thinker"], "image": "static/img/ux_ui.jpg"},
    {"career": "Graphic Designer", "requirements": "design, art, software tools", "universities": "Pratt Institute, Rhode Island School of Design", "fit_types": ["Creative Thinker"], "image": "static/img/graphic_designer.jpg"},
    {"career": "Digital Marketer", "requirements": "marketing, communication, analytics", "universities": "NYU, UPenn (Wharton), USC", "fit_types": ["Communicative Leader"], "image": "static/img/digital_marketer.jpg"},
    {"career": "SEO Specialist", "requirements": "marketing, writing, data", "universities": "NYU, Boston University", "fit_types": ["Communicative Leader", "Analytical Mind"], "image": "static/img/seo.jpg"},
    {"career": "Biologist/Research Scientist", "requirements": "science, biology, lab work", "universities": "Harvard, Stanford, MIT", "fit_types": ["Analytical Mind"], "image": "static/img/biologist.jpg"},
    {"career": "Environmental Scientist", "requirements": "science, ecology, data", "universities": "Yale, UC Berkeley", "fit_types": ["Analytical Mind"], "image": "static/img/environmental_scientist.jpg"},
    {"career": "Product Manager", "requirements": "business, communication, tech", "universities": "Stanford, UPenn", "fit_types": ["Communicative Leader", "Tech Enthusiast"], "image": "static/img/product_manager.jpg"},
    {"career": "Web Developer", "requirements": "programming, design, frontend", "universities": "MIT, University of Washington", "fit_types": ["Tech Enthusiast", "Creative Thinker"], "image": "static/img/web_developer.jpg"},
    {"career": "AI Specialist", "requirements": "programming, machine learning, math", "universities": "Carnegie Mellon, Stanford", "fit_types": ["Tech Enthusiast", "Analytical Mind"], "image": "static/img/ai_specialist.jpg"},
    {"career": "Content Creator", "requirements": "marketing, design, writing", "universities": "USC, NYU", "fit_types": ["Creative Thinker", "Communicative Leader"], "image": "static/img/content_creator.jpg"},
    {"career": "Architect", "requirements": "design, art, math, spatial reasoning", "universities": "ETH Zurich, MIT, TU Delft", "fit_types": ["Creative Thinker", "Analytical Mind"], "image": "static/img/architect.jpg"}
]

def find_career_matches(skills_str: str, personality_type: str):
    if not skills_str:
        my_skills = set()
    else:
        my_skills = {s.strip().lower() for s in skills_str.split(",") if s.strip()}

    is_architect_combo = "art" in my_skills and "math" in my_skills

    matches = []
    for career in CAREERS:
        req_skills = {r.strip().lower() for r in career["requirements"].split(",")}
        overlap = len(req_skills & my_skills)
        missing = len(req_skills - my_skills)
        type_fit = 5 if personality_type in career.get("fit_types", []) else 0

        score = (overlap * 3) + type_fit - (missing * 1)

        if is_architect_combo and career["career"].lower() == "architect":
            score += 6

        details_text = (
            f"Grow by learning {', '.join(sorted(req_skills - my_skills))}"
            if req_skills - my_skills else
            "You already match the key skills—great fit!"
        )

        matches.append({
            "career": career["career"],
            "university": career["universities"],
            "score": max(score, 0),
            "details": details_text,
            "image": career.get("image", "")
        })

    return sorted(matches, key=lambda x: x["score"], reverse=True)

def find_complementary_matches(db: Session, skills_str: str, q: str = None):
    matches = find_career_matches(skills_str, "")
    if q:
        ql = q.lower()
        matches = [m for m in matches if ql in m["career"].lower() or ql in m["university"].lower() or ql in m["details"].lower()]
    return matches
