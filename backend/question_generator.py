from __future__ import annotations

import random
import uuid
from dataclasses import dataclass
from typing import Literal, Sequence

import sympy as sp
from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

# 允许在题目中出现的未知数集合，后面会根据难度选择其中 1~3 个。
VARIABLE_NAMES: tuple[str, ...] = ("x", "y", "z")
VARIABLE_SYMBOLS: dict[str, sp.Symbol] = {name: sp.Symbol(name) for name in VARIABLE_NAMES}

# 兼容原有只用 x 的实现
x = VARIABLE_SYMBOLS["x"]

_TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application,)

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
    expression_latex: str
    solution_expression: str
    topic: Topic
    difficulty_level: DifficultyLevel
    difficulty_score: int


def expression_text_to_latex(text: str) -> str:
    """Convert the human input string to LaTeX for nicer display."""

    sanitized = text.replace("^", "**")
    try:
        expr = parse_expr(
            sanitized,
            local_dict=VARIABLE_SYMBOLS,
            transformations=_TRANSFORMATIONS,
            evaluate=False,
        )
        return sp.latex(expr)
    except Exception:
        # 回退到原始字符串，至少保证有内容可展示。
        return text


def humanize_expression(expr: sp.Expr, symbols: Sequence[sp.Symbol] | None = None) -> str:
    """Convert a SymPy expression to the input format like 2x^2 + 3xy - 5."""

    expr = sp.expand(expr)
    # 默认只按 x 处理，以兼容老数据；多元题目会显式传入 symbols。
    symbol_list: Sequence[sp.Symbol] = symbols or (x,)
    try:
        poly = sp.Poly(expr, *symbol_list)
    except sp.PolynomialError:
        # Fallback for expressions that are not plain polynomials (e.g. with division)
        text = str(expr)
        return text.replace("**", "^").replace("*", "")

    if poly.is_zero:
        return "0"

    parts: list[str] = []
    for monom, coeff in poly.terms():
        # 系数可能是分数，如果无法安全转成 int，则退回简单字符串形式。
        try:
            coeff_int = int(coeff)
        except (TypeError, ValueError):
            text = str(expr)
            return text.replace("**", "^").replace("*", "")

        if coeff_int == 0:
            continue

        sign = "+" if coeff_int > 0 else "-"
        abs_coeff = abs(coeff_int)

        # monom 是一个元组，长度等于变量个数，例如 (2, 1, 0) 表示 x^2 y^1 z^0。
        var_factors: list[str] = []
        for power, symbol in zip(monom, symbol_list):
            if power == 0:
                continue
            if power == 1:
                var_factors.append(symbol.name)
            else:
                var_factors.append(f"{symbol.name}^{power}")

        if not var_factors:
            # 常数项
            term_body = f"{abs_coeff}"
        else:
            vars_part = "".join(var_factors)
            if abs_coeff == 1:
                term_body = vars_part
            else:
                term_body = f"{abs_coeff}{vars_part}"

        parts.append(f" {sign} {term_body}")

    text = "".join(parts).strip()
    if text.startswith("+"):
        text = text[1:].strip()
    text = text.replace("  ", " ")
    text = text.replace("+-", "-")
    return text


def random_polynomial(
    variables: Sequence[sp.Symbol],
    max_total_degree: int,
    coeff_min: int = -6,
    coeff_max: int = 6,
) -> sp.Expr:
    """Generate a small random polynomial in the given variables."""

    term_count = random.randint(2, 4)
    expr = sp.Integer(0)
    for _ in range(term_count):
        coeff = random.randint(coeff_min, coeff_max)
        if coeff == 0:
            continue
        monomial = sp.Integer(1)
        total_degree = 0
        # 为当前项随机选择每个变量的指数，控制总次数不超过 max_total_degree。
        for symbol in variables:
            if total_degree >= max_total_degree:
                power = 0
            else:
                power = random.randint(0, max_total_degree - total_degree)
            if power > 0:
                monomial *= symbol**power
                total_degree += power
        if total_degree == 0:
            # 避免所有指数都为 0 导致纯常数项
            symbol = random.choice(list(variables))
            monomial = symbol
        expr += coeff * monomial
    if expr == 0:
        return random_polynomial(variables, max_total_degree, coeff_min, coeff_max)
    return expr


def build_add_sub_expression(variables: Sequence[sp.Symbol]) -> tuple[str, sp.Expr]:
    # 多项式加减：随机组合 2-4 个多项式，并记录括号表达式方便前端显示。
    term_count = random.randint(2, 4)
    segments: list[str] = []
    total_expr = sp.Integer(0)
    for index in range(term_count):
        poly = random_polynomial(variables, random.choice([2, 3]))
        display = humanize_expression(poly, variables)
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


def build_mul_div_expression(
    variables: Sequence[sp.Symbol],
) -> tuple[str, sp.Expr]:
    # 乘除题包含三种结构，全部保证结果仍旧是整式，便于比对。
    pattern = random.choice(["binomial_product", "monomial_product", "polynomial_division"])
    if pattern == "binomial_product":
        var = random.choice(list(variables))
        a1, b1 = random.randint(-5, 5), random.randint(-5, 5)
        a2, b2 = random.randint(-5, 5), random.randint(-5, 5)
        a1 = a1 or 1
        a2 = a2 or -1
        expr1 = a1 * var + b1
        expr2 = a2 * var + b2
        display = f"({humanize_expression(expr1, variables)})({humanize_expression(expr2, variables)})"
        return display, sp.expand(expr1 * expr2)
    if pattern == "monomial_product":
        var = random.choice(list(variables))
        coeff = random.randint(2, 6)
        power = random.randint(1, 3)
        mono = coeff * var**power
        poly = random_polynomial(variables, random.choice([2, 3]))
        display = f"({humanize_expression(mono, variables)})({humanize_expression(poly, variables)})"
        return display, sp.expand(mono * poly)
    # polynomial_division
    # 为了保持可约性，这里仍然只在一个变量上构造除法结构。
    var = random.choice(list(variables))
    divisor = random_polynomial((var,), 1)
    quotient = random_polynomial((var,), random.choice([1, 2]))
    dividend = sp.expand(divisor * quotient)
    display = f"({humanize_expression(dividend, (var,))}) / ({humanize_expression(divisor, (var,))})"
    return display, sp.simplify(dividend / divisor)


def build_factorization_expression(
    variables: Sequence[sp.Symbol],
    difficulty_level: DifficultyLevel,
) -> tuple[str, sp.Expr]:
    # 因式分解题基于常见模式：
    # - 完全平方
    # - 二次三项式
    # - 平方差
    # - 分组提取
    # - 高次乘法：如 (ax^2+bx+c)(dx+e)
    # - 多元二次：如 (ax+by+c)(dx+ey+f)
    if difficulty_level == "basic":
        patterns = ["square", "quadratic", "diff_square", "grouping"]
    else:
        patterns = [
            "square",
            "quadratic",
            "diff_square",
            "grouping",
            "quadratic_times_linear",
            "multi_var_quadratic",
        ]
    pattern = random.choice(patterns)

    if pattern == "square":
        var = random.choice(list(variables))
        a = random.randint(1, 4)
        b = random.randint(-6, 6)
        expr = sp.expand((a * var + b) ** 2)
        return humanize_expression(expr, variables), expr
    if pattern == "quadratic":
        var = random.choice(list(variables))
        p = random.randint(1, 4)
        q = random.randint(1, 4)
        m = random.randint(-6, 6)
        n = random.randint(-6, 6)
        expr = sp.expand((p * var + m) * (q * var + n))
        return humanize_expression(expr, variables), expr
    if pattern == "diff_square":
        var1 = random.choice(list(variables))
        # 平方差可以是单变量也可以是多变量，例如 (ax)^2 - (by)^2
        if len(variables) >= 2 and random.random() < 0.5:
            var2 = random.choice([s for s in variables if s is not var1])
        else:
            var2 = var1
        # 避免 (ax)^2 与 (bx)^2 完全相同导致表达式恒为 0。
        while True:
            a = random.randint(2, 6)
            b = random.randint(1, 5)
            if not (var1 is var2 and a == b):
                break
        expr = (a * var1) ** 2 - (b * var2) ** 2
        return humanize_expression(expr, variables), expr
    if pattern == "quadratic_times_linear":
        # 形如 (ax^2 + bx + c)(dx + e)，体现“配方法 / 双十字相乘”的综合难度。
        var = random.choice(list(variables))
        a = random.randint(1, 3)
        b = random.randint(-5, 5)
        c = random.randint(-5, 5)
        d = random.randint(1, 3)
        e = random.randint(-5, 5)
        expr = sp.expand((a * var**2 + b * var + c) * (d * var + e))
        return humanize_expression(expr, variables), expr
    if pattern == "multi_var_quadratic" and len(variables) >= 2:
        # 形如 (ax + by + c)(dx + ey + f)，需要对多元二次式分解。
        v1, v2 = random.sample(list(variables), 2)
        a1 = random.randint(1, 4)
        b1 = random.randint(1, 4)
        a2 = random.randint(1, 4)
        b2 = random.randint(1, 4)
        c1 = random.randint(-5, 5)
        c2 = random.randint(-5, 5)
        expr = sp.expand((a1 * v1 + b1 * v2 + c1) * (a2 * v1 + b2 * v2 + c2))
        return humanize_expression(expr, variables), expr
    # grouping：按分组提取公因式的思路构造。
    var = random.choice(list(variables))
    a = random.randint(1, 5)
    b = random.randint(1, 5)
    c = random.randint(-6, 6)
    d = random.randint(-6, 6)
    expr = sp.expand((a * var + c) * var + (b * var + d) * var)
    return humanize_expression(expr, variables), expr


def compute_difficulty(expr: sp.Expr, topic: Topic) -> int:
    """Rough difficulty estimation between 0 and 100."""

    expanded = sp.expand(expr)

    # 当前题目实际涉及到的未知数个数
    used_symbols = [
        s for s in expanded.free_symbols if s.name in VARIABLE_SYMBOLS
    ] or [x]

    poly = None
    try:
        poly = sp.Poly(expanded, *used_symbols)
    except sp.PolynomialError:
        poly = None

    if poly is not None:
        degree = poly.total_degree()
        term_count = len(poly.terms())
        # 对于多元多项式，all_coeffs 不可用，退而求其次使用 coeffs。
        try:
            coeffs = list(poly.all_coeffs())
        except Exception:
            coeffs = list(poly.coeffs())
        max_coeff = 1.0
        has_fraction = False
        for c in coeffs:
            try:
                value = float(c)
            except TypeError:
                continue
            if value != int(value):
                has_fraction = True
            max_coeff = max(max_coeff, abs(value))
    else:
        # 非多项式场景给一个保守估计
        degree = 2
        # 粗略按加号切分估算项数
        term_count = max(1, len(str(expanded).replace("-", "+").split("+")))
        has_fraction = "/" in str(expanded)
        max_coeff = 3.0

    var_count = len({s.name for s in used_symbols})

    # 通过“次数 + 项数 + 系数大小 + 未知数个数 + 是否复杂题型”综合估计难度。
    score = 0.0
    score += degree * 15
    score += term_count * 6
    score += min(max_coeff, 10.0) * 2
    # 多一个未知数，适当加一点难度
    if var_count > 1:
        score += (var_count - 1) * 8
    if has_fraction:
        score += 6

    if topic == "factorization":
        # 因式分解整体偏难一些
        score += 10
        if degree >= 3:
            score += 8
        if var_count >= 2:
            score += 5
    if topic == "mul_div":
        score += 5

    score = max(0.0, min(100.0, score))
    return int(round(score))


def generate_question(topic: Topic, difficulty_level: DifficultyLevel) -> GeneratedQuestion:
    if topic not in {"add_sub", "mul_div", "factorization"}:
        raise ValueError("未知题型")

    target_range = DIFFICULTY_RANGES[difficulty_level]
    # 因式分解整体偏难一些，基础题也可能落在 60 分左右，这里单独放宽 basic 的区间。
    if topic == "factorization" and difficulty_level == "basic":
        target_range = (0, 70)

    # 根据难度选取题目使用的未知数：
    # - basic：固定只使用 x
    # - intermediate / advanced：在 x, y, z 中随机选择 2~3 个
    if difficulty_level == "basic":
        symbols: Sequence[sp.Symbol] = (VARIABLE_SYMBOLS["x"],)
    else:
        count = random.randint(2, min(3, len(VARIABLE_NAMES)))
        names = random.sample(VARIABLE_NAMES, k=count)
        symbols = tuple(VARIABLE_SYMBOLS[name] for name in sorted(names))

    for _ in range(200):
        if topic == "add_sub":
            expression_text, expr = build_add_sub_expression(symbols)
            solution = sp.simplify(expr)
        elif topic == "mul_div":
            expression_text, expr = build_mul_div_expression(symbols)
            solution = sp.simplify(expr)
        else:
            expression_text, expr = build_factorization_expression(symbols, difficulty_level)
            solution = sp.factor(expr)

        difficulty_score = compute_difficulty(expr, topic)
        if target_range[0] <= difficulty_score <= target_range[1]:
            expression_latex = expression_text_to_latex(expression_text)
            return GeneratedQuestion(
                question_id=str(uuid.uuid4()),
                expression_text=expression_text,
                expression_latex=expression_latex,
                solution_expression=str(solution),
                topic=topic,
                difficulty_level=difficulty_level,
                difficulty_score=difficulty_score,
            )
    raise RuntimeError("未能在合理次数内生成满足难度的题目")
