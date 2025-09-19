import sqlite3
from typing import List, Tuple, Optional

class DBManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS livros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                autor TEXT NOT NULL,
                ano_publicacao INTEGER NOT NULL,
                preco REAL NOT NULL
            )
        """)
        conn.close()

    def get_all_books(self) -> List[Tuple]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("SELECT id, titulo, autor, ano_publicacao, preco FROM livros ORDER BY id")
            return cur.fetchall()

    def find_books_by_author(self, term: str) -> List[Tuple]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "SELECT id, titulo, autor, ano_publicacao, preco FROM livros WHERE autor LIKE ? ORDER BY id",
                (f"%{term}%",)
            )
            return cur.fetchall()

    def add_book(self, titulo: str, autor: str, ano: int, preco: float) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO livros (titulo, autor, ano_publicacao, preco) VALUES (?, ?, ?, ?)",
                (titulo, autor, ano, preco)
            )
            conn.commit()

    def update_price(self, livro_id: int, novo_preco: float) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("UPDATE livros SET preco = ? WHERE id = ?", (novo_preco, livro_id))
            conn.commit()
            return cur.rowcount

    def remove_book(self, livro_id: int) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("DELETE FROM livros WHERE id = ?", (livro_id,))
            conn.commit()
            return cur.rowcount