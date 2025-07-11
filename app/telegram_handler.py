# app/telegram_handler.py
import os
import logging
import json
from collections import deque
from telethon import TelegramClient, events
from telethon.sessions import StringSession

from . import config
from . import gemini_analyzer as gemini
from . import database as db
from . import sheets

if config.TELETHON_SESSION_STRING:
    session = StringSession(config.TELETHON_SESSION_STRING)
else:
    session = config.TELEGRAM_SESSION_NAME

client = TelegramClient(session, config.TELEGRAM_API_ID, config.TELEGRAM_API_HASH)
recently_processed_signatures = deque(maxlen=100)

@client.on(events.NewMessage(chats=config.TARGET_CHANNELS))
async def handle_new_message(event):
    global recently_processed_signatures
    channel_name, message_text, image_file_path = event.chat.title, event.message.text or "", None
    
    if event.message.document and 'video' in event.message.document.mime_type:
        logging.info(f"Ignorando GIF/vídeo de '{channel_name}'."); return
    
    message_signature = f"{event.chat.id}_{hash(message_text)}" if not event.message.photo else f"{event.chat.id}_{event.message.file.size}"
    
    if message_signature in recently_processed_signatures:
        logging.info(f"Ignorando mensagem duplicada de '{channel_name}'."); return
    recently_processed_signatures.append(message_signature)
    
    logging.info(f"📥 Nova mensagem de '{channel_name}' (ID: {event.id})")
    
    try:
        if event.message.photo:
            image_file_path = await event.download_media(file=f"temp_image_{event.id}.jpg")
        
        # --- DEBATE DE IAS ---
        # ETAPA 1: O "Leitor" extrai os dados brutos
        logging.info("Chamando IA Leitora...")
        raw_data = await gemini.run_gemini_request(gemini.PROMPT_READER, message_text, image_file_path, channel_name)

        if not raw_data or raw_data.get('is_bet') is False:
            logging.info("Leitor determinou que a mensagem não é uma aposta. Ignorando.")
            return
        
        # ETAPA 2: O "Analista Mestre" formata os dados
        logging.info("Leitor extraiu dados brutos. Chamando Analista Mestre...")
        final_bets = await gemini.run_gemini_request(gemini.PROMPT_ANALYZER, message_text, image_file_path, channel_name, extra_data=json.dumps(raw_data, ensure_ascii=False))

        if not final_bets or not isinstance(final_bets, list):
            logging.error("Analista Mestre falhou em processar os dados brutos. Ignorando aposta.")
            return
            
        # ETAPA 3: Processar as apostas finais
        logging.info(f"Analista Mestre finalizou {len(final_bets)} aposta(s). Verificando com a memória...")
        for bet_data in final_bets:
            bet_data['tipster'] = channel_name # Garante o tipster correto
            fingerprint = db.create_fingerprint(bet_data)
            existing_bet = db.check_db_for_bet(fingerprint)
            if existing_bet is None:
                new_row = sheets.write_to_sheet(bet_data)
                unidade = bet_data.get('unidade')
                if new_row and unidade is not None:
                    db.log_bet_to_db(fingerprint, channel_name, new_row, unidade)
            else:
                logging.info(f"Aposta duplicada encontrada no DB (FP: {fingerprint[:6]}...). Ignorando.")

    except Exception as e:
        logging.error(f"ERRO NÃO TRATADO no handle_new_message: {e}", exc_info=True)
    finally:
        if image_file_path and os.path.exists(image_file_path):
            os.remove(image_file_path)
        logging.info("--- Fim do processamento ---")