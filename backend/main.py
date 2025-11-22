from __future__ import annotations

from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional

from .config import get_settings
from .database import Base, engine, get_db
from .foods import FOOD_MAP, FOODS
from .models import FoodPurchase, Question, User
from .question_generator import generate_question
from .schemas import (
    BatchQuestion,
    BuyFoodRequest,
    BuyFoodResponse,
    BatchGenerateRequest,
    BatchGenerateResponse,
    CheckAnswerRequest,
    CheckAnswerResponse,
    FoodItem,
    FoodListResponse,
    GenerateQuestionRequest,
    GenerateQuestionResponse,
    LoginRequest,
    LoginResponse,
    RecentQuestionsResponse,
    UserSummaryResponse,
    HistoryCreate,
    HistoryResponse,
)
from .services import (
    AnswerResult,
    create_history_entry,
    generate_batch_questions,
    get_cat_score,
    get_cat_stage,
    get_history_entries,
    get_recent_questions,
    next_stage_threshold,
    process_answer,
)

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


def _get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="未找到该学生")
    return user


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
        expressionLatex=question.expression_latex,
        difficultyScore=db_question.difficulty_score,
    )


@app.post("/api/questions/batch", response_model=BatchGenerateResponse)
def batch_generate_questions(payload: BatchGenerateRequest):
    questions = generate_batch_questions(payload.count, payload.difficulty)
    return BatchGenerateResponse(
        questions=[
            BatchQuestion.model_validate(q, from_attributes=True)
            for q in questions
        ]
    )


@app.post("/api/check_answer", response_model=CheckAnswerResponse)
def check_answer(payload: CheckAnswerRequest, db: Session = Depends(get_db)):
    user = _get_user_or_404(db, payload.user_id)

    question = db.query(Question).filter(
        Question.question_id == payload.question_id,
        Question.user_id == user.id,
    ).first()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在或已过期")

    try:
        result: AnswerResult = process_answer(db, question, user, payload.user_answer)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return CheckAnswerResponse(
        isCorrect=result.is_correct,
        difficultyScore=result.difficulty_score,
        scoreChange=result.score_change,
        newTotalScore=result.new_total_score,
        attemptCount=result.attempt_count,
        solutionExpression=result.solution_expression,
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

    cat_score = get_cat_score(db, user.id)

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
    user = _get_user_or_404(db, user_id)

    cat_score = get_cat_score(db, user.id)

    return UserSummaryResponse(
        userId=user.id,
        totalScore=user.total_score,
        catScore=cat_score,
        currentCatStage=get_cat_stage(cat_score),
        nextStageScore=next_stage_threshold(cat_score),
        updated_at=datetime.utcnow(),
    )


@app.get("/api/users/{user_id}/recent_questions", response_model=RecentQuestionsResponse)
def recent_questions(user_id: int, db: Session = Depends(get_db)):
    _get_user_or_404(db, user_id)

    questions = get_recent_questions(db, user_id)
    return RecentQuestionsResponse(questions=questions)


@app.post("/api/history", response_model=HistoryResponse)
def post_history(payload: HistoryCreate, db: Session = Depends(get_db)):
    _get_user_or_404(db, payload.user_id)
    return create_history_entry(db, payload)


@app.get("/api/history", response_model=list[HistoryResponse])
def get_history(
    user_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = 0,
    min_score: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db),
):
    _get_user_or_404(db, user_id)
    return get_history_entries(
        db, user_id, limit, offset, min_score, date_from, date_to
    )
