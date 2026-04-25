"""Integration tests for the /users router (register, login, me)."""
from app.auth.hashing import verify_password
from app.models.user import User


# ---------- POST /users/register ----------

def test_register_success(client, db_session):
    resp = client.post(
        "/users/register",
        json={
            "username": "gg453",
            "email": "gg453@example.com",
            "password": "strongpass1",
        },
    )
    assert resp.status_code == 201
    body = resp.json()

    # Response contract
    assert body["username"] == "gg453"
    assert body["email"] == "gg453@example.com"
    assert "id" in body and "created_at" in body
    assert "password" not in body and "password_hash" not in body

    # Persistence + hashing: password is not stored in plaintext.
    user = db_session.query(User).filter_by(username="gg453").first()
    assert user is not None
    assert user.password_hash != "strongpass1"
    assert verify_password("strongpass1", user.password_hash)


def test_register_duplicate_username_409(client):
    payload = {"username": "dup", "email": "first@x.com", "password": "strongpass1"}
    assert client.post("/users/register", json=payload).status_code == 201

    payload2 = {"username": "dup", "email": "second@x.com", "password": "strongpass1"}
    resp = client.post("/users/register", json=payload2)
    assert resp.status_code == 409


def test_register_duplicate_email_409(client):
    payload = {"username": "userone", "email": "same@x.com", "password": "strongpass1"}
    assert client.post("/users/register", json=payload).status_code == 201

    payload2 = {"username": "usertwo", "email": "same@x.com", "password": "strongpass1"}
    resp = client.post("/users/register", json=payload2)
    assert resp.status_code == 409


def test_register_invalid_email_422(client):
    resp = client.post(
        "/users/register",
        json={"username": "ok", "email": "not-an-email", "password": "strongpass1"},
    )
    assert resp.status_code == 422


def test_register_short_password_422(client):
    resp = client.post(
        "/users/register",
        json={"username": "ok", "email": "ok@x.com", "password": "short"},
    )
    assert resp.status_code == 422


# ---------- POST /users/login ----------

def test_login_success_returns_token(client, registered_user):
    resp = client.post(
        "/users/login",
        json={
            "username": registered_user["username"],
            "password": registered_user["password"],
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body and body["access_token"]
    assert body["token_type"] == "bearer"


def test_login_wrong_password_401(client, registered_user):
    resp = client.post(
        "/users/login",
        json={
            "username": registered_user["username"],
            "password": "WRONGpass1",
        },
    )
    assert resp.status_code == 401


def test_login_unknown_user_401(client):
    resp = client.post(
        "/users/login",
        json={"username": "ghost", "password": "whatever1"},
    )
    assert resp.status_code == 401


# ---------- GET /users/me ----------

def test_me_requires_auth(client):
    resp = client.get("/users/me")
    assert resp.status_code == 401


def test_me_returns_current_user(auth_client, registered_user):
    resp = auth_client.get("/users/me")
    assert resp.status_code == 200
    body = resp.json()
    assert body["username"] == registered_user["username"]
    assert body["email"] == registered_user["email"]


def test_me_rejects_bad_token(client):
    client.headers.update({"Authorization": "Bearer not-a-real-jwt"})
    resp = client.get("/users/me")
    assert resp.status_code == 401
