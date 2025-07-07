# app/telegram_handler.py - Versão Final com Login por String

import os
import logging
from collections import deque
from telethon import TelegramClient, events
from telethon.sessions import StringSession # Importa a classe necessária

from . import config
from . import gemini_analyzer as gemini
from . import database as db
from . import sheets

# --- LÓGICA DE LOGIN INTELIGENTE ---
if config.TELETHON_SESSION_STRING:
    # Na nuvem (Railway), usa a String de Sessão da variável de ambiente
    logging.info("Iniciando cliente a partir da STRING DE SESSÃO.")
    session = StringSession(config.TELETHON_SESSION_STRING)
else:
    # Localmente, usa o arquivo .session
    logging.info("String de Sessão não encontrada, iniciando cliente a partir do arquivo .session local.")
    session = config.TELEGRAM_SESSION_NAME

client = TelegramClient(session, config.TELEGRAM_API_ID, config.TELEGRAM_API_HASH)
# (O resto do arquivo, com a função handle_new_message, é idêntico)
recently_processed_signatures = deque(maxlen=50)

@client.on(events.NewMessage(chats=config.TARGET_CHANNELS))
async def handle_new_message(event):
    global recently_processed_signatures
    # ... (cole aqui toda a função handle_new_message da versão anterior, sem nenhuma alteração)
    channel_name, message_text, image_file_path = event.chat.title, event.message.text or "", None
    if event.message.document and 'video' in event.message.document.mime_type:
        logging.info(f"Ignorando GIF/vídeo de '{channel_name}'."); return
    if event.message.photo: message_signature = f"{event.chat.id}_{event.message.file.size}"
    else: message_signature = f"{event.chat.id}_{message_text}"
    if message_signature in recently_processed_signatures:
        logging.info(f"Ignorando mensagem duplicada de '{channel_name}'."); return
    recently_processed_signatures.append(message_signature)
    logging.info(f"📥 Nova mensagem de '{channel_name}' (ID: {event.id})")
    try:
        if event.message.photo: image_file_path = await event.download_media(file=f"temp_image_{event.id}.jpg")
        list_of_bets = await gemini.get_gemini_analysis(message_text, image_file_path, channel_name)
        if not list_of_bets:
            logging.info("IA não encontrou apostas válidas ou classificou como TRASH."); return
        logging.info(f"IA encontrou {len(list_of_bets)} apostas. Verificando com a memória...")
        for bet_data in list_of_bets:
            bet_data['tipster'] = channel_name
            fingerprint = db.create_fingerprint(bet_data)
            existing_bet = db.check_db_for_bet(fingerprint)
            if existing_bet is None:
                logging.info(f"Aposta (FP: {fingerprint[:6]}...) é nova. Planilhando...")
                new_row = sheets.write_to_sheet(bet_data)
                unidade = bet_data.get('unidade') or bet_data.get('stake')
                if new_row and unidade is not None:
                    db.log_bet_to_db(fingerprint, channel_name, new_row, unidade)
            else:
                if channel_name == config.MAIN_TIPSTER_NAME and existing_bet['tipster'] != config.MAIN_TIPSTER_NAME:
                     unidade = bet_data.get('unidade') or bet_data.get('stake')
                     if unidade is not None:
                        logging.warning(f"SOBRESCREVENDO! Nova aposta do Carro-Chefe '{channel_name}' encontrada.")
                        # sheets.update_stake_in_sheet(existing_bet['row'], unidade); db.update_stake_in_db(fingerprint, unidade)
                else:
                    logging.info(f"Aposta duplicada encontrada no DB (FP: {fingerprint[:6]}...). Ignorando.")
    finally:
        if image_file_path and os.path.exists(image_file_path): os.remove(image_file_path)
        logging.info("--- Fim do processamento ---")