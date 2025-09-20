import csv
from .validators import validate_text, validate_year, validate_price, ValidationError
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Any, Mapping, Optional


class FileManager:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.data_dir = self.base_dir / "data"
        self.backup_dir = self.base_dir / "backups"
        self.exports_dir = self.base_dir / "exports"
        self.db_path = self.data_dir / "livraria.db"
        self.max_backups = 5
        self.ensure_dirs()

    def ensure_dirs(self) -> None:
        for d in (self.data_dir, self.backup_dir, self.exports_dir):
            d.mkdir(parents=True, exist_ok=True)

    def backup_db(self) -> Path:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        backup_file = self.backup_dir / f"backup_livraria_{timestamp}.db"
        if not self.db_path.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.db_path, "w", encoding="utf-8"):
                pass
        shutil.copy2(self.db_path, backup_file)
        self.clean_old_backups()
        return backup_file

    def clean_old_backups(self) -> None:
        backups = sorted(
            self.backup_dir.glob("backup_livraria_*.db"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for old in backups[self.max_backups:]:
            try:
                old.unlink()
            except Exception as e:
                print(f"[Aviso] Não foi possível remover backup '{old.name}': {e}")

    @staticmethod
    def _normalize_row(item: Any) -> Tuple[Optional[Any], Any, Any, Any, Any]:
        """
        Normaliza diferentes formatos de 'livro' para a tupla:
        (id, titulo, autor, ano_publicacao, preco)
        - Aceita dict (id?, titulo|title, autor|author, ano_publicacao|ano|year, preco|price)
        - Aceita tupla/lista (id, titulo, autor, ano_publicacao, preco) OU (titulo, autor, ano_publicacao, preco)
        - Aceita objetos com atributos correspondentes
        """
        if isinstance(item, Mapping):
            id_ = item.get("id")
            titulo = item.get("titulo") or item.get("title")
            autor = item.get("autor") or item.get("author")
            ano = item.get("ano_publicacao") or item.get("ano") or item.get("year")
            preco = item.get("preco") or item.get("price")
            return (id_, titulo, autor, ano, preco)

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

    @staticmethod
    def _detect_dialect(sample_text: str) -> csv.Dialect:
        try:
            return csv.Sniffer().sniff(sample_text, delimiters=",;\t|")
        except Exception:
            return csv.excel

    def export_to_csv(self, books: List[Tuple], outfile_name: str = "livros_exportados.csv") -> Path:
        """
        Exporta livros para CSV de forma consistente.
        Aceita:
          - sequência de tuplas/listas (id, titulo, autor, ano_publicacao, preco) OU (titulo, autor, ano_publicacao, preco)
          - sequência de dicts com chaves: id?, titulo|title, autor|author, ano_publicacao|ano|year, preco|price

        Se houver ao menos um 'id' não-nulo, inclui a coluna 'id' no CSV.
        """
        path = self.exports_dir / outfile_name
        self.exports_dir.mkdir(parents=True, exist_ok=True)

        normalized_rows = [self._normalize_row(item) for item in books]
        has_any_id = any(r[0] is not None for r in normalized_rows)

        header = ["id", "titulo", "autor", "ano_publicacao", "preco"] if has_any_id \
                 else ["titulo", "autor", "ano_publicacao", "preco"]

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for r in normalized_rows:
                if has_any_id:
                    writer.writerow([r[0], r[1], r[2], r[3], r[4]])
                else:
                    writer.writerow([r[1], r[2], r[3], r[4]])

        return path

    def get_csv_data(self, csv_path: str) -> List[dict]:
        """
        Lê um CSV e retorna lista de dicts.
        Faz detecção de delimitador (vírgula/;/\t/|) via csv.Sniffer.
        Preserva os nomes originais das colunas.
        """
        path = Path(csv_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError("Arquivo não encontrado.")

        with open(path, "r", encoding="utf-8") as f:
            sample = f.read(4096)
            f.seek(0)
            dialect = self._detect_dialect(sample)
            reader = csv.DictReader(f, dialect=dialect)
            return [row for row in reader]

def import_from_csv(db, csv_path: str):
    """
    Lê um CSV e insere no banco.
    Aceita cabeçalhos com ou sem 'id' e sinônimos:
      - titulo | title
      - autor  | author
      - ano_publicacao | ano | year
      - preco  | price

    Retorna (inseridos, ignorados, erros:list[str]).
    """
    p = Path(csv_path).expanduser().resolve()
    if not p.exists():
        return 0, 0, [f"Arquivo não encontrado: {p}"]

    inserted = 0
    skipped = 0
    errors: List[str] = []

    with p.open("r", encoding="utf-8") as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        except Exception:
            dialect = csv.excel

        reader = csv.DictReader(f, dialect=dialect)
        raw_headers = [(h or "").strip() for h in (reader.fieldnames or [])]
        headers_map = {h.lower(): h for h in raw_headers}

        def pick(*keys_lower: str) -> Optional[str]:
            for k in keys_lower:
                if k in headers_map:
                    return headers_map[k]
            return None

        col_titulo = pick("titulo", "title")
        col_autor = pick("autor", "author")
        col_ano = pick("ano_publicacao", "ano", "year")
        col_preco = pick("preco", "price")

        missing = [name for name, col in {
            "titulo": col_titulo, "autor": col_autor, "ano_publicacao": col_ano, "preco": col_preco
        }.items() if col is None]

        if missing:
            errors.append(
                "Cabeçalho inválido. Esperado pelo menos as colunas: "
                "titulo (ou title), autor (ou author), ano_publicacao (ou ano/year), preco (ou price). "
                f"Faltando: {', '.join(missing)}"
            )
            return 0, 0, errors

        for i, row in enumerate(reader, start=2):
            try:
                raw_titulo = row.get(col_titulo, "") if col_titulo else ""
                raw_autor = row.get(col_autor, "") if col_autor else ""
                raw_ano = row.get(col_ano, "") if col_ano else ""
                raw_preco = row.get(col_preco, "") if col_preco else ""


                titulo = validate_text("Título", raw_titulo)
                autor = validate_text("Autor", raw_autor)
                ano = validate_year("Ano de publicação", raw_ano)

                preco_str = str(raw_preco).replace(" ", "")
                if "," in preco_str and "." not in preco_str:
                    preco_str = preco_str.replace(",", ".")
                preco = validate_price("Preço", preco_str)

                db.add_book(titulo, autor, ano, preco)
                inserted += 1

            except Exception as e:
                skipped += 1
                errors.append(f"Linha {i}: {e}")

    return inserted, skipped, errors