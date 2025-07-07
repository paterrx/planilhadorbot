# app/config.py - Versão Final para Nuvem

import os
import json
from dotenv import load_dotenv

load_dotenv()

# --- CONSTANTES DE CONFIGURAÇÃO ---
DB_FILE = "bets_memory.db"
CONFIG_JSON_FILE = "config.json"

# --- LÓGICA INTELIGENTE DE CREDENCIAIS ---
# No Railway, vamos ler de uma variável de ambiente. Localmente, do arquivo.
GOOGLE_CREDENTIALS_JSON_STR = os.getenv('GOOGLE_CREDENTIALS_JSON')
CREDENTIALS_FILE = "credentials.json"

if GOOGLE_CREDENTIALS_JSON_STR:
    # Se estamos na nuvem, cria o arquivo credentials.json a partir da variável
    CREDENTIALS_FILE = "temp_credentials.json"
    with open(CREDENTIALS_FILE, 'w') as f:
        f.write(GOOGLE_CREDENTIALS_JSON_STR)

# --- SEGREDOS E CONFIGS ---
TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
# ... (o resto do arquivo é idêntico)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
MAIN_TIPSTER_NAME = os.getenv('MAIN_TIPSTER_NAME')
TELEGRAM_SESSION_NAME = 'planilhadorbot'
STAKE_COLUMN_NUMBER = 12
try:
    with open(CONFIG_JSON_FILE, 'r') as f:
        _config_data = json.load(f)
        TARGET_CHANNELS = _config_data.get("target_channels", [])
except FileNotFoundError:
    TARGET_CHANNELS = []
try:
    LIST_CASAS = [line.strip() for line in open('casas.txt', 'r', encoding='utf-8') if line.strip() and line.strip() != '-']
except FileNotFoundError:
    LIST_CASAS = []