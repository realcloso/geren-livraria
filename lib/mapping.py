# Mapeia sinônimos de chaves/cabeçalhos para um padrão unificado.
# Usado para normalizar dicionários e objetos.
KEY_MAP = {
    "id": "id",
    "titulo": "titulo",
    "title": "titulo",
    "autor": "autor",
    "author": "author",
    "ano_publicacao": "ano_publicacao",
    "ano": "ano_publicacao",
    "year": "ano_publicacao",
    "preco": "preco",
    "price": "preco",
}

# Define os sinônimos esperados para as colunas ao importar de arquivos CSV.
# A chave é o nome padrão da coluna no sistema, e o valor é uma tupla de
# possíveis nomes de cabeçalho no arquivo CSV.
CSV_COLUMN_ALIASES = {
    "titulo": ("titulo", "title"),
    "autor": ("autor", "author"),
    "ano_publicacao": ("ano_publicacao", "ano", "year"),
    "preco": ("preco", "price"),
}