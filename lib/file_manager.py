import csv
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional

from . import mapping
from .validators import (_normalize_row, validate_text, validate_year, validate_price, ValidationError)


class FileManager:
    """
    Gerencia a estrutura de arquivos e diretórios da aplicação.
    """
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.data_dir = self.base_dir / "data"
        self.backup_dir = self.base_dir / "backups"
        self.exports_dir = self.base_dir / "exports"
        self.db_path = self.data_dir / "livraria.db"
        self.max_backups = 5
        self.ensure_dirs()

    def ensure_dirs(self) -> None:
        """
        Cria os diretórios 'data', 'backups' e 'exports' se eles não existirem.
        """
        for d in (self.data_dir, self.backup_dir, self.exports_dir):
            d.mkdir(parents=True, exist_ok=True)

    def backup_db(self) -> Path:
        """
        Cria um backup do arquivo do banco de dados.
        """
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
        """
        Remove os arquivos de backup mais antigos.
        """
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


# A anotação @staticmethod em Python transforma uma função dentro de uma classe em um método estático, ou seja:
# Ele não recebe automaticamente o parâmetro self (instância da classe) nem cls (classe).
# Funciona como uma função normal, mas fica organizada dentro da classe, porque faz sentido conceitualmente estar ligada a ela.
    @staticmethod
    def _detect_dialect(sample_text: str) -> csv.Dialect:
        """
        Tenta detectar o delimitador (dialect) de um arquivo CSV.
        """
        try:
            return csv.Sniffer().sniff(sample_text, delimiters=",;\t|")
        except Exception:
            return csv.excel

    def export_to_csv(self, books: List[Tuple], outfile_name: str = "livros_exportados.csv") -> Path:
        """
        Exporta uma lista de dados de livros para um arquivo CSV.
        """
        path = self.exports_dir / outfile_name
        self.exports_dir.mkdir(parents=True, exist_ok=True)

        normalized_rows = [_normalize_row(item) for item in books]
        has_any_id = any(r[0] is not None for r in normalized_rows)

        header = ["id", "titulo", "autor", "ano_publicacao", "preco"] if has_any_id \
                 else ["titulo", "autor", "ano_publicacao", "preco"]

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for r in normalized_rows:
                writer.writerow(r if has_any_id else r[1:])
        return path

    def get_csv_data(self, csv_path: str) -> List[dict]:
        """
        Lê um arquivo CSV e retorna os dados como uma lista de dicionários.
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
    Função independente para importar dados de um arquivo CSV para o banco de dados.
    """
    p = Path(csv_path).expanduser().resolve()
    if not p.exists():
        return 0, 0, [f"Arquivo não encontrado: {p}"]

    inserted, skipped, errors = 0, 0, []

    with p.open("r", encoding="utf-8") as f:
        sample = f.read(4096)
        f.seek(0)
        dialect = FileManager._detect_dialect(sample)
        reader = csv.DictReader(f, dialect=dialect)
        
        raw_headers = { (h or "").strip().lower(): h for h in (reader.fieldnames or []) }

        def find_col_name(*aliases: str) -> Optional[str]:
            for alias in aliases:
                if alias in raw_headers:
                    return raw_headers[alias]
            return None

        col_titulo = find_col_name(*mapping.CSV_COLUMN_ALIASES["titulo"])
        col_autor = find_col_name(*mapping.CSV_COLUMN_ALIASES["autor"])
        col_ano = find_col_name(*mapping.CSV_COLUMN_ALIASES["ano_publicacao"])
        col_preco = find_col_name(*mapping.CSV_COLUMN_ALIASES["preco"])

        missing = [name for name, col in {
            "titulo": col_titulo, "autor": col_autor, "ano": col_ano, "preco": col_preco
        }.items() if col is None]

        if missing:
            errors.append(f"Cabeçalho inválido. Colunas faltando: {', '.join(missing)}")
            return 0, 0, errors

        for i, row in enumerate(reader, start=2):
            try:
                titulo = validate_text("Título", row.get(col_titulo, ""))
                autor = validate_text("Autor", row.get(col_autor, ""))
                ano = validate_year("Ano", row.get(col_ano, ""))
                preco = validate_price("Preço", row.get(col_preco, ""))
                
                if db.add_book(titulo, autor, ano, preco):
                    inserted += 1
                else:
                    skipped += 1
            except ValidationError as e:
                errors.append(f"Linha {i}: {e}")
                skipped += 1

    return inserted, skipped, errors