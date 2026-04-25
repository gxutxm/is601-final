"""Integration tests for the /calculations BREAD endpoints."""


# ---------- Auth enforcement ----------

def test_endpoints_require_auth(client):
    """Every calculation endpoint should reject unauthenticated requests."""
    assert client.get("/calculations").status_code == 401
    assert client.post("/calculations", json={"a": 1, "b": 2, "type": "Add"}).status_code == 401
    assert client.get("/calculations/1").status_code == 401
    assert client.put("/calculations/1", json={"a": 1}).status_code == 401
    assert client.delete("/calculations/1").status_code == 401


# ---------- Add ----------

def test_create_calculation_success(auth_client):
    resp = auth_client.post(
        "/calculations",
        json={"a": 6, "b": 7, "type": "Multiply"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["a"] == 6
    assert body["b"] == 7
    assert body["type"] == "Multiply"
    assert body["result"] == 42
    assert "id" in body
    assert "user_id" in body  # auto-populated from the JWT
    assert "created_at" in body


def test_create_divide_by_zero_422(auth_client):
    """Pydantic model_validator should catch this before the route runs."""
    resp = auth_client.post(
        "/calculations",
        json={"a": 10, "b": 0, "type": "Divide"},
    )
    assert resp.status_code == 422


def test_create_invalid_type_422(auth_client):
    resp = auth_client.post(
        "/calculations",
        json={"a": 2, "b": 3, "type": "BogusOp"},
    )
    assert resp.status_code == 422


def test_create_missing_field_422(auth_client):
    resp = auth_client.post(
        "/calculations",
        json={"a": 2, "type": "Add"},  # missing b
    )
    assert resp.status_code == 422


# ---------- Browse ----------

def test_browse_empty_list(auth_client):
    resp = auth_client.get("/calculations")
    assert resp.status_code == 200
    assert resp.json() == []


def test_browse_only_returns_current_users_calcs(auth_client, client):
    # User A creates two calcs
    auth_client.post("/calculations", json={"a": 1, "b": 2, "type": "Add"})
    auth_client.post("/calculations", json={"a": 5, "b": 3, "type": "Sub"})

    # Register + log in user B
    client.post(
        "/users/register",
        json={"username": "userb", "email": "b@example.com", "password": "strongpass1"},
    )
    tok_b = client.post(
        "/users/login",
        json={"username": "userb", "password": "strongpass1"},
    ).json()["access_token"]

    # User B's view should be empty — strict row-level isolation.
    resp = client.get(
        "/calculations",
        headers={"Authorization": f"Bearer {tok_b}"},
    )
    assert resp.status_code == 200
    assert resp.json() == []


# ---------- Read ----------

def test_read_calculation_success(auth_client):
    created = auth_client.post(
        "/calculations", json={"a": 9, "b": 3, "type": "Divide"}
    ).json()
    resp = auth_client.get(f"/calculations/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["result"] == 3


def test_read_missing_404(auth_client):
    resp = auth_client.get("/calculations/99999")
    assert resp.status_code == 404


def test_read_other_users_calc_404(auth_client, client):
    # User A creates a calculation
    calc_id = auth_client.post(
        "/calculations", json={"a": 1, "b": 2, "type": "Add"}
    ).json()["id"]

    # User B tries to read it
    client.post(
        "/users/register",
        json={"username": "snoop", "email": "snoop@example.com", "password": "strongpass1"},
    )
    tok = client.post(
        "/users/login",
        json={"username": "snoop", "password": "strongpass1"},
    ).json()["access_token"]

    resp = client.get(
        f"/calculations/{calc_id}",
        headers={"Authorization": f"Bearer {tok}"},
    )
    # 404 (not 403) — don't leak existence of other users' rows.
    assert resp.status_code == 404


# ---------- Edit ----------

def test_update_recomputes_result(auth_client):
    created = auth_client.post(
        "/calculations", json={"a": 2, "b": 3, "type": "Add"}
    ).json()
    assert created["result"] == 5

    resp = auth_client.put(
        f"/calculations/{created['id']}",
        json={"a": 10, "b": 20, "type": "Add"},
    )
    assert resp.status_code == 200
    assert resp.json()["result"] == 30


def test_update_partial_only_changes_type(auth_client):
    created = auth_client.post(
        "/calculations", json={"a": 4, "b": 2, "type": "Add"}
    ).json()
    assert created["result"] == 6

    # Only send "type"; a and b stay the same but result recomputes.
    resp = auth_client.put(
        f"/calculations/{created['id']}",
        json={"type": "Multiply"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "Multiply"
    assert body["result"] == 8


def test_update_divide_by_zero_422(auth_client):
    created = auth_client.post(
        "/calculations", json={"a": 1, "b": 1, "type": "Add"}
    ).json()
    resp = auth_client.put(
        f"/calculations/{created['id']}",
        json={"type": "Divide", "b": 0},
    )
    assert resp.status_code == 422


def test_update_missing_404(auth_client):
    resp = auth_client.put(
        "/calculations/99999", json={"a": 1, "b": 2, "type": "Add"}
    )
    assert resp.status_code == 404


# ---------- Delete ----------

def test_delete_success_then_404(auth_client):
    created = auth_client.post(
        "/calculations", json={"a": 1, "b": 1, "type": "Add"}
    ).json()

    resp = auth_client.delete(f"/calculations/{created['id']}")
    assert resp.status_code == 204

    # Verify it's really gone
    resp2 = auth_client.get(f"/calculations/{created['id']}")
    assert resp2.status_code == 404


def test_delete_missing_404(auth_client):
    resp = auth_client.delete("/calculations/99999")
    assert resp.status_code == 404


def test_delete_other_users_calc_404(auth_client, client):
    calc_id = auth_client.post(
        "/calculations", json={"a": 1, "b": 2, "type": "Add"}
    ).json()["id"]

    client.post(
        "/users/register",
        json={"username": "thief", "email": "thief@example.com", "password": "strongpass1"},
    )
    tok = client.post(
        "/users/login",
        json={"username": "thief", "password": "strongpass1"},
    ).json()["access_token"]

    resp = client.delete(
        f"/calculations/{calc_id}",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert resp.status_code == 404

    # And it's still there for the owner
    assert auth_client.get(f"/calculations/{calc_id}").status_code == 200


# ---------- Full BREAD flow (smoke) ----------

def test_full_bread_flow(auth_client):
    # Create
    created = auth_client.post(
        "/calculations", json={"a": 100, "b": 4, "type": "Divide"}
    ).json()
    cid = created["id"]
    assert created["result"] == 25

    # Read
    assert auth_client.get(f"/calculations/{cid}").status_code == 200

    # Update
    updated = auth_client.put(
        f"/calculations/{cid}", json={"a": 8, "b": 2, "type": "Multiply"}
    ).json()
    assert updated["result"] == 16

    # Browse contains the updated calc
    browse = auth_client.get("/calculations").json()
    assert any(c["id"] == cid for c in browse)

    # Delete
    assert auth_client.delete(f"/calculations/{cid}").status_code == 204
    assert auth_client.get(f"/calculations/{cid}").status_code == 404
