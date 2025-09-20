from __future__ import annotations
import re
from datetime import datetime
from typing import Any


class ValidationError(ValueError):
    pass


def _coerce_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def validate_text(label: str, value: Any, *, min_len: int = 1, max_len: int = 200) -> str:
    s = _coerce_str(value)
    if len(s) < min_len:
        raise ValidationError(f"{label} não pode ser vazio.")
    if len(s) > max_len:
        raise ValidationError(f"{label} deve ter no máximo {max_len} caracteres.")
    if not re.search(r"[A-Za-zÀ-ÿ0-9]", s):
        raise ValidationError(f"{label} parece inválido.")
    return s


def validate_year(label: str, value: Any, *, min_year: int = 1400) -> int:
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
    s = s.replace(" ", "")
    if "," in s and "." not in s:
        s = s.replace(",", ".")
    return s


def validate_price(label: str, value: Any, *, min_value: float = 0.0, max_value: float = 1_000_000.0) -> float:
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
