from __future__ import annotations
import os
from datetime import datetime
from string import Template
from typing import Iterable, Sequence, Mapping, Any, List

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

HTML_TEMPLATE = Template("""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Relatório de Livros</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  :root { --bg:#0f172a; --card:#111827; --ink:#e5e7eb; --muted:#9ca3af; --accent:#22d3ee; }
  * { box-sizing: border-box; }
  body { margin:0; font-family: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, 'Helvetica Neue', Arial; background: var(--bg); color: var(--ink); }
  .wrap { max-width: 1100px; margin: 40px auto; padding: 0 16px; }
  h1 { font-size: 28px; margin: 0 0 12px; }
  .meta { color: var(--muted); margin-bottom: 24px; font-size: 14px; }
  .card { background: linear-gradient(180deg, rgba(34,211,238,0.08), rgba(34,211,238,0.02)); border: 1px solid rgba(34,211,238,0.15); border-radius: 16px; padding: 18px; }
  table { width: 100%; border-collapse: collapse; }
  thead th { text-align: left; font-weight: 600; font-size: 14px; color: var(--ink); border-bottom: 1px solid rgba(229,231,235,0.15); padding: 10px 8px; }
  tbody td { border-bottom: 1px solid rgba(229,231,235,0.08); padding: 12px 8px; font-size: 14px; }
  tbody tr:hover { background: rgba(34,211,238,0.06); }
  .badge { display: inline-block; padding: 3px 8px; border-radius: 999px; background: rgba(34,211,238,0.12); color: var(--ink); font-size: 12px; border: 1px solid rgba(34,211,238,0.25); }
  .ft { margin-top: 12px; color: var(--muted); font-size: 12px; }
</style>
</head>
<body>
  <div class="wrap">
    <h1>Relatório de Livros</h1>
    <div class="meta">Gerado em <span class="badge">$generated_at</span> — Total: <span class="badge">$total</span></div>
    <div class="card">
      <table>
        <thead>
          <tr>
            <th style="width:80px">ID</th>
            <th>Título</th>
            <th>Autor</th>
            <th style="width:140px">Ano</th>
            <th style="width:140px">Preço (R$)</th>
          </tr>
        </thead>
        <tbody>
          $rows
        </tbody>
      </table>
      <div class="ft">Exportado pela CLI da Livraria</div>
    </div>
  </div>
</body>
</html>
""")

def _row_html(cells: Sequence[str]) -> str:
    return "<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"

def generate_html_report(books: Iterable[Any], outfile: str = "exports/relatorio_livros.html") -> str:
    os.makedirs(os.path.dirname(outfile) or ".", exist_ok=True)
    normalized = _normalize_books(books)
    rows = []
    for b in normalized:
        id_ = b.get("id", "")
        titulo = b.get("titulo", "") or ""
        autor = b.get("autor", "") or ""
        ano = b.get("ano_publicacao", "") or ""
        preco = b.get("preco", "")
        preco_str = f"{float(preco):.2f}".replace(".", ",") if isinstance(preco, (int, float)) else (str(preco) or "")
        rows.append(_row_html([str(id_), titulo, autor, str(ano), preco_str]))
    html = HTML_TEMPLATE.substitute(
        generated_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
        total=len(normalized),
        rows="\n".join(rows),
    )
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(html)
    return os.path.abspath(outfile)

def generate_pdf_report(books: Iterable[Any], outfile: str = "exports/relatorio_livros.pdf") -> str:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.pdfgen import canvas
        from reportlab.platypus import Table, TableStyle
    except Exception as exc:
        raise ImportError("Para PDF, instale 'reportlab' (pip install reportlab).") from exc
    os.makedirs(os.path.dirname(outfile) or ".", exist_ok=True)
    normalized = _normalize_books(books)
    data: List[List[str]] = [["ID", "Título", "Autor", "Ano", "Preço (R$)"]]
    for b in normalized:
        preco = b.get("preco", "")
        preco_str = f"{float(preco):.2f}".replace(".", ",") if isinstance(preco, (int, float)) else (str(preco) or "")
        data.append([
            str(b.get("id", "")),
            str(b.get("titulo", "") or ""),
            str(b.get("autor", "") or ""),
            str(b.get("ano_publicacao", "") or ""),
            preco_str
        ])
    c = canvas.Canvas(outfile, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, height - 40, "Relatório de Livros")
    c.setFont("Helvetica", 9)
    c.drawString(40, height - 56, f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} — Total: {len(normalized)}")
    table = Table(data, colWidths=[40, 220, 160, 60, 70])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F3F4F6")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EEF2FF")]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
    ]))
    table_w, table_h = table.wrapOn(c, width - 80, height - 120)
    table.drawOn(c, 40, height - 90 - table_h)
    c.showPage()
    c.save()
    return os.path.abspath(outfile)
