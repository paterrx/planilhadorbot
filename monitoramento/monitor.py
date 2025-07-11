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
from app.sheets import get_gspread_client
from monitoramento import api_football_handler
from monitoramento import juiz_analyzer

# --- CONFIGURAÇÃO ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - GUARDIÃO - %(levelname)s - %(message)s', stream=sys.stdout)
MAIN_SPREADSHEET_ID = "1zmv8q_XhIeRSXtM4SPu7uXyOU7bfKwt1_I2_oncafCc"
BOT_SPREADSHEET_ID = config.SPREADSHEET_ID # Usa o mesmo ID do bot principal

def get_existing_games(worksheet):
    """Pega a lista de jogos já presentes na planilha principal para evitar duplicatas."""
    try:
        # Pega as colunas 'Jogos' e 'Entrada' para criar um identificador único
        col_data = worksheet.get_all_values()
        if len(col_data) < 1: return set()
        
        # Assumindo que 'Jogos' é a coluna F (índice 5) e 'Entrada' é a H (índice 7)
        return set(f"{row[5]}_{row[7]}" for row in col_data[1:]) # Pula o cabeçalho
    except Exception as e:
        logging.error(f"Erro ao buscar jogos existentes na planilha principal: {e}")
        return set()

async def copy_new_bets(bot_worksheet, main_worksheet):
    """Copia novas apostas da planilha do bot para a planilha principal."""
    logging.info("Iniciando verificação de novas apostas para copiar...")
    try:
        bot_records = bot_worksheet.get_all_records()
        if not bot_records:
            logging.info("Nenhuma aposta na planilha do bot para copiar."); return

        bot_df = pd.DataFrame(bot_records)
        existing_identifiers = get_existing_games(main_worksheet)
        
        new_bets = []
        for index, row in bot_df.iterrows():
            identifier = f"{row.get('Jogos')}_{row.get('Entrada')}"
            if identifier not in existing_identifiers:
                # Prepara a linha para inserção, garantindo a ordem correta das colunas
                # da planilha principal. Adiciona colunas vazias se necessário.
                new_row_data = [
                    row.get('Dia do Mês', ''), row.get('Tipster', ''), row.get('Casa de Apostas', ''),
                    row.get('Tipo de Aposta', ''), row.get('Competição', ''), row.get('Jogos', ''),
                    row.get('Descrição da Aposta', ''), row.get('Entrada', ''), row.get('Live ou Pré-Live', ''),
                    row.get('Esporte', ''), row.get('Odd', ''), row.get('Unidade', ''),
                    '', '', '' # Colunas M, N, O (Resultado, Situação, Lucro)
                ]
                new_bets.append(new_row_data)
                existing_identifiers.add(identifier) # Evita copiar duplicatas na mesma execução

        if new_bets:
            logging.warning(f"Encontradas {len(new_bets)} novas apostas. Copiando para a planilha principal...")
            main_worksheet.append_rows(new_bets, value_input_option='USER_ENTERED')
            logging.info(f"✅ {len(new_bets)} novas apostas copiadas com sucesso!")
        else:
            logging.info("Nenhuma aposta nova encontrada para copiar.")

    except Exception as e:
        logging.error(f"Erro durante o processo de cópia de apostas: {e}", exc_info=True)


async def check_and_resolve_bets(worksheet):
    """Verifica apostas pendentes na planilha principal e tenta resolvê-las."""
    logging.info("Iniciando verificação de apostas pendentes para resolver...")
    try:
        all_records = worksheet.get_all_records()
        if not all_records:
            logging.info("Planilha principal vazia. Nenhuma aposta para resolver.")
            return

        df = pd.DataFrame(all_records)
        if 'Situação' not in df.columns or 'Resultado' not in df.columns:
            logging.warning("Colunas 'Situação' ou 'Resultado' não encontradas. Pulando resolução.")
            return

        pending_bets = df[df['Situação'] == ''].copy()
        if pending_bets.empty:
            logging.info("Nenhuma aposta com situação vazia para resolver.")
            return

        logging.warning(f"Encontradas {len(pending_bets)} apostas pendentes. Iniciando resolução...")
        for index, bet in pending_bets.iterrows():
            sheet_row_index = index + 2
            try:
                times_str = bet.get('Jogos', '')
                if not times_str or 'vs' not in str(times_str).lower():
                    logging.warning(f"Jogos mal formatados na linha {sheet_row_index}: '{times_str}'. Marcando como 'Pendente'.")
                    worksheet.update_cell(sheet_row_index, 14, 'Pendente') # Coluna N = Situação
                    continue
                
                time1, time2 = [t.strip() for t in times_str.split('vs')]
                season = str(datetime.now().year)

                fixture_id = api_football_handler.find_fixture_id(time1, time2, season)
                if not fixture_id:
                    logging.info(f"Partida para '{times_str}' ainda não finalizada ou não encontrada.")
                    continue

                statistics = api_football_handler.get_fixture_statistics(fixture_id)
                if not statistics:
                    logging.warning(f"Estatísticas não disponíveis para a partida ID {fixture_id}.")
                    worksheet.update_cell(sheet_row_index, 14, 'Pendente')
                    continue
                
                status = await juiz_analyzer.resolve_bet_with_gemini(bet, statistics)
                if status in ['Green', 'Red', 'Pendente']:
                    worksheet.update_cell(sheet_row_index, 14, status) # Coluna N = Situação
                    logging.info(f"Aposta na linha {sheet_row_index} ('{times_str}') atualizada para {status}.")
                
                await asyncio.sleep(12) # Pausa para não exceder o limite da API-Football (5 req/min)

            except Exception as e:
                logging.error(f"Erro ao resolver aposta da linha {sheet_row_index}: {e}")
                worksheet.update_cell(sheet_row_index, 14, 'Erro')

    except Exception as e:
        logging.error(f"Erro ao buscar ou processar apostas pendentes: {e}", exc_info=True)


async def main():
    logging.info("🤖 Guardião 'Copiador e Juiz' iniciando seu turno...")
    
    try:
        gc = get_gspread_client()
        bot_worksheet = gc.open_by_key(BOT_SPREADSHEET_ID).sheet1
        main_worksheet = gc.open_by_key(MAIN_SPREADSHEET_ID).worksheet("Julho")
    except gspread.exceptions.WorksheetNotFound:
        logging.error("ERRO CRÍTICO: A aba 'Julho' não foi encontrada na planilha principal. Encerrando.")
        return
    except Exception as e:
        logging.error(f"ERRO CRÍTICO ao conectar-se às planilhas: {e}", exc_info=True)
        return

    while True:
        try:
            # Missão 1: Copiar novas apostas
            await copy_new_bets(bot_worksheet, main_worksheet)
            
            # Pausa para garantir que a planilha principal seja atualizada
            await asyncio.sleep(10)

            # Missão 2: Resolver apostas pendentes
            await check_and_resolve_bets(main_worksheet)
            
            logging.info("Ciclo de vigilância concluído. Próxima verificação em 15 minutos.")
            await asyncio.sleep(900)

        except KeyboardInterrupt:
            logging.info("Guardião encerrando o turno."); break
        except Exception as e:
            logging.error(f"Ocorreu um erro inesperado no loop do guardião: {e}", exc_info=True)
            await asyncio.sleep(120)

if __name__ == '__main__':
    asyncio.run(main())
