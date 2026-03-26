from pydantic import BaseModel, EmailStr, field_validator
import re
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_complexity(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one digit")
        return value

class UserResponse(BaseModel):
    userID: str
    email: str
    degrees: Optional[dict] = None
    jobexperience: Optional[dict] = None
    projects: Optional[dict] = None
    publications: Optional[dict] = None
    languages: Optional[dict] = None
    skills: Optional[dict] = None
    availability: Optional[int] = None
    preferences: Optional[dict] = None

class UserUpdate(BaseModel):
    degrees: Optional[dict] = None
    jobexperience: Optional[dict] = None
    projects: Optional[dict] = None
    publications: Optional[dict] = None
    languages: Optional[dict] = None
    skills: Optional[dict] = None
    availability: Optional[int] = None
    preferences: Optional[dict] = None

class Preferences(BaseModel):
    field: str
    location: str
    remote: bool
    compensation: int


class Token(BaseModel):
    access_token: str
    token_type: str