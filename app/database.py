# app/database.py
import sqlite3
import hashlib
import logging
from . import config

def create_fingerprint(bet_data):
    jogos = bet_data.get('jogos', '');
    if not isinstance(jogos, str): jogos = str(jogos)
    descricao = bet_data.get('descricao_da_aposta') or bet_data.get('descricao_da_posta', '')
    entrada = bet_data.get('entrada', '')
    data_string = f"{jogos}_{descricao}_{entrada}".lower()
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