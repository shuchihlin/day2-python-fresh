from pydantic import BaseModel, EmailStr
from typing import Optional, List


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    token: str
    email: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class ConfirmResetRequest(BaseModel):
    token: str
    new_password: str


class UserProfile(BaseModel):
    id: int
    email: str
    name: str


class Post(BaseModel):
    id: int
    title: str
    content: str


class UserWithPosts(BaseModel):
    user: UserProfile
    posts: List[Post]


class ErrorResponse(BaseModel):
    error: str
