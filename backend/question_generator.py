from __future__ import annotations

import random
import uuid
from dataclasses import dataclass
from collections import Counter
from typing import Literal, Sequence

import sympy as sp

# 允许在题目中出现的未知数集合，后面会根据难度选择其中 1~3 个。
VARIABLE_NAMES: tuple[str, ...] = ("x", "y", "z")
VARIABLE_SYMBOLS: dict[str, sp.Symbol] = {name: sp.Symbol(name) for name in VARIABLE_NAMES}

# 兼容原有只用 x 的实现
x = VARIABLE_SYMBOLS["x"]

Topic = Literal["add_sub", "mul_div", "poly_ops", "factorization", "mixed_ops"]
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
    min_terms: int = 1,
) -> sp.Expr:
    """Generate a small random polynomial in the given variables."""

    var_list = list(variables)
    if not var_list:
        var_list = [x]

    for _ in range(20):
        term_count = random.randint(max(2, min_terms), max(4, min_terms))
        expr = sp.Integer(0)
        for _ in range(term_count):
            coeff = random.randint(coeff_min, coeff_max)
            if coeff == 0:
                continue
            monomial = sp.Integer(1)
            total_degree = 0
            # 为当前项随机选择每个变量的指数，控制总次数不超过 max_total_degree。
            for symbol in var_list:
                if total_degree >= max_total_degree:
                    power = 0
                else:
                    power = random.randint(0, max_total_degree - total_degree)
                if power > 0:
                    monomial *= symbol**power
                    total_degree += power
            if total_degree == 0:
                # 避免所有指数都为 0 导致纯常数项
                symbol = random.choice(var_list)
                monomial = symbol
            expr += coeff * monomial
        if expr == 0:
            continue
        try:
            poly_view = sp.Poly(expr, *var_list)
        except sp.PolynomialError:
            return expr
        if len(poly_view.terms()) >= min_terms:
            return expr
    return expr


def build_add_sub_expression(
    variables: Sequence[sp.Symbol],
    difficulty_level: DifficultyLevel,
) -> tuple[str, str, sp.Expr]:
    # 多项式加减：随机组合 2-4 个多项式，并记录括号表达式方便前端显示。
    config = {
        "basic": {
            "group_range": (3, 4),
            "degree_choices": [1, 2],
            "coeff_range": (-4, 4),
            "min_merge_targets": 2,
            "min_result_terms": 3,
            "min_degree": 1,
            "max_result_terms": 5,
        },
        "intermediate": {
            "group_range": (3, 5),
            "degree_choices": [2, 3],
            "coeff_range": (-7, 7),
            "min_merge_targets": 3,
            "min_result_terms": 4,
            "min_degree": 2,
            "max_result_terms": 7,
        },
        "advanced": {
            "group_range": (4, 5),
            "degree_choices": [2, 4],
            "coeff_range": (-8, 8),
            "min_merge_targets": 4,
            "min_result_terms": 5,
            "min_degree": 2,
            "max_result_terms": 9,
        },
    }[difficulty_level]

    var_list = list(variables) or [x]
    shared_terms: list[sp.Expr] = []
    min_merge_targets = config["min_merge_targets"]
    min_result_terms = config["min_result_terms"]
    min_degree = config["min_degree"]
    attempt = 0
    max_attempts = 160
    while attempt < max_attempts:
        attempt += 1
        if attempt in {80, 120}:
            min_merge_targets = max(1, min_merge_targets - 1)
            min_result_terms = max(2, min_result_terms - 1)
            if difficulty_level == "basic":
                min_degree = 1
            else:
                min_degree = max(1, min_degree - 1)
        group_count = random.randint(*config["group_range"])
        segments: list[str] = []
        latex_segments: list[str] = []
        total_expr = sp.Integer(0)
        monom_counts: Counter[tuple[int, ...]] = Counter()

        aborted = False
        for index in range(group_count):
            coeff_min, coeff_max = config["coeff_range"]
            for _ in range(8):
                max_degree = random.choice(config["degree_choices"])
                poly = random_polynomial(
                    variables,
                    max_degree,
                    coeff_min=coeff_min,
                    coeff_max=coeff_max,
                    min_terms=2,
                )
                # 高级难度中偶尔插入一次高次项，制造平方/立方的感觉。
                if difficulty_level != "basic" and random.random() < 0.4:
                    var = random.choice(var_list)
                    high_power = random.randint(2, 3 if difficulty_level == "intermediate" else 4)
                    booster = random.randint(1, 3) * var**high_power
                    poly += booster

                # 强制制造可合并项：从之前的单项式中挑一些加入当前括号。
                if shared_terms and random.random() < 0.8:
                    term = random.choice(shared_terms)
                    coeff = random.randint(-4, 4) or 1
                    poly += coeff * term

                poly = sp.expand(poly)
                if poly != 0:
                    break
            else:
                aborted = True
                break

            if index == 0:
                sign = 1
                prefix = ""
                latex_prefix = ""
            else:
                sign = random.choice([1, -1])
                prefix = " + " if sign == 1 else " - "
                latex_prefix = " + " if sign == 1 else " - "

            total_expr += sign * poly
            display = humanize_expression(poly, variables)
            segments.append(f"{prefix}({display})")
            latex_poly = sp.latex(poly)
            latex_segments.append(f"{latex_prefix}\\left({latex_poly}\\right)")

            try:
                poly_terms = sp.Poly(poly, *variables).terms()
            except sp.PolynomialError:
                poly_terms = []
            current_terms: list[sp.Expr] = []
            for monom, _ in poly_terms:
                monom_counts[monom] += 1
                term_expr = sp.Integer(1)
                for power, symbol in zip(monom, var_list):
                    if power:
                        term_expr *= symbol**power
                current_terms.append(term_expr)

            if current_terms:
                sample = random.sample(current_terms, k=min(len(current_terms), 2))
                shared_terms.extend(sample)
                if len(shared_terms) > 12:
                    shared_terms = shared_terms[-12:]

        if aborted:
            continue

        try:
            expanded = sp.expand(total_expr)
            poly_view = sp.Poly(expanded, *variables)
            term_count = len(poly_view.terms())
            degree = poly_view.total_degree()
        except sp.PolynomialError:
            continue

        merge_targets = sum(1 for count in monom_counts.values() if count > 1)
        if merge_targets < min_merge_targets:
            continue
        if term_count < min_result_terms:
            continue
        max_result_terms = config.get("max_result_terms")
        if max_result_terms and term_count > max_result_terms:
            continue
        if degree < min_degree:
            continue

        display_expression = "".join(segments).strip()
        latex_expression = "".join(latex_segments).lstrip()
        return display_expression, latex_expression, expanded

    raise RuntimeError("无法生成满足要求的整式加减题")


def build_mul_div_expression(
    variables: Sequence[sp.Symbol],
) -> tuple[str, str, sp.Expr]:
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
        latex_display = f"\\left({sp.latex(expr1)}\\right)\\left({sp.latex(expr2)}\\right)"
        return display, latex_display, sp.expand(expr1 * expr2)
    if pattern == "monomial_product":
        var = random.choice(list(variables))
        coeff = random.randint(2, 6)
        power = random.randint(1, 3)
        mono = coeff * var**power
        poly = random_polynomial(variables, random.choice([2, 3]))
        display = f"({humanize_expression(mono, variables)})({humanize_expression(poly, variables)})"
        latex_display = f"\\left({sp.latex(mono)}\\right)\\left({sp.latex(poly)}\\right)"
        return display, latex_display, sp.expand(mono * poly)
    # polynomial_division
    # 为了保持可约性，这里仍然只在一个变量上构造除法结构。
    var = random.choice(list(variables))
    divisor = random_polynomial((var,), 1)
    quotient = random_polynomial((var,), random.choice([1, 2]))
    dividend = sp.expand(divisor * quotient)
    display = f"({humanize_expression(dividend, (var,))}) / ({humanize_expression(divisor, (var,))})"
    latex_display = f"\\frac{{{sp.latex(dividend)}}}{{{sp.latex(divisor)}}}"
    return display, latex_display, sp.simplify(dividend / divisor)


def build_factorization_expression(
    variables: Sequence[sp.Symbol],
    difficulty_level: DifficultyLevel,
) -> tuple[str, str, sp.Expr]:
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
        return humanize_expression(expr, variables), sp.latex(expr), expr
    if pattern == "quadratic":
        var = random.choice(list(variables))
        p = random.randint(1, 4)
        q = random.randint(1, 4)
        m = random.randint(-6, 6)
        n = random.randint(-6, 6)
        expr = sp.expand((p * var + m) * (q * var + n))
        return humanize_expression(expr, variables), sp.latex(expr), expr
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
        return humanize_expression(expr, variables), sp.latex(expr), expr
    if pattern == "quadratic_times_linear":
        # 形如 (ax^2 + bx + c)(dx + e)，体现“配方法 / 双十字相乘”的综合难度。
        var = random.choice(list(variables))
        a = random.randint(1, 3)
        b = random.randint(-5, 5)
        c = random.randint(-5, 5)
        d = random.randint(1, 3)
        e = random.randint(-5, 5)
        expr = sp.expand((a * var**2 + b * var + c) * (d * var + e))
        return humanize_expression(expr, variables), sp.latex(expr), expr
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
        return humanize_expression(expr, variables), sp.latex(expr), expr
    # grouping：按分组提取公因式的思路构造。
    var = random.choice(list(variables))
    a = random.randint(1, 5)
    b = random.randint(1, 5)
    c = random.randint(-6, 6)
    d = random.randint(-6, 6)
    expr = sp.expand((a * var + c) * var + (b * var + d) * var)
    return humanize_expression(expr, variables), sp.latex(expr), expr


def build_mixed_ops_expression(variables: Sequence[sp.Symbol]) -> tuple[str, str, sp.Expr]:
    """生成整式加减乘除混合表达式，确保化简后为多项式。"""
    is_basic = len(variables) == 1
    if is_basic:
        patterns = ["add_mul", "div_add"]
    else:
        patterns = ["add_mul", "div_add", "multi_div_add"]
    pattern = random.choice(patterns)

    text_segments: list[str] = []
    latex_segments: list[str] = []
    expr = sp.Integer(0)

    if pattern == "add_mul":
        # 模式 A: 加减与乘法混合，如 P1 +/- M * P2 +/- P3
        p1 = random_polynomial(variables, random.choice([1, 2]))
        m_coeff = random.choice([2, 3, 4])
        m_var = random.choice(list(variables))
        m = m_coeff * m_var
        p2 = random_polynomial(variables, random.choice([1, 2]))
        p3 = random_polynomial(variables, 1)

        signs = [1, random.choice([1, -1]), random.choice([1, -1])]
        parts = [p1, signs[1] * m * p2, signs[2] * p3]

        for i, part in enumerate(parts):
            if i == 0:
                prefix = ""
                latex_prefix = ""
            else:
                prefix = " + " if signs[i] > 0 else " - "
                latex_prefix = " + " if signs[i] > 0 else " - "
            display_part = humanize_expression(part, variables)
            text_segments.append(f"{prefix}({display_part})")
            latex_part = sp.latex(part)
            latex_segments.append(f"{latex_prefix}\\left({latex_part}\\right)")

        expr = sum(parts)

    elif pattern == "div_add":
        # 模式 B: 可约除法 + 加减乘
        var = random.choice(list(variables))
        divisor = random_polynomial((var,), 1)
        if divisor == 0:
            return build_mixed_ops_expression(variables)  # retry
        quotient = random_polynomial((var,), random.choice([1, 2]))
        dividend = sp.expand(divisor * quotient)

        div_text = f"({humanize_expression(dividend, variables)}) / ({humanize_expression(divisor, variables)})"
        div_latex = f"\\frac{{{sp.latex(dividend)}}}{{{sp.latex(divisor)}}}"
        text_segments.append(div_text)
        latex_segments.append(div_latex)

        p1 = random_polynomial(variables, 1)
        sign1 = random.choice([1, -1])
        prefix1 = " + " if sign1 > 0 else " - "
        latex_prefix1 = " + " if sign1 > 0 else " - "
        text_segments.append(f"{prefix1}{humanize_expression(p1, variables)}")
        latex_segments.append(f"{latex_prefix1}{sp.latex(p1)}")

        m_coeff = random.choice([2, 3])
        m_var = random.choice(list(variables))
        m = m_coeff * m_var
        p2 = random_polynomial(variables, 1)
        sign2 = random.choice([1, -1])
        prefix2 = " + " if sign2 > 0 else " - "
        latex_prefix2 = " + " if sign2 > 0 else " - "
        text_segments.append(f"{prefix2}{humanize_expression(m, variables)}({humanize_expression(p2, variables)})")
        latex_segments.append(f"{latex_prefix2}{sp.latex(m)}\\left({sp.latex(p2)}\\right)")

        expr = sp.simplify(dividend / divisor + sign1 * p1 + sign2 * m * p2)

    elif pattern == "multi_div_add":
        # 模式 C: 多个可约除 + 加减，多元
        var1 = random.choice(list(variables))
        divisor1 = random_polynomial((var1,), 1)
        if divisor1 == 0:
            return build_mixed_ops_expression(variables)
        quotient1 = random_polynomial(variables, 1)
        dividend1 = sp.expand(divisor1 * quotient1)

        div1_text = f"({humanize_expression(dividend1, variables)}) / ({humanize_expression(divisor1, variables)})"
        div1_latex = f"\\frac{{{sp.latex(dividend1)}}}{{{sp.latex(divisor1)}}}"
        text_segments.append(div1_text)
        latex_segments.append(div1_latex)

        var2 = random.choice([v for v in variables if v != var1]) if len(variables) > 1 else var1
        divisor2 = random_polynomial((var2,), 1)
        if divisor2 == 0:
            return build_mixed_ops_expression(variables)
        quotient2 = random_polynomial(variables, 1)
        dividend2 = sp.expand(divisor2 * quotient2)

        sign_div2 = random.choice([1, -1])
        prefix_div2 = " + " if sign_div2 > 0 else " - "
        latex_prefix_div2 = " + " if sign_div2 > 0 else " - "
        div2_text = f"({humanize_expression(dividend2, variables)}) / ({humanize_expression(divisor2, variables)})"
        div2_latex = f"\\frac{{{sp.latex(dividend2)}}}{{{sp.latex(divisor2)}}}"
        text_segments.append(f"{prefix_div2}{div2_text}")
        latex_segments.append(f"{latex_prefix_div2}{div2_latex}")

        p3 = random_polynomial(variables, 1)
        sign_p3 = random.choice([1, -1])
        prefix_p3 = " + " if sign_p3 > 0 else " - "
        latex_prefix_p3 = " + " if sign_p3 > 0 else " - "
        text_segments.append(f"{prefix_p3}{humanize_expression(p3, variables)}")
        latex_segments.append(f"{latex_prefix_p3}{sp.latex(p3)}")

        expr = sp.simplify(dividend1 / divisor1 + sign_div2 * (dividend2 / divisor2) + sign_p3 * p3)

    expression_text = "".join(text_segments).strip()
    expression_latex = "".join(latex_segments).strip()
    if expression_text.startswith("+ "):
        expression_text = expression_text[2:]
    if expression_latex.startswith("+"):
        expression_latex = expression_latex[1:]

    return expression_text, expression_latex, expr


def build_poly_ops_expression(
    variables: Sequence[sp.Symbol],
    difficulty_level: DifficultyLevel,
) -> tuple[str, str, sp.Expr]:
    """整式加减与乘除的折中题型，保证表达式同时含有拆括号/加减与乘除结构。"""

    var_choices = list(variables) or [x]
    segments: list[str] = []
    latex_segments: list[str] = []
    expr = sp.Integer(0)

    def _poly(degree: int, min_terms: int = 2) -> sp.Expr:
        return random_polynomial(
            variables,
            degree,
            coeff_min=-6 if difficulty_level == "basic" else -8,
            coeff_max=6 if difficulty_level == "basic" else 8,
            min_terms=min_terms,
        )

    def _append(piece: sp.Expr, text: str, latex_text: str, sign: int = 1) -> None:
        nonlocal expr
        expr += sign * piece
        if not segments:
            prefix_text = ""
            prefix_latex = ""
        else:
            prefix_text = " + " if sign > 0 else " - "
            prefix_latex = " + " if sign > 0 else " - "
        segments.append(f"{prefix_text}{text}")
        latex_segments.append(f"{prefix_latex}{latex_text}")

    base = _poly(2)
    _append(base, f"({humanize_expression(base, variables)})", f"\\left({sp.latex(base)}\\right)", 1)

    patterns = ["frac_mul", "double_mul", "nested_mix"]
    if difficulty_level != "basic":
        patterns.append("fraction_double")
    pattern = random.choice(patterns)

    if pattern == "frac_mul":
        var = random.choice(var_choices)
        divisor = random_polynomial((var,), 1, min_terms=1)
        if divisor == 0:
            divisor = var
        quotient = random_polynomial((var,), random.choice([1, 2]), min_terms=1)
        dividend = sp.expand(divisor * quotient)
        frac = sp.simplify(dividend / divisor)
        frac_text = f"({humanize_expression(dividend, variables)}) / ({humanize_expression(divisor, variables)})"
        frac_latex = f"\\frac{{{sp.latex(dividend)}}}{{{sp.latex(divisor)}}}"
        _append(frac, frac_text, frac_latex, random.choice([1, -1]))

        mono = random.randint(2, 4) * random.choice(var_choices)
        mul_poly = _poly(2)
        mul_expr = sp.expand(mono * mul_poly)
        mul_text = f"({humanize_expression(mono, variables)})({humanize_expression(mul_poly, variables)})"
        mul_latex = f"\\left({sp.latex(mono)}\\right)\\left({sp.latex(mul_poly)}\\right)"
        _append(mul_expr, mul_text, mul_latex, random.choice([1, -1]))

    elif pattern == "double_mul":
        mono1 = random.randint(2, 5) * random.choice(var_choices)
        mono2 = random.randint(2, 4) * random.choice(var_choices)
        poly1 = _poly(2)
        poly2 = _poly(1)
        term1 = sp.expand(mono1 * poly1)
        term2 = sp.expand(mono2 * poly2)
        text1 = f"({humanize_expression(mono1, variables)})({humanize_expression(poly1, variables)})"
        text2 = f"({humanize_expression(mono2, variables)})({humanize_expression(poly2, variables)})"
        latex1 = f"\\left({sp.latex(mono1)}\\right)\\left({sp.latex(poly1)}\\right)"
        latex2 = f"\\left({sp.latex(mono2)}\\right)\\left({sp.latex(poly2)}\\right)"
        _append(term1, text1, latex1, random.choice([1, -1]))
        _append(term2, text2, latex2, random.choice([1, -1]))

    elif pattern == "nested_mix":
        inner = _poly(1)
        outer = _poly(2)
        combined = sp.expand(inner + outer)
        combo_text = f"(({humanize_expression(inner, variables)}) + ({humanize_expression(outer, variables)}))"
        combo_latex = f"\\left(\\left({sp.latex(inner)}\\right)+\\left({sp.latex(outer)}\\right)\\right)"
        _append(combined, combo_text, combo_latex, random.choice([1, -1]))

        mono = random.randint(2, 4) * random.choice(var_choices)
        bonus = _poly(2)
        bonus_expr = sp.expand(mono * bonus)
        bonus_text = f"({humanize_expression(mono, variables)})({humanize_expression(bonus, variables)})"
        bonus_latex = f"\\left({sp.latex(mono)}\\right)\\left({sp.latex(bonus)}\\right)"
        _append(bonus_expr, bonus_text, bonus_latex, random.choice([1, -1]))

    else:  # fraction_double
        var1 = random.choice(var_choices)
        divisor1 = random_polynomial((var1,), 1, min_terms=1) or var1
        quotient1 = random_polynomial((var1,), random.choice([1, 2]), min_terms=1)
        dividend1 = sp.expand(divisor1 * quotient1)
        frac1 = sp.simplify(dividend1 / divisor1)
        text1 = f"({humanize_expression(dividend1, variables)}) / ({humanize_expression(divisor1, variables)})"
        latex1 = f"\\frac{{{sp.latex(dividend1)}}}{{{sp.latex(divisor1)}}}"
        _append(frac1, text1, latex1, random.choice([1, -1]))

        divisor2_var = random.choice(var_choices)
        divisor2 = random_polynomial((divisor2_var,), 1, min_terms=1) or divisor2_var
        quotient2 = random_polynomial((divisor2_var,), 1, min_terms=1)
        dividend2 = sp.expand(divisor2 * quotient2)
        frac2 = sp.simplify(dividend2 / divisor2)
        text2 = f"({humanize_expression(dividend2, variables)}) / ({humanize_expression(divisor2, variables)})"
        latex2 = f"\\frac{{{sp.latex(dividend2)}}}{{{sp.latex(divisor2)}}}"
        _append(frac2, text2, latex2, random.choice([1, -1]))

    tail = _poly(1)
    _append(tail, f"({humanize_expression(tail, variables)})", f"\\left({sp.latex(tail)}\\right)", random.choice([1, -1]))

    display_expression = "".join(segments).strip()
    latex_expression = "".join(latex_segments).strip()
    return display_expression, latex_expression, sp.simplify(expr)


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
    if topic == "add_sub":
        degree_weight = 6.0
        term_weight = 3.0
        coeff_weight = 1.2
        base_bonus = 5.0
    elif topic == "poly_ops":
        degree_weight = 8.0
        term_weight = 4.0
        coeff_weight = 1.5
        base_bonus = 4.0
    else:
        degree_weight = 15.0
        term_weight = 6.0
        coeff_weight = 2.0
        base_bonus = 0.0

    score = base_bonus
    score += degree * degree_weight
    score += term_count * term_weight
    score += min(max_coeff, 10.0) * coeff_weight
    # 多一个未知数，适当加一点难度
    if var_count > 1:
        score += (var_count - 1) * 8
    if has_fraction:
        score += 6

    if topic == "add_sub":
        if degree >= 3:
            score += 18
        if degree >= 4:
            score += 8
        if term_count >= 6:
            score += 6
        if var_count >= 2:
            score += 12

    if topic == "poly_ops":
        if term_count >= 6:
            score += 8
        if degree >= 3:
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
    if topic == "mixed_ops":
        score += 8

    score = max(0.0, min(100.0, score))
    return int(round(score))


def generate_question(topic: Topic, difficulty_level: DifficultyLevel) -> GeneratedQuestion:
    if topic not in {"add_sub", "mul_div", "poly_ops", "factorization", "mixed_ops"}:
        raise ValueError("未知题型")

    target_range = DIFFICULTY_RANGES[difficulty_level]
    # 因式分解整体偏难一些，基础题也可能落在 60 分左右，这里单独放宽 basic 的区间。
    if topic == "factorization" and difficulty_level == "basic":
        target_range = (0, 70)
    if topic == "poly_ops":
        poly_ranges: dict[DifficultyLevel, tuple[int, int]] = {
            "basic": (15, 55),
            "intermediate": (40, 75),
            "advanced": (60, 100),
        }
        target_range = poly_ranges[difficulty_level]

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
            expression_text, expression_latex, expr = build_add_sub_expression(symbols, difficulty_level)
            solution = sp.simplify(expr)
        elif topic == "mul_div":
            expression_text, expression_latex, expr = build_mul_div_expression(symbols)
            solution = sp.simplify(expr)
        elif topic == "poly_ops":
            expression_text, expression_latex, expr = build_poly_ops_expression(symbols, difficulty_level)
            solution = sp.simplify(expr)
        elif topic == "mixed_ops":
            expression_text, expression_latex, expr = build_mixed_ops_expression(symbols)
            solution = sp.simplify(expr)
        else:  # factorization
            expression_text, expression_latex, expr = build_factorization_expression(symbols, difficulty_level)
            solution = sp.factor(expr)

        difficulty_score = compute_difficulty(expr, topic)
        if target_range[0] <= difficulty_score <= target_range[1]:
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


def generate_batch(count: int, difficulty: DifficultyLevel | None = None) -> list[GeneratedQuestion]:
    """Generate a batch of questions with random topics."""
    questions: list[GeneratedQuestion] = []
    topics: list[Topic] = ["add_sub", "mul_div", "poly_ops", "factorization", "mixed_ops"]
    difficulties: list[DifficultyLevel] = ["basic", "intermediate", "advanced"]

    attempts = 0
    # 防止无限循环，设定一个较大的尝试上限
    while len(questions) < count and attempts < count * 10:
        attempts += 1
        level: DifficultyLevel = difficulty or random.choice(difficulties)
        topic = random.choice(topics)
        try:
            questions.append(generate_question(topic, level))
        except RuntimeError:
            continue

    if len(questions) < count:
        raise RuntimeError(f"未能在合理次数内生成批量题目 ({len(questions)}/{count})")

    return questions
