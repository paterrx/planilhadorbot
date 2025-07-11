# monitoramento/monitor.py

import gspread
import pandas as pd
import logging
import time
import sys
import os
import asyncio
from datetime import datetime

# Garante que o script possa encontrar os outros módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import config
from app.database import initialize_database
from monitoramento import api_football_handler
from monitoramento import juiz_analyzer

# --- CONFIGURAÇÃO ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - GUARDIÃO - %(levelname)s - %(message)s', stream=sys.stdout)
MAIN_SPREADSHEET_ID = "1zmv8q_XhIeRSXtM4SPu7uXyOU7bfKwt1_I2_oncafCc"
BOT_SPREADSHEET_ID = "1DrsPb6_tlYbeVs8d2lCoMiWBBukqtb1AxXKsioJSW98" 

# --- FUNÇÕES ---
def get_gspread_client():
    if config.GOOGLE_CREDENTIALS_DICT:
        return gspread.service_account_from_dict(config.GOOGLE_CREDENTIALS_DICT)
    else:
        return gspread.service_account(filename=config.CREDENTIALS_FILE_PATH)

async def check_and_resolve_bets(worksheet, df):
    """Verifica apostas pendentes e tenta resolvê-las."""
    if 'Situação' not in df.columns:
        logging.warning("Coluna 'Situação' não encontrada na planilha principal. Pulando resolução de apostas.")
        return

    pending_bets = df[df['Situação'] == ''].copy()
    
    if pending_bets.empty:
        logging.info("Nenhuma aposta pendente para resolver.")
        return

    logging.warning(f"Encontradas {len(pending_bets)} apostas pendentes. Iniciando resolução...")
    for index, bet in pending_bets.iterrows():
        sheet_row_index = index + 2
        
        try:
            times_str = bet.get('Jogos', '')
            if not times_str or 'vs' not in str(times_str).lower():
                logging.warning(f"Jogos mal formatados ou ausentes na linha {sheet_row_index}: '{times_str}'. Pulando.")
                continue
                
            time1, time2 = [t.strip() for t in times_str.split('vs')]
            season = str(datetime.now().year)

            fixture_id = api_football_handler.find_fixture_id(time1, time2, season)
            if not fixture_id:
                logging.info(f"Partida para '{times_str}' ainda não finalizada ou não encontrada pela API.")
                continue

            statistics = api_football_handler.get_fixture_statistics(fixture_id)
            if not statistics:
                logging.warning(f"Estatísticas não disponíveis para a partida ID {fixture_id}.")
                continue
            
            status = await juiz_analyzer.resolve_bet_with_gemini(bet, statistics)
            
            if status in ['Green', 'Red']:
                # A coluna 'Situação' é a 14ª (N)
                worksheet.update_cell(sheet_row_index, 14, status)
                logging.info(f"Aposta na linha {sheet_row_index} ('{times_str}') atualizada para {status}.")
            
            await asyncio.sleep(10) # Pausa para respeitar o limite de requisições da API

        except Exception as e:
            logging.error(f"Erro ao tentar resolver aposta da linha {sheet_row_index}: {e}")

async def main():
    logging.info("🤖 Guardião 'Juiz' da Planilha iniciando seu turno...")
    initialize_database()
    
    try:
        gc = get_gspread_client()
        main_worksheet = gc.open_by_key(MAIN_SPREADSHEET_ID).worksheet("Julho")
    except gspread.exceptions.WorksheetNotFound:
        logging.error("ERRO CRÍTICO: A aba 'Julho' não foi encontrada na sua planilha principal. Encerrando.")
        return
    except Exception as e:
        logging.error(f"ERRO CRÍTICO ao abrir a planilha principal: {e}")
        return

    while True:
        try:
            all_records = main_worksheet.get_all_records()
            if not all_records:
                logging.info("Planilha principal vazia. Aguardando 5 minutos...")
                await asyncio.sleep(300)
                continue
            
            await check_and_resolve_bets(main_worksheet, pd.DataFrame(all_records))
            
            # Adicionar aqui a lógica futura de cópia e de avaliação de TRASH se necessário
            
            logging.info("Vigilância contínua. Próxima verificação em 15 minutos.")
            await asyncio.sleep(900)

        except KeyboardInterrupt:
            logging.info("Guardião encerrando o turno."); break
        except Exception as e:
            logging.error(f"Ocorreu um erro inesperado no loop do guardião: {e}"); await asyncio.sleep(120)

if __name__ == '__main__':
    asyncio.run(main())
