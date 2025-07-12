# monitoramento/api_football_handler.py
import requests
import logging
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import config

API_URL = "https://v3.football.api-sports.io"
HEADERS = {
    'x-rapidapi-host': "v3.football.api-sports.io",
    'x-rapidapi-key': config.API_FOOTBALL_KEY
}

def find_fixture_id(team1, team2, season):
    if not config.API_FOOTBALL_KEY: return None
    try:
        logging.info(f"API: Buscando partida: {team1} vs {team2}...")
        team_response = requests.get(f"{API_URL}/teams", headers=HEADERS, params={'name': team1})
        team_response.raise_for_status()
        team_data = team_response.json()
        if team_data.get('results', 0) == 0: return None
        team_id = team_data['response'][0]['team']['id']

        fixtures_response = requests.get(f"{API_URL}/fixtures", headers=HEADERS, params={'team': team_id, 'season': season})
        fixtures_response.raise_for_status()
        fixtures_data = fixtures_response.json()

        for fixture in fixtures_data.get('response', []):
            away_team_name = fixture['teams']['away']['name']
            if team2.lower() in away_team_name.lower():
                if fixture['fixture']['status']['short'] in ['FT', 'AET', 'PEN']:
                    return fixture['fixture']['id']
        return None
    except Exception as e:
        logging.error(f"API: Erro ao buscar fixture ID: {e}"); return None

def get_fixture_statistics(fixture_id):
    if not config.API_FOOTBALL_KEY: return None
    try:
        logging.info(f"API: Buscando estatísticas para a partida ID: {fixture_id}...")
        response = requests.get(f"{API_URL}/fixtures/statistics", headers=HEADERS, params={'fixture': fixture_id})
        response.raise_for_status()
        data = response.json()
        if data.get('results', 0) > 0: return data['response']
        return None
    except Exception as e:
        logging.error(f"API: Erro ao buscar estatísticas: {e}"); return None
