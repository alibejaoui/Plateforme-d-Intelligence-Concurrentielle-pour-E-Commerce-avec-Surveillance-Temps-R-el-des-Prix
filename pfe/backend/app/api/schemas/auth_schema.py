"""
Authentication schemas
"""
from pydantic import BaseModel, EmailStr
from typing import Optional


class Token(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data schema"""
    user_id: Optional[int] = None
    email: Optional[str] = None


class UserLogin(BaseModel):
    """User login request schema"""
    email: EmailStr
    password: str


class UserRegister(BaseModel):
    """User registration request schema"""
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    """User response schema"""
    id: int
    email: str
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool
    
    class Config:
        from_attributes = True

