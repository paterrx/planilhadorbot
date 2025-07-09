# app/telegram_handler.py
import os, logging, json
from collections import deque
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from . import config, gemini_analyzer as gemini, database as db, sheets

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
    if event.message.photo: message_signature = f"{event.chat.id}_{event.message.file.size}"
    else: message_signature = f"{event.chat.id}_{hash(message_text)}"
    if message_signature in recently_processed_signatures:
        logging.info(f"Ignorando mensagem duplicada de '{channel_name}'."); return
    recently_processed_signatures.append(message_signature)
    logging.info(f"📥 Nova mensagem de '{channel_name}' (ID: {event.id})")
    try:
        if event.message.photo: image_file_path = await event.download_media(file=f"temp_image_{event.id}.jpg")
        
        classification = await gemini.run_gemini_request(gemini.PROMPT_CLASSIFIER, message_text, image_file_path, channel_name)
        bet_type = classification.get('bet_type', 'TRASH') if isinstance(classification, dict) else 'ERROR'

        if bet_type not in gemini.PROMPT_MAP:
            logging.info(f"Mensagem classificada como '{bet_type}'. Ignorando."); return

        logging.info(f"Mensagem classificada como '{bet_type}'. Chamando especialista...")
        list_of_bets_draft = await gemini.run_gemini_request(gemini.PROMPT_MAP[bet_type], message_text, image_file_path, channel_name)

        if not list_of_bets_draft or not isinstance(list_of_bets_draft, list):
            logging.info("Especialista não retornou apostas válidas."); return

        logging.info(f"Especialista encontrou {len(list_of_bets_draft)} rascunhos. Iniciando Prova Real...")
        
        final_bets = []
        for bet_draft in list_of_bets_draft:
            logging.info(f"Revisando rascunho: {bet_draft.get('entrada')}")
            revisor1_bet = await gemini.run_gemini_request(gemini.PROMPT_QA_REFINER, message_text, image_file_path, channel_name, extra_data=json.dumps(bet_draft, ensure_ascii=False))
            if not revisor1_bet or not isinstance(revisor1_bet, dict):
                logging.warning("Revisor 1 falhou ou rejeitou. Descartando aposta.")
                continue
            
            # A "Prova Real Insana" - um segundo revisor para garantir
            logging.info("Enviando para Revisor Chefe...")
            revisor2_bet = await gemini.run_gemini_request(gemini.PROMPT_QA_REFINER, message_text, image_file_path, channel_name, extra_data=json.dumps(revisor1_bet, ensure_ascii=False))
            
            if revisor2_bet and isinstance(revisor2_bet, dict):
                logging.info(f"✅ Prova Real completa! Aposta aprovada.")
                final_bets.append(revisor2_bet)
            else:
                logging.warning("Revisor Chefe falhou ou rejeitou. Descartando aposta.")

        if not final_bets:
            logging.info("Nenhuma aposta sobreviveu ao processo de revisão."); return
            
        logging.info(f"Revisão concluída. {len(final_bets)} apostas aprovadas para planilhamento.")
        for bet_data in final_bets:
            bet_data['tipster'] = channel_name
            fingerprint = db.create_fingerprint(bet_data)
            existing_bet = db.check_db_for_bet(fingerprint)
            if existing_bet is None:
                new_row = sheets.write_to_sheet(bet_data)
                unidade = bet_data.get('unidade') or bet_data.get('stake')
                if new_row and unidade is not None:
                    db.log_bet_to_db(fingerprint, channel_name, new_row, unidade)
            else:
                if channel_name == config.MAIN_TIPSTER_NAME and existing_bet['tipster'] != config.MAIN_TIPSTER_NAME:
                    unidade = bet_data.get('unidade') or bet_data.get('stake')
                    if unidade is not None:
                        logging.warning(f"SOBRESCREVENDO! Nova aposta do Carro-Chefe '{channel_name}' encontrada.")
                        sheets.update_stake_in_sheet(existing_bet['row'], unidade)
                        db.update_stake_in_db(fingerprint, unidade)
                else:
                    logging.info(f"Aposta duplicada encontrada no DB (FP: {fingerprint[:6]}...). Ignorando.")
    finally:
        if image_file_path and os.path.exists(image_file_path):
            os.remove(image_file_path)
        logging.info("--- Fim do processamento ---")