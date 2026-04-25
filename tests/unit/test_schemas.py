"""Unit tests for Pydantic user schemas."""
from datetime import datetime
import pytest
from pydantic import ValidationError
from app.schemas.user import UserCreate, UserRead


def test_user_create_valid():
    u = UserCreate(username="gg453", email="gg@example.com", password="strongpass1")
    assert u.username == "gg453"
    assert u.email == "gg@example.com"
    assert u.password == "strongpass1"


def test_user_create_invalid_email():
    with pytest.raises(ValidationError):
        UserCreate(username="gg453", email="not-an-email", password="strongpass1")


def test_user_create_short_password():
    with pytest.raises(ValidationError):
        UserCreate(username="gg453", email="gg@example.com", password="short")


def test_user_create_short_username():
    with pytest.raises(ValidationError):
        UserCreate(username="gg", email="gg@example.com", password="strongpass1")


def test_user_read_omits_password_hash():
    """UserRead must not contain password fields."""
    fields = UserRead.model_fields.keys()
    assert "password" not in fields
    assert "password_hash" not in fields


def test_user_read_from_attributes():
    """UserRead should serialize from an ORM-like object."""
    class FakeORM:
        id = 1
        username = "gg453"
        email = "gg@example.com"
        created_at = datetime(2026, 1, 1, 12, 0, 0)

    read = UserRead.model_validate(FakeORM())
    dumped = read.model_dump()
    assert dumped["id"] == 1
    assert "password_hash" not in dumped
