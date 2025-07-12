import os
import logging
import json
from collections import deque
from telethon import TelegramClient, events
from telethon.sessions import StringSession

from . import config
from .parser import generic_parse
from . import gemini_analyzer as gemini
from . import database as db
from . import sheets

# inicializa client
if config.TELETHON_SESSION_STRING:
    session = TelegramClient(
        StringSession(config.TELETHON_SESSION_STRING),
        config.TELEGRAM_API_ID,
        config.TELEGRAM_API_HASH
    )
else:
    session = TelegramClient(
        config.TELEGRAM_SESSION_NAME,
        config.TELEGRAM_API_ID,
        config.TELEGRAM_API_HASH
    )

recently_processed = deque(maxlen=100)

@session.on(events.NewMessage(chats=config.TARGET_CHANNELS))
async def handle_new_message(event):
    chat = await event.get_chat()
    channel = getattr(chat, 'title', str(chat.id))

    text = event.message.message or ""
    sig = f"{channel}-{event.id}-{hash(text)}"
    if sig in recently_processed:
        logging.info("Ignorando duplicata em %s", channel)
        return
    recently_processed.append(sig)

    logging.info("📥 Mensagem nova em %s (ID %d)", channel, event.id)
    img = None
    try:
        if event.message.photo:
            img = await event.download_media(file=f"temp_{event.id}.jpg")

        # 1) parser híbrido
        raw = await generic_parse(text)
        logging.debug("RAW_EXTRAIDO: %s", raw)

        # 2) Analista Mestre
        bets = await gemini.run_gemini_request(
            gemini.PROMPT_REFINER,
            text,
            img,
            channel,
            extra_data=json.dumps(raw, ensure_ascii=False)
        )
        if not isinstance(bets, list):
            logging.error("Esperava lista, recebeu %s", type(bets))
            return

        # grava cada aposta
        for b in bets:
            fp = db.create_fingerprint(b)
            if db.check_db_for_bet(fp) is None:
                row = sheets.write_to_sheet(b)
                stake = b.get('stake') or b.get('unidade')
                if row is not None and stake is not None:
                    db.log_bet_to_db(fp, channel, row, stake)
                    logging.info("Gravou linha %s", row)
            else:
                logging.info("Já processada (FP %s…)", fp[:8])

    except Exception:
        logging.exception("Erro ao processar mensagem")
    finally:
        if img and os.path.exists(img):
            os.remove(img)
        logging.info("--- fim ---")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    session.start()
    session.run_until_disconnected()
