# app/config.py
import os
import json
from dotenv import load_dotenv

load_dotenv()

# --- CONSTANTES DE CONFIGURAÇÃO ---
DB_FILE = "bets_memory.db"
CREDENTIALS_FILE = "credentials.json"
CONFIG_JSON_FILE = "config.json"
TELEGRAM_SESSION_NAME = 'planilhadorbot'
STAKE_COLUMN_NUMBER = 12

# --- SEGREDOS LIDOS DO .ENV ---
TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
MAIN_TIPSTER_NAME = os.getenv('MAIN_TIPSTER_NAME')

# --- CONFIGURAÇÕES DINÂMICAS ---
try:
    with open(CONFIG_JSON_FILE, 'r', encoding='utf-8') as f:
        _config_data = json.load(f)
        TARGET_CHANNELS = _config_data.get("target_channels", [])
except FileNotFoundError:
    TARGET_CHANNELS = []

# --- CONTEXTOS LIDOS DOS ARQUIVOS TXT ---
def load_context_list_from_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and line.strip() != '-']
    except FileNotFoundError:
        return []

LIST_CASAS = load_context_list_from_file('casas.txt')