# monitoramento/monitor.py

import gspread
import pandas as pd
import logging
import time
import sys
import os
import asyncio
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import config
from app.database import initialize_database
# O monitoramento agora se torna mais simples, apenas logando por enquanto
# A lógica de resolução será a próxima etapa

logging.basicConfig(level=logging.INFO, format='%(asctime)s - MONITOR - %(levelname)s - %(message)s', stream=sys.stdout)

async def main():
    logging.info("🤖 Guardião 'Monitor' iniciando seu turno de vigilância...")
    initialize_database()
    
    while True:
        try:
            logging.info("Ciclo de monitoramento iniciado... (Lógica de cópia e resolução a ser implementada)")
            # Aqui entrará a lógica para copiar apostas da planilha do bot para a principal
            # E a lógica para chamar a API-Football e o Juiz
            
            await asyncio.sleep(900) # Roda a cada 15 minutos

        except KeyboardInterrupt:
            logging.info("Guardião Monitor encerrando o turno."); break
        except Exception as e:
            logging.error(f"Ocorreu um erro inesperado no loop do Monitor: {e}"); await asyncio.sleep(120)

if __name__ == '__main__':
    asyncio.run(main())