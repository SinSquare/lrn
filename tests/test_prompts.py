"""Tests for GET /prompts."""


def test_prompts_limit(client, seed_prompts):
    resp = client.get("/prompts", params={"limit": 2})
    assert resp.status_code == 200
    body = resp.json()
    assert [p["id"] for p in body["prompts"]] == [5, 4]
    assert [p["prompt"] for p in body["prompts"]] == ["prompt-5", "prompt-4"]
    assert body["meta"]["next_id"] == 3


def test_prompts_from_filter(client, seed_prompts):
    resp = client.get("/prompts", params={"from": 3, "limit": 10})
    assert resp.status_code == 200
    body = resp.json()
    assert [p["id"] for p in body["prompts"]] == [3, 2, 1]
    assert body["meta"]["next_id"] is None


def test_prompts_from_with_limit_sets_next_id(client, seed_prompts):
    resp = client.get("/prompts", params={"from": 4, "limit": 2})
    assert resp.status_code == 200
    body = resp.json()
    assert [p["id"] for p in body["prompts"]] == [4, 3]
    assert body["meta"]["next_id"] == 2


def test_prompts_invalid_limit_returns_400(client):
    resp = client.get("/prompts", params={"limit": 0})
    assert resp.status_code == 400
    body = resp.json()
    assert set(body.keys()) == {"message"}
    assert isinstance(body["message"], str)
    assert "limit" in body["message"]


def test_prompts_invalid_from_returns_400(client):
    resp = client.get("/prompts", params={"from": 0})
    assert resp.status_code == 400
    body = resp.json()
    assert set(body.keys()) == {"message"}
    assert isinstance(body["message"], str)
    assert "from" in body["message"]


def test_prompts_non_integer_limit_returns_400(client):
    resp = client.get("/prompts", params={"limit": "abc"})
    assert resp.status_code == 400
    body = resp.json()
    assert set(body.keys()) == {"message"}
    assert isinstance(body["message"], str)
    assert body["message"]
