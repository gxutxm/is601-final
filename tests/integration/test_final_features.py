"""Integration tests for the final-project additions: new ops + /stats."""


# ---------- New operation types via the API ----------

def test_create_power_calculation(auth_client):
    resp = auth_client.post(
        "/calculations", json={"a": 2, "b": 10, "type": "Power"}
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["type"] == "Power"
    assert body["result"] == 1024


def test_create_modulus_calculation(auth_client):
    resp = auth_client.post(
        "/calculations", json={"a": 17, "b": 5, "type": "Modulus"}
    )
    assert resp.status_code == 201
    assert resp.json()["result"] == 2


def test_create_root_calculation(auth_client):
    resp = auth_client.post(
        "/calculations", json={"a": 27, "b": 3, "type": "Root"}
    )
    assert resp.status_code == 201
    # Cube root of 27 ≈ 3.0, allow tiny float wobble
    assert abs(resp.json()["result"] - 3.0) < 1e-9


def test_modulus_by_zero_422(auth_client):
    resp = auth_client.post(
        "/calculations", json={"a": 10, "b": 0, "type": "Modulus"}
    )
    assert resp.status_code == 422


def test_root_zero_degree_422(auth_client):
    resp = auth_client.post(
        "/calculations", json={"a": 9, "b": 0, "type": "Root"}
    )
    assert resp.status_code == 422


def test_root_even_root_of_negative_422(auth_client):
    resp = auth_client.post(
        "/calculations", json={"a": -4, "b": 2, "type": "Root"}
    )
    assert resp.status_code == 422


def test_update_to_power_recomputes_result(auth_client):
    created = auth_client.post(
        "/calculations", json={"a": 3, "b": 4, "type": "Add"}
    ).json()
    assert created["result"] == 7

    resp = auth_client.put(
        f"/calculations/{created['id']}",
        json={"a": 2, "b": 8, "type": "Power"},
    )
    assert resp.status_code == 200
    assert resp.json()["result"] == 256


# ---------- Stats endpoint ----------

def test_stats_requires_auth(client):
    resp = client.get("/calculations/stats")
    assert resp.status_code == 401


def test_stats_empty_state(auth_client):
    resp = auth_client.get("/calculations/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 0
    assert body["by_type"] == {}
    assert body["most_used_type"] is None
    assert body["avg_a"] is None
    assert body["avg_b"] is None
    assert body["avg_result"] is None


def test_stats_after_single_calc(auth_client):
    auth_client.post("/calculations", json={"a": 6, "b": 7, "type": "Multiply"})

    resp = auth_client.get("/calculations/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["by_type"] == {"Multiply": 1}
    assert body["most_used_type"] == "Multiply"
    assert body["avg_a"] == 6
    assert body["avg_b"] == 7
    assert body["avg_result"] == 42


def test_stats_aggregates_across_types(auth_client):
    # Three Add, one Multiply, one Power
    auth_client.post("/calculations", json={"a": 1, "b": 2, "type": "Add"})
    auth_client.post("/calculations", json={"a": 3, "b": 4, "type": "Add"})
    auth_client.post("/calculations", json={"a": 5, "b": 6, "type": "Add"})
    auth_client.post("/calculations", json={"a": 2, "b": 3, "type": "Multiply"})
    auth_client.post("/calculations", json={"a": 2, "b": 8, "type": "Power"})

    resp = auth_client.get("/calculations/stats")
    body = resp.json()
    assert body["total"] == 5
    assert body["by_type"] == {"Add": 3, "Multiply": 1, "Power": 1}
    assert body["most_used_type"] == "Add"  # 3 > 1, 1


def test_stats_scoped_to_current_user(auth_client, client):
    # User A creates calcs
    auth_client.post("/calculations", json={"a": 1, "b": 2, "type": "Add"})
    auth_client.post("/calculations", json={"a": 5, "b": 5, "type": "Multiply"})

    # User B registers + logs in
    client.post(
        "/users/register",
        json={"username": "userb", "email": "b@example.com", "password": "strongpass1"},
    )
    tok_b = client.post(
        "/users/login",
        json={"username": "userb", "password": "strongpass1"},
    ).json()["access_token"]

    # User B sees zero — A's calcs don't leak into B's stats
    resp = client.get(
        "/calculations/stats",
        headers={"Authorization": f"Bearer {tok_b}"},
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


def test_stats_averages_are_correct(auth_client):
    # Two adds with predictable averages
    auth_client.post("/calculations", json={"a": 10, "b": 20, "type": "Add"})  # =30
    auth_client.post("/calculations", json={"a": 30, "b": 40, "type": "Add"})  # =70

    body = auth_client.get("/calculations/stats").json()
    assert body["total"] == 2
    assert body["avg_a"] == 20         # (10+30)/2
    assert body["avg_b"] == 30         # (20+40)/2
    assert body["avg_result"] == 50    # (30+70)/2
