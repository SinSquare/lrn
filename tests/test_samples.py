"""Tests for GET /samples."""


def test_samples_limit(client, seed_samples):
    resp = client.get("/samples", params={"limit": 2})
    assert resp.status_code == 200
    body = resp.json()
    assert [s["id"] for s in body["samples"]] == [5, 4]
    assert [s["prompt"] for s in body["samples"]] == ["triage prompt", "triage prompt"]
    assert [s["message"] for s in body["samples"]] == [
        "sample message number 5 with enough text",
        "sample message number 4 with enough text",
    ]
    assert [s["output"]["summary"] for s in body["samples"]] == [
        "Summary for sample 5",
        "Summary for sample 4",
    ]
    assert all(s["expected_output"] is None for s in body["samples"])
    assert all(s["updated_at"] is None for s in body["samples"])
    assert body["meta"]["next_id"] == 3


def test_samples_from_filter(client, seed_samples):
    resp = client.get("/samples", params={"from": 3, "limit": 10})
    assert resp.status_code == 200
    body = resp.json()
    assert [s["id"] for s in body["samples"]] == [3, 2, 1]
    assert body["meta"]["next_id"] is None


def test_samples_from_with_limit_sets_next_id(client, seed_samples):
    resp = client.get("/samples", params={"from": 4, "limit": 2})
    assert resp.status_code == 200
    body = resp.json()
    assert [s["id"] for s in body["samples"]] == [4, 3]
    assert body["meta"]["next_id"] == 2


def test_samples_invalid_limit_returns_400(client):
    resp = client.get("/samples", params={"limit": 0})
    assert resp.status_code == 400
    body = resp.json()
    assert set(body.keys()) == {"message"}
    assert isinstance(body["message"], str)
    assert "limit" in body["message"]


def test_samples_invalid_from_returns_400(client):
    resp = client.get("/samples", params={"from": 0})
    assert resp.status_code == 400
    body = resp.json()
    assert set(body.keys()) == {"message"}
    assert isinstance(body["message"], str)
    assert "from" in body["message"]


def test_samples_non_integer_limit_returns_400(client):
    resp = client.get("/samples", params={"limit": "abc"})
    assert resp.status_code == 400
    body = resp.json()
    assert set(body.keys()) == {"message"}
    assert isinstance(body["message"], str)
    assert body["message"]
