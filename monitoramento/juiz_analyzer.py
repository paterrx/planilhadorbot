import logging
import json
import sys
import os
import asyncio

# Adiciona a pasta raiz ao path para que possamos importar de 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importa a função de request do nosso bot principal
from app.gemini_analyzer import run_gemini_request

# --- PROMPT DO JUIZ ---
PROMPT_BET_RESOLVER = """
Você é um Juiz de apostas de elite. Sua única tarefa é receber os dados de uma aposta e os resultados estatísticos de uma partida e determinar se a aposta foi "Green" ou "Red".
Responda com um único JSON: {"status": "VALOR"}. Onde VALOR pode ser "Green", "Red" ou "Pendente".

**DADOS DA APOSTA:**
- Mercado: `{descricao_da_aposta}`
- Seleção: `{entrada}`

**ESTATÍSTICAS FINAIS DO JOGO:**
```json
{extra_data}
```  
Analise os dados com lógica rigorosa e determine o resultado.

Exemplo 1: Se o mercado é "Total de Chutes" e a seleção é "Mais de 9.5", e nas estatísticas o total de chutes ("Total Shots") de ambos os times somados foi 11, o status é "Green". Se foi 9, é "Red".

Exemplo 2: Se o mercado é "Jogador - Faltas Cometidas" e a seleção é "Fabian Ruiz - Mais de 0.5", você deve olhar as estatísticas do jogador "Fabian Ruiz" e verificar o valor de "Fouls Committed". Se for 1 ou mais, é "Green". Se for 0, é "Red".

Se a estatística necessária não estiver presente no JSON, retorne {"status": "Pendente"}.
"""

async def resolve_bet_with_gemini(bet, statistics_json):
    """
    Usa a IA 'Juiz' para determinar o resultado de uma aposta e retorna o status.
    """
    try:
        # Pega os dados da aposta a partir do objeto 'bet' (que é uma linha do DataFrame)
        descricao = bet.get('Descrição da Aposta', '')
        entrada = bet.get('Entrada', '')

        logging.info(f"Enviando para o Juiz: Mercado='{descricao}', Entrada='{entrada}'")
        
        # Prepara os dados para o prompt do Juiz
        extra_data = json.dumps(statistics_json, ensure_ascii=False, indent=2)
        
        prompt = PROMPT_BET_RESOLVER.format(
            descricao_da_aposta=descricao,
            entrada=entrada,
            extra_data=extra_data
        )
        
        # Chama a função de request genérica, passando o prompt do Juiz
        result_json = await run_gemini_request(prompt, "Resolver esta aposta.", None, "Juiz")

        if isinstance(result_json, dict) and result_json.get('status') in ['Green', 'Red', 'Pendente']:
            status = result_json.get('status')
            logging.warning(f"✅ Veredito do Juiz: {status}!")
            return status
        else:
            logging.error(
                f"Juiz não conseguiu determinar o resultado para a aposta: {descricao} | {entrada}"
            )
            return "Pendente"

    except Exception as e:
        logging.error(f"❌ Erro crítico ao chamar o Juiz: {e}")
        return "Pendente"
