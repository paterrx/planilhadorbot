#!/usr/bin/env python3
# monitoramento/monitor.py

import logging
import sys
import os
import time
import asyncio
import gspread
import pandas as pd
from datetime import datetime
import google.generativeai as genai  # type: ignore

# permite importar app e monitoramento
sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..")))

from app import config
from app.database import initialize_database
from monitoramento.api_football_handler import find_fixture_id, get_fixture_statistics
from monitoramento.juiz_analyzer import PROMPT_BET_RESOLVER

# --- CLIENTE GEMINI ---
genai.configure(api_key=config.GEMINI_API_KEY)

# --- LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - MONITOR - %(levelname)s - %(message)s',
    stream=sys.stdout
)

BOT_SHEET = config.SPREADSHEET_ID
MAIN_SHEET = config.SPREADSHEET_ID  # ou outra se precisar

async def monitor_loop():
    initialize_database()
    gc = gspread.service_account_from_dict(config.GOOGLE_CREDENTIALS_DICT)
    sh_bot = gc.open_by_key(BOT_SHEET).sheet1
    sh_main = gc.open_by_key(MAIN_SHEET).sheet1

    while True:
        logging.info("🔄 Iniciando ciclo de monitoramento")
        df = pd.DataFrame(sh_main.get_all_records())

        for idx, row in df.iterrows():
            casa = row.get("time_casa")
            fora = row.get("time_fora")
            season = datetime.now().year
            fid = find_fixture_id(casa, fora, season)
            if not fid:
                continue

            stats = get_fixture_statistics(fid)
            if not stats:
                continue

            payload = row.to_dict()
            user_input = json.dumps(payload, ensure_ascii=False)
            resp = await genai.chat.completions.create(  # type: ignore[attr-defined]
                model=config.GEMINI_MODEL,
                user=user_input,
                prompt=PROMPT_BET_RESOLVER,
                temperature=0.0
            )
            result = json.loads(resp.choices[0].message)  # type: ignore[attr-defined]
            status = result.get("status")

            # grava status na planilha do bot
            sh_bot.update_cell(idx + 2, config.STAKE_COLUMN_NUMBER + 2, status)
            logging.info("✅ %s vs %s => %s", casa, fora, status)

        logging.info("⏱ Dormindo 5min")
        time.sleep(300)

def main():
    asyncio.run(monitor_loop())

if __name__ == "__main__":
    main()
