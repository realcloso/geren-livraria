from __future__ import annotations
from datetime import datetime
from string import Template
from typing import Iterable, Any
from pathlib import Path
from .validators import _normalize_books

try:
    from xhtml2pdf import pisa
except ImportError:
    pisa = None


def _load_html_template() -> Template:
    """
    Carrega o conteúdo do arquivo 'template.html'.
    """
    try:
        template_path = Path(__file__).parent / "template.html"
        with open(template_path, "r", encoding="utf-8") as f:
            return Template(f.read())
    except FileNotFoundError as e:
        msg = ("O arquivo de template 'template.html' não foi encontrado. "
               "Certifique-se de que ele está na mesma pasta que reporting.py.")
        raise FileNotFoundError(msg) from e

HTML_TEMPLATE = _load_html_template()


def _create_html_rows(books: Iterable[Any]) -> str:
    """
    Cria as linhas de uma tabela HTML a partir de uma lista de dados de livros.
    """
    rows = []
    normalized = _normalize_books(books)
    for b in normalized:
        id_ = b.get("id", "")
        titulo = b.get("titulo", "") or ""
        autor = b.get("autor", "") or ""
        ano = b.get("ano_publicacao", "") or ""
        preco = b.get("preco")
        preco_str = f"{float(preco):.2f}".replace(".", ",") if isinstance(preco, (int, float)) else (str(preco) or "")
        
        row_html = f"""
          <tr>
            <td>{id_}</td><td>{titulo}</td><td>{autor}</td>
            <td>{ano}</td><td>{preco_str}</td>
          </tr>
        """
        rows.append(row_html)
    return "".join(rows)


def generate_html_report(books: Iterable[Any], outfile: str | Path = "exports/relatorio_livros.html") -> str:
    """
    Gera um relatório HTML completo a partir de uma lista de livros.
    """
    outfile = Path(outfile)
    outfile.parent.mkdir(parents=True, exist_ok=True)
    
    html = HTML_TEMPLATE.substitute(
        generated_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
        total=len(list(books)),
        rows=_create_html_rows(books),
    )
    
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(html)
        
    return str(outfile.resolve())


def generate_pdf_report(books: Iterable[Any], outfile: str | Path = "exports/relatorio_livros.pdf") -> str:
    """
    Gera um relatório em formato PDF a partir de uma lista de livros.
    """
    if pisa is None:
        raise ImportError("Para gerar PDFs, instale 'xhtml2pdf' (pip install xhtml2pdf).")
    
    outfile = Path(outfile)
    outfile.parent.mkdir(parents=True, exist_ok=True)
    
    html_content = HTML_TEMPLATE.substitute(
        generated_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
        total=len(list(books)),
        rows=_create_html_rows(books),
    )
    
    with open(outfile, "w+b") as pdf_file:
        pisa_status = pisa.CreatePDF(html_content.encode("utf-8"), dest=pdf_file)
        
    if pisa_status.err:
        raise RuntimeError(f"Ocorreu um erro ao gerar o PDF. Código: {pisa_status.err}")
    
    return str(outfile.resolve())