"""User routes: registration, JSON login, OAuth2 form login, and /me."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field, model_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.hashing import hash_password, verify_password
from app.auth.jwt import create_access_token, get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserRead

router = APIRouter(prefix="/users", tags=["users"])


# Flexible login payload — accepts either username OR email so the front-end
# can stay email-first while keeping existing tests that use `username`.
class FlexibleLogin(BaseModel):
    username: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    password: str = Field(..., min_length=1, max_length=128)

    @model_validator(mode="after")
    def one_identifier_required(self):
        if not self.username and not self.email:
            raise ValueError("Provide either `username` or `email`")
        return self


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists",
        )
    db.refresh(user)
    return user


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Log in with username or email and receive a JWT",
)
def login(payload: FlexibleLogin, db: Session = Depends(get_db)) -> Token:
    """Accepts either `username` or `email` as the identifier."""
    query = db.query(User)
    user = (
        query.filter(User.email == payload.email).first()
        if payload.email
        else query.filter(User.username == payload.username).first()
    )
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(subject=user.id))


@router.post(
    "/token",
    response_model=Token,
    summary="OAuth2-compatible login (form-encoded) for Swagger UI",
)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    """Form-encoded login endpoint — used by Swagger's Authorize button."""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(subject=user.id))


@router.get(
    "/me",
    response_model=UserRead,
    summary="Return the currently authenticated user",
)
def read_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
