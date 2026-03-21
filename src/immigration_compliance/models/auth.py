"""Authentication and user models."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    APPLICANT = "applicant"
    ATTORNEY = "attorney"
    EMPLOYER = "employer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    first_name: str
    last_name: str
    role: UserRole = UserRole.APPLICANT
    # Attorney-specific fields
    bar_number: str = ""
    jurisdiction: str = ""
    years_experience: int = 0
    specializations: str = ""


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    role: UserRole
    bar_number: str = ""
    jurisdiction: str = ""
    years_experience: int = 0
    specializations: str = ""


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class TokenData(BaseModel):
    user_id: str
    role: UserRole
