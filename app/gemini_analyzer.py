# app/gemini_analyzer.py - v14.1 (Mestre Detetive)

import asyncio
import json
import logging
from datetime import datetime
import google.generativeai as genai
from . import config

# (A função run_gemini_request permanece a mesma)
async def run_gemini_request(prompt, message_text, image_path, channel_name):
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    today_date = datetime.now().strftime('%d/%m/%Y')
    final_prompt = prompt.replace("{today_date}", today_date).replace("{message_text}", message_text).replace("{channel_name}", channel_name)
    content_to_send = [final_prompt]
    if image_path:
        loop = asyncio.get_running_loop()
        image_part = await loop.run_in_executor(None, lambda: genai.upload_file(image_path))
        content_to_send.append(image_part)
    response = await model.generate_content_async(content_to_send, request_options={"timeout": 120})
    logging.info(f"--- RESPOSTA BRUTA DA IA ---\n{response.text}\n--------------------------")
    clean_text = response.text.strip().replace('\u00a0', ' ')
    start_char, end_char = ('[', ']') if '[' in clean_text else ('{', '}')
    try:
        start_index = clean_text.find(start_char); end_index = clean_text.rfind(end_char) + 1
        if start_index != -1 and end_index != 0:
            json_str = clean_text[start_index:end_index]
            return json.loads(json_str)
        return None
    except Exception as e:
        logging.error(f"Erro ao limpar ou decodificar JSON: {e}"); return None

# --- PROMPTS DOS ESPECIALISTAS (VERSÃO FINALÍSSIMA) ---
PROMPT_CLASSIFIER = """
Você é um Classificador Mestre. Sua tarefa é analisar a mensagem e seguir uma árvore de decisão para determinar o tipo de aposta. Sua única resposta deve ser um JSON: {"bet_type": "VALOR"}.

**ÁRVORE DE DECISÃO:**
1.  **É LIXO?** O propósito é um resumo de resultados (com muitos ✅/❌), um comentário, meme, ou um texto curto e ambíguo SEM imagem (provavelmente um anúncio)? - Se sim, responda `{"bet_type": "TRASH"}`.
2.  **É UMA ESCADA (LADDER)?** Mostra o mesmo mercado/jogador com linhas crescentes (ex: Chutes 2+, 3+, 4+)? - Se sim, responda `{"bet_type": "LADDER"}`.
3.  **É UM CRIAR APOSTA (BET BUILDER)?** Mostra múltiplas seleções diferentes para o MESMO JOGO, combinadas em uma odd final? - Se sim, responda `{"bet_type": "BET_BUILDER"}`.
4.  **É UMA LISTA DE SIMPLES (MULTI_SIMPLE)?** Mostra uma lista de apostas para JOGOS DIFERENTES? - Se sim, responda `{"bet_type": "MULTI_SIMPLE"}`.
5.  **SE NENHUM DOS ANTERIORES,** é uma aposta única e direta? - Se sim, responda `{"bet_type": "SIMPLE"}`.

NÃO responda nada além do JSON.
Conteúdo para análise:
Texto: "{message_text}"
"""

# MANUAL DE REGRAS MESTRE PARA TODOS OS EXTRATORES (v. Final)
EXTRACTOR_RULES = """
CADA JSON DEVE TER TODAS as chaves: "is_bet", "dia_do_mes", "tipster", "casa_de_apostas", "tipo_de_aposta", "competicao", "jogos", "descricao_da_aposta", "entrada", "live_ou_pre_live", "esporte", "odd", "unidade".
REGRAS DE DETETIVE:
- `tipster`: PRIORIDADE MÁXIMA - Se o texto indicar "Forwarded from", use o nome do canal original. Senão, use `{channel_name}`.
- `unidade`: PRIORIDADE MÁXIMA - DEVE ser um número float. Procure por '%' ou 'u' em qualquer parte do texto. Exemplos: "3% - Limite R$200" -> 3.0. "Vale 1.75%" -> 1.75.
- `competicao`: Use seu conhecimento para inferir a liga (Ex: "Real Madrid vs Borussia" -> "UEFA Champions League"). Se não souber, use "N/A".
- `casa_de_apostas`: Procure no texto ou no link. Se a imagem tiver a interface da Betano ou Superbet, use esse nome. Padrão: "N/A".
- `jogos`: DEVE ser um texto plano "Time A vs Time B".
- PADRÕES: `dia_do_mes`={today_date}, `live_ou_pre_live`="PRÉ LIVE", `is_bet`=`true`.
- SAÍDA: APENAS a lista JSON pura.
"""

PROMPT_SIMPLE_EXTRACTOR = f"Você é um especialista em extrair UMA APOSTA SIMPLES. Retorne uma LISTA com UM ÚNICO objeto JSON.\n{EXTRACTOR_RULES}\nREGRAS PARA SIMPLES:\n- `descricao_da_aposta`: O nome do mercado.\n- `entrada`: A seleção específica.\n- `tipo_de_aposta`: DEVE ser 'SIMPLES'.\nConteúdo:\nTexto: \"{{message_text}}\""
PROMPT_LADDER_EXTRACTOR = f"Você é um especialista em extrair APOSTAS EM ESCADA (LADDER). Trate cada linha da escada como um objeto JSON separado na lista.\n{EXTRACTOR_RULES}\nREGRAS PARA ESCADA:\n- `descricao_da_aposta`: O mercado base.\n- `entrada`: A linha específica (ex: '2+').\n- `tipo_de_aposta`: DEVE ser 'SIMPLES' para cada degrau.\n- Associe a unidade e odd corretas a cada linha.\nConteúdo:\nTexto: \"{{message_text}}\""
PROMPT_BET_BUILDER_EXTRACTOR = f"Você é um especialista em extrair UMA APOSTA 'CRIAR APOSTA'. Retorne uma LISTA com UM ÚNICO objeto JSON.\n{EXTRACTOR_RULES}\nREGRAS PARA CRIAR APOSTA:\n- `tipo_de_aposta`: DEVE ser 'CRIAR APOSTA'.\n- `descricao_da_aposta`: Um resumo dos mercados.\n- `entrada`: A combinação das seleções.\n- `odd`: A odd final combinada.\nConteúdo:\nTexto: \"{{message_text}}\""
PROMPT_MULTI_SIMPLE_EXTRACTOR = f"Você é um especialista em extrair VÁRIAS APOSTAS SIMPLES de uma lista. Trate cada aposta como um objeto JSON separado.\n{EXTRACTOR_RULES}\nREGRAS PARA MULTI-SIMPLES:\n- `tipo_de_aposta`: DEVE ser 'SIMPLES' para cada item, a menos que esteja escrito 'Múltipla'.\nConteúdo:\nTexto: \"{{message_text}}\""

PROMPT_MAP = {
    'SIMPLE': PROMPT_SIMPLE_EXTRACTOR,
    'LADDER': PROMPT_LADDER_EXTRACTOR,
    'BET_BUILDER': PROMPT_BET_BUILDER_EXTRACTOR,
    'MULTI_SIMPLE': PROMPT_MULTI_SIMPLE_EXTRACTOR
}