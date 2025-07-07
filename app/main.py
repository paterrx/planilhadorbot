# app/main.py - v13.1 (Correção Final de Deploy)

import asyncio
import logging
# A MUDANÇA ESTÁ AQUI: Usando import relativo
from .telegram_handler import client

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
    # Usamos um import local aqui para garantir que o config seja carregado
    from . import config

    await client.start()
    logging.info(f"🤖 O Planilhador (v. Final) está online...")
    logging.info(f"Ouvindo {len(config.TARGET_CHANNELS)} canais.")
    await client.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot encerrado.")