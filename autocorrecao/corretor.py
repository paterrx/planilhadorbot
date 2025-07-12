# autocorrecao/corretor.py
import logging
import time
import sys
import os
import asyncio
import gspread
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import config
from app.database import initialize_database, check_db_for_bet, create_fingerprint, update_stake_in_db
from app.sheets import get_gspread_client
from app.gemini_analyzer import run_gemini_request, PROMPT_ERROR_DETECTOR

logging.basicConfig(level=logging.INFO, format='%(asctime)s - CORRETOR - %(levelname)s - %(message)s', stream=sys.stdout)
BOT_SPREADSHEET_ID = config.SPREADSHEET_ID 
MAIN_SPREADSHEET_ID = "1zmv8q_XhIeRSXtM4SPu7uXyOU7bfKwt1_I2_oncafCc"

async def correct_bet_data(main_worksheet, bot_worksheet, main_sheet_row):
    try:
        main_sheet_row_index = main_sheet_row.name + 2
        
        fingerprint_to_find = create_fingerprint(main_sheet_row.to_dict())
        
        db_entry = check_db_for_bet(fingerprint_to_find)
        if not db_entry:
            logging.warning(f"Não foi possível encontrar a aposta original no DB para a linha {main_sheet_row_index} da planilha principal.")
            return False

        bot_sheet_row_number = db_entry['row']
        bot_sheet_row_data = bot_worksheet.row_values(bot_sheet_row_number)
        
        original_context = f"Dados da planilha do bot (linha {bot_sheet_row_number}): {bot_sheet_row_data}"
        
        logging.info(f"Enviando para o Detetive de Erros. Contexto: {original_context[:100]}...")
        
        correction_result = await run_gemini_request(
            PROMPT_ERROR_DETECTOR,
            original_context,
            None,
            "ErrorDetector",
            extra_data=str(main_sheet_row.to_dict())
        )

        if correction_result and 'correcao_sugerida' in correction_result:
            corrected_value = correction_result['correcao_sugerida']
            if corrected_value is not None:
                logging.warning(f"✅ CORREÇÃO SUGERIDA para linha {main_sheet_row_index}: {corrected_value}. Aplicando...")
                
                main_worksheet.update_cell(main_sheet_row_index, config.STAKE_COLUMN_NUMBER, str(corrected_value).replace('.',','))
                update_stake_in_db(fingerprint_to_find, corrected_value)
                return True
    except Exception as e:
        logging.error(f"Erro no processo de correção para a linha {main_sheet_row_index}: {e}")
    return False

async def main():
    logging.info("🤖 Guardião 'Corretor' iniciando seu turno de auditoria...")
    initialize_database()
    
    try:
        gc = get_gspread_client()
        bot_worksheet = gc.open_by_key(BOT_SPREADSHEET_ID).sheet1
        main_worksheet = gc.open_by_key(MAIN_SPREADSHEET_ID).worksheet("Julho")
    except Exception as e:
        logging.error(f"ERRO CRÍTICO ao abrir planilhas: {e}"); return

    while True:
        try:
            logging.info("Auditoria iniciada...")
            main_df = pd.DataFrame(main_worksheet.get_all_records())
            
            if main_df.empty:
                await asyncio.sleep(1200)
                continue

            main_df['UnidadeNum'] = pd.to_numeric(main_df['Unidade'].astype(str).str.replace(',', '.'), errors='coerce')
            
            error_rows = main_df[main_df['UnidadeNum'].isnull() | (main_df['UnidadeNum'] == 100.0)]

            if not error_rows.empty:
                logging.warning(f"Encontradas {len(error_rows)} linhas com potenciais erros para corrigir.")
                for index, row in error_rows.iterrows():
                    await correct_bet_data(main_worksheet, bot_worksheet, row)
                    await asyncio.sleep(30)
            else:
                logging.info("Nenhum erro óbvio encontrado na auditoria.")

            logging.info("Auditoria concluída. Próxima verificação em 20 minutos.")
            await asyncio.sleep(1200)

        except KeyboardInterrupt:
            logging.info("Guardião Corretor encerrando o turno."); break
        except Exception as e:
            logging.error(f"Ocorreu um erro inesperado no loop do Corretor: {e}"); await asyncio.sleep(120)

if __name__ == '__main__':
    asyncio.run(main())
