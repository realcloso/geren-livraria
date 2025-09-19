# file: main.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Gerenciamento de Livraria (CLI)
"""
from __future__ import annotations
from pathlib import Path

from lib.db import DBManager
from lib.file_manager import FileManager
from lib.utils import input_int, input_float, input_nonempty

class LivrariaCLI:
    def __init__(self):
        BASE_DIR = Path(__file__).resolve().parent
        self.file_manager = FileManager(BASE_DIR)
        self.db_manager = DBManager(str(self.file_manager.db_path))

    def adicionar_livro(self) -> None:
        print("\n=== Adicionar novo livro ===")
        titulo = input_nonempty("Título: ")
        autor = input_nonempty("Autor: ")
        ano = input_int("Ano de publicação: ")
        preco = input_float("Preço (ex.: 39.90): ")
        
        self.file_manager.backup_db()
        self.db_manager.add_book(titulo, autor, ano, preco)
        print("✔ Livro adicionado com sucesso!")

    def exibir_livros(self) -> None:
        print("\n=== Todos os livros ===")
        rows = self.db_manager.get_all_books()
        if not rows:
            print("(vazio)")
            return
        self._print_books(rows)

    def atualizar_preco(self) -> None:
        print("\n=== Atualizar preço de um livro ===")
        livro_id = input_int("ID do livro: ")
        novo_preco = input_float("Novo preço: ")
        
        self.file_manager.backup_db()
        updated_count = self.db_manager.update_price(livro_id, novo_preco)
        
        if updated_count == 0:
            print("⚠ ID não encontrado.")
        else:
            print("✔ Preço atualizado com sucesso!")

    def remover_livro(self) -> None:
        print("\n=== Remover um livro ===")
        livro_id = input_int("ID do livro: ")
        
        self.file_manager.backup_db()
        removed_count = self.db_manager.remove_book(livro_id)
        
        if removed_count == 0:
            print("⚠ ID não encontrado.")
        else:
            print("✔ Livro removido com sucesso!")

    def buscar_por_autor(self) -> None:
        print("\n=== Buscar livros por autor ===")
        termo = input_nonempty("Autor (termo de busca): ")
        rows = self.db_manager.find_books_by_author(f"%{termo}%")
        if not rows:
            print("Nenhum livro encontrado para esse autor.")
            return
        self._print_books(rows)

    def exportar_csv(self) -> None:
        print("\n=== Exportar dados para CSV ===")
        books = self.db_manager.get_all_books()
        path = self.file_manager.export_to_csv(books)
        print(f"✔ Exportado para: {path}")

    def importar_csv(self) -> None:
        print("\n=== Importar dados a partir de CSV ===")
        caminho = input_nonempty("Informe o caminho do CSV (ex.: exports/livros_exportados.csv): ")

        try:
            csv_data = self.file_manager.get_csv_data(caminho)
            self.file_manager.backup_db()
            
            inseridos = 0
            for row in csv_data:
                try:
                    titulo = (row.get("titulo") or "").strip()
                    autor = (row.get("autor") or "").strip()
                    ano = int((row.get("ano_publicacao") or "0").strip())
                    preco = float((row.get("preco") or "0").replace(",", ".").strip())
                    if not titulo or not autor or ano <= 0 or preco < 0:
                        raise ValueError
                    self.db_manager.add_book(titulo, autor, ano, preco)
                    inseridos += 1
                except (ValueError, KeyError):
                    print(f"⚠ Ignorando linha com dados inválidos: {row}")
            
            print(f"✔ Importação concluída. Inseridos: {inseridos}")
            
        except FileNotFoundError as e:
            print(f"⚠ {e}")
        except Exception as e:
            print(f"⚠ Erro durante a importação: {e}")

    def fazer_backup_manual(self) -> None:
        path = self.file_manager.backup_db()
        print(f"✔ Backup criado: {path.name}")
        backups = sorted(self.file_manager.backup_dir.glob('backup_livraria_*.db'), key=lambda p: p.stat().st_mtime, reverse=True)[:5]
        print("Backups recentes:")
        for b in backups:
            print(" -", b.name)

    def _print_books(self, rows: list):
        print(f"{'ID':<4} {'TÍTULO':<30} {'AUTOR':<22} {'ANO':<6} {'PREÇO':>8}")
        print("-"*76)
        for _id, titulo, autor, ano, preco in rows:
            print(f"{_id:<4} {titulo[:30]:<30} {autor[:22]:<22} {ano:<6} R$ {preco:>7.2f}")

    def menu(self) -> None:
        while True:
            print("\n=== Sistema de Gerenciamento de Livraria ===")
            print("1. Adicionar novo livro")
            print("2. Exibir todos os livros")
            print("3. Atualizar preço de um livro")
            print("4. Remover um livro")
            print("5. Buscar livros por autor")
            print("6. Exportar dados para CSV")
            print("7. Importar dados de CSV")
            print("8. Fazer backup do banco de dados")
            print("9. Sair")
            opcao = input("Escolha uma opção: ").strip()
            
            actions = {
                "1": self.adicionar_livro,
                "2": self.exibir_livros,
                "3": self.atualizar_preco,
                "4": self.remover_livro,
                "5": self.buscar_por_autor,
                "6": self.exportar_csv,
                "7": self.importar_csv,
                "8": self.fazer_backup_manual
            }

            if opcao in actions:
                actions[opcao]()
            elif opcao == "9":
                print("Até mais!")
                break
            else:
                print("Opção inválida. Tente novamente.")

if __name__ == "__main__":
    cli = LivrariaCLI()
    cli.menu()