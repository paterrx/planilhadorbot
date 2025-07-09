# app/gemini_analyzer.py

import asyncio
import json
import logging
from datetime import datetime
import google.generativeai as genai
from . import config

async def run_gemini_request(prompt, message_text, image_path, channel_name):
    """Função genérica e robusta para fazer um request à API do Gemini."""
    try:
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
        
        start_index = clean_text.find(start_char)
        end_index = clean_text.rfind(end_char) + 1
        
        if start_index != -1 and end_index != 0:
            json_str = clean_text[start_index:end_index]
            return json.loads(json_str)
        
        return None
    except Exception as e:
        logging.error(f"❌ Erro crítico na função run_gemini_request: {e}")
        return None

# --- PROMPTS PARA O DEBATE DOS ESPECIALISTAS ---

PROMPT_SKEPTIC_CLASSIFIER = """
Você é um classificador cético e rigoroso. Sua única tarefa é determinar se a mensagem é uma **recomendação de aposta clara e acionável** ou se é apenas um comentário, aviso, análise de jogo ou relatório de resultados.
Responda com um único JSON: {"is_bet": true/false}.
- `is_bet` é `true` APENAS se a mensagem explicitamente instrui a fazer uma aposta agora, contendo mercado, odd e stake/unidade.
- `is_bet` é `false` se for um comentário (ex: "Initially, it was not clear..."), um aviso sobre uma aposta futura, um relatório de green/red, ou qualquer texto que não seja uma aposta completa e imediata.

Conteúdo para análise:
Texto: "{message_text}"
"""

PROMPT_MASTER_EXTRACTOR = """
Você é um robô extrator de dados de apostas. Sua tarefa é analisar o conteúdo (texto e imagem) e retornar uma LISTA de objetos JSON com as apostas encontradas. Se não encontrar uma aposta clara, retorne uma lista vazia `[]`.

**LÓGICAS DE ANÁLISE ESTRUTURAL:**
- **CRIAR APOSTA / REI DO PITACO:** Se múltiplas seleções do MESMO JOGO estão agrupadas (com ou sem "Pechincha"), trate como UMA ÚNICA aposta do tipo "CRIAR APOSTA".
- **ESCADA (LADDER):** Se o mesmo mercado se repete com linhas crescentes (ex: Chutes 2+, 3+, 4+), trate CADA LINHA como um objeto JSON separado na lista.
- **MÚLTIPLA SIMPLES:** Se a mensagem lista várias apostas de jogos diferentes, trate CADA UMA como um objeto JSON separado.

**MANUAL DE PREENCHIMENTO PARA CADA JSON (SEJA RIGOROSO):**
-   CADA JSON DEVE TER TODAS as chaves: "is_bet", "dia_do_mes", "tipster", "casa_de_apostas", "tipo_de_aposta", "competicao", "jogos", "descricao_da_aposta", "entrada", "live_ou_pre_live", "esporte", "odd", "unidade".
-   `is_bet`: Sempre `true`.
-   `unidade`: É CRÍTICO. DEVE ser um número float. Se houver "Limite da aposta: R$X", a unidade é X. Senão, procure por '%' ou 'u'.
-   `casa_de_apostas`: Procure no texto ou no link. Padrão: "N/A".
-   `jogos`: DEVE ser um texto plano "Time A vs Time B".
-   `tipster`: Se "Forwarded from", use o nome do canal original. Senão, use `{channel_name}`.

**SAÍDA OBRIGATÓRIA:** APENAS a lista JSON pura, sem markdown.

Conteúdo para análise:
Texto da mensagem: "{message_text}"
"""