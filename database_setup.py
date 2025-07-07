# database_setup.py

import sqlite3
import os

DB_FILE = "bets_memory.db"

# Apaga o banco de dados antigo se ele existir, para começar do zero
if os.path.exists(DB_FILE):
    os.remove(DB_FILE)
    print(f"Banco de dados antigo ('{DB_FILE}') removido.")

# Conecta ao banco de dados (isso criará o arquivo)
conn = sqlite3.connect(DB_FILE)
print(f"Arquivo de banco de dados '{DB_FILE}' criado com sucesso.")

# Cria um "cursor" para executar comandos
cursor = conn.cursor()

# Comando SQL para criar nossa tabela de memória
create_table_query = """
CREATE TABLE IF NOT EXISTS apostas_processadas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fingerprint TEXT NOT NULL UNIQUE,
    tipster TEXT NOT NULL,
    spreadsheet_row INTEGER NOT NULL,
    unidade REAL NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

# Executa o comando
cursor.execute(create_table_query)
print("Tabela 'apostas_processadas' criada com sucesso.")

# Salva as alterações e fecha a conexão
conn.commit()
conn.close()

print("Configuração do banco de dados concluída.")