import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.anyio
async def test_generate_success(monkeypatch):
    async def fake_llm(s, u):
        return "Fake answer"

    monkeypatch.setattr(
       "services.llm_client.call_llm_async",
       fake_llm
    )

    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post("/generate", json={
            "user_message":"test","intent":"i","entities":{},"context_data":""},
            headers={"x-api-key":"supersecret-service-key"})
    assert resp.status_code == 200
    assert resp.json()["final_answer"] == "Fake answer"