# monitoramento/monitor.py
print("--- SCRIPT DO MONITOR INICIADO ---")

import gspread
import pandas as pd
import logging
import time
import sys
import os
import asyncio
from datetime import datetime

# Garante que o script possa encontrar os outros módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import config
from app.database import initialize_database
from monitoramento import api_football_handler
from monitoramento import juiz_analyzer

# --- CONFIGURAÇÃO ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - GUARDIÃO - %(levelname)s - %(message)s', stream=sys.stdout)
MAIN_SPREADSHEET_ID = "1zmv8q_XhIeRSXtM4SPu7uXyOU7bfKwt1_I2_oncafCc"
BOT_SPREADSHEET_ID = config.SPREADSHEET_ID 

# (O resto do código permanece o mesmo...)
# ... (cole o código completo do monitor.py que te enviei anteriormente aqui)
