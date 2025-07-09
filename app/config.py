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

# --- SEGREDOS LIDOS DO .ENV ---
TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
MAIN_TIPSTER_NAME = os.getenv('MAIN_TIPSTER_NAME')
TELETHON_SESSION_STRING = os.getenv('TELETHON_SESSION_STRING')

# --- LÓGICA INTELIGENTE DE CREDENCIAIS ---
GOOGLE_CREDENTIALS_JSON_STR = os.getenv('GOOGLE_CREDENTIALS_JSON')
GOOGLE_CREDENTIALS_DICT = None

if GOOGLE_CREDENTIALS_JSON_STR:
    try:
        GOOGLE_CREDENTIALS_DICT = json.loads(GOOGLE_CREDENTIALS_JSON_STR)
    except json.JSONDecodeError:
        logging.error("ERRO CRÍTICO: Falha ao decodificar GOOGLE_CREDENTIALS_JSON.")
elif not os.path.exists(CREDENTIALS_FILE_PATH):
     logging.warning(f"AVISO: O arquivo '{CREDENTIALS_FILE_PATH}' não foi encontrado para uso local.")

# --- CONFIGURAÇÕES DINÂMICAS ---
try:
    with open(CONFIG_JSON_FILE, 'r', encoding='utf-8') as f:
        _config_data = json.load(f)
        TARGET_CHANNELS = _config_data.get("target_channels", [])
except FileNotFoundError:
    TARGET_CHANNELS = []

# --- CONTEXTOS ---
try:
    LIST_CASAS = [line.strip() for line in open('casas.txt', 'r', encoding='utf-8') if line.strip() and line.strip() != '-']
except FileNotFoundError:
    LIST_CASAS = []