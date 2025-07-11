# app/database.py
import sqlite3
import hashlib
import logging
from . import config

def initialize_database():
    try:
        conn = sqlite3.connect(config.DB_FILE); cursor = conn.cursor()
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
        conn.commit(); conn.close()
        logging.info("Banco de dados inicializado e tabela garantida.")
    except Exception as e:
        logging.error(f"Erro ao inicializar o banco de dados: {e}")

def create_fingerprint(bet_data):
    jogos = str(bet_data.get('jogos', ''))
    descricao = str(bet_data.get('descricao_da_aposta', ''))
    entrada = str(bet_data.get('entrada', ''))
    casa = str(bet_data.get('casa_de_apostas', '')).lower()
    data_string = f"{jogos}_{descricao}_{entrada}_{casa}".lower()
    return hashlib.md5(data_string.encode()).hexdigest()

def log_bet_to_db(fingerprint, tipster, row, unidade):
    try:
        conn = sqlite3.connect(config.DB_FILE); cursor = conn.cursor()
        cursor.execute("INSERT INTO apostas_processadas (fingerprint, tipster, spreadsheet_row, unidade) VALUES (?, ?, ?, ?)", (fingerprint, tipster, row, unidade))
        conn.commit(); conn.close()
        logging.info(f"Aposta (FP: {fingerprint[:6]}...) salva no banco de dados.")
    except Exception as e: logging.error(f"Erro ao salvar aposta no DB: {e}")

def check_db_for_bet(fingerprint):
    try:
        conn = sqlite3.connect(config.DB_FILE); cursor = conn.cursor()
        cursor.execute("SELECT tipster, spreadsheet_row, unidade FROM apostas_processadas WHERE fingerprint = ?", (fingerprint,))
        result = cursor.fetchone(); conn.close()
        return {'tipster': result[0], 'row': result[1], 'unidade': result[2]} if result else None
    except Exception as e:
        logging.error(f"Erro ao checar aposta no DB: {e}"); return None

def update_stake_in_db(fingerprint, new_unidade):
    try:
        conn = sqlite3.connect(config.DB_FILE); cursor = conn.cursor()
        cursor.execute("UPDATE apostas_processadas SET unidade = ? WHERE fingerprint = ?", (new_unidade, fingerprint))
        conn.commit(); conn.close()
        logging.info(f"Unidade da aposta {fingerprint[:6]}... atualizada no DB.")
    except Exception as e: logging.error(f"Erro ao atualizar unidade no DB: {e}")
