# app/telegram_handler.py

import os
import logging
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
recently_processed_signatures = deque(maxlen=100) # Aumentado para lidar com mais mensagens

@client.on(events.NewMessage(chats=config.TARGET_CHANNELS))
async def handle_new_message(event):
    global recently_processed_signatures
    channel_name, message_text, image_file_path = event.chat.title, event.message.text or "", None
    
    if event.message.document and 'video' in event.message.document.mime_type:
        logging.info(f"Ignorando GIF/vídeo de '{channel_name}'."); return
    
    # Cria uma assinatura única para a mensagem para evitar processamento duplicado rápido
    if event.message.photo:
        message_signature = f"{event.chat.id}_{event.message.file.size}"
    else:
        message_signature = f"{event.chat.id}_{hash(message_text)}"
    
    if message_signature in recently_processed_signatures:
        logging.info(f"Ignorando mensagem duplicada recente de '{channel_name}'."); return
    recently_processed_signatures.append(message_signature)
    
    logging.info(f"📥 Nova mensagem de '{channel_name}' (ID: {event.id})")
    
    try:
        if event.message.photo:
            image_file_path = await event.download_media(file=f"temp_image_{event.id}.jpg")
        
        # --- DEBATE DOS ESPECIALISTAS ---
        # ETAPA 1: O Extrator Otimista gera os rascunhos
        logging.info("Chamando Extrator Otimista...")
        list_of_bets_draft = await gemini.run_gemini_request(gemini.PROMPT_MASTER_EXTRACTOR, message_text, image_file_path, channel_name)

        # ETAPA 2: O Classificador Cético dá o seu veredito
        logging.info("Chamando Classificador Cético...")
        classification = await gemini.run_gemini_request(gemini.PROMPT_SKEPTIC_CLASSIFIER, message_text, image_file_path, channel_name)
        is_bet_approved = classification.get('is_bet', False) if isinstance(classification, dict) else False

        # ETAPA 3: O Juiz Mestre (nosso código) toma a decisão final
        if not is_bet_approved:
            logging.warning(f"VEREDITO: O Classificador Cético REJEITOU a mensagem de '{channel_name}'. Não é uma aposta válida.")
            return

        if not list_of_bets_draft or not isinstance(list_of_bets_draft, list):
            logging.warning(f"VEREDITO: O Cético APROVOU, mas o Extrator não encontrou dados válidos. Ignorando.")
            return

        logging.info(f"VEREDITO: Aprovado! O Extrator encontrou {len(list_of_bets_draft)} aposta(s) e o Cético confirmou. Verificando com a memória...")
        
        for bet_data in list_of_bets_draft:
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
                # Lógica para o tipster principal poder sobrescrever
                if channel_name == config.MAIN_TIPSTER_NAME and existing_bet['tipster'] != config.MAIN_TIPSTER_NAME:
                    unidade = bet_data.get('unidade') or bet_data.get('stake')
                    if unidade is not None:
                        logging.warning(f"SOBRESCREVENDO! Nova aposta do Carro-Chefe '{channel_name}' encontrada.")
                        sheets.update_stake_in_sheet(existing_bet['row'], unidade)
                        db.update_stake_in_db(fingerprint, unidade) # Atualiza no DB também
                else:
                    logging.info(f"Aposta duplicada encontrada no DB (FP: {fingerprint[:6]}...). Ignorando.")
    finally:
        if image_file_path and os.path.exists(image_file_path):
            os.remove(image_file_path)
        logging.info("--- Fim do processamento ---")