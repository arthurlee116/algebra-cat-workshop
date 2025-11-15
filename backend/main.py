from __future__ import annotations

from datetime import datetime

import sympy as sp
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session
from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

from .config import get_settings
from .database import Base, engine, get_db
from .foods import FOOD_MAP, FOODS
from .models import FoodPurchase, Question, QuestionAttempt, User
from .question_generator import (
    DifficultyLevel,
    Topic,
    VARIABLE_SYMBOLS,
    generate_question,
)
from .schemas import (
    BuyFoodRequest,
    BuyFoodResponse,
    CheckAnswerRequest,
    CheckAnswerResponse,
    FoodItem,
    FoodListResponse,
    GenerateQuestionRequest,
    GenerateQuestionResponse,
    LoginRequest,
    LoginResponse,
    UserSummaryResponse,
)
from .services import get_cat_stage, get_score_change, next_stage_threshold

# Ensure tables exist before the first request
Base.metadata.create_all(bind=engine)

app = FastAPI(title="七年级整式练习 API", version="1.0.0")
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_SYMBOLS = VARIABLE_SYMBOLS
_TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application,)


def _normalize_expr(text: str) -> sp.Expr:
    sanitized = text.replace("^", "**")
    try:
        expr = parse_expr(sanitized, local_dict=_SYMBOLS, transformations=_TRANSFORMATIONS, evaluate=True)
        return sp.simplify(expr)
    except Exception as exc:  # pragma: no cover - sympy errors are contextual
        raise HTTPException(status_code=400, detail=f"无法解析表达式: {exc}") from exc


def _clamp_score(value: int) -> int:
    return value if value > 0 else 0


def _get_cat_score(db: Session, user_id: int) -> int:
    total = (
        db.query(func.coalesce(func.sum(FoodPurchase.cost), 0))
        .filter(FoodPurchase.user_id == user_id)
        .scalar()
    )
    return int(total or 0)


@app.post("/api/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .filter(
            User.chinese_name == payload.chinese_name,
            User.english_name == payload.english_name,
            User.class_name == payload.class_name,
        )
        .first()
    )
    if not user:
        user = User(
            chinese_name=payload.chinese_name,
            english_name=payload.english_name,
            class_name=payload.class_name,
            total_score=0,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return LoginResponse(
        userId=user.id,
        chinese_name=user.chinese_name,
        english_name=user.english_name,
        class_name=user.class_name,
        total_score=user.total_score,
    )


@app.post("/api/generate_question", response_model=GenerateQuestionResponse)
def create_question(payload: GenerateQuestionRequest, db: Session = Depends(get_db)):
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="未找到该学生")

    topic = payload.topic
    difficulty_level = payload.difficulty_level
    try:
        question = generate_question(topic=topic, difficulty_level=difficulty_level)  # type: ignore[arg-type]
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    db_question = Question(
        question_id=question.question_id,
        user_id=user.id,
        expression_text=question.expression_text,
        solution_expression=question.solution_expression,
        topic=question.topic,
        difficulty_level=question.difficulty_level,
        difficulty_score=question.difficulty_score,
    )
    db.add(db_question)
    db.commit()

    return GenerateQuestionResponse(
        questionId=db_question.question_id,
        topic=db_question.topic,
        difficultyLevel=db_question.difficulty_level,
        expressionText=db_question.expression_text,
        difficultyScore=db_question.difficulty_score,
    )


@app.post("/api/check_answer", response_model=CheckAnswerResponse)
def check_answer(payload: CheckAnswerRequest, db: Session = Depends(get_db)):
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="未找到该学生")

    question = db.query(Question).filter(
        Question.question_id == payload.question_id,
        Question.user_id == user.id,
    ).first()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在或已过期")

    if question.is_solved:
        raise HTTPException(status_code=400, detail="该题已答对，请获取下一题")

    if question.attempts_used >= 3:
        raise HTTPException(status_code=400, detail="该题已达到三次机会，请获取下一题")

    correct_expr = _normalize_expr(question.solution_expression)
    user_expr = _normalize_expr(payload.user_answer)
    is_correct = sp.simplify(correct_expr - user_expr) == 0

    question.attempts_used += 1
    if is_correct:
        question.is_solved = True

    # 只有答对或者三次机会全部用尽仍然错误时才变动积分
    if is_correct:
        score_change = get_score_change(question.difficulty_level, True)
    elif question.attempts_used >= 3:
        score_change = get_score_change(question.difficulty_level, False)
    else:
        score_change = 0

    if score_change:
        user.total_score = _clamp_score(user.total_score + score_change)

    db_attempt = QuestionAttempt(
        question_id=question.question_id,
        user_id=user.id,
        expression_text=question.expression_text,
        topic=question.topic,
        difficulty_level=question.difficulty_level,
        difficulty_score=question.difficulty_score,
        user_answer=payload.user_answer,
        is_correct=is_correct,
        score_change=score_change,
        attempt_index=question.attempts_used,
    )
    db.add(db_attempt)
    db.commit()
    db.refresh(user)
    db.refresh(question)

    # 如果机会用尽，返回标准答案
    solution = None
    if question.attempts_used >= 3:
        solution = question.solution_expression

    return CheckAnswerResponse(
        isCorrect=is_correct,
        difficultyScore=question.difficulty_score,
        scoreChange=score_change,
        newTotalScore=user.total_score,
        attemptCount=question.attempts_used,
        solutionExpression=solution,
    )


@app.post("/api/buy_food", response_model=BuyFoodResponse)
def buy_food(payload: BuyFoodRequest, db: Session = Depends(get_db)):
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="未找到该学生")

    food = FOOD_MAP.get(payload.food_id)
    if not food:
        raise HTTPException(status_code=404, detail="未找到该食物")

    if user.total_score < food.price:
        raise HTTPException(status_code=400, detail="积分不足")

    user.total_score -= food.price
    purchase = FoodPurchase(
        user_id=user.id,
        food_id=food.food_id,
        food_name=food.name,
        cost=food.price,
    )
    db.add(purchase)
    db.commit()
    db.refresh(user)

    cat_score = _get_cat_score(db, user.id)

    return BuyFoodResponse(
        success=True,
        newTotalScore=user.total_score,
        currentCatStage=get_cat_stage(cat_score),
    )


@app.get("/api/foods", response_model=FoodListResponse)
def list_foods():
    return FoodListResponse(
        foods=[
            FoodItem(
                foodId=food.food_id,
                name=food.name,
                description=food.description,
                price=food.price,
                image=food.image,
            )
            for food in FOODS
        ]
    )


@app.get("/api/users/{user_id}/summary", response_model=UserSummaryResponse)
def summary(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="未找到该学生")

    cat_score = _get_cat_score(db, user.id)

    return UserSummaryResponse(
        userId=user.id,
        totalScore=user.total_score,
        catScore=cat_score,
        currentCatStage=get_cat_stage(cat_score),
        nextStageScore=next_stage_threshold(cat_score),
        updated_at=datetime.utcnow(),
    )
