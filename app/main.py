# app/main.py
import asyncio
import logging
import sys
from .telegram_handler import client
from .database import initialize_database

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - PLANILHADOR - %(levelname)s - %(message)s',
    stream=sys.stdout
)

async def main():
    logging.info("Inicializando o banco de dados...")
    initialize_database()
    from . import config
    await client.start()
    logging.info(f"🤖 O Planilhador vFinal está online, ouvindo {len(config.TARGET_CHANNELS)} canais...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot Planilhador encerrado.")
