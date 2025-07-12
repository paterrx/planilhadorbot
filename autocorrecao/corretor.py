#!/usr/bin/env python3
# autocorrecao/corretor.py

import logging
import sys
import os
import asyncio
import gspread
import pandas as pd
from datetime import datetime
import google.generativeai as genai  # type: ignore

# permite importar app
sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..")))

from app import config
from app.database import initialize_database, create_fingerprint, update_stake_in_db
from app.gemini_analyzer import PROMPT_REFINER  # vamos reaproveitar o mesmo prompt

# --- CLIENTE GEMINI ---
genai.configure(api_key=config.GEMINI_API_KEY)

# --- LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - CORRETOR - %(levelname)s - %(message)s',
    stream=sys.stdout
)

BOT_SPREADSHEET_ID = config.SPREADSHEET_ID

async def run_error_detector(df: pd.DataFrame):
    """
    Para cada linha: envia ao Gemini (PROMPT_REFINER)
    e, se retornar campo 'new_stake', atualiza DB e planilha.
    """
    gc = gspread.service_account_from_dict(config.GOOGLE_CREDENTIALS_DICT)
    sh = gc.open_by_key(BOT_SPREADSHEET_ID).sheet1

    for _, row in df.iterrows():
        data = row.to_dict()
        fp = data.get("fingerprint")
        logging.info("⏳ Verificando FP=%s", fp)

        # monta chamada
        user_input = json.dumps(data, ensure_ascii=False)
        resp = await genai.chat.completions.create(        # type: ignore[attr-defined]
            model=config.GEMINI_MODEL,
            user=user_input,
            prompt=PROMPT_REFINER,
            temperature=0.0
        )
        text = resp.choices[0].message  # type: ignore[attr-defined]

        try:
            corr = json.loads(text)
        except Exception:
            logging.error("JSON inválido do corretor: %s", text)
            continue

        new_stake = corr.get("new_stake")
        if new_stake is not None:
            update_stake_in_db(fp, new_stake)
            # atualiza planilha
            sh.update_cell(
                int(data["sheet_row"]),
                config.STAKE_COLUMN_NUMBER,
                str(new_stake).replace(".", ",")
            )
            logging.info("✅ Atualizado FP=%s para %su", fp, new_stake)

def main():
    initialize_database()
    # Exemplo de como carregar suas apostas pendentes:
    # df = pd.read_excel("para_correcao.xlsx")
    # asyncio.run(run_error_detector(df))

if __name__ == "__main__":
    main()
