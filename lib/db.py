import sqlite3
from pathlib import Path

class DBManager:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS livros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo TEXT NOT NULL,
                    autor TEXT NOT NULL,
                    ano_publicacao INTEGER NOT NULL,
                    preco REAL NOT NULL
                )
            """)
            conn.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_livro_unique
                ON livros (titulo, autor, ano_publicacao)
            """)
            conn.commit()

    def add_book(self, titulo: str, autor: str, ano: int, preco: float) -> int:
        """
        Insere um livro. Evita duplicatas por (titulo, autor, ano_publicacao).
        Retorna:
          1 se inseriu,
          0 se ignorou (duplicado).
        """
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "INSERT OR IGNORE INTO livros (titulo, autor, ano_publicacao, preco) VALUES (?, ?, ?, ?)",
                (titulo, autor, ano, preco)
            )
            conn.commit()
            return cur.rowcount 

    def get_all_books(self):
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute(
                "SELECT id, titulo, autor, ano_publicacao, preco FROM livros ORDER BY id"
            ).fetchall()

    def update_price(self, book_id: int, new_price: float) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "UPDATE livros SET preco = ? WHERE id = ?",
                (new_price, book_id)
            )
            conn.commit()
            return cur.rowcount

    def remove_book(self, book_id: int) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("DELETE FROM livros WHERE id = ?", (book_id,))
            conn.commit()
            return cur.rowcount

    def find_books_by_author(self, termo: str):
        like = f"%{termo}%"
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute(
                "SELECT id, titulo, autor, ano_publicacao, preco "
                "FROM livros WHERE autor LIKE ? ORDER BY id",
                (like,)
            ).fetchall()
