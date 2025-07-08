# monitor.py - O Guardião da Planilha (v3.0 - com Detecção de Edição)

import gspread
import pandas as pd
import logging
import time
import sqlite3
import hashlib
import sys
from dotenv import load_dotenv

# Garante que o Python encontre nossos outros módulos
sys.path.insert(0, '.')
from app import config

# --- CONFIGURAÇÃO DO LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - GUARDIÃO - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("monitor.log", mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def get_gspread_client():
    """Retorna um cliente gspread autenticado."""
    if config.GOOGLE_CREDENTIALS_DICT:
        return gspread.service_account_from_dict(config.GOOGLE_CREDENTIALS_DICT)
    else:
        # Garante que o config tenha o caminho do arquivo para uso local
        return gspread.service_account(filename=getattr(config, 'CREDENTIALS_FILE_PATH', 'credentials.json'))

def create_fingerprint_from_sheet(row):
    """Cria um identificador único para uma aposta a partir de uma LINHA da planilha."""
    jogos = str(row.get('Jogos', ''))
    descricao = str(row.get('Descrição da Aposta', ''))
    entrada = str(row.get('Entrada', ''))
    casa = str(row.get('Casa de Apostas', '')).lower()
    
    data_string = f"{jogos}_{descricao}_{entrada}_{casa}".lower()
    return hashlib.md5(data_string.encode()).hexdigest()

def fetch_spreadsheet_data():
    """Busca todos os dados da planilha e os retorna como um DataFrame do Pandas."""
    try:
        logging.info("Buscando dados da planilha...")
        client = get_gspread_client()
        spreadsheet = client.open_by_key(config.SPREADSHEET_ID)
        worksheet = spreadsheet.sheet1
        
        data = worksheet.get_all_records()
        if not data:
            logging.warning("Planilha está vazia.")
            return pd.DataFrame()

        df = pd.DataFrame(data)
        df['fingerprint'] = df.apply(create_fingerprint_from_sheet, axis=1)
        
        logging.info(f"✅ Sucesso! {len(df)} linhas lidas e processadas.")
        return df
    except Exception as e:
        logging.error(f"❌ Erro ao buscar dados da planilha: {e}")
        return None

def sync_db_with_sheet(fingerprint, new_unidade_str):
    """Atualiza a unidade de uma aposta na memória do bot."""
    try:
        # Converte a unidade para float, lidando com vírgulas
        new_unidade = float(str(new_unidade_str).replace(',', '.'))

        conn = sqlite3.connect(config.DB_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE apostas_processadas SET unidade = ? WHERE fingerprint = ?", (new_unidade, fingerprint))
        conn.commit()
        
        if cursor.rowcount > 0:
            logging.warning(f"📝 Edição detectada! Unidade da aposta {fingerprint[:6]}... sincronizada para {new_unidade} no DB.")
        
        conn.close()
    except (ValueError, TypeError):
        logging.error(f"Erro ao converter a nova unidade '{new_unidade_str}' para número. Sincronização pulada.")
    except Exception as e:
        logging.error(f"❌ Erro ao sincronizar edição no banco de dados: {e}")

def remove_bet_from_db(fingerprint):
    """Remove uma aposta da memória (banco de dados) pelo seu fingerprint."""
    try:
        conn = sqlite3.connect(config.DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM apostas_processadas WHERE fingerprint = ?", (fingerprint,))
        conn.commit()
        
        if cursor.rowcount > 0:
            logging.warning(f"🗑️ Exclusão detectada! Aposta com fingerprint {fingerprint[:6]}... removida da memória do bot.")
        
        conn.close()
    except Exception as e:
        logging.error(f"❌ Erro ao remover aposta do banco de dados: {e}")


def main():
    """Função principal do loop de monitoramento."""
    logging.info("🤖 Guardião da Planilha iniciando seu turno...")
    
    # Carrega a função de inicialização do DB para garantir que a tabela exista
    from app.database import initialize_database
    initialize_database()

    dados_antigos = fetch_spreadsheet_data()
    
    if dados_antigos is None:
        logging.error("Não foi possível buscar os dados iniciais. Encerrando o monitor.")
        return

    logging.info("Vigilância iniciada. Verificando por mudanças a cada 60 segundos...")
    
    while True:
        try:
            time.sleep(60)
            
            dados_atuais = fetch_spreadsheet_data()
            if dados_atuais is None: continue

            # Lógica para Detecção de Exclusão
            fingerprints_antigos = set(dados_antigos['fingerprint'])
            fingerprints_atuais = set(dados_atuais['fingerprint'])
            apostas_removidas = fingerprints_antigos - fingerprints_atuais
            
            if apostas_removidas:
                for fp in apostas_removidas: remove_bet_from_db(fp)

            # Lógica para Detecção de Edição
            # Merge para encontrar linhas correspondentes e comparar a coluna 'Unidade'
            if not dados_antigos.empty and not dados_atuais.empty:
                merged_df = pd.merge(dados_antigos, dados_atuais, on='fingerprint', suffixes=('_antigo', '_atual'))
                # Filtra apenas as linhas onde a unidade mudou
                mudancas = merged_df[merged_df['Unidade_antigo'] != merged_df['Unidade_atual']]
                
                for index, row in mudancas.iterrows():
                    sync_db_with_sheet(row['fingerprint'], row['Unidade_atual'])

            dados_antigos = dados_atuais.copy()

        except KeyboardInterrupt:
            logging.info("Guardião encerrando o turno."); break
        except Exception as e:
            logging.error(f"Ocorreu um erro inesperado no loop do guardião: {e}"); time.sleep(120)

if __name__ == '__main__':
    main()