# test_api.py (Versão de Diagnóstico)

import sys
import requests
from dotenv import load_dotenv
import os
import json

# Adiciona a pasta raiz ao path para que possamos importar de 'app'
sys.path.insert(0, '.')

print("--- Iniciando teste de diagnóstico na API-Football ---")

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()
API_FOOTBALL_KEY = os.getenv('API_FOOTBALL_KEY')

if not API_FOOTBALL_KEY:
    print("\n❌ ERRO CRÍTICO: A variável API_FOOTBALL_KEY não foi encontrada no seu arquivo .env!")
else:
    API_URL = "https://v3.football.api-sports.io/teams"
    HEADERS = {
        'x-rapidapi-host': "v3.football.api-sports.io",
        'x-rapidapi-key': API_FOOTBALL_KEY
    }
    PARAMS = {'name': 'Real Madrid'}

    try:
        print(f"Enviando requisição para a API com a chave: ...{API_FOOTBALL_KEY[-4:]}")
        response = requests.get(API_URL, headers=HEADERS, params=PARAMS)
        
        print(f"\nStatus da Resposta: {response.status_code}")
        print("--- Conteúdo da Resposta da API ---")
        # Imprime a resposta formatada para fácil leitura
        try:
            print(json.dumps(response.json(), indent=2))
        except json.JSONDecodeError:
            print(response.text)
        print("------------------------------------")

        if response.status_code == 200 and response.json().get('results', 0) > 0:
            print("\n✅ SUCESSO! A conexão e a busca funcionaram!")
        else:
            print("\n❌ FALHA! A API respondeu, mas não retornou resultados. Verifique as mensagens de erro na resposta acima. A causa mais comum é não ter se 'inscrito' no plano gratuito para o esporte 'Football' no painel da API-Football.")

    except Exception as e:
        print(f"\n❌ ERRO FATAL na requisição: {e}")