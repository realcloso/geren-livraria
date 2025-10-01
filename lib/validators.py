from __future__ import annotations
import re
from datetime import datetime
from typing import Any


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


def validate_text(label: str, value: Any, *, min_len: int = 1, max_len: int = 200) -> str:
    """
    Valida uma string de texto, como um título ou nome de autor.
    - O valor é primeiro convertido para string e tem espaços removidos.
    - Verifica se o comprimento está dentro dos limites `min_len` e `max_len`.
    - Usa uma expressão regular (`re.search`) para garantir que a string
      contenha pelo menos uma letra ou número, evitando strings vazias
      ou compostas apenas por caracteres especiais.
    - Em caso de falha, lança uma `ValidationError`.
    - Retorna a string validada e limpa.
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
    - Primeiro, tenta converter o valor para um número inteiro.
    - Se a conversão falhar, lança um erro.
    - Depois, verifica se o ano está dentro de um intervalo razoável,
      definido por `min_year` e o ano atual mais um (para permitir
      entradas de livros a serem publicados em breve).
    - Lança uma `ValidationError` se o ano estiver fora do intervalo.
    - Retorna o ano validado como um inteiro.
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


def validate_price(label: str, value: Any, *, min_value: float = 0.0, max_value: float = 1_000_000.0) -> float:
    """
    Valida um valor como um preço.
    - Primeiro, a string é normalizada usando `_normalize_decimal_str`
      para lidar com a vírgula como separador decimal.
    - Tenta converter a string normalizada para um `float`.
    - Verifica se o preço está dentro de um intervalo válido,
      definido por `min_value` e `max_value`.
    - O valor final é arredondado para duas casas decimais.
    - Em caso de erro, uma `ValidationError` é lançada com uma mensagem descritiva.
    - Retorna o preço validado como um float.
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