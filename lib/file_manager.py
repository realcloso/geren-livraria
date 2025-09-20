import csv
from .validators import validate_text, validate_year, validate_price, ValidationError
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

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
            with open(self.db_path, "w") as f:
                pass
        shutil.copy2(self.db_path, backup_file)
        self.clean_old_backups()
        return backup_file

    def clean_old_backups(self) -> None:
        backups = sorted(self.backup_dir.glob("backup_livraria_*.db"),
                         key=lambda p: p.stat().st_mtime, reverse=True)
        for old in backups[self.max_backups:]:
            try:
                old.unlink()
            except Exception as e:
                print(f"[Aviso] Não foi possível remover backup '{old.name}': {e}")

    def export_to_csv(self, books: List[Tuple]) -> Path:
        path = self.exports_dir / "livros_exportados.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["titulo", "autor", "ano_publicacao", "preco"])
            for row in books:
                if isinstance(row, (list, tuple)):
                    if len(row) == 5:
                        row = row[1:]
                    writer.writerow(row)
                elif isinstance(row, dict):
                    writer.writerow([
                        row.get('titulo'),
                        row.get('autor'),
                        row.get('ano_publicacao'),
                        row.get('preco')
                    ])
        return path

    def get_csv_data(self, csv_path: str) -> List[dict]:
        path = Path(csv_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError("Arquivo não encontrado.")
        data = []
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        return data

def import_from_csv(db, csv_path: str):
    """
    Lê um CSV e insere no banco.
    Espera cabeçalho: titulo, autor, ano_publicacao, preco
    Retorna (inseridos, ignorados, erros:list[str]).
    """
    import csv
    from pathlib import Path
    p = Path(csv_path).expanduser().resolve()
    if not p.exists():
        return 0, 0, [f"Arquivo não encontrado: {p}"]

    inserted = 0
    skipped = 0
    errors = []

    with p.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        expected = {"titulo", "autor", "ano_publicacao", "preco"}
        headers = {(h or "").strip().lower() for h in (reader.fieldnames or [])}
        if not expected.issubset(headers):
            errors.append("Cabeçalho inválido. Esperado: titulo, autor, ano_publicacao, preco")
            return 0, 0, errors

        for i, row in enumerate(reader, start=2):
            try:
                titulo = validate_text("Título", row.get("titulo", ""))
                autor = validate_text("Autor", row.get("autor", ""))
                ano = validate_year("Ano de publicação", row.get("ano_publicacao", "0"))
                preco = validate_price("Preço", row.get("preco", "0"))
                db.add_book(titulo, autor, ano, preco)
                inserted += 1
            except Exception as e:
                skipped += 1
                errors.append(f"Linha {i}: {e}")

    return inserted, skipped, errors
