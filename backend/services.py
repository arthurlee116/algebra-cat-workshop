from __future__ import annotations

from typing import Literal

DifficultyLevel = Literal["basic", "intermediate", "advanced"]

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
