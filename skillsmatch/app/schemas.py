# app/schemas.py
from pydantic import BaseModel

class UserBase(BaseModel):
    name: str
    skill: str
    bio: str | None = None

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int

    class Config:
        from_attributes = True


class AuthUserCreate(BaseModel):
    username: str
    email: str
    password: str


class AuthUserOut(BaseModel):
    id: int
    username: str
    email: str
    name: str | None = None
    skills: str | None = None
    favorite_subject: str | None = None
    bio: str | None = None

    class Config:
        from_attributes = True