import csv
from .validators import validate_text, validate_year, validate_price, ValidationError
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Any, Mapping, Optional


class FileManager:
    """
    Gerencia a estrutura de arquivos e diretórios da aplicação.
    Responsável por operações como garantir a existência de diretórios,
    fazer backups do banco de dados, limpar backups antigos, e
    lidar com a exportação e importação de dados em arquivos CSV.
    """
    def __init__(self, base_dir: Path):
        # Define os caminhos base para dados, backups e exports
        self.base_dir = base_dir
        self.data_dir = self.base_dir / "data"
        self.backup_dir = self.base_dir / "backups"
        self.exports_dir = self.base_dir / "exports"
        self.db_path = self.data_dir / "livraria.db"
        self.max_backups = 5  # Limite máximo de backups a serem mantidos
        self.ensure_dirs() # Garante que os diretórios necessários existam

    def ensure_dirs(self) -> None:
        """
        Cria os diretórios 'data', 'backups' e 'exports' se eles não existirem.
        O método 'mkdir(parents=True, exist_ok=True)' é usado para evitar erros
        se os diretórios já existirem ou para criar a estrutura completa.
        """
        for d in (self.data_dir, self.backup_dir, self.exports_dir):
            d.mkdir(parents=True, exist_ok=True)

    def backup_db(self) -> Path:
        """
        Cria um backup do arquivo do banco de dados (livraria.db).
        O backup é nomeado com um timestamp para ser único e fácil de rastrear.
        Após a cópia, chama 'clean_old_backups' para remover backups antigos.
        Retorna o caminho do arquivo de backup recém-criado.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        backup_file = self.backup_dir / f"backup_livraria_{timestamp}.db"
        if not self.db_path.exists():
            # Se o banco de dados não existir, cria o diretório e um arquivo vazio
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.db_path, "w", encoding="utf-8"):
                pass
        shutil.copy2(self.db_path, backup_file) # Copia o arquivo do banco de dados
        self.clean_old_backups() # Limpa backups mais antigos que o limite
        return backup_file

    def clean_old_backups(self) -> None:
        """
        Remove os arquivos de backup mais antigos para manter o número
        total de backups dentro do limite definido por 'max_backups'.
        Ele lista todos os arquivos de backup, os ordena por data de modificação
        (do mais novo para o mais velho) e remove os que excedem o limite.
        """
        backups = sorted(
            self.backup_dir.glob("backup_livraria_*.db"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for old in backups[self.max_backups:]:
            try:
                old.unlink() # Deleta o arquivo
            except Exception as e:
                print(f"[Aviso] Não foi possível remover backup '{old.name}': {e}")

    @staticmethod
    def _normalize_row(item: Any) -> Tuple[Optional[Any], Any, Any, Any, Any]:
        """
        Método estático para unificar diferentes formatos de dados de livros
        (dicionários, tuplas, listas ou objetos) em uma tupla consistente
        com a estrutura (id, titulo, autor, ano_publicacao, preco).
        Isso simplifica o processamento posterior, como na exportação para CSV.
        """
        if isinstance(item, Mapping): # Caso o item seja um dicionário
            id_ = item.get("id")
            titulo = item.get("titulo") or item.get("title") # Aceita 'titulo' ou 'title'
            autor = item.get("autor") or item.get("author") # Aceita 'autor' ou 'author'
            ano = item.get("ano_publicacao") or item.get("ano") or item.get("year") # Aceita vários sinônimos
            preco = item.get("preco") or item.get("price") # Aceita 'preco' ou 'price'
            return (id_, titulo, autor, ano, preco)

        if isinstance(item, (list, tuple)): # Caso o item seja uma lista ou tupla
            if len(item) >= 5:
                return (item[0], item[1], item[2], item[3], item[4])
            if len(item) == 4:
                # Se a tupla tiver 4 elementos, assume que o 'id' está ausente
                t, a, y, p = item
                return (None, t, a, y, p)

            padded = list(item[:5]) + [None] * max(0, 5 - len(item))
            return (padded[0], padded[1], padded[2], padded[3], padded[4])

        # Caso o item seja um objeto com atributos
        return (
            getattr(item, "id", None),
            getattr(item, "titulo", None),
            getattr(item, "autor", None),
            getattr(item, "ano_publicacao", None),
            getattr(item, "preco", None),
        )

    @staticmethod
    def _detect_dialect(sample_text: str) -> csv.Dialect:
        """
        Método estático para tentar detectar o delimitador (dialect) de um arquivo CSV
        usando a classe 'csv.Sniffer'. Se a detecção falhar, retorna o dialect padrão 'csv.excel'.
        Isso torna a leitura de CSVs mais robusta, aceitando diferentes formatos de delimitadores.
        """
        try:
            return csv.Sniffer().sniff(sample_text, delimiters=",;\t|")
        except Exception:
            return csv.excel

    def export_to_csv(self, books: List[Tuple], outfile_name: str = "livros_exportados.csv") -> Path:
        """
        Exporta uma lista de dados de livros para um arquivo CSV.
        Primeiro, normaliza a lista de livros para um formato consistente.
        Verifica se algum dos livros tem um 'id' para decidir se a coluna 'id' deve ser incluída no cabeçalho.
        Em seguida, escreve o cabeçalho e os dados no arquivo CSV.
        Retorna o caminho do arquivo de exportação criado.
        """
        path = self.exports_dir / outfile_name
        self.exports_dir.mkdir(parents=True, exist_ok=True)

        normalized_rows = [self._normalize_row(item) for item in books] # Normaliza os dados
        has_any_id = any(r[0] is not None for r in normalized_rows) # Verifica se 'id' deve ser incluído

        header = ["id", "titulo", "autor", "ano_publicacao", "preco"] if has_any_id \
                 else ["titulo", "autor", "ano_publicacao", "preco"]

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header) # Escreve o cabeçalho
            for r in normalized_rows:
                if has_any_id:
                    writer.writerow([r[0], r[1], r[2], r[3], r[4]]) # Escreve a linha completa
                else:
                    writer.writerow([r[1], r[2], r[3], r[4]]) # Escreve a linha sem 'id'

        return path

    def get_csv_data(self, csv_path: str) -> List[dict]:
        """
        Lê um arquivo CSV do caminho especificado e retorna os dados como
        uma lista de dicionários.
        Usa 'csv.Sniffer' para detectar o dialeto do CSV (delimitador, etc.) de forma dinâmica,
        tornando-o flexível a diferentes formatos.
        """
        path = Path(csv_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError("Arquivo não encontrado.")

        with open(path, "r", encoding="utf-8") as f:
            sample = f.read(4096)
            f.seek(0)
            dialect = self._detect_dialect(sample) # Detecta o dialeto
            reader = csv.DictReader(f, dialect=dialect)
            return [row for row in reader]


def import_from_csv(db, csv_path: str):
    """
    Função independente para importar dados de um arquivo CSV para o banco de dados.
    Primeiro, valida a existência do arquivo e detecta seu dialeto.
    Em seguida, mapeia os cabeçalhos do CSV para sinônimos de colunas (e.g., 'title' -> 'titulo').
    Itera sobre cada linha do arquivo, valida os dados de cada coluna usando as funções 'validate_text',
    'validate_year' e 'validate_price' e, se a validação for bem-sucedida, insere o livro no banco de dados.
    Mantém contagens de livros inseridos e ignorados, e uma lista de erros encontrados.
    Retorna uma tupla contendo (inseridos, ignorados, erros).
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
            """Função auxiliar para encontrar o nome da coluna original a partir de sinônimos."""
            for k in keys_lower:
                if k in headers_map:
                    return headers_map[k]
            return None

        # Mapeia as colunas necessárias usando os sinônimos
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

        for i, row in enumerate(reader, start=2): # Começa a contagem de linhas do CSV em 2 (cabeçalho + primeira linha)
            try:
                # Obtém os valores brutos da linha
                raw_titulo = row.get(col_titulo, "") if col_titulo else ""
                raw_autor = row.get(col_autor, "") if col_autor else ""
                raw_ano = row.get(col_ano, "") if col_ano else ""
                raw_preco = row.get(col_preco, "") if col_preco else ""

                # Converte e valida cada valor, tratando erros
                titulo = validate_text("Título", raw_titulo)
                autor = validate_text("Autor", raw_autor)
                ano = validate_year("Ano de publicação", raw_ano)

                # Trata a formatação do preço, convertendo vírgula para ponto se necessário
                preco_str = str(raw_preco).replace(" ", "")
                if "," in preco_str and "." not in preco_str:
                    preco_str = preco_str.replace(",", ".")
                preco = validate_price("Preço", preco_str)

                # Adiciona o livro ao banco de dados e incrementa o contador
                db.add_book(titulo, autor, ano, preco)
                inserted += 1

            except Exception as e:
                # Captura e registra erros para linhas inválidas, incrementando o contador de ignorados
                skipped += 1
                errors.append(f"Linha {i}: {e}")

    return inserted, skipped, errors