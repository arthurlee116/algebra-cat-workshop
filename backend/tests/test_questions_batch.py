import pytest
import pytest_asyncio
from httpx import AsyncClient
from backend.main import app
from backend.schemas import BatchGenerateRequest


@pytest.mark.asyncio
async def test_batch_generate_valid_count():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        resp = await ac.post("/api/questions/batch", json={"count": 5})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["questions"]) == 5
        for q in data["questions"]:
            assert "questionId" in q
            assert "expressionText" in q
            assert "solutionExpression" in q
            assert q["topic"] in ["add_sub", "mul_div", "poly_ops", "factorization", "mixed_ops"]


@pytest.mark.asyncio
async def test_batch_generate_with_difficulty():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        resp = await ac.post("/api/questions/batch", json={"count": 3, "difficulty": "basic"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["questions"]) == 3
        for q in data["questions"]:
            assert q["difficultyLevel"] == "basic"


@pytest.mark.asyncio
async def test_batch_generate_count_zero():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        resp = await ac.post("/api/questions/batch", json={"count": 0})
        assert resp.status_code == 422
        data = resp.json()
        assert "count" in str(data["detail"])


@pytest.mark.asyncio
async def test_batch_generate_count_too_large():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        resp = await ac.post("/api/questions/batch", json={"count": 21})
        assert resp.status_code == 422
        data = resp.json()
        assert "count" in str(data["detail"])


@pytest.mark.asyncio
async def test_batch_generate_invalid_difficulty():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        resp = await ac.post("/api/questions/batch", json={"count": 1, "difficulty": "invalid"})
        assert resp.status_code == 422
        data = resp.json()
        assert "difficulty" in str(data["detail"])


@pytest.mark.asyncio
async def test_batch_generate_max_count():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        resp = await ac.post("/api/questions/batch", json={"count": 20})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["questions"]) == 20
