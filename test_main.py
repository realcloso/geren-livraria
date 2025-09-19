# file: test_main.py
import unittest
from unittest.mock import patch, MagicMock, call
from io import StringIO
import sys
from pathlib import Path

sys.path.append('lib')
from main import LivrariaCLI
from db import DBManager
from file_manager import FileManager
from utils import input_int, input_float, input_nonempty

class TestLivrariaCLI(unittest.TestCase):
    def setUp(self):
        self.mock_db_manager = MagicMock(spec=DBManager)
        self.mock_file_manager = MagicMock(spec=FileManager)
        
        self.mock_file_manager.db_path = Path('mocked_data/livraria.db')
        
        with patch('main.DBManager', return_value=self.mock_db_manager), \
             patch('main.FileManager', return_value=self.mock_file_manager):
            self.cli = LivrariaCLI()

    def test_adicionar_livro_success(self):
        with patch('builtins.input', side_effect=['Titulo Teste', 'Autor Teste', '2022', '49.90']), \
             patch('builtins.print') as mock_print:
            self.cli.adicionar_livro()
            self.mock_file_manager.backup_db.assert_called_once()
            self.mock_db_manager.add_book.assert_called_once_with('Titulo Teste', 'Autor Teste', 2022, 49.9)
            mock_print.assert_any_call("✔ Livro adicionado com sucesso!")

    def test_exibir_livros_empty(self):
        self.mock_db_manager.get_all_books.return_value = []
        with patch('builtins.print') as mock_print:
            self.cli.exibir_livros()
            mock_print.assert_any_call("(vazio)")

    def test_exibir_livros_with_data(self):
        self.mock_db_manager.get_all_books.return_value = [(1, 'A', 'B', 2000, 10.0)]
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            self.cli.exibir_livros()
            output = mock_stdout.getvalue()
            self.assertIn("=== Todos os livros ===", output)
            self.assertIn("ID", output)
            self.assertIn("TÍTULO", output)
            self.assertIn("AUTOR", output)
            self.assertIn("ANO", output)
            self.assertIn("PREÇO", output)
            self.assertRegex(output, r"1\s+A")

    def test_atualizar_preco_success(self):
        self.mock_db_manager.update_price.return_value = 1
        with patch('builtins.input', side_effect=['1', '50.00']), \
             patch('builtins.print') as mock_print:
            self.cli.atualizar_preco()
            self.mock_file_manager.backup_db.assert_called_once()
            self.mock_db_manager.update_price.assert_called_once_with(1, 50.0)
            mock_print.assert_any_call("✔ Preço atualizado com sucesso!")

    def test_atualizar_preco_not_found(self):
        self.mock_db_manager.update_price.return_value = 0
        with patch('builtins.input', side_effect=['99', '50.00']), \
             patch('builtins.print') as mock_print:
            self.cli.atualizar_preco()
            self.mock_file_manager.backup_db.assert_called_once()
            mock_print.assert_any_call("⚠ ID não encontrado.")

    def test_remover_livro_success(self):
        self.mock_db_manager.remove_book.return_value = 1
        with patch('builtins.input', side_effect=['1']), \
             patch('builtins.print') as mock_print:
            self.cli.remover_livro()
            self.mock_file_manager.backup_db.assert_called_once()
            self.mock_db_manager.remove_book.assert_called_once_with(1)
            mock_print.assert_any_call("✔ Livro removido com sucesso!")

    def test_remover_livro_not_found(self):
        self.mock_db_manager.remove_book.return_value = 0
        with patch('builtins.input', side_effect=['99']), \
             patch('builtins.print') as mock_print:
            self.cli.remover_livro()
            self.mock_file_manager.backup_db.assert_called_once()
            mock_print.assert_any_call("⚠ ID não encontrado.")

    def test_buscar_por_autor_success(self):
        self.mock_db_manager.find_books_by_author.return_value = [(1, 'A', 'B', 2000, 10.0)]
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout, \
             patch('builtins.input', return_value='Autor'):
            self.cli.buscar_por_autor()
            output = mock_stdout.getvalue()
            self.mock_db_manager.find_books_by_author.assert_called_once_with('%Autor%')
            self.assertIn("=== Buscar livros por autor ===", output)
            self.assertIn("ID", output)
            self.assertIn("TÍTULO", output)
            self.assertIn("AUTOR", output)
            self.assertIn("ANO", output)
            self.assertIn("PREÇO", output)
            self.assertRegex(output, r"1\s+A")

    def test_exportar_csv(self):
        self.mock_db_manager.get_all_books.return_value = [(1, 'A', 'B', 2000, 10.0)]
        self.mock_file_manager.export_to_csv.return_value = 'exports/test.csv'
        with patch('builtins.print') as mock_print:
            self.cli.exportar_csv()
            self.mock_file_manager.export_to_csv.assert_called_once_with(self.mock_db_manager.get_all_books.return_value)
            mock_print.assert_any_call("✔ Exportado para: exports/test.csv")

    def test_importar_csv_success(self):
        mock_csv_data = [{'titulo': 'CSV Book', 'autor': 'CSV Author', 'ano_publicacao': '2023', 'preco': '99.99'}]
        self.mock_file_manager.get_csv_data.return_value = mock_csv_data
        with patch('builtins.input', return_value='exports/test.csv'), \
             patch('builtins.print') as mock_print:
            self.cli.importar_csv()
            self.mock_file_manager.backup_db.assert_called_once()
            self.mock_db_manager.add_book.assert_called_once_with('CSV Book', 'CSV Author', 2023, 99.99)
            mock_print.assert_any_call("✔ Importação concluída. Inseridos: 1")

    def test_importar_csv_file_not_found(self):
        self.mock_file_manager.get_csv_data.side_effect = FileNotFoundError('Arquivo não encontrado.')
        with patch('builtins.input', return_value='non_existent.csv'), \
             patch('builtins.print') as mock_print:
            self.cli.importar_csv()
            mock_print.assert_any_call("⚠ Arquivo não encontrado.")

    def test_fazer_backup_manual(self):
        mock_path_one = MagicMock()
        mock_path_one.name = "backup_test_1.db"
        mock_path_one.stat.return_value = MagicMock(st_mtime=1672531200)

        mock_path_two = MagicMock()
        mock_path_two.name = "backup_test_2.db"
        mock_path_two.stat.return_value = MagicMock(st_mtime=1672617600)

        self.mock_file_manager.backup_db.return_value = mock_path_one
        self.mock_file_manager.backup_dir = MagicMock()
        self.mock_file_manager.backup_dir.glob.return_value = [
            mock_path_two,
            mock_path_one
        ]
        
        with patch('builtins.print') as mock_print:
            self.cli.fazer_backup_manual()
            self.mock_file_manager.backup_db.assert_called_once()
            mock_print.assert_any_call("✔ Backup criado: backup_test_1.db")
            mock_print.assert_any_call('Backups recentes:')

    @patch('sys.stdout', new_callable=StringIO)
    def test_menu_options(self, mock_stdout):
        with patch('builtins.input', side_effect=['1', '9']):
            self.cli.adicionar_livro = MagicMock()
            self.cli.menu()
            self.cli.adicionar_livro.assert_called_once()
        
        with patch('builtins.input', side_effect=['10', '9']):
            self.cli.adicionar_livro.reset_mock()
            self.cli.menu()
            self.cli.adicionar_livro.assert_not_called()
            output = mock_stdout.getvalue()
            self.assertIn("Opção inválida. Tente novamente.", output)
        
        with patch('builtins.input', side_effect=['9']):
            self.cli.menu()
            output = mock_stdout.getvalue()
            self.assertIn("Até mais!", output)
