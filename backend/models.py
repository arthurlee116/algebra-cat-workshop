from __future__ import annotations

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    chinese_name = Column(String, nullable=False)
    english_name = Column(String, nullable=False)
    class_name = Column(String, nullable=False)
    total_score = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    questions = relationship("Question", back_populates="user")
    attempts = relationship("QuestionAttempt", back_populates="user")
    purchases = relationship("FoodPurchase", back_populates="user")


class Question(Base):
    __tablename__ = "questions"

    question_id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expression_text = Column(String, nullable=False)
    solution_expression = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    difficulty_level = Column(String, nullable=False)
    difficulty_score = Column(Integer, nullable=False)
    attempts_used = Column(Integer, default=0)
    is_solved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="questions")
    attempts = relationship("QuestionAttempt", back_populates="question")


class QuestionAttempt(Base):
    __tablename__ = "question_attempts"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(String, ForeignKey("questions.question_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expression_text = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    difficulty_level = Column(String, nullable=False)
    difficulty_score = Column(Integer, nullable=False)
    user_answer = Column(String, nullable=False)
    is_correct = Column(Boolean, default=False)
    score_change = Column(Integer, default=0)
    attempt_index = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="attempts")
    question = relationship("Question", back_populates="attempts")


class FoodPurchase(Base):
    __tablename__ = "food_purchases"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    food_id = Column(String, nullable=False)
    food_name = Column(String, nullable=False)
    cost = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="purchases")


class HistoryEntry(Base):
    __tablename__ = "history_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_text = Column(String, nullable=False)
    user_answer = Column(String, nullable=False)
    score = Column(Integer, nullable=False)
    correct_answer = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
