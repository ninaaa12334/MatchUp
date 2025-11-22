# app/models.py
from sqlalchemy import Column, Integer, String, Text
from .database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    skill = Column(Text, nullable=False)  # "Python, Figma, Marketing"
    bio = Column(String, default="Collaborator on Skillsmatch")


class AuthUser(Base):
    __tablename__ = "auth_users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=True)
    skills = Column(Text, nullable=True)
    favorite_subject = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    session_token = Column(String, index=True, nullable=True)