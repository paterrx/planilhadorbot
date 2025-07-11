# autocorrecao/corretor.py
print("--- SCRIPT DO CORRETOR INICIADO ---")

import logging
import time
import sys
import os
import asyncio
import gspread
import pandas as pd
from datetime import datetime

# Adiciona a pasta raiz ao path para que os imports de 'app' funcionem
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import config
from app.database import initialize_database, create_fingerprint, update_stake_in_db
from app.gemini_analyzer import run_gemini_request, PROMPT_ERROR_DETECTOR

# --- CONFIGURAÇÃO ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - CORRETOR - %(levelname)s - %(message)s', stream=sys.stdout)
BOT_SPREADSHEET_ID = config.SPREADSHEET_ID 
MAIN_SPREADSHEET_ID = "1zmv8q_XhIeRSXtM4SPu7uXyOU7bfKwt1_I2_oncafCc"

# (O resto do código permanece o mesmo...)
# ... (cole o código completo do corretor.py que te enviei anteriormente aqui)
