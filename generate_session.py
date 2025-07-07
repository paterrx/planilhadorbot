# generate_session.py (Versão Segura)

from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv
import os

load_dotenv()

api_id = os.getenv('TELEGRAM_API_ID')
api_hash = os.getenv('TELEGRAM_API_HASH')

print("Iniciando o processo para gerar sua String de Sessão...")
with TelegramClient(StringSession(), api_id, api_hash) as client:
    session_string = client.session.save()
    print("\nSUCESSO! Sua String de Sessão do Telethon é:\n")
    print(session_string)