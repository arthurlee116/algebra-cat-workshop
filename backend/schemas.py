from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    chinese_name: str
    english_name: str
    class_name: str


class LoginResponse(BaseModel):
    user_id: int = Field(alias="userId")
    chinese_name: str
    english_name: str
    class_name: str
    total_score: int

    class Config:
        populate_by_name = True


class GenerateQuestionRequest(BaseModel):
    user_id: int = Field(alias="userId")
    topic: str
    difficulty_level: str = Field(alias="difficultyLevel")


class GenerateQuestionResponse(BaseModel):
    question_id: str = Field(alias="questionId")
    topic: str
    difficulty_level: str = Field(alias="difficultyLevel")
    expression_text: str = Field(alias="expressionText")
    difficulty_score: int = Field(alias="difficultyScore")


class CheckAnswerRequest(BaseModel):
    user_id: int = Field(alias="userId")
    question_id: str = Field(alias="questionId")
    expression_text: str = Field(alias="expressionText")
    topic: str
    difficulty_level: str = Field(alias="difficultyLevel")
    user_answer: str = Field(alias="userAnswer")


class CheckAnswerResponse(BaseModel):
    is_correct: bool = Field(alias="isCorrect")
    difficulty_score: int = Field(alias="difficultyScore")
    score_change: int = Field(alias="scoreChange")
    new_total_score: int = Field(alias="newTotalScore")
    attempt_count: int = Field(alias="attemptCount")


class BuyFoodRequest(BaseModel):
    user_id: int = Field(alias="userId")
    food_id: str = Field(alias="foodId")


class BuyFoodResponse(BaseModel):
    success: bool
    new_total_score: int = Field(alias="newTotalScore")
    current_cat_stage: int = Field(alias="currentCatStage")


class FoodItem(BaseModel):
    food_id: str = Field(alias="foodId")
    name: str
    description: str
    price: int
    image: str


class FoodListResponse(BaseModel):
    foods: list[FoodItem]


class UserSummaryResponse(BaseModel):
    user_id: int = Field(alias="userId")
    total_score: int = Field(alias="totalScore")
    current_cat_stage: int = Field(alias="currentCatStage")
    next_stage_score: int = Field(alias="nextStageScore")
    updated_at: datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
