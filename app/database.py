# app/database.py
import sqlite3
import hashlib
import logging
from . import config

def initialize_database():
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
            unidade REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
        cursor.execute(create_table_query)
        conn.commit(); conn.close()
        logging.info("Banco de dados inicializado e tabela 'apostas_processadas' garantida.")
    except Exception as e:
        logging.error(f"Erro CRÍTICO ao inicializar o banco de dados: {e}")

def create_fingerprint(bet_data):
    jogos = bet_data.get('jogos', '');
    if not isinstance(jogos, str): jogos = str(jogos)
    descricao = bet_data.get('descricao_da_aposta') or bet_data.get('descricao_da_posta', '')
    entrada = bet_data.get('entrada', '')
    casa = str(bet_data.get('casa_de_apostas', '')).lower()
    data_string = f"{jogos}_{descricao}_{entrada}_{casa}".lower()
    return hashlib.md5(data_string.encode()).hexdigest()

def log_bet_to_db(fingerprint, tipster, row, unidade):
    try:
        conn = sqlite3.connect(config.DB_FILE); cursor = conn.cursor()
        cursor.execute("INSERT INTO apostas_processadas (fingerprint, tipster, spreadsheet_row, unidade) VALUES (?, ?, ?, ?)",(fingerprint, tipster, row, unidade))
        conn.commit(); conn.close()
        logging.info(f"Aposta com fingerprint {fingerprint[:6]}... salva no banco de dados.")
    except Exception as e: logging.error(f"Erro ao salvar aposta no banco de dados: {e}")

def check_db_for_bet(fingerprint):
    conn = sqlite3.connect(config.DB_FILE); cursor = conn.cursor()
    cursor.execute("SELECT tipster, spreadsheet_row, unidade FROM apostas_processadas WHERE fingerprint = ?", (fingerprint,))
    result = cursor.fetchone(); conn.close()
    return {'tipster': result[0], 'row': result[1], 'unidade': result[2]} if result else None

def update_stake_in_db(fingerprint, new_unidade):
    try:
        conn = sqlite3.connect(config.DB_FILE); cursor = conn.cursor()
        cursor.execute("UPDATE apostas_processadas SET unidade = ? WHERE fingerprint = ?", (new_unidade, fingerprint))
        conn.commit(); conn.close()
        logging.info(f"Unidade da aposta {fingerprint[:6]}... atualizada no DB para {new_unidade}.")
    except Exception as e: logging.error(f"Erro ao atualizar unidade no DB: {e}")