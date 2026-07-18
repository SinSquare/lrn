"""Tests for POST /process."""

from unittest.mock import AsyncMock, patch

from tests.conftest import make_triage

PROCESS_MESSAGE = "checkout is broken and payments fail for all users"


def test_process_creates_sample_and_schedules_review(client, seed_prompts):
    triage = make_triage(summary="Payments outage")

    with (
        patch("lrn.routes.process.get_config") as get_config,
        patch(
            "lrn.routes.process.triage_message",
            new=AsyncMock(return_value=triage),
        ) as triage_mock,
        patch(
            "lrn.routes.process.review_sample_background",
            new=AsyncMock(),
        ) as review_mock,
    ):
        get_config.return_value.gemini_api_key = "test-key"
        resp = client.post("/process", json={"message": PROCESS_MESSAGE})

    assert resp.status_code == 200
    assert resp.json()["summary"] == "Payments outage"
    triage_mock.assert_awaited_once()
    review_mock.assert_awaited_once()
    sample_id = review_mock.await_args.args[0]
    assert isinstance(sample_id, int)

    samples = client.get("/samples", params={"limit": 1}).json()["samples"]
    assert samples[0]["id"] == sample_id
    assert samples[0]["message"] == PROCESS_MESSAGE
    assert samples[0]["output"]["summary"] == "Payments outage"
    assert samples[0]["score"] is None


def test_process_missing_api_key_returns_500(client, seed_prompts):
    with patch("lrn.routes.process.get_config") as get_config:
        get_config.return_value.gemini_api_key = None
        resp = client.post("/process", json={"message": PROCESS_MESSAGE})

    assert resp.status_code == 500
    assert resp.json() == {"message": "Gemini API key is not configured"}


def test_process_no_prompt_returns_404(client):
    with (
        patch("lrn.routes.process.get_config") as get_config,
        patch(
            "lrn.routes.process.triage_message",
            new=AsyncMock(return_value=make_triage()),
        ),
    ):
        get_config.return_value.gemini_api_key = "test-key"
        resp = client.post("/process", json={"message": PROCESS_MESSAGE})

    assert resp.status_code == 404
    assert resp.json() == {"message": "No prompt found"}


def test_process_invalid_message_returns_400(client, seed_prompts):
    with patch("lrn.routes.process.get_config") as get_config:
        get_config.return_value.gemini_api_key = "test-key"
        resp = client.post("/process", json={"message": "too short"})

    assert resp.status_code == 400
    body = resp.json()
    assert set(body.keys()) == {"message"}
    assert "message" in body["message"]
