from sqlalchemy import Column, Integer, String
from .database import Base

class AuthUser(Base):
    __tablename__ = "auth_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    session_token = Column(String, index=True, nullable=True)

    # Optional profile fields
    name = Column(String, nullable=True)
    skills = Column(String, nullable=True)
    bio = Column(String, nullable=True)
