# monitoramento/api_football_handler.py

import requests
import logging
import sys
import os
import time

# Adiciona a pasta raiz ao path para que possamos importar de 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import config

API_URL = "https://v3.football.api-sports.io"
HEADERS = {
    'x-rapidapi-host': "v3.football.api-sports.io",
    'x-rapidapi-key': config.API_FOOTBALL_KEY
}

def find_fixture_id(team1, team2, season):
    """Encontra o ID de uma partida finalizada entre dois times."""
    if not config.API_FOOTBALL_KEY: 
        logging.error("API-FOOTBALL: Chave não configurada.")
        return None
    try:
        logging.info(f"API-FOOTBALL: Buscando partida: {team1} vs {team2}...")
        
        # Procura pelo Time 1 para obter o ID
        team_response = requests.get(f"{API_URL}/teams", headers=HEADERS, params={'name': team1})
        team_response.raise_for_status()
        team_data = team_response.json()
        
        if team_data.get('results', 0) == 0:
            logging.warning(f"API-FOOTBALL: Time '{team1}' não encontrado.")
            return None
        
        team_id = team_data['response'][0]['team']['id']

        # Usa o ID do Time 1 para buscar todos os seus jogos na temporada
        fixtures_response = requests.get(f"{API_URL}/fixtures", headers=HEADERS, params={'team': team_id, 'season': season})
        fixtures_response.raise_for_status()
        fixtures_data = fixtures_response.json()

        # Itera sobre os jogos para encontrar a correspondência exata
        for fixture in fixtures_data.get('response', []):
            home_team_name = fixture['teams']['home']['name']
            away_team_name = fixture['teams']['away']['name']
            
            # Compara os times de forma mais flexível
            if (team1.lower() in home_team_name.lower() and team2.lower() in away_team_name.lower()) or \
               (team2.lower() in home_team_name.lower() and team1.lower() in away_team_name.lower()):
                
                # Verifica se o jogo já terminou
                if fixture['fixture']['status']['short'] in ['FT', 'AET', 'PEN']:
                    logging.info(f"API-FOOTBALL: Partida encontrada e finalizada! ID: {fixture['fixture']['id']}")
                    return fixture['fixture']['id']
        
        logging.info(f"API-FOOTBALL: Partida para '{team1} vs {team2}' não encontrada ou ainda não finalizada.")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"API-FOOTBALL: Erro na requisição ao buscar fixture: {e}")
        if e.response:
            logging.error(f"Resposta da API (status {e.response.status_code}): {e.response.text}")
        return None
    except Exception as e:
        logging.error(f"API-FOOTBALL: Erro inesperado ao buscar fixture ID: {e}")
        return None

def get_fixture_statistics(fixture_id):
    """Busca as estatísticas detalhadas de uma partida pelo seu ID."""
    if not config.API_FOOTBALL_KEY:
        logging.error("API-FOOTBALL: Chave não configurada.")
        return None
    try:
        logging.info(f"API-FOOTBALL: Buscando estatísticas para a partida ID: {fixture_id}...")
        response = requests.get(f"{API_URL}/fixtures/statistics", headers=HEADERS, params={'fixture': fixture_id})
        response.raise_for_status()
        data = response.json()
        if data.get('results', 0) > 0:
            return data['response'] # Retorna a lista de estatísticas dos dois times
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"API-FOOTBALL: Erro na requisição de estatísticas: {e}")
        if e.response:
            logging.error(f"Resposta da API (status {e.response.status_code}): {e.response.text}")
        return None
    except Exception as e:
        logging.error(f"API-FOOTBALL: Erro inesperado ao buscar estatísticas: {e}")
        return None
