from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class APIModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class LoginRequest(APIModel):
    chinese_name: str
    english_name: str
    class_name: str


class LoginResponse(APIModel):
    user_id: int = Field(alias="userId")
    chinese_name: str
    english_name: str
    class_name: str
    total_score: int


class GenerateQuestionRequest(APIModel):
    user_id: int = Field(alias="userId")
    topic: str
    difficulty_level: str = Field(alias="difficultyLevel")


class GenerateQuestionResponse(APIModel):
    question_id: str = Field(alias="questionId")
    topic: str
    difficulty_level: str = Field(alias="difficultyLevel")
    expression_text: str = Field(alias="expressionText")
    expression_latex: str = Field(alias="expressionLatex")
    difficulty_score: int = Field(alias="difficultyScore")


class CheckAnswerRequest(APIModel):
    user_id: int = Field(alias="userId")
    question_id: str = Field(alias="questionId")
    expression_text: str = Field(alias="expressionText")
    topic: str
    difficulty_level: str = Field(alias="difficultyLevel")
    user_answer: str = Field(alias="userAnswer")


class CheckAnswerResponse(APIModel):
    is_correct: bool = Field(alias="isCorrect")
    difficulty_score: int = Field(alias="difficultyScore")
    score_change: int = Field(alias="scoreChange")
    new_total_score: int = Field(alias="newTotalScore")
    attempt_count: int = Field(alias="attemptCount")
    solution_expression: str | None = Field(default=None, alias="solutionExpression")


class BuyFoodRequest(APIModel):
    user_id: int = Field(alias="userId")
    food_id: str = Field(alias="foodId")


class BuyFoodResponse(APIModel):
    success: bool
    new_total_score: int = Field(alias="newTotalScore")
    current_cat_stage: int = Field(alias="currentCatStage")


class FoodItem(APIModel):
    food_id: str = Field(alias="foodId")
    name: str
    description: str
    price: int
    image: str


class FoodListResponse(APIModel):
    foods: list[FoodItem]


class UserSummaryResponse(APIModel):
    user_id: int = Field(alias="userId")
    total_score: int = Field(alias="totalScore")
    cat_score: int = Field(alias="catScore")
    current_cat_stage: int = Field(alias="currentCatStage")
    next_stage_score: int = Field(alias="nextStageScore")
    updated_at: datetime

    model_config = ConfigDict(
        populate_by_name=True,
        json_encoders={datetime: lambda v: v.isoformat()},
    )


class BatchGenerateRequest(APIModel):
    count: int = Field(..., gt=0, le=20)
    difficulty: Optional[Literal["basic", "intermediate", "advanced"]] = None


class BatchQuestion(APIModel):
    question_id: str = Field(..., alias="questionId")
    topic: Literal["add_sub", "mul_div", "poly_ops", "factorization", "mixed_ops"]
    difficulty_level: Literal["basic", "intermediate", "advanced"] = Field(..., alias="difficultyLevel")
    expression_text: str = Field(..., alias="expressionText")
    expression_latex: str = Field(..., alias="expressionLatex")
    difficulty_score: int = Field(..., alias="difficultyScore")
    solution_expression: str = Field(..., alias="solutionExpression")


class BatchGenerateResponse(APIModel):
    questions: list[BatchQuestion]


class RecentQuestion(APIModel):
    question_id: str = Field(..., alias="questionId")
    expression_text: str = Field(..., alias="expressionText")
    created_at: datetime = Field(..., alias="createdAt")


class RecentQuestionsResponse(APIModel):
    questions: list[RecentQuestion]


class HistoryCreate(APIModel):
    user_id: int
    question_text: str
    user_answer: str
    score: int
    correct_answer: Optional[str] = None


class HistoryResponse(APIModel):
    id: int
    user_id: int
    question_text: str
    user_answer: str
    score: int
    correct_answer: Optional[str] | None
    created_at: datetime

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        json_encoders={datetime: lambda v: v.isoformat()},
    )
