# app/api_football_handler.py

import requests
import logging
from . import config

API_URL = "https://v3.football.api-sports.io"
HEADERS = {
    'x-rapidapi-host': "v3.football.api-sports.io",
    'x-rapidapi-key': config.API_FOOTBALL_KEY
}

def find_match(team_name, season, league_id=None):
    """Busca por uma partida específica na API-Football."""
    if not config.API_FOOTBALL_KEY:
        logging.error("Chave da API-Football não configurada.")
        return None

    # O parâmetro correto para busca de time é 'name'
    team_params = {'name': team_name}
        
    try:
        logging.info(f"Buscando o time '{team_name}' na API-Football...")
        response = requests.get(f"{API_URL}/teams", headers=HEADERS, params=team_params)
        response.raise_for_status() 
        data = response.json()
        
        # Adiciona um log para vermos a resposta da busca do time
        logging.info(f"Resposta da busca de time: {data}")

        if data.get('results', 0) > 0:
            team_id = data['response'][0]['team']['id']
            logging.info(f"Time '{team_name}' encontrado com ID: {team_id}. Buscando jogos da temporada {season}...")
            
            fixtures_params = {'team': team_id, 'season': season}
            if league_id:
                fixtures_params['league'] = league_id
            
            fixtures_response = requests.get(f"{API_URL}/fixtures", headers=HEADERS, params=fixtures_params)
            fixtures_response.raise_for_status()
            fixtures_data = fixtures_response.json()
            
            return fixtures_data['response']

        else:
            logging.warning(f"Nenhum time encontrado para a busca: '{team_name}'")
            return None

    except requests.exceptions.RequestException as e:
        logging.error(f"Erro na requisição para a API-Football: {e}")
        # Loga a resposta da API em caso de erro para facilitar o debug
        if e.response:
            logging.error(f"Resposta da API (status {e.response.status_code}): {e.response.text}")
        return None