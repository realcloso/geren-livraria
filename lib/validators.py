from __future__ import annotations
import re
from datetime import datetime
from typing import Any, Mapping, Tuple, Optional, List, Iterable

from . import mapping


class ValidationError(ValueError):
    """
    Uma classe de exceção personalizada, herdada de ValueError.
    É usada para sinalizar que a validação de um valor falhou.
    Isso permite que o código que chama as funções de validação
    possa tratar especificamente os erros de validação,
    diferenciando-os de outros tipos de erros.
    """
    pass


def _coerce_str(value: Any) -> str:
    """
    Função auxiliar interna para converter qualquer valor para uma string.
    Se o valor for `None`, retorna uma string vazia.
    Caso contrário, converte o valor para string e remove espaços em branco
    no início e no fim. Isso padroniza a entrada para as funções de validação.
    """
    if value is None:
        return ""
    return str(value).strip()


def _normalize_decimal_str(s: str) -> str:
    """
    Função auxiliar interna para padronizar a string de um número decimal.
    - Remove espaços em branco.
    - Converte vírgulas para pontos se a string contiver uma vírgula
      e não um ponto, o que é um padrão comum em países de língua portuguesa
      e ajuda a garantir que a conversão para `float` funcione corretamente.
    """
    s = s.replace(" ", "")
    if "," in s and "." not in s:
        s = s.replace(",", ".")
    return s


def _normalize_row(item: Any) -> Tuple[Optional[Any], Any, Any, Any, Any]:
    """
    Unifica diferentes formatos de dados de livros (dicionários, tuplas,
    listas ou objetos) em uma tupla consistente com a estrutura
    (id, titulo, autor, ano_publicacao, preco).
    """
    if isinstance(item, Mapping):
        d = {mapping.KEY_MAP.get(str(k).lower(), k): v for k, v in item.items()}
        return (
            d.get("id"),
            d.get("titulo"),
            d.get("autor"),
            d.get("ano_publicacao"),
            d.get("preco"),
        )

    if isinstance(item, (list, tuple)):
        if len(item) >= 5:
            return (item[0], item[1], item[2], item[3], item[4])
        if len(item) == 4:
            t, a, y, p = item
            return (None, t, a, y, p)
        padded = list(item[:5]) + [None] * max(0, 5 - len(item))
        return (padded[0], padded[1], padded[2], padded[3], padded[4])

    return (
        getattr(item, "id", None),
        getattr(item, "titulo", None),
        getattr(item, "autor", None),
        getattr(item, "ano_publicacao", None),
        getattr(item, "preco", None),
    )


def _normalize_books(books: Iterable[Any]) -> List[dict]:
    """
    Normaliza uma lista de livros de diferentes formatos em uma lista
    consistente de dicionários, usando o mapeamento centralizado.
    """
    normalized: List[dict] = []
    for item in books:
        if isinstance(item, Mapping):
            out = {}
            for k, v in dict(item).items():
                kn = mapping.KEY_MAP.get(str(k).lower(), k)
                out[kn] = v
            normalized.append({
                "id": out.get("id"),
                "titulo": out.get("titulo"),
                "autor": out.get("autor"),
                "ano_publicacao": out.get("ano_publicacao"),
                "preco": out.get("preco"),
            })
        elif isinstance(item, (tuple, list)) and len(item) >= 5:
            normalized.append({
                "id": item[0], "titulo": item[1], "autor": item[2],
                "ano_publicacao": item[3], "preco": item[4],
            })
        else:
            normalized.append({
                "id": getattr(item, "id", None),
                "titulo": getattr(item, "titulo", None),
                "autor": getattr(item, "autor", None),
                "ano_publicacao": getattr(item, "ano_publicacao", None),
                "preco": getattr(item, "preco", None),
            })
    return normalized


def validate_text(label: str, value: Any, *, min_len: int = 1, max_len: int = 200) -> str:
    """
    Valida uma string de texto, como um título ou nome de autor.
    """
    s = _coerce_str(value)
    if len(s) < min_len:
        raise ValidationError(f"{label} não pode ser vazio.")
    if len(s) > max_len:
        raise ValidationError(f"{label} deve ter no máximo {max_len} caracteres.")
    if not re.search(r"[A-Za-zÀ-ÿ0-9]", s):
        raise ValidationError(f"{label} parece inválido.")
    return s


def validate_year(label: str, value: Any, *, min_year: int = 1400) -> int:
    """
    Valida um valor como um ano.
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


def validate_price(label: str, value: Any, *, min_value: float = 0.0, max_value: float = 1_000_000.0) -> float:
    """
    Valida um valor como um preço.
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