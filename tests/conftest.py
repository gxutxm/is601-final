"""Shared pytest fixtures — transactional DB + TestClient + authenticated client."""
import os

# Ensure tests use a deterministic JWT secret (must be set before importing app).
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-do-not-use-in-prod")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base, get_db
from app.main import app


@pytest.fixture(scope="session")
def db_url() -> str:
    return os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5432/fastapi_calc_test",
    )


@pytest.fixture(scope="session")
def engine(db_url):
    eng = create_engine(db_url, future=True)
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)


@pytest.fixture()
def db_session(engine):
    """A clean session per test using a transactional rollback."""
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(
        bind=connection, autoflush=False, autocommit=False, future=True
    )
    session = Session()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session):
    """TestClient with the get_db dependency overridden to the test session."""

    def _override():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def registered_user(client):
    """Register a baseline test user and return their credentials."""
    creds = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "strongpass1",
    }
    resp = client.post("/users/register", json=creds)
    assert resp.status_code == 201, resp.text
    return creds


@pytest.fixture()
def auth_token(client, registered_user):
    """Log in the registered user and return the bearer token."""
    resp = client.post(
        "/users/login",
        json={
            "username": registered_user["username"],
            "password": registered_user["password"],
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture()
def auth_client(client, auth_token):
    """TestClient pre-loaded with the Authorization header."""
    client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return client
