import unittest
from unittest.mock import patch, MagicMock
from io import StringIO
from pathlib import Path
import sys

from main import LivrariaCLI

class TestLivrariaCLI(unittest.TestCase):
    def setUp(self):
        self.mock_db_manager = MagicMock(name="DBManager")
        self.mock_file_manager = MagicMock(name="FileManager")
        self.mock_file_manager.db_path = Path("mocked_data/livraria.db")
        self.mock_file_manager.backup_dir = MagicMock()
        self.mock_file_manager.backup_dir.glob.return_value = []

        self.p_db = patch("main.DBManager", return_value=self.mock_db_manager)
        self.p_fm = patch("main.FileManager", return_value=self.mock_file_manager)
        self.p_db.start()
        self.p_fm.start()

        self.cli = LivrariaCLI()

    def tearDown(self):
        self.p_db.stop()
        self.p_fm.stop()

    def test_adicionar_livro_success(self):
        with patch("builtins.input", side_effect=["Titulo Teste", "Autor Teste", "2022", "49.90"]), \
             patch("builtins.print") as mock_print:
            self.cli.adicionar_livro()
            self.mock_file_manager.backup_db.assert_called_once()
            self.mock_db_manager.add_book.assert_called_once_with("Titulo Teste", "Autor Teste", 2022, 49.9)
            mock_print.assert_any_call("✔ Livro adicionado com sucesso!")

    def test_exibir_livros_empty(self):
        self.mock_db_manager.get_all_books.return_value = []
        with patch("builtins.print") as mock_print:
            self.cli.exibir_livros()
            mock_print.assert_any_call("(vazio)")

    def test_exibir_livros_with_data(self):
        self.mock_db_manager.get_all_books.return_value = [(1, "A", "B", 2000, 10.0)]
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            self.cli.exibir_livros()
            out = mock_stdout.getvalue()
            self.assertIn("=== Todos os livros ===", out)
            self.assertIn("ID", out)
            self.assertIn("TÍTULO", out)
            self.assertIn("AUTOR", out)
            self.assertIn("ANO", out)
            self.assertIn("PREÇO", out)
            self.assertRegex(out, r"1\s+A")

    def test_atualizar_preco_success(self):
        self.mock_db_manager.update_price.return_value = 1
        with patch("builtins.input", side_effect=["1", "50.00"]), \
             patch("builtins.print") as mock_print:
            self.cli.atualizar_preco()
            self.mock_file_manager.backup_db.assert_called_once()
            self.mock_db_manager.update_price.assert_called_once_with(1, 50.0)
            mock_print.assert_any_call("✔ Preço atualizado com sucesso!")

    def test_atualizar_preco_not_found(self):
        self.mock_db_manager.update_price.return_value = 0
        with patch("builtins.input", side_effect=["99", "50.00"]), \
             patch("builtins.print") as mock_print:
            self.cli.atualizar_preco()
            self.mock_file_manager.backup_db.assert_called_once()
            mock_print.assert_any_call("⚠ ID não encontrado.")

    def test_remover_livro_success(self):
        self.mock_db_manager.remove_book.return_value = 1
        with patch("builtins.input", side_effect=["1"]), \
             patch("builtins.print") as mock_print:
            self.cli.remover_livro()
            self.mock_file_manager.backup_db.assert_called_once()
            self.mock_db_manager.remove_book.assert_called_once_with(1)
            mock_print.assert_any_call("✔ Livro removido com sucesso!")

    def test_remover_livro_not_found(self):
        self.mock_db_manager.remove_book.return_value = 0
        with patch("builtins.input", side_effect=["99"]), \
             patch("builtins.print") as mock_print:
            self.cli.remover_livro()
            self.mock_file_manager.backup_db.assert_called_once()
            mock_print.assert_any_call("⚠ ID não encontrado.")

    def test_buscar_por_autor_success(self):
        self.mock_db_manager.find_books_by_author.return_value = [(1, "A", "B", 2000, 10.0)]
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout, \
             patch("builtins.input", return_value="Autor"):
            self.cli.buscar_por_autor()
            self.mock_db_manager.find_books_by_author.assert_called_once()
            arg = self.mock_db_manager.find_books_by_author.call_args[0][0]
            self.assertIn("Autor", arg)
            out = mock_stdout.getvalue()
            self.assertIn("=== Buscar livros por autor ===", out)
            self.assertRegex(out, r"1\s+A")

    def test_exportar_csv(self):
        self.mock_db_manager.get_all_books.return_value = [(1, "A", "B", 2000, 10.0)]
        self.mock_file_manager.export_to_csv.return_value = "exports/test.csv"
        with patch("builtins.print") as mock_print:
            self.cli.exportar_csv()
            self.mock_file_manager.export_to_csv.assert_called_once_with(self.mock_db_manager.get_all_books.return_value)
            mock_print.assert_any_call("✔ Exportado para: exports/test.csv")

    def test_importar_csv_success(self):
        mock_csv_data = [{"titulo": "CSV Book", "autor": "CSV Author", "ano_publicacao": "2023", "preco": "99.99"}]
        self.mock_file_manager.get_csv_data.return_value = mock_csv_data
        with patch("builtins.input", return_value="exports/test.csv"), \
             patch("builtins.print") as mock_print:
            self.cli.importar_csv()
            self.mock_file_manager.backup_db.assert_called_once()
            self.mock_db_manager.add_book.assert_called_once_with("CSV Book", "CSV Author", 2023, 99.99)
            mock_print.assert_any_call("✔ Importação concluída. Inseridos: 1")

    def test_importar_csv_file_not_found(self):
        self.mock_file_manager.get_csv_data.side_effect = FileNotFoundError("Arquivo não encontrado.")
        with patch("builtins.input", return_value="non_existent.csv"), \
             patch("builtins.print") as mock_print:
            self.cli.importar_csv()
            mock_print.assert_any_call("⚠ Arquivo não encontrado.")

    def test_fazer_backup_manual(self):
        mock_path_one = MagicMock()
        mock_path_one.name = "backup_test_1.db"
        mock_path_two = MagicMock()
        mock_path_two.name = "backup_test_2.db"
        mock_path_two.stat.return_value = MagicMock(st_mtime=2)
        mock_path_one.stat.return_value = MagicMock(st_mtime=1)

        self.mock_file_manager.backup_db.return_value = mock_path_one
        self.mock_file_manager.backup_dir.glob.return_value = [mock_path_two, mock_path_one]

        with patch("builtins.print") as mock_print:
            self.cli.fazer_backup_manual()
            self.mock_file_manager.backup_db.assert_called_once()
            mock_print.assert_any_call("✔ Backup criado: backup_test_1.db")
            mock_print.assert_any_call("Backups recentes:")

    def test_menu_options_flow(self):
        self.cli.gerar_relatorio_html = MagicMock()
        self.cli.gerar_relatorio_pdf = MagicMock()
        self.cli.adicionar_livro = MagicMock()

        with patch("builtins.input", side_effect=["1", "11"]):
            self.cli.menu()
            self.cli.adicionar_livro.assert_called_once()

        with patch("builtins.input", side_effect=["99", "11"]), \
             patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            self.cli.menu()
            out = mock_stdout.getvalue()
            self.assertIn("Opção inválida. Tente novamente.", out)

        self.cli.gerar_relatorio_html.reset_mock()
        self.cli.gerar_relatorio_pdf.reset_mock()
        with patch("builtins.input", side_effect=["9", "10", "11"]):
            self.cli.menu()
            self.cli.gerar_relatorio_html.assert_called_once()
            self.cli.gerar_relatorio_pdf.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
