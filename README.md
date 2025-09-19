# Sistema de Gerenciamento de Livraria (CLI)

Este projeto implementa um sistema completo de gerenciamento de uma livraria utilizando **SQLite**, **CSV** e **manipulação de arquivos** (backups) — tudo com **biblioteca padrão do Python**.

## Recursos
- Banco de dados **SQLite** (`data/livraria.db`) com tabela `livros(id, titulo, autor, ano_publicacao, preco)`.
- **CRUD** completo: adicionar, listar, atualizar preço, remover, buscar por autor.
- **Exportar** dados para CSV (`exports/livros_exportados.csv`).
- **Importar** de CSV para o banco (ignora linhas inválidas).
- **Backup automático** antes de **inserir**, **atualizar** ou **remover** (cópia do `livraria.db` em `backups/backup_livraria_*.db`).
- **Limpeza de backups**: mantém apenas os **5** mais recentes.
- Validações básicas de entrada (ano e preço).
- Menu de execução via terminal.

## Como executar
1. Requisitos: **Python 3.10+** (apenas bibliotecas padrão).
2. No terminal, navegue até a pasta do projeto e rode:
   ```bash
   python3 main.py
   ```
3. Para testes automatizados.
  ```bash
  python3 -m unittest test_main.py
  ```
4. Use o menu para operar o sistema.

## CSV de exemplo (para importação)
Crie um arquivo CSV com cabeçalho:
```
titulo,autor,ano_publicacao,preco
Dom Casmurro,Machado de Assis,1899,39.90
O Alquimista,Paulo Coelho,1988,29.90
```
Depois escolha **"7. Importar dados de CSV"** e informe o caminho (ex.: `exports/livros_exportados.csv`).

## Observações
- Os diretórios necessários são criados automaticamente na primeira execução.
- Backups são feitos **automaticamente** antes de operações de escrita e também podem ser acionados manualmente (opção 8).
- O sistema mantém apenas os **5** últimos arquivos em `backups/`.
