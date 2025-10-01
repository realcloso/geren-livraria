from __future__ import annotations
from pathlib import Path
from lib.db import DBManager
from lib.file_manager import FileManager
from lib.validators import validate_text, validate_year, validate_price, ValidationError
from lib.utils import input_int, input_nonempty
from lib.reporting import generate_html_report, generate_pdf_report


class LivrariaCLI:
    """
    Interface de linha de comando (CLI) para o sistema de gerenciamento da livraria.
    Esta classe atua como o ponto central da aplicação, orquestrando as operações
    de gerenciamento de livros, backup e relatórios, utilizando as classes
    `DBManager` e `FileManager`.
    """
    def __init__(self):
        # Define o diretório base para a aplicação e inicializa as classes de gerenciamento.
        BASE_DIR = Path(__file__).resolve().parent
        self.file_manager = FileManager(BASE_DIR)
        self.db_manager = DBManager(str(self.file_manager.db_path))

    def adicionar_livro(self) -> None:
        """
        Coleta dados do usuário para um novo livro (título, autor, ano, preço).
        Valida cada entrada usando as funções do módulo `validators`.
        Em seguida, faz um backup do banco de dados e adiciona o livro.
        Trata possíveis erros de validação ou de banco de dados.
        """
        print("\n=== Adicionar novo livro ===")
        try:
            # Solicita e valida cada campo do livro
            titulo_raw = input_nonempty("Título: ")
            autor_raw = input_nonempty("Autor: ")
            ano_raw = input_nonempty("Ano de publicação: ")
            preco_raw = input_nonempty("Preço (ex.: 39.90): ")

            titulo = validate_text("Título", titulo_raw)
            autor = validate_text("Autor", autor_raw)
            ano = validate_year("Ano de publicação", ano_raw)
            preco = validate_price("Preço", str(preco_raw).replace(",", ".").strip())

            # Realiza o backup e a inserção no banco de dados
            self.file_manager.backup_db()
            inserted = self.db_manager.add_book(titulo, autor, ano, preco)
            if inserted:
                print("✔ Livro adicionado com sucesso!")
            else:
                print("⚠ Livro possivelmente duplicado (mesmo título, autor e ano). Não inserido.")
        except ValidationError as e:
            print(f"⚠ Dados inválidos: {e}")
            return
        except Exception as e:
            print(f"⚠ Erro ao adicionar: {e}")

    def exibir_livros(self) -> None:
        """
        Busca e exibe todos os livros armazenados no banco de dados.
        Formata a saída de forma tabular para uma leitura mais fácil.
        """
        print("\n=== Todos os livros ===")
        rows = self.db_manager.get_all_books()
        if not rows:
            print("(vazio)")
            return
        # Imprime o cabeçalho da tabela
        print('ID   TÍTULO                         AUTOR                  ANO    PREÇO')
        # Itera sobre os resultados e imprime cada linha formatada
        for _id, titulo, autor, ano, preco in rows:
            print(f"{_id:<4} {titulo:<30} {autor:<22} {ano:<6} R$   {preco:>.2f}")

    def atualizar_preco(self) -> None:
        """
        Permite ao usuário atualizar o preço de um livro existente,
        identificado pelo seu ID. Valida a entrada do novo preço antes de
        fazer o backup e a atualização no banco de dados.
        """
        print("\n=== Atualizar preço de um livro ===")
        try:
            livro_id = input_int("ID do livro: ")
            novo_preco_raw = input_nonempty("Novo preço: ")
            # Valida o novo preço e atualiza o registro
            novo_preco = validate_price("Preço", str(novo_preco_raw).replace(",", ".").strip())
            self.file_manager.backup_db()
            updated_count = self.db_manager.update_price(livro_id, novo_preco)
            if updated_count == 0:
                print("⚠ ID não encontrado.")
            else:
                print("✔ Preço atualizado com sucesso!")
        except ValidationError as e:
            print(f"⚠ Valor inválido: {e}")
        except Exception as e:
            print(f"⚠ Erro ao atualizar: {e}")

    def remover_livro(self) -> None:
        """
        Remove um livro do banco de dados a partir de seu ID.
        Faz um backup antes de executar a remoção.
        """
        print("\n=== Remover um livro ===")
        livro_id = input_int("ID do livro: ")
        self.file_manager.backup_db()
        removed_count = self.db_manager.remove_book(livro_id)
        if removed_count == 0:
            print("⚠ ID não encontrado.")
        else:
            print("✔ Livro removido com sucesso!")

    def buscar_por_autor(self) -> None:
        """
        Busca livros no banco de dados com base em um termo de busca para o autor.
        Exibe os resultados em formato de tabela, similar à função `exibir_livros`.
        """
        print("\n=== Buscar livros por autor ===")
        termo = input_nonempty("Autor (termo de busca): ")
        rows = self.db_manager.find_books_by_author(termo)
        if not rows:
            print("Nenhum livro encontrado para esse autor.")
            return
        # Imprime o cabeçalho e os resultados formatados
        print('ID   TÍTULO                         AUTOR                  ANO    PREÇO')
        for _id, titulo, autor, ano, preco in rows:
            print(f"{_id:<4} {titulo:<30} {autor:<22} {ano:<6} R$   {preco:>.2f}")

    def exportar_csv(self) -> None:
        """
        Exporta todos os livros do banco de dados para um arquivo CSV.
        Utiliza o `FileManager` para gerenciar a criação do arquivo de exportação.
        """
        print("\n=== Exportar dados para CSV ===")
        books = self.db_manager.get_all_books()
        path = self.file_manager.export_to_csv(books)
        print(f"✔ Exportado para: {path}")

    def importar_csv(self) -> None:
        """
        Importa dados de um arquivo CSV para o banco de dados.
        Lê o arquivo usando `FileManager.get_csv_data` e itera sobre os registros.
        Para cada registro, extrai os dados, os valida e os adiciona ao banco.
        Conta os registros inseridos e ignorados e exibe um resumo ao final.
        """
        print("\n=== Importar dados a partir de CSV ===")
        caminho = input_nonempty("Informe o caminho do CSV (ex.: exports/livros_exportados.csv): ")

        inseridos = 0
        ignorados = 0
        erros = []

        try:
            # Tenta ler o CSV e fazer o backup antes da importação
            csv_data = self.file_manager.get_csv_data(caminho)
            self.file_manager.backup_db()

            # Itera sobre cada linha do CSV, valida e insere no banco
            for i, row in enumerate(csv_data, start=1):
                try:
                    # Tenta validar os dados e adicionar o livro
                    titulo = validate_text("Título", row.get("titulo") or row.get("title", ""))
                    autor = validate_text("Autor", row.get("autor") or row.get("author", ""))
                    ano = validate_year("Ano de publicação", row.get("ano_publicacao") or row.get("ano") or row.get("year", ""))
                    preco = validate_price("Preço", row.get("preco") or row.get("price", ""))
                    self.db_manager.add_book(titulo, autor, ano, preco)
                    inseridos += 1
                except (ValidationError, KeyError) as e:
                    # Captura erros de validação ou chaves ausentes
                    ignorados += 1
                    erros.append(f"Linha {i}: {e}")

            # Exibe o resumo da importação
            print(f"✔ Importação concluída. Inseridos: {inseridos} | Ignorados: {ignorados}")
            if erros:
                print("— Erros encontrados:")
                for msg in erros[:10]:
                    print("  •", msg)
                if len(erros) > 10:
                    print(f"  • (+{len(erros)-10} outros)")

        except FileNotFoundError:
            print("⚠ Arquivo não encontrado.")
        except Exception as e:
            print(f"⚠ Erro durante a importação: {e}")

    def fazer_backup_manual(self) -> None:
        """
        Gera um backup manual do banco de dados e exibe o caminho
        do arquivo de backup, junto com uma lista dos backups mais recentes.
        """
        path = self.file_manager.backup_db()
        print(f"✔ Backup criado: {path.name}")
        backups = sorted(self.file_manager.backup_dir.glob('backup_livraria_*.db'),
                         key=lambda p: p.stat().st_mtime, reverse=True)[:5]
        print("Backups recentes:")
        for b in backups:
            print(" -", b.name)

    def gerar_relatorio_html(self) -> None:
        """
        Busca todos os livros e gera um relatório em formato HTML.
        Utiliza a função `generate_html_report` do módulo de relatórios.
        """
        books = self.db_manager.get_all_books()
        out = self.file_manager.exports_dir / "relatorio_livros.html"
        try:
            path = generate_html_report(books, out)
            print(f"✔ Relatório HTML gerado em: {path}")
        except Exception as e:
            print(f"⚠ Erro ao gerar HTML: {e}")

    def gerar_relatorio_pdf(self) -> None:
        """
        Busca todos os livros e gera um relatório em formato PDF.
        Utiliza a função `generate_pdf_report` do módulo de relatórios.
        Trata o erro de dependência caso a biblioteca `xhtml2pdf` não esteja instalada.
        """
        books = self.db_manager.get_all_books()
        out = self.file_manager.exports_dir / "relatorio_livros.pdf"
        try:
            path = generate_pdf_report(books, out)
            print(f"✔ Relatório PDF gerado em: {path}")
        except ImportError as e:
            print(f"⚠ Não foi possível gerar PDF: {e}\nDica: instale com `pip install xhtml2pdf`.")
        except Exception as e:
            print(f"⚠ Erro ao gerar PDF: {e}")

    def menu(self) -> None:
        """
        Exibe o menu principal da aplicação e gerencia as escolhas do usuário
        em um loop contínuo. Chama o método correspondente à opção selecionada.
        """
        while True:
            # Exibe as opções do menu
            print("\n=== Sistema de Gerenciamento de Livraria ===")
            print("1. Adicionar novo livro")
            print("2. Exibir todos os livros")
            print("3. Atualizar preço de um livro")
            print("4. Remover um livro")
            print("5. Buscar livros por autor")
            print("6. Exportar dados para CSV")
            print("7. Importar dados de CSV")
            print("8. Fazer backup do banco de dados")
            print("9. Gerar relatório HTML")
            print("10. Gerar relatório PDF")
            print("11. Sair")
            opcao = input("Escolha uma opção: ").strip()

            # Mapeia as opções para os métodos correspondentes
            actions = {
                "1": self.adicionar_livro,
                "2": self.exibir_livros,
                "3": self.atualizar_preco,
                "4": self.remover_livro,
                "5": self.buscar_por_autor,
                "6": self.exportar_csv,
                "7": self.importar_csv,
                "8": self.fazer_backup_manual,
                "9": self.gerar_relatorio_html,
                "10": self.gerar_relatorio_pdf,
            }

            if opcao in actions:
                actions[opcao]() # Chama o método
            elif opcao == "11":
                print("Até mais!")
                break
            else:
                print("Opção inválida. Tente novamente.")

# Só rodará como script, se o arquivo for importado como módulo em outro script,
# o código não será executado
if __name__ == "__main__":
    cli = LivrariaCLI()
    cli.menu()