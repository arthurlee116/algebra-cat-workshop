import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app

@pytest.mark.asyncio
async def test_batch_generate_valid_count():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/questions/batch", json={"count": 5})
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data["questions"]) == 5
    for q in data["questions"]:
        assert "solutionExpression" in q
        assert q["difficultyLevel"] == "basic"

@pytest.mark.asyncio
async def test_batch_generate_invalid_count_low():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/questions/batch", json={"count": 0})
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_batch_generate_invalid_count_high():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/questions/batch", json={"count": 21})
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_batch_generate_with_difficulty():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/questions/batch", json={"count": 3, "difficulty": "advanced"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["questions"]) == 3
    for q in data["questions"]:
        assert q["difficultyLevel"] == "advanced"
