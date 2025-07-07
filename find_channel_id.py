# find_channel_id.py (Versão Segura)

import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()

TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
TELEGRAM_SESSION_NAME = 'planilhadorbot'

async def main():
    print("Conectando para listar seus grupos e canais...")
    client = TelegramClient(TELEGRAM_SESSION_NAME, TELEGRAM_API_ID, TELEGRAM_API_HASH)
    await client.start()
    print("-" * 50 + "\nLISTA DE CANAIS E GRUPOS\n")
    async for dialog in client.iter_dialogs():
        if dialog.is_group or dialog.is_channel:
            print(f"Nome: {dialog.name.ljust(40)} | ID: {dialog.id}")
    print("-" * 50)
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())