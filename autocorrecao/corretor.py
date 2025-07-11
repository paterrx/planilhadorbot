# autocorrecao/corretor.py

import logging
import time
import sys
import os
import asyncio
import gspread
import pandas as pd
from datetime import datetime

# Adiciona a pasta raiz ao path para que os imports de 'app' funcionem
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import config
from app.database import initialize_database, check_db_for_bet, create_fingerprint, update_stake_in_db
from app.sheets import get_gspread_client, update_stake_in_sheet
from app.gemini_analyzer import run_gemini_request, PROMPT_ERROR_DETECTOR

# --- CONFIGURAÇÃO ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - CORRETOR - %(levelname)s - %(message)s', stream=sys.stdout)

# ID da sua planilha do bot, onde a mensagem original está implícita nos dados
BOT_SPREADSHEET_ID = "1DrsPb6_tlYbeVs8d2lCoMiWBBukqtb1AxXKsioJSW98" 

async def correct_bet_data(main_sheet_row, bot_sheet_row_data):
    """Usa a IA Detetive para corrigir os dados e atualiza a planilha e o DB."""
    try:
        # Pega a linha completa do bot para dar contexto à IA
        original_context = str(bot_sheet_row_data)
        
        logging.info(f"Enviando para o Detetive de Erros. Contexto: {original_context[:100]}...")
        
        correction_result = await run_gemini_request(
            PROMPT_ERROR_DETECTOR,
            original_context, # Usa a linha do bot como o 'message_text' para o prompt
            None, # Sem imagem
            "ErrorDetector",
            extra_data=str(main_sheet_row.to_dict())
        )

        if correction_result and 'correcao_sugerida' in correction_result:
            corrected_value = correction_result['correcao_sugerida']
            if corrected_value is not None:
                logging.warning(f"✅ CORREÇÃO SUGERIDA: {corrected_value}. Aplicando...")
                
                # A lógica aqui assume que o principal erro a ser corrigido é a 'unidade'
                # Atualiza a planilha principal
                # update_stake_in_sheet(main_sheet_row.name + 2, corrected_value) # +2 para ajustar o índice do pandas
                
                # Atualiza o banco de dados
                fingerprint = create_fingerprint(main_sheet_row.to_dict())
                update_stake_in_db(fingerprint, corrected_value)
                return True
    except Exception as e:
        logging.error(f"Erro no processo de correção: {e}")
    return False

async def main():
    logging.info("🤖 Guardião 'Corretor' iniciando seu turno de auditoria...")
    initialize_database()
    
    try:
        gc = get_gspread_client()
        bot_worksheet = gc.open_by_key(BOT_SPREADSHEET_ID).sheet1
        # Assumindo que a planilha principal é a mesma para este exemplo, mas poderia ser diferente
        main_worksheet = gc.open_by_key(BOT_SPREADSHEET_ID).sheet1 
    except Exception as e:
        logging.error(f"ERRO CRÍTICO ao abrir planilhas: {e}"); return

    while True:
        try:
            logging.info("Auditoria iniciada...")
            bot_df = pd.DataFrame(bot_worksheet.get_all_records())
            
            # Identifica linhas com erros óbvios (ex: unidade vazia ou 100)
            # A coluna 'Unidade' pode vir como string, então convertemos para numérico
            bot_df['UnidadeNum'] = pd.to_numeric(bot_df['Unidade'].str.replace(',', '.'), errors='coerce')
            
            error_rows = bot_df[bot_df['UnidadeNum'].isnull() | (bot_df['UnidadeNum'] == 100.0)]

            if not error_rows.empty:
                logging.warning(f"Encontradas {len(error_rows)} linhas com potenciais erros para corrigir.")
                for index, row in error_rows.iterrows():
                    # Para cada linha com erro, chama o processo de correção
                    await correct_bet_data(row, row.to_dict())
                    await asyncio.sleep(20) # Delay para não sobrecarregar a API do Gemini
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