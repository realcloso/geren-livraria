# lib/validators.py
from __future__ import annotations

import re
from datetime import datetime
from typing import Any


class ValidationError(ValueError):
    """Erro de validação de entrada do usuário."""
    pass


def _coerce_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def validate_text(label: str, value: Any, *, min_len: int = 1, max_len: int = 200) -> str:
    """
    Valida um texto genérico (título, autor).
    - remove espaços em volta
    - checa tamanho mínimo/máximo
    - evita somente pontuação
    """
    s = _coerce_str(value)

    if len(s) < min_len:
        raise ValidationError(f"{label} não pode ser vazio.")

    if len(s) > max_len:
        raise ValidationError(f"{label} deve ter no máximo {max_len} caracteres.")

    # Evita strings só com pontuação/whitespace
    if not re.search(r"[A-Za-zÀ-ÿ0-9]", s):
        raise ValidationError(f"{label} parece inválido.")

    return s


def validate_year(label: str, value: Any, *, min_year: int = 1400) -> int:
    """
    Valida um ano inteiro plausível de publicação.
    Aceita string com espaços; rejeita valores fora do intervalo [min_year, ano_atual+1].
    """
    s = _coerce_str(value)
    if not s:
        raise ValidationError(f"{label} não pode ser vazio.")

    try:
        year = int(s)
    except Exception:
        raise ValidationError(f"{label} deve ser um número inteiro (ex.: 1999).")

    current_plus_one = datetime.now().year + 1
    if year < min_year or year > current_plus_one:
        raise ValidationError(f"{label} deve estar entre {min_year} e {current_plus_one}.")

    return year


def _normalize_decimal_str(s: str) -> str:
    """
    Converte '12,34' -> '12.34'; mantém números já com ponto.
    Remove espaços.
    """
    s = s.replace(" ", "")
    # Se tiver vírgula e ponto, assume que vírgula é milhar e ponto é decimal? (caso raro)
    # Estratégia simples: se tiver vírgula e não tiver ponto, troca vírgula -> ponto.
    if "," in s and "." not in s:
        s = s.replace(",", ".")
    return s


def validate_price(label: str, value: Any, *, min_value: float = 0.0, max_value: float = 1_000_000.0) -> float:
    """
    Valida um preço (float) >= 0.
    Aceita entrada com vírgula ou ponto.
    """
    s = _coerce_str(value)
    if not s:
        raise ValidationError(f"{label} não pode ser vazio.")

    s = _normalize_decimal_str(s)

    try:
        price = float(s)
    except Exception:
        raise ValidationError(f"{label} deve ser um número (ex.: 35.90).")

    if price < min_value:
        raise ValidationError(f"{label} deve ser maior ou igual a {min_value:.2f}.")
    if price > max_value:
        raise ValidationError(f"{label} não pode ser maior que {max_value:.2f}.")

    return round(price, 2)
