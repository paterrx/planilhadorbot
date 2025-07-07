# app/telegram_handler.py
import os
import logging
from collections import deque
from telethon import TelegramClient, events

from . import config
from . import gemini_analyzer as gemini
from . import database as db
from . import sheets

client = TelegramClient(config.TELEGRAM_SESSION_NAME, config.TELEGRAM_API_ID, config.TELEGRAM_API_HASH)
recently_processed_signatures = deque(maxlen=50)

@client.on(events.NewMessage(chats=config.TARGET_CHANNELS))
async def handle_new_message(event):
    global recently_processed_signatures
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
        if event.message.photo:
            image_file_path = await event.download_media(file=f"temp_image_{event.id}.jpg")
        
        classification = await gemini.run_gemini_request(gemini.PROMPT_CLASSIFIER, message_text, image_file_path, channel_name)
        bet_type = classification.get('bet_type', 'TRASH') if classification else 'ERROR'

        if bet_type in gemini.PROMPT_MAP:
            logging.info(f"Mensagem classificada como '{bet_type}'. Chamando especialista...")
            list_of_bets = await gemini.run_gemini_request(gemini.PROMPT_MAP[bet_type], message_text, image_file_path, channel_name)
        else:
            logging.info(f"Mensagem classificada como '{bet_type}'. Ignorando."); return

        if not list_of_bets or not isinstance(list_of_bets, list):
            logging.info("Especialista não retornou apostas válidas."); return

        logging.info(f"Especialista encontrou {len(list_of_bets)} apostas. Verificando com a memória...")
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
                logging.info(f"Aposta duplicada encontrada no DB (FP: {fingerprint[:6]}...). Ignorando.")
    finally:
        if image_file_path and os.path.exists(image_file_path): os.remove(image_file_path)
        logging.info("--- Fim do processamento ---")