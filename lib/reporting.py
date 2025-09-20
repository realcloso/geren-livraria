from __future__ import annotations
import os
from datetime import datetime
from string import Template
from typing import Iterable, Sequence, Mapping, Any, List
from pathlib import Path

# Try to import pisa, otherwise, raise an informative error
try:
    from xhtml2pdf import pisa
except ImportError:
    pisa = None

def _normalize_books(books: Iterable[Any]) -> List[dict]:
    normalized: List[dict] = []
    for item in books:
        if isinstance(item, Mapping):
            d = dict(item)
            key_map = {
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
                kn = key_map.get(k, k)
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
                "id": item[0],
                "titulo": item[1],
                "autor": item[2],
                "ano_publicacao": item[3],
                "preco": item[4],
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

def _load_html_template() -> Template:
    """Loads the HTML template from the external file."""
    try:
        with open(Path(__file__).parent / "template.html", "r", encoding="utf-8") as f:
            return Template(f.read())
    except FileNotFoundError as e:
        raise FileNotFoundError("O arquivo de template 'template.html' não foi encontrado. Certifique-se de que ele está na mesma pasta que reporting.py.") from e

HTML_TEMPLATE = _load_html_template()

def _create_html_rows(books: Iterable[Any]) -> str:
    """Helper function to create HTML table rows from a list of book tuples."""
    rows = []
    normalized = _normalize_books(books)
    for b in normalized:
        id_ = b.get("id", "")
        titulo = b.get("titulo", "") or ""
        autor = b.get("autor", "") or ""
        ano = b.get("ano_publicacao", "") or ""
        preco = b.get("preco", "")
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
    """Generates an HTML report of books and saves it to a file."""
    outfile = Path(outfile)
    outfile.parent.mkdir(parents=True, exist_ok=True)
    
    html = HTML_TEMPLATE.substitute(
        generated_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
        total=len(books),
        rows=_create_html_rows(books),
    )
    
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(html)
        
    return str(outfile.resolve())

def generate_pdf_report(books: Iterable[Any], outfile: str | Path = "exports/relatorio_livros.pdf") -> str:
    """Generates a PDF report of books."""
    if pisa is None:
        raise ImportError("Para gerar PDFs, instale 'xhtml2pdf' (pip install xhtml2pdf).")
    
    outfile = Path(outfile)
    outfile.parent.mkdir(parents=True, exist_ok=True)
    
    html_content = HTML_TEMPLATE.substitute(
        generated_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
        total=len(books),
        rows=_create_html_rows(books),
    )
    
    with open(outfile, "w+b") as pdf_file:
        pisa_status = pisa.CreatePDF(
            html_content.encode("utf-8"),  # Convert the HTML string to bytes
            dest=pdf_file,
        )
        
    if pisa_status.err:
        raise RuntimeError(f"Ocorreu um erro ao gerar o PDF. Código do erro: {pisa_status.err}")
    
    return str(outfile.resolve())