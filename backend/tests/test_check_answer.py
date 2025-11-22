import pytest
from httpx import AsyncClient

from backend.main import app
from backend.models import Question


async def _create_user(ac: AsyncClient, suffix: str) -> int:
    resp = await ac.post(
        "/api/login",
        json={
            "chinese_name": f"测试{suffix}",
            "english_name": f"Tester{suffix}",
            "class_name": f"Class{suffix}",
        },
    )
    resp.raise_for_status()
    return resp.json()["userId"]


async def _generate_question(ac: AsyncClient, user_id: int, db) -> Question:
    resp = await ac.post(
        "/api/generate_question",
        json={"userId": user_id, "topic": "add_sub", "difficultyLevel": "basic"},
    )
    resp.raise_for_status()
    question_id = resp.json()["questionId"]
    question = db.get(Question, question_id)
    assert question is not None
    return question


@pytest.mark.asyncio
async def test_check_answer_correct_flow(db_session):
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        user_id = await _create_user(ac, "Correct")
        question = await _generate_question(ac, user_id, db_session)

        resp = await ac.post(
            "/api/check_answer",
            json={
                "userId": user_id,
                "questionId": question.question_id,
                "expressionText": question.expression_text,
                "topic": question.topic,
                "difficultyLevel": question.difficulty_level,
                "userAnswer": question.solution_expression,
            },
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["isCorrect"] is True
        assert data["attemptCount"] == 1
        assert data["scoreChange"] > 0
        assert data["solutionExpression"] is None


@pytest.mark.asyncio
async def test_check_answer_attempt_limits_and_solution_reveal(db_session):
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        user_id = await _create_user(ac, "Limits")
        question = await _generate_question(ac, user_id, db_session)

        wrong_answer = "0"
        # exhaust attempts
        for attempt in range(1, 4):
            resp = await ac.post(
                "/api/check_answer",
                json={
                    "userId": user_id,
                    "questionId": question.question_id,
                    "expressionText": question.expression_text,
                    "topic": question.topic,
                    "difficultyLevel": question.difficulty_level,
                    "userAnswer": wrong_answer,
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["attemptCount"] == attempt

        assert data["solutionExpression"] == question.solution_expression
        assert data["isCorrect"] is False

        # fourth attempt should be rejected
        resp = await ac.post(
            "/api/check_answer",
            json={
                "userId": user_id,
                "questionId": question.question_id,
                "expressionText": question.expression_text,
                "topic": question.topic,
                "difficultyLevel": question.difficulty_level,
                "userAnswer": wrong_answer,
            },
        )
        assert resp.status_code == 400
        assert "三次机会" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_check_answer_rejects_suspicious_input(db_session):
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        user_id = await _create_user(ac, "BadInput")
        question = await _generate_question(ac, user_id, db_session)

        resp = await ac.post(
            "/api/check_answer",
            json={
                "userId": user_id,
                "questionId": question.question_id,
                "expressionText": question.expression_text,
                "topic": question.topic,
                "difficultyLevel": question.difficulty_level,
                "userAnswer": "1; import os",
            },
        )

        assert resp.status_code == 400
        assert "无效字符" in resp.json()["detail"]
