# find_channel_id.py (Versão Segura e à Prova de Falhas)

import asyncio
import os
import sys
from dotenv import load_dotenv
from telethon import TelegramClient

# Carrega as variáveis do arquivo .env
load_dotenv()

# Lê as credenciais de forma segura do ambiente
TELEGRAM_API_ID = os.getenv('TELEGRAM_API_ID')
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH')
TELEGRAM_SESSION_NAME = 'planilhadorbot'

# --- VERIFICAÇÃO DE SEGURANÇA ---
if not TELEGRAM_API_ID or not TELEGRAM_API_HASH:
    print("ERRO: TELEGRAM_API_ID ou TELEGRAM_API_HASH não encontrados!")
    print("Por favor, verifique se o seu arquivo '.env' existe na mesma pasta e contém as chaves corretas.")
    sys.exit(1) # Encerra o script se as chaves não forem encontradas

async def main():
    print("Conectando para listar seus grupos e canais...")
    
    # Converte o ID para inteiro, pois o .env o lê como texto
    client = TelegramClient(TELEGRAM_SESSION_NAME, int(TELEGRAM_API_ID), TELEGRAM_API_HASH)
    
    try:
        await client.start()
        print("-" * 50 + "\nLISTA DE CANAIS E GRUPOS\n")
        
        async for dialog in client.iter_dialogs():
            if dialog.is_group or dialog.is_channel:
                print(f"Nome: {dialog.name.ljust(40)} | ID: {dialog.id}")

        print("-" * 50)
        
        await client.disconnect()
        
    except Exception as e:
        print(f"\nOcorreu um erro durante a conexão: {e}")
        print("Verifique se sua conexão com a internet está ativa e se as credenciais estão corretas.")

if __name__ == '__main__':
    asyncio.run(main())