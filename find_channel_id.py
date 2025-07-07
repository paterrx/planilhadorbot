# find_channel_id.py

import asyncio
from telethon import TelegramClient

# Suas credenciais, que já usamos antes
TELEGRAM_API_ID = 23767719
TELEGRAM_API_HASH = '238e12910fd0755bd76d58b09705fe9c'
TELEGRAM_SESSION_NAME = 'planilhadorbot'

async def main():
    print("Conectando para listar seus grupos e canais...")

    # Usa a sessão existente para conectar instantaneamente
    client = TelegramClient(TELEGRAM_SESSION_NAME, TELEGRAM_API_ID, TELEGRAM_API_HASH)
    await client.start()

    print("-" * 50)
    print("LISTA DE CANAIS E GRUPOS\n")

    async for dialog in client.iter_dialogs():
        if dialog.is_group or dialog.is_channel:
            print(f"Nome: {dialog.name.ljust(40)} | ID: {dialog.id}")

    print("-" * 50)

    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())