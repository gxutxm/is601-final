"""Integration tests requiring a real Postgres database."""
import pytest
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.auth.hashing import hash_password, verify_password


def test_create_and_read_user(db_session):
    user = User(
        username="gg453",
        email="gg@example.com",
        password_hash=hash_password("strongpass1"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.created_at is not None
    assert verify_password("strongpass1", user.password_hash)


def test_username_uniqueness(db_session):
    db_session.add(User(username="dup", email="a@x.com", password_hash=hash_password("pw12345678")))
    db_session.commit()
    db_session.add(User(username="dup", email="b@x.com", password_hash=hash_password("pw12345678")))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_email_uniqueness(db_session):
    db_session.add(User(username="user1", email="same@x.com", password_hash=hash_password("pw12345678")))
    db_session.commit()
    db_session.add(User(username="user2", email="same@x.com", password_hash=hash_password("pw12345678")))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_api_create_user_success(client):
    resp = client.post(
        "/users/register",
        json={"username": "apitest", "email": "api@example.com", "password": "strongpass1"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["username"] == "apitest"
    assert body["email"] == "api@example.com"
    assert "password" not in body
    assert "password_hash" not in body


def test_api_create_user_invalid_email(client):
    resp = client.post(
        "/users/register",
        json={"username": "bademail", "email": "not-an-email", "password": "strongpass1"},
    )
    assert resp.status_code == 422


def test_api_duplicate_username_returns_409(client):
    payload = {"username": "twice", "email": "first@x.com", "password": "strongpass1"}
    assert client.post("/users/register", json=payload).status_code == 201
    payload2 = {"username": "twice", "email": "second@x.com", "password": "strongpass1"}
    resp = client.post("/users/register", json=payload2)
    assert resp.status_code == 409
