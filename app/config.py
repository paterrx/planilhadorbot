# app/config.py
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

# --- CONSTANTES ---
DB_FILE = "bets_memory.db"
CREDENTIALS_FILE_PATH = "credentials.json"
CONFIG_JSON_FILE = "config.json"
TELEGRAM_SESSION_NAME = 'planilhadorbot'
STAKE_COLUMN_NUMBER = 12
# --- MELHORIA: UPGRADE DO MODELO DE IA ---
GEMINI_MODEL = 'gemini-1.5-pro-latest'

# --- SEGREDOS ---
TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
MAIN_TIPSTER_NAME = os.getenv('MAIN_TIPSTER_NAME')
TELETHON_SESSION_STRING = os.getenv('TELETHON_SESSION_STRING')
API_FOOTBALL_KEY = os.getenv('API_FOOTBALL_KEY')

# --- LÓGICA DE CREDENCIAIS ---
GOOGLE_CREDENTIALS_JSON_STR = os.getenv('GOOGLE_CREDENTIALS_JSON')
GOOGLE_CREDENTIALS_DICT = None
if GOOGLE_CREDENTIALS_JSON_STR:
    try:
        GOOGLE_CREDENTIALS_DICT = json.loads(GOOGLE_CREDENTIALS_JSON_STR)
    except json.JSONDecodeError:
        logging.error("ERRO CRÍTICO: Falha ao decodificar GOOGLE_CREDENTIALS_JSON.")
elif not os.path.exists(CREDENTIALS_FILE_PATH):
     logging.warning(f"AVISO: O arquivo '{CREDENTIALS_FILE_PATH}' não foi encontrado.")

# --- CONFIGS DINÂMICAS ---
try:
    with open(CONFIG_JSON_FILE, 'r', encoding='utf-8') as f:
        TARGET_CHANNELS = json.load(f).get("target_channels", [])
except FileNotFoundError:
    TARGET_CHANNELS = []

# --- CONTEXTOS ---
def load_context_list_from_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    except FileNotFoundError:
        logging.warning(f"Arquivo de contexto '{filename}' não encontrado.")
        return []

LIST_CASAS = load_context_list_from_file('casas.txt')
LIST_TIPSTERS = load_context_list_from_file('tipster.txt')
LIST_TIPOS_APOSTA = load_context_list_from_file('tiposDeAposta.txt')
