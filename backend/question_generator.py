from __future__ import annotations

import random
import uuid
from dataclasses import dataclass
from typing import Literal

import sympy as sp

x = sp.Symbol("x")

Topic = Literal["add_sub", "mul_div", "factorization"]
DifficultyLevel = Literal["basic", "intermediate", "advanced"]

# Target ranges for each difficulty bucket so the generator can retry until
# the computed score falls inside the requested interval.
DIFFICULTY_RANGES: dict[DifficultyLevel, tuple[int, int]] = {
    "basic": (0, 33),
    "intermediate": (34, 66),
    "advanced": (67, 100),
}


@dataclass
class GeneratedQuestion:
    question_id: str
    expression_text: str
    solution_expression: str
    topic: Topic
    difficulty_level: DifficultyLevel
    difficulty_score: int


def humanize_expression(expr: sp.Expr) -> str:
    """Convert a SymPy expression to the input format x^2 + 3x."""

    expr = sp.expand(expr)
    try:
        poly = sp.Poly(expr, x)
    except sp.PolynomialError:
        # Fallback for expressions that are not plain polynomials (e.g. with division)
        text = str(expr)
        return text.replace("**", "^").replace("*", "")

    if poly.is_zero:
        return "0"

    parts: list[str] = []
    for monom, coeff in poly.terms():
        exponent = monom[0]
        coeff_int = int(coeff)
        if coeff_int == 0:
            continue
        sign = "+" if coeff_int > 0 else "-"
        abs_coeff = abs(coeff_int)
        if exponent == 0:
            term_body = f"{abs_coeff}"
        elif exponent == 1:
            term_body = "x" if abs_coeff == 1 else f"{abs_coeff}x"
        else:
            power = f"x^{exponent}"
            term_body = power if abs_coeff == 1 else f"{abs_coeff}{power}"
        parts.append(f" {sign} {term_body}")

    text = "".join(parts).strip()
    if text.startswith("+"):
        text = text[1:].strip()
    text = text.replace("  ", " ")
    text = text.replace("+-", "-")
    return text


def random_polynomial(max_degree: int, coeff_min: int = -6, coeff_max: int = 6) -> sp.Expr:
    degree = random.randint(1, max_degree)
    expr = sp.Integer(0)
    for power in range(degree, -1, -1):
        coeff = random.randint(coeff_min, coeff_max)
        if coeff == 0:
            continue
        expr += coeff * x**power
    if expr == 0:
        return random_polynomial(max_degree, coeff_min, coeff_max)
    return expr


def build_add_sub_expression() -> tuple[str, sp.Expr]:
    # 多项式加减：随机组合 2-4 个多项式，并记录括号表达式方便前端显示。
    term_count = random.randint(2, 4)
    segments = []
    total_expr = sp.Integer(0)
    for index in range(term_count):
        poly = random_polynomial(random.choice([2, 3]))
        display = humanize_expression(poly)
        if index == 0:
            sign = 1
            prefix = ""
        else:
            sign = random.choice([1, -1])
            prefix = " + " if sign == 1 else " - "
        total_expr += sign * poly
        segments.append(f"{prefix}({display})")
    display_expression = "".join(segments)
    return display_expression, total_expr


def build_mul_div_expression() -> tuple[str, sp.Expr]:
    # 乘除题包含三种结构，全部保证结果仍旧是整式，便于比对。
    pattern = random.choice(["binomial_product", "monomial_product", "polynomial_division"])
    if pattern == "binomial_product":
        a1, b1 = random.randint(-5, 5), random.randint(-5, 5)
        a2, b2 = random.randint(-5, 5), random.randint(-5, 5)
        a1 = a1 or 1
        a2 = a2 or -1
        expr1 = a1 * x + b1
        expr2 = a2 * x + b2
        display = f"({humanize_expression(expr1)})({humanize_expression(expr2)})"
        return display, sp.expand(expr1 * expr2)
    if pattern == "monomial_product":
        coeff = random.randint(2, 6)
        power = random.randint(1, 3)
        mono = coeff * x**power
        poly = random_polynomial(random.choice([2, 3]))
        display = f"({humanize_expression(mono)})({humanize_expression(poly)})"
        return display, sp.expand(mono * poly)
    # polynomial_division
    divisor = random_polynomial(1)
    quotient = random_polynomial(random.choice([1, 2]))
    dividend = sp.expand(divisor * quotient)
    display = f"({humanize_expression(dividend)}) / ({humanize_expression(divisor)})"
    return display, sp.simplify(dividend / divisor)


def build_factorization_expression() -> tuple[str, sp.Expr]:
    # 因式分解题基于常见模式（完全平方、二次三项式、平方差、分组提取）。
    pattern = random.choice(["square", "quadratic", "diff_square", "grouping"])
    if pattern == "square":
        a = random.randint(1, 4)
        b = random.randint(-6, 6)
        expr = sp.expand((a * x + b) ** 2)
        return humanize_expression(expr), expr
    if pattern == "quadratic":
        p = random.randint(1, 4)
        q = random.randint(1, 4)
        m = random.randint(-6, 6)
        n = random.randint(-6, 6)
        expr = sp.expand((p * x + m) * (q * x + n))
        return humanize_expression(expr), expr
    if pattern == "diff_square":
        a = random.randint(2, 6)
        b = random.randint(1, 5)
        expr = (a * x) ** 2 - (b) ** 2
        return humanize_expression(expr), expr
    # grouping
    a = random.randint(1, 5)
    b = random.randint(1, 5)
    c = random.randint(-6, 6)
    d = random.randint(-6, 6)
    expr = sp.expand((a * x + c) * x + (b * x + d) * x)
    return humanize_expression(expr), expr


def compute_difficulty(expr: sp.Expr, topic: Topic) -> int:
    """Rough difficulty estimation between 0 and 100."""

    expanded = sp.expand(expr)
    poly = None
    try:
        poly = sp.Poly(expanded, x)
    except sp.PolynomialError:
        pass

    degree = poly.degree() if poly else 2
    term_count = len(poly.terms()) if poly else len(str(expanded).split("+"))
    coeffs = [abs(int(c)) for c in (poly.all_coeffs() if poly else [1])]
    max_coeff = max(coeffs) if coeffs else 1

    # 通过“次数 + 项数 + 系数大小”近似难度，难题也会叠加额外分值。
    score = degree * 18 + term_count * 8 + min(max_coeff, 10) * 2
    if topic == "factorization":
        score += 10
    if topic == "mul_div":
        score += 5
    score = max(0, min(100, score))
    return int(score)


def generate_question(topic: Topic, difficulty_level: DifficultyLevel) -> GeneratedQuestion:
    if topic not in {"add_sub", "mul_div", "factorization"}:
        raise ValueError("未知题型")

    target_range = DIFFICULTY_RANGES[difficulty_level]
    for _ in range(200):
        if topic == "add_sub":
            expression_text, expr = build_add_sub_expression()
            solution = sp.simplify(expr)
        elif topic == "mul_div":
            expression_text, expr = build_mul_div_expression()
            solution = sp.simplify(expr)
        else:
            expression_text, expr = build_factorization_expression()
            solution = sp.factor(expr)

        difficulty_score = compute_difficulty(expr, topic)
        if target_range[0] <= difficulty_score <= target_range[1]:
            return GeneratedQuestion(
                question_id=str(uuid.uuid4()),
                expression_text=expression_text,
                solution_expression=str(solution),
                topic=topic,
                difficulty_level=difficulty_level,
                difficulty_score=difficulty_score,
            )
    raise RuntimeError("未能在合理次数内生成满足难度的题目")
