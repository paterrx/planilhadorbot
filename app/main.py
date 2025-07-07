# app/main.py - v13.2 (A Versão Final de Deploy)

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import logging
from app.telegram_handler import client

# --- CONFIGURAÇÃO DO LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log", mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

async def main():
    from app import config
    
    await client.start()
    logging.info(f"🤖 O Planilhador (v. Final Deploy) está online...")
    logging.info(f"Ouvindo {len(config.TARGET_CHANNELS)} canais.")
    await client.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot encerrado.")