from __future__ import annotations
from pathlib import Path
from datetime import datetime

HTML_TEMPLATE = """<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8">
  <title>Relatório — Livraria</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color:#222; }}
    h1 {{ margin: 0 0 8px 0; }}
    .meta {{ color:#666; margin-bottom:16px; }}
    table {{ border-collapse: collapse; width:100%; }}
    th, td {{ border:1px solid #ddd; padding:8px; }}
    th {{ background:#f4f4f4; text-align:left; }}
    tfoot td {{ font-weight:bold; }}
    .right {{ text-align:right; }}
  </style>
</head>
<body>
  <h1>Relatório de Livros</h1>
  <div class="meta">Gerado em: {generated_at}</div>
  <table>
    <thead>
      <tr>
        <th>ID</th><th>Título</th><th>Autor</th><th>Ano</th><th class="right">Preço (R$)</th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
    <tfoot>
      <tr>
        <td colspan="4">Total de livros</td>
        <td class="right">{count}</td>
      </tr>
      <tr>
        <td colspan="4">Soma dos preços</td>
        <td class="right">{sum_prices:.2f}</td>
      </tr>
      <tr>
        <td colspan="4">Preço médio</td>
        <td class="right">{avg_price:.2f}</td>
      </tr>
    </tfoot>
  </table>
</body>
</html>"""

def generate_html_report(books, out_path: Path) -> Path:
    """books: sequência de (id, titulo, autor, ano_publicacao, preco)"""
    rows = []
    total = 0.0
    for _id, titulo, autor, ano, preco in books:
        rows.append(
            f"<tr><td>{_id}</td><td>{titulo}</td><td>{autor}</td><td>{ano}</td>"
            f"<td class='right'>{float(preco):.2f}</td></tr>"
        )
        total += float(preco)
    count = len(books)
    avg = (total / count) if count else 0.0
    html = HTML_TEMPLATE.format(
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        rows_html="\n".join(rows) or "<tr><td colspan='5'>(vazio)</td></tr>",
        count=count,
        sum_prices=total,
        avg_price=avg
    )
    out_path = Path(out_path)
    out_path.write_text(html, encoding="utf-8")
    return out_path

def generate_pdf_report(books, out_path: Path) -> Path:
    """
    Gera PDF usando reportlab, se instalado.
    pip install reportlab
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
    except Exception as e:
        raise RuntimeError("Biblioteca 'reportlab' não está instalada. Instale com: pip install reportlab") from e

    width, height = A4
    c = canvas.Canvas(str(out_path), pagesize=A4)

    y = height - 20*mm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(20*mm, y, "Relatório de Livros")
    y -= 8*mm
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.grey)
    c.drawString(20*mm, y, f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.setFillColor(colors.black)
    y -= 10*mm

    headers = ["ID","Título","Autor","Ano","Preço (R$)"]
    widths = [15*mm, 60*mm, 45*mm, 20*mm, 25*mm]

    c.setFont("Helvetica-Bold", 10)
    x = 20*mm
    for h, w in zip(headers, widths):
        c.drawString(x, y, h)
        x += w
    y -= 6*mm
    c.line(20*mm, y, width-20*mm, y)
    y -= 4*mm

    c.setFont("Helvetica", 10)
    total = 0.0
    for _id, titulo, autor, ano, preco in books:
        x = 20*mm
        row = [str(_id), str(titulo), str(autor), str(ano), f"{float(preco):.2f}"]
        for val, w in zip(row, widths):
            c.drawString(x, y, val[:40])
            x += w
        total += float(preco)
        y -= 6*mm
        if y < 20*mm:
            c.showPage()
            y = height - 20*mm
            c.setFont("Helvetica", 10)

    count = len(books)
    avg = (total / count) if count else 0.0
    if y < 35*mm:
        c.showPage()
        y = height - 20*mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20*mm, y, f"Total de livros: {count}")
    y -= 6*mm
    c.drawString(20*mm, y, f"Soma dos preços: R$ {total:.2f}")
    y -= 6*mm
    c.drawString(20*mm, y, f"Preço médio: R$ {avg:.2f}")

    c.showPage()
    c.save()
    return out_path
