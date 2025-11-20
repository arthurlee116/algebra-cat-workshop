import pytest
from fastapi.testclient import TestClient
from backend.main import app


client = TestClient(app)


def test_recent_questions_empty():
    # Create new user
    login_data = {
        "chinese_name": "Test User CN",
        "english_name": "Test User EN",
        "class_name": "Test Class",
    }
    login_resp = client.post("/api/login", json=login_data)
    assert login_resp.status_code == 200
    user_id = login_resp.json()["userId"]

    # No questions yet
    resp = client.get(f"/api/users/{user_id}/recent_questions")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["questions"]) == 0


def test_recent_questions_one():
    # Create user
    login_data = {
        "chinese_name": "Test CN2",
        "english_name": "Test EN2",
        "class_name": "Test Class2",
    }
    login_resp = client.post("/api/login", json=login_data)
    user_id = login_resp.json()["userId"]

    # Generate one question
    gen_data = {
        "userId": user_id,
        "topic": "add_sub",
        "difficultyLevel": "basic",
    }
    gen_resp = client.post("/api/generate_question", json=gen_data)
    assert gen_resp.status_code == 200

    # Get recent
    resp = client.get(f"/api/users/{user_id}/recent_questions")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["questions"]) == 1
    q = data["questions"][0]
    assert q["expressionText"]  # non empty
    assert "createdAt" in q


def test_recent_questions_multiple_limit():
    # Create user
    login_data = {
        "chinese_name": "Test CN3",
        "english_name": "Test EN3",
        "class_name": "Test Class3",
    }
    login_resp = client.post("/api/login", json=login_data)
    user_id = login_resp.json()["userId"]

    # Generate 6 questions
    for i in range(6):
        gen_data = {
            "userId": user_id,
            "topic": "add_sub",
            "difficultyLevel": "basic",
        }
        gen_resp = client.post("/api/generate_question", json=gen_data)
        assert gen_resp.status_code == 200

    # Get recent: should be 5, newest first
    resp = client.get(f"/api/users/{user_id}/recent_questions")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["questions"]) == 5
    # Check ordered by created_at desc (ISO strings lex sortable)
    times = [q["createdAt"] for q in data["questions"]]
    assert times == sorted(times, reverse=True)


def test_recent_questions_invalid_user():
    resp = client.get("/api/users/999/recent_questions")
    assert resp.status_code == 404
