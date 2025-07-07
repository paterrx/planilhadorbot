# app/config.py

import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

# --- LÓGICA INTELIGENTE DE CREDENCIAIS (A PEÇA QUE FALTAVA) ---
GOOGLE_CREDENTIALS_JSON_STR = os.getenv('GOOGLE_CREDENTIALS_JSON')
CREDENTIALS_FILE = "credentials.json" # Padrão para rodar no seu PC

if GOOGLE_CREDENTIALS_JSON_STR:
    # Se a variável de ambiente existir (estamos na nuvem),
    # cria um arquivo temporário com o conteúdo dela.
    CREDENTIALS_FILE = "temp_credentials.json"
    with open(CREDENTIALS_FILE, 'w') as f:
        f.write(GOOGLE_CREDENTIALS_JSON_STR)
    logging.info("Arquivo de credenciais criado a partir da variável de ambiente para uso na nuvem.")
# --- FIM DA LÓGICA ---


# --- CONSTANTES DE CONFIGURAÇÃO ---
DB_FILE = "bets_memory.db"
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

# --- CONFIGURAÇÕES DINÂMICAS ---
try:
    with open(CONFIG_JSON_FILE, 'r', encoding='utf-8') as f:
        _config_data = json.load(f)
        TARGET_CHANNELS = _config_data.get("target_channels", [])
except FileNotFoundError:
    TARGET_CHANNELS = []

# --- CONTEXTOS LIDOS DOS ARQUIVOS TXT ---
try:
    LIST_CASAS = [line.strip() for line in open('casas.txt', 'r', encoding='utf-8') if line.strip() and line.strip() != '-']
except FileNotFoundError:
    LIST_CASAS = []