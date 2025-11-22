from __future__ import annotations

import random
from typing import Optional
from datetime import datetime, timedelta

from .question_generator import DifficultyLevel, GeneratedQuestion, Topic, generate_question

from sqlalchemy.orm import Session
from .models import Question, HistoryEntry
from .schemas import RecentQuestion, HistoryCreate, HistoryResponse

# 计分规则：根据难度决定一次答对和答错的分差。
SCORE_RULES: dict[DifficultyLevel, tuple[int, int]] = {
    "basic": (1, -1),
    "intermediate": (3, -1),
    "advanced": (5, -1),
}


def get_score_change(difficulty_level: DifficultyLevel, is_correct: bool) -> int:
    correct, incorrect = SCORE_RULES[difficulty_level]
    return correct if is_correct else incorrect


def get_cat_stage(total_score: int) -> int:
    if total_score <= 50:
        return 1
    if total_score <= 150:
        return 2
    if total_score <= 300:
        return 3
    return 4


def next_stage_threshold(total_score: int) -> int:
    stage = get_cat_stage(total_score)
    if stage == 1:
        return 51
    if stage == 2:
        return 151
    if stage == 3:
        return 301
    return total_score


def generate_batch_questions(count: int, difficulty: Optional[DifficultyLevel] = None) -> list[GeneratedQuestion]:
    topics = ["add_sub", "mul_div", "poly_ops", "factorization", "mixed_ops"]
    difficulty_levels = ["basic", "intermediate", "advanced"]
    questions = []
    for _ in range(count):
        topic = random.choice(topics)
        diff_level = difficulty or random.choice(difficulty_levels)
        q = generate_question(topic, diff_level)
        questions.append(q)
    return questions


def get_recent_questions(db: Session, user_id: int) -> list[RecentQuestion]:
    questions = (
        db.query(Question)
        .filter(Question.user_id == user_id)
        .order_by(Question.created_at.desc())
        .limit(5)
        .all()
    )
    return [
        RecentQuestion(
            question_id=q.question_id,
            expression_text=q.expression_text,
            created_at=q.created_at,
        )
        for q in questions
    ]


def create_history_entry(db: Session, history: HistoryCreate) -> HistoryResponse:
    db_history = HistoryEntry(**history.model_dump())
    db.add(db_history)
    db.commit()
    db.refresh(db_history)
    return HistoryResponse.model_validate(db_history, from_attributes=True)


def get_history_entries(
    db: Session,
    user_id: int,
    limit: int = 20,
    offset: int = 0,
    min_score: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> list[HistoryResponse]:
    query = db.query(HistoryEntry).filter(HistoryEntry.user_id == user_id).order_by(HistoryEntry.created_at.desc())
    if min_score is not None:
        query = query.filter(HistoryEntry.score >= min_score)
    if date_from:
        query = query.filter(HistoryEntry.created_at >= date_from)
    if date_to:
        # If the client sends a date-only value (parsed as midnight), include the entire day by
        # filtering up to but not including the next day.
        if date_to.time() == datetime.min.time():
            query = query.filter(HistoryEntry.created_at < date_to + timedelta(days=1))
        else:
            query = query.filter(HistoryEntry.created_at <= date_to)
    histories = query.offset(offset).limit(limit).all()
    return [HistoryResponse.model_validate(h, from_attributes=True) for h in histories]
