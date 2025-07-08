# app/database.py

import sqlite3
import hashlib
import logging
from . import config

def initialize_database():
    """Cria a tabela do banco de dados se ela não existir."""
    # Garante que o arquivo de log já esteja configurado
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO)

    try:
        conn = sqlite3.connect(config.DB_FILE)
        cursor = conn.cursor()
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
        cursor.execute(create_table_query)
        conn.commit()
        conn.close()
        logging.info("Banco de dados inicializado e tabela 'apostas_processadas' garantida.")
    except Exception as e:
        logging.error(f"Erro CRÍTICO ao inicializar o banco de dados: {e}")

def create_fingerprint(bet_data):
    """Cria um identificador único para uma aposta."""
    jogos = bet_data.get('jogos', '');
    if not isinstance(jogos, str): jogos = str(jogos)
    descricao = bet_data.get('descricao_da_aposta') or bet_data.get('descricao_da_posta', '')
    entrada = bet_data.get('entrada', '')
    data_string = f"{jogos}_{descricao}_{entrada}".lower()
    return hashlib.md5(data_string.encode()).hexdigest()

def log_bet_to_db(fingerprint, tipster, row, unidade):
    """Salva uma aposta processada no banco de dados."""
    try:
        conn = sqlite3.connect(config.DB_FILE); cursor = conn.cursor()
        cursor.execute("INSERT INTO apostas_processadas (fingerprint, tipster, spreadsheet_row, unidade) VALUES (?, ?, ?, ?)",(fingerprint, tipster, row, unidade))
        conn.commit(); conn.close()
        logging.info(f"Aposta com fingerprint {fingerprint[:6]}... salva no banco de dados.")
    except Exception as e: logging.error(f"Erro ao salvar aposta no banco de dados: {e}")

def check_db_for_bet(fingerprint):
    """Verifica se uma aposta já existe no DB e retorna seus dados."""
    conn = sqlite3.connect(config.DB_FILE); cursor = conn.cursor()
    cursor.execute("SELECT tipster, spreadsheet_row, unidade FROM apostas_processadas WHERE fingerprint = ?", (fingerprint,))
    result = cursor.fetchone(); conn.close()
    return {'tipster': result[0], 'row': result[1], 'unidade': result[2]} if result else None