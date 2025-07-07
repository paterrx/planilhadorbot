# app/main.py
import asyncio
import logging
from app.telegram_handler import client
from app import database # Importa nosso módulo de database

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
    # --- ETAPA DE INICIALIZAÇÃO ---
    logging.info("Inicializando o banco de dados...")
    database.initialize_database()

    from app import config # Import local para garantir que tudo foi carregado

    await client.start()
    logging.info(f"🤖 O Planilhador (v. Autossuficiente) está online...")
    logging.info(f"Ouvindo {len(config.TARGET_CHANNELS)} canais.")
    await client.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot encerrado.")