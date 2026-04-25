"""Pydantic schemas for the User resource (Pydantic v2)."""
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserCreate(BaseModel):
    """Payload for creating a new user. Accepts a raw password."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class UserLogin(BaseModel):
    """Payload for logging in with username + password."""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)


class UserRead(BaseModel):
    """Public-facing user representation. Never exposes the password hash."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    created_at: datetime


class Token(BaseModel):
    """Response body returned by the login endpoint."""

    access_token: str
    token_type: str = "bearer"
