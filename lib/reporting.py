from __future__ import annotations
from datetime import datetime
from string import Template
from typing import Iterable, Mapping, Any, List
from pathlib import Path

# Tenta importar o pisa, caso contrário informa um erro
try:
    # ferramneta para gerar pdf a partir do html
    from xhtml2pdf import pisa
except ImportError:
    pisa = None

def _normalize_books(books: Iterable[Any]) -> List[dict]:
    """
    Normaliza uma lista de livros de diferentes formatos (dicionários, tuplas,
    listas ou objetos com atributos) em uma lista consistente de dicionários.
    Isso garante que a lógica de geração de relatórios possa processar
    dados de diversas fontes sem precisar de checagens repetitivas.
    Ele lida com sinônimos de chaves (ex: 'title' e 'titulo').
    """
    normalized: List[dict] = []
    for item in books:
        if isinstance(item, Mapping): # Se o item é um dicionário ou similar
            d = dict(item)
            key_map = {
                # Mapeia sinônimos de chaves para um padrão unificado
                "id": "id",
                "titulo": "titulo",
                "title": "titulo",
                "autor": "autor",
                "author": "autor",
                "ano_publicacao": "ano_publicacao",
                "ano": "ano_publicacao",
                "year": "ano_publicacao",
                "preco": "preco",
                "price": "preco",
            }
            out = {}
            for k, v in d.items():
                kn = key_map.get(k, k) # Pega o nome padronizado da chave
                out[kn] = v
            normalized.append({
                "id": out.get("id"),
                "titulo": out.get("titulo"),
                "autor": out.get("autor"),
                "ano_publicacao": out.get("ano_publicacao"),
                "preco": out.get("preco"),
            })
        elif isinstance(item, (tuple, list)) and len(item) >= 5: # Se o item é uma tupla/lista com 5+ elementos
            normalized.append({
                "id": item[0],
                "titulo": item[1],
                "autor": item[2],
                "ano_publicacao": item[3],
                "preco": item[4],
            })
        else: # Se o item é um objeto com atributos
            normalized.append({
                "id": getattr(item, "id", None),
                "titulo": getattr(item, "titulo", None),
                "autor": getattr(item, "autor", None),
                "ano_publicacao": getattr(item, "ano_publicacao", None),
                "preco": getattr(item, "preco", None),
            })
    return normalized

def _load_html_template() -> Template:
    """
    Carrega o conteúdo do arquivo 'template.html' e o retorna como um
    objeto `string.Template`.
    A função busca o arquivo no mesmo diretório do script `reporting.py`.
    Se o arquivo não for encontrado, uma exceção `FileNotFoundError` é levantada,
    com uma mensagem informativa.
    """
    try:
        with open(Path(__file__).parent / "template.html", "r", encoding="utf-8") as f:
            return Template(f.read())
    except FileNotFoundError as e:
        raise FileNotFoundError("O arquivo de template 'template.html' não foi encontrado. Certifique-se de que ele está na mesma pasta que reporting.py.") from e

# Carrega o template HTML na inicialização do módulo
HTML_TEMPLATE = _load_html_template()

def _create_html_rows(books: Iterable[Any]) -> str:
    """
    Cria as linhas de uma tabela HTML a partir de uma lista de dados de livros.
    Primeiro, normaliza os dados de entrada usando `_normalize_books`.
    Em seguida, itera sobre a lista normalizada e gera uma string HTML para
    cada linha da tabela (`<tr>...</tr>`), formatando os dados de forma adequada.
    Concatena todas as strings de linha em uma única string para ser inserida no template.
    """
    rows = []
    normalized = _normalize_books(books) # Normaliza os dados
    for b in normalized:
        # Extrai os dados do dicionário normalizado, com valores padrão para evitar erros
        id_ = b.get("id", "")
        titulo = b.get("titulo", "") or ""
        autor = b.get("autor", "") or ""
        ano = b.get("ano_publicacao", "") or ""
        preco = b.get("preco", "")
        # Formata o preço para duas casas decimais com vírgula, se for um número
        preco_str = f"{float(preco):.2f}".replace(".", ",") if isinstance(preco, (int, float)) else (str(preco) or "")
        
        row_html = f"""
          <tr>
            <td>{id_}</td>
            <td>{titulo}</td>
            <td>{autor}</td>
            <td>{ano}</td>
            <td>{preco_str}</td>
          </tr>
        """
        rows.append(row_html)
    return "".join(rows)

def generate_html_report(books: Iterable[Any], outfile: str | Path = "exports/relatorio_livros.html") -> str:
    """
    Gera um relatório HTML completo a partir de uma lista de livros.
    Cria o diretório de destino se ele não existir.
    Usa o template HTML carregado globalmente (`HTML_TEMPLATE`) e substitui
    os placeholders por dados dinâmicos: a data de geração, o total de livros
    e as linhas da tabela HTML geradas por `_create_html_rows`.
    Salva o conteúdo final em um arquivo `.html`.
    """
    outfile = Path(outfile)
    outfile.parent.mkdir(parents=True, exist_ok=True) # Cria o diretório de exports
    
    html = HTML_TEMPLATE.substitute(
        generated_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
        total=len(books),
        rows=_create_html_rows(books),
    )
    
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(html)
        
    return str(outfile.resolve()) # Retorna o caminho absoluto do arquivo gerado

def generate_pdf_report(books: Iterable[Any], outfile: str | Path = "exports/relatorio_livros.pdf") -> str:
    """
    Gera um relatório em formato PDF a partir de uma lista de livros.
    Verifica se a biblioteca `xhtml2pdf` (`pisa`) foi importada com sucesso.
    Se não, levanta um erro para informar o usuário.
    Gera o conteúdo HTML da mesma forma que `generate_html_report` e, em seguida,
    usa a biblioteca `xhtml2pdf` para converter o HTML para PDF.
    Salva o PDF em um arquivo no caminho de saída especificado.
    """
    if pisa is None:
        raise ImportError("Para gerar PDFs, instale 'xhtml2pdf' (pip install xhtml2pdf).")
    
    outfile = Path(outfile)
    outfile.parent.mkdir(parents=True, exist_ok=True) # Cria o diretório de exports
    
    # Gera o conteúdo HTML para ser convertido em PDF
    html_content = HTML_TEMPLATE.substitute(
        generated_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
        total=len(books),
        rows=_create_html_rows(books),
    )
    
    with open(outfile, "w+b") as pdf_file:
        # Usa a função `CreatePDF` da biblioteca `xhtml2pdf` para a conversão
        pisa_status = pisa.CreatePDF(
            html_content.encode("utf-8"),  # Converte o HTML para bytes
            dest=pdf_file,
        )
        
    if pisa_status.err:
        raise RuntimeError(f"Ocorreu um erro ao gerar o PDF. Código do erro: {pisa_status.err}")
    
    return str(outfile.resolve()) # Retorna o caminho absoluto do arquivo gerado