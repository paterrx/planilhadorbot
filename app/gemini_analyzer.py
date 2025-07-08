# app/gemini_analyzer.py

# (código idêntico até os prompts)
import asyncio, json, logging
from datetime import datetime
import google.generativeai as genai
from . import config

async def run_gemini_request(prompt, message_text, image_path, channel_name):
    # ...
# (a função run_gemini_request permanece a mesma)
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

PROMPT_CLASSIFIER = """
Você é um Classificador Mestre. Sua tarefa é analisar o propósito da mensagem. Responda com um JSON: {"bet_type": "VALOR"}.
- Se for um resumo de resultados, balanço, ou um comentário sobre um jogo, classifique como "TRASH".
- Se for uma recomendação de aposta nova, classifique como: "SIMPLE", "BET_BUILDER", "LADDER", ou "MULTI_SIMPLE".
Conteúdo:
Texto: "{message_text}"
"""

EXTRACTOR_RULES = """
CADA JSON DEVE TER TODAS as chaves: "is_bet", "dia_do_mes", "tipster", "casa_de_apostas", "tipo_de_aposta", "competicao", "jogos", "descricao_da_aposta", "entrada", "live_ou_pre_live", "esporte", "odd", "unidade".
REGRAS OBRIGATÓRIAS:
- `is_bet`: `true`.
- `tipster`: Se "Forwarded from", use o nome original. Senão, use `{channel_name}`.
- `dia_do_mes`: Use a data do evento. Se ausente ou "Hoje", use `{today_date}`.
- **LÓGICA DE UNIDADE:** Se houver um "Limite da aposta: R$X" e a unidade for 100% ou não especificada, a `unidade` é o valor X. Se não, procure por '%' ou 'u'. É CRÍTICO.
- `casa_de_apostas`: Procure no texto ou no link. Padrão: "N/A".
- `jogos`: DEVE ser um texto plano "Time A vs Time B".
- `live_ou_pre_live`: DEVE ser "PRÉ LIVE", a menos que o texto diga "LIVE".
- `SAÍDA`: APENAS a lista JSON pura, sem markdown.
"""

# (O resto dos prompts dos especialistas permanecem os mesmos)
PROMPT_SIMPLE_EXTRACTOR = f"..."
PROMPT_LADDER_EXTRACTOR = f"..."
PROMPT_BET_BUILDER_EXTRACTOR = f"..."
PROMPT_MULTI_SIMPLE_EXTRACTOR = f"""
Você é um especialista em extrair VÁRIAS APOSTAS SIMPLES de uma lista. Trate cada aposta da lista como um objeto JSON separado.
{EXTRACTOR_RULES}
REGRAS PARA MULTI-SIMPLES:
- `tipo_de_aposta`: DEVE ser "SIMPLES", a menos que o texto diga "Múltipla" ou "Pechincha", nesses casos use esses termos.
Conteúdo:
Texto: "{{message_text}}"
"""

PROMPT_MAP = {
    'SIMPLE': PROMPT_SIMPLE_EXTRACTOR,
    'LADDER': PROMPT_LADDER_EXTRACTOR,
    'BET_BUILDER': PROMPT_BET_BUILDER_EXTRACTOR,
    'MULTI_SIMPLE': PROMPT_MULTI_SIMPLE_EXTRACTOR
}