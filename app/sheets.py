# app/sheets.py
import gspread
import re
import logging
from datetime import datetime
from . import config

def get_gspread_client():
    if config.GOOGLE_CREDENTIALS_DICT:
        return gspread.service_account_from_dict(config.GOOGLE_CREDENTIALS_DICT)
    else:
        return gspread.service_account(filename=config.CREDENTIALS_FILE_PATH)

def log_to_trash_sheet(data_dict):
    """Registra uma instrução importante na aba 'Registro TRASH'."""
    try:
        logging.warning(f"LIXO IMPORTANTE DETECTADO: {data_dict.get('instruction')}")
        gc = get_gspread_client()
        sh = gc.open_by_key(config.SPREADSHEET_ID)
        worksheet = sh.worksheet("Registro TRASH")

        row_to_insert = [
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            data_dict.get('tipster', ''),
            data_dict.get('instruction', ''),
            data_dict.get('game_reference', ''),
            data_dict.get('original_text', '')
        ]
        worksheet.append_row(row_to_insert, value_input_option='USER_ENTERED')
        logging.info("✅ Instrução importante registrada na aba 'Registro TRASH'.")
    except gspread.exceptions.WorksheetNotFound:
        logging.error("ERRO: A aba 'Registro TRASH' não foi encontrada na sua planilha. Por favor, crie-a.")
    except Exception as e:
        logging.error(f"❌ Erro ao registrar na aba TRASH: {e}")

def write_to_sheet(data_dict):
    try:
        logging.info("Conectando à planilha...")
        gc = get_gspread_client(); sh = gc.open_by_key(config.SPREADSHEET_ID); worksheet = sh.sheet1
        jogos = data_dict.get('jogos', '');
        if not isinstance(jogos, str): jogos = str(jogos)
        descricao = data_dict.get('descricao_da_aposta') or data_dict.get('descricao_da_posta', '')
        unidade = data_dict.get('unidade') or data_dict.get('stake')
        entrada = data_dict.get('entrada', '')
        if isinstance(entrada, str) and entrada.startswith(('+', '-', '=', '@')):
            entrada = f"'{entrada}"
        def get_correct_casing(value, context_list):
            if not value or not isinstance(value, str): return value
            for item in context_list:
                if item.lower() in value.lower(): return item
            return value
        casa_corrigida = get_correct_casing(data_dict.get('casa_de_apostas', ''), config.LIST_CASAS)
        row_to_insert = [
            data_dict.get('dia_do_mes') or datetime.now().strftime('%d/%m/%Y'), 
            data_dict.get('tipster', ''),
            casa_corrigida, data_dict.get('tipo_de_aposta', 'SIMPLES'),
            data_dict.get('competicao', ''), jogos,
            descricao, entrada,
            data_dict.get('live_ou_pre_live', 'PRÉ LIVE'), data_dict.get('esporte', ''),
            str(data_dict.get('odd', '')).replace('.', ','),
            str(unidade if unidade is not None else '').replace('.', ','), '', '',
        ]
        result = worksheet.append_row(row_to_insert, value_input_option='USER_ENTERED')
        updated_range = result['updates']['updatedRange']
        match = re.search(r'A(\d+)', updated_range)
        if not match: raise ValueError("Não foi possível determinar o número da linha.")
        row_number = int(match.group(1))
        logging.info(f"✅ Aposta planilhada com sucesso na linha {row_number}!")
        return row_number
    except Exception as e:
        logging.error(f"❌ Erro ao escrever na planilha: {e}"); return None

def update_stake_in_sheet(row, new_unidade):
    try:
        logging.info(f"Atualizando unidade na linha {row} para {new_unidade}...")
        gc = get_gspread_client(); sh = gc.open_by_key(config.SPREADSHEET_ID); worksheet = sh.sheet1
        worksheet.update_cell(row, config.STAKE_COLUMN_NUMBER, str(new_unidade).replace('.', ','))
        logging.info("✅ Unidade atualizada com sucesso na planilha!"); return True
    except Exception as e:
        logging.error(f"❌ Erro ao atualizar unidade na planilha: {e}"); return False