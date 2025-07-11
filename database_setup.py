import sqlite3
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - SETUP - %(levelname)s - %(message)s')
DB_FILE = "bets_memory.db"

if os.path.exists(DB_FILE):
    os.remove(DB_FILE)
    logging.info(f"Banco de dados antigo ('{DB_FILE}') removido.")

try:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS apostas_processadas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fingerprint TEXT NOT NULL UNIQUE,
        tipster TEXT NOT NULL,
        spreadsheet_row INTEGER NOT NULL,
        unidade REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    conn.close()
    logging.info("Banco de dados e tabela 'apostas_processadas' criados com sucesso.")
except Exception as e:
    logging.error(f"Erro ao criar banco de dados: {e}")