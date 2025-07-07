# app/main.py
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
    # Aqui importamos e usamos as configurações para garantir que tudo foi carregado
    from app import config
    
    await client.start()
    logging.info(f"🤖 O Planilhador v13.0 (Arquitetura Profissional) está online...")
    logging.info(f"Ouvindo {len(config.TARGET_CHANNELS)} canais.")
    await client.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot encerrado.")