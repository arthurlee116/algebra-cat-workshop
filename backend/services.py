from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import sympy as sp
from sqlalchemy import func
from sqlalchemy.orm import Session
from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

from .question_generator import (
    DifficultyLevel,
    GeneratedQuestion,
    VARIABLE_SYMBOLS,
    generate_question,
)
from .models import FoodPurchase, HistoryEntry, Question, QuestionAttempt, User
from .schemas import HistoryCreate, HistoryResponse, RecentQuestion

# 计分规则：根据难度决定一次答对和答错的分差。
SCORE_RULES: dict[DifficultyLevel, tuple[int, int]] = {
    "basic": (1, -1),
    "intermediate": (3, -1),
    "advanced": (5, -1),
}

MAX_ATTEMPTS_PER_QUESTION = 3
MAX_INPUT_LENGTH = 200
_TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application,)


def get_score_change(difficulty_level: DifficultyLevel, is_correct: bool) -> int:
    correct, incorrect = SCORE_RULES[difficulty_level]
    return correct if is_correct else incorrect


def clamp_score(value: int) -> int:
    return value if value > 0 else 0


def _sanitize_input(text: str) -> str:
    if len(text) > MAX_INPUT_LENGTH:
        raise ValueError("表达式过长，请缩短输入")
    if "__" in text or any(ch in text for ch in [";", "\n", "\r"]):
        raise ValueError("表达式包含无效字符")
    return text.replace("^", "**")


def normalize_expr(text: str) -> sp.Expr:
    sanitized = _sanitize_input(text)
    try:
        expr = parse_expr(
            sanitized,
            local_dict=VARIABLE_SYMBOLS,
            transformations=_TRANSFORMATIONS,
            evaluate=True,
        )
        return sp.simplify(expr)
    except Exception as exc:  # pragma: no cover - sympy errors are contextual
        raise ValueError(f"无法解析表达式: {exc}") from exc


def compare_expressions(left: sp.Expr, right: sp.Expr) -> bool:
    return sp.simplify(left - right) == 0


def get_cat_stage(total_score: int) -> int:
    if total_score <= 50:
        return 1
    if total_score <= 150:
        return 2
    if total_score <= 200:
        return 3
    return 4


def next_stage_threshold(total_score: int) -> int:
    stage = get_cat_stage(total_score)
    if stage == 1:
        return 51
    if stage == 2:
        return 151
    if stage == 3:
        return 201
    return total_score


def get_cat_score(db: Session, user_id: int) -> int:
    total = (
        db.query(func.coalesce(func.sum(FoodPurchase.cost), 0))
        .filter(FoodPurchase.user_id == user_id)
        .scalar()
    )
    return int(total or 0)


@dataclass
class AnswerResult:
    is_correct: bool
    difficulty_score: int
    score_change: int
    new_total_score: int
    attempt_count: int
    solution_expression: str | None


def _guard_attempt_status(question: Question) -> None:
    if question.is_solved:
        raise ValueError("该题已答对，请获取下一题")
    if question.attempts_used >= MAX_ATTEMPTS_PER_QUESTION:
        raise ValueError("该题已达到三次机会，请获取下一题")


def process_answer(
    db: Session,
    question: Question,
    user: User,
    user_answer: str,
) -> AnswerResult:
    _guard_attempt_status(question)

    correct_expr = normalize_expr(question.solution_expression)
    user_expr = normalize_expr(user_answer)
    is_correct = compare_expressions(correct_expr, user_expr)

    question.attempts_used += 1
    if is_correct:
        question.is_solved = True

    if is_correct:
        score_change = get_score_change(question.difficulty_level, True)
    elif question.attempts_used >= MAX_ATTEMPTS_PER_QUESTION:
        score_change = get_score_change(question.difficulty_level, False)
    else:
        score_change = 0

    if score_change:
        user.total_score = clamp_score(user.total_score + score_change)

    db_attempt = QuestionAttempt(
        question_id=question.question_id,
        user_id=user.id,
        expression_text=question.expression_text,
        topic=question.topic,
        difficulty_level=question.difficulty_level,
        difficulty_score=question.difficulty_score,
        user_answer=user_answer,
        is_correct=is_correct,
        score_change=score_change,
        attempt_index=question.attempts_used,
    )
    db.add(db_attempt)
    db.commit()
    db.refresh(user)
    db.refresh(question)

    solution = question.solution_expression if question.attempts_used >= MAX_ATTEMPTS_PER_QUESTION else None

    return AnswerResult(
        is_correct=is_correct,
        difficulty_score=question.difficulty_score,
        score_change=score_change,
        new_total_score=user.total_score,
        attempt_count=question.attempts_used,
        solution_expression=solution,
    )


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
