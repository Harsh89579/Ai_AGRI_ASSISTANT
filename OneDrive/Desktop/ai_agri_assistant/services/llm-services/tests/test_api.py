import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.anyio
async def test_generate_success(monkeypatch):

    def fake_llm(system, user):
        return "Fake answer"

    monkeypatch.setattr(
        "services.llm_client.call_llm",
        fake_llm
    )

    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post(
            "/generate",
            json={
                "user_message": "test",
                "intent": "i",
                "entities": {},
                "context_data": ""
            },
            headers={"x-api-key": "supersecret-service-key"}
        )

    assert resp.status_code == 200
    assert resp.json()["final_answer"] == "Fake answer"