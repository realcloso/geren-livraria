import unittest
from unittest import mock
from unittest.mock import Mock, patch, MagicMock
from io import StringIO
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent))

from main import LivrariaCLI
from lib.validators import ValidationError


class TestLivrariaCLI(unittest.TestCase):
    def setUp(self):
        self.mock_db_manager = MagicMock(name="DBManager")
        self.mock_file_manager = MagicMock(name="FileManager")
        self.mock_file_manager.db_path = Path("mocked_data/livraria.db")

        self.mock_file_manager.exports_dir = MagicMock(spec=Path)
        self.mock_file_manager.exports_dir.__truediv__.side_effect = lambda x: Path(f"mocked_exports_dir/{x}")
        
        mock_backup_path = MagicMock(spec=Path)
        mock_backup_path.name = "backup_test.db"
        mock_stat = MagicMock()
        mock_stat.st_mtime = 123456789.0
        mock_backup_path.stat.return_value = mock_stat
        self.mock_file_manager.backup_dir.glob.return_value = [mock_backup_path]


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
             patch("builtins.print") as mock_print, \
             patch("main.validate_text", side_effect=["Titulo Teste", "Autor Teste"]), \
             patch("main.validate_year", return_value=2022), \
             patch("main.validate_price", return_value=49.90):

            self.mock_db_manager.add_book.return_value = 1
            self.cli.adicionar_livro()
            mock_print.assert_any_call("✔ Livro adicionado com sucesso!")

    def test_adicionar_livro_validation_error(self):
        with patch("main.input_nonempty", side_effect=ValidationError("Título não pode ser vazio.")), \
             patch("builtins.print") as mock_print:
            self.cli.adicionar_livro()
            mock_print.assert_any_call("⚠ Dados inválidos: Título não pode ser vazio.")

    def test_exibir_livros_empty(self):
        self.mock_db_manager.get_all_books.return_value = []
        with patch("builtins.print") as mock_print:
            self.cli.exibir_livros()
            mock_print.assert_any_call("(vazio)")

    def test_exibir_livros_with_data(self):
        mock_books = [(1, "O Pequeno Príncipe", "Antoine de Saint-Exupéry", 1943, 29.90)]
        self.mock_db_manager.get_all_books.return_value = mock_books

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            self.cli.exibir_livros()
            output = mock_stdout.getvalue()
            for value in ["1", "O Pequeno Príncipe", "Antoine de Saint-Exupéry", "1943", "29.90"]:
                self.assertIn(value, output)

    def test_atualizar_preco_success(self):
        with patch("builtins.input", side_effect=["1", "55.50"]), \
             patch("builtins.print") as mock_print, \
             patch("main.validate_price", return_value=55.5):
            self.mock_db_manager.update_price.return_value = 1
            self.cli.atualizar_preco()
            mock_print.assert_any_call("✔ Preço atualizado com sucesso!")

    def test_remover_livro_success(self):
        with patch("builtins.input", side_effect=["1"]), \
             patch("builtins.print") as mock_print:
            self.mock_db_manager.remove_book.return_value = 1
            self.cli.remover_livro()
            mock_print.assert_any_call("✔ Livro removido com sucesso!")

    def test_buscar_por_autor(self):
        self.mock_db_manager.find_books_by_author.return_value = []
        with patch("builtins.input", return_value="Autor Teste"), \
             patch("builtins.print") as mock_print:
            self.cli.buscar_por_autor()
            mock_print.assert_any_call("Nenhum livro encontrado para esse autor.")

    def test_exportar_csv(self):
        self.mock_db_manager.get_all_books.return_value = []
        mock_path = Path("exports/test.csv")
        self.mock_file_manager.export_to_csv.return_value = mock_path
        with patch("builtins.print") as mock_print:
            self.cli.exportar_csv()
            mock_print.assert_any_call(f"✔ Exportado para: {mock_path}")

    def test_importar_csv_success(self):
        csv_data = [{"titulo": "CSV Book", "autor": "CSV Author", "ano_publicacao": "2023", "preco": "99.99"}]
        with patch("builtins.input", side_effect=["path/to/mocked.csv"]), \
             patch("builtins.print") as mock_print:
            self.mock_file_manager.get_csv_data.return_value = csv_data
            self.mock_db_manager.add_book.return_value = 1
            self.cli.importar_csv()
            mock_print.assert_any_call("✔ Importação concluída. Inseridos: 1 | Ignorados: 0")

    def test_importar_csv_file_not_found(self):
        self.mock_file_manager.get_csv_data.side_effect = FileNotFoundError("Arquivo não encontrado.")
        with patch("builtins.input", side_effect=["non_existent.csv"]), \
             patch("builtins.print") as mock_print:
            self.cli.importar_csv()
            mock_print.assert_any_call("⚠ Arquivo não encontrado.")

    def test_fazer_backup_manual(self):
        mock_path = MagicMock()
        mock_path.name = "backup_test.db"
        self.mock_file_manager.backup_db.return_value = mock_path
        
        with patch("builtins.print") as mock_print:
            self.cli.fazer_backup_manual()
            mock_print.assert_any_call("✔ Backup criado: backup_test.db")
            mock_print.assert_any_call(" -", "backup_test.db")

    def test_gerar_relatorio_html(self):
        with patch('main.generate_html_report', return_value=Path("mocked_exports/relatorio.html")) as mock_gerador_html, \
            patch('builtins.print') as mock_print:
            self.cli.gerar_relatorio_html()
            mock_gerador_html.assert_called_once()
            mock_print.assert_any_call(mock.ANY)

    def test_gerar_relatorio_pdf(self):
        with patch('main.generate_pdf_report', return_value=Path("mocked_exports/relatorio.pdf")) as mock_gerador_pdf, \
            patch('builtins.print') as mock_print:
            self.cli.gerar_relatorio_pdf()
            mock_gerador_pdf.assert_called_once()
            mock_print.assert_any_call(mock.ANY)

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
            output = mock_stdout.getvalue()
            self.assertIn("Opção inválida. Tente novamente.", output)