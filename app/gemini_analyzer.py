# app/gemini_analyzer.py - A Versão Mestre Definitiva

import asyncio
import json
import logging
from datetime import datetime
import google.generativeai as genai
from . import config

async def run_gemini_request(prompt, message_text, image_path, channel_name, extra_data=""):
    """Função genérica e robusta para fazer um request à API do Gemini."""
    try:
        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        today_date = datetime.now().strftime('%d/%m/%Y')
        final_prompt = prompt.replace("{today_date}", today_date).replace("{message_text}", message_text).replace("{channel_name}", channel_name).replace("{extra_data}", extra_data)

        content_to_send = [final_prompt]
        if image_path:
            loop = asyncio.get_running_loop()
            image_part = await loop.run_in_executor(None, lambda: genai.upload_file(image_path))
            content_to_send.append(image_part)
        
        response = await model.generate_content_async(content_to_send, request_options={"timeout": 120})
        
        logging.info(f"--- RESPOSTA BRUTA DA IA (MODELO: {prompt[:25]}...) ---\n{response.text}\n--------------------------")
        
        clean_text = response.text.strip().replace('\u00a0', ' ')
        start_char, end_char = ('[', ']') if '[' in clean_text else ('{', '}')
        
        start_index = clean_text.find(start_char)
        end_index = clean_text.rfind(end_char) + 1
        
        if start_index != -1 and end_index > start_index:
            json_str = clean_text[start_index:end_index]
            return json.loads(json_str)
        
        logging.error(f"Nenhum JSON/Lista JSON válido encontrado na resposta: {clean_text}")
        return None

    except Exception as e:
        logging.error(f"❌ Erro crítico na função run_gemini_request: {e}")
        return None

# --- PROMPTS DOS ESPECIALISTAS E REVISOR (VERSÃO FINALÍSSIMA) ---

PROMPT_CLASSIFIER = """
Você é um Classificador Mestre. Sua tarefa é analisar a mensagem e seguir uma árvore de decisão para determinar o tipo de aposta com 100% de precisão. Sua única resposta deve ser um JSON: {"bet_type": "VALOR"}.

**ÁRVORE DE DECISÃO:**
1.  **É LIXO?** O propósito principal da mensagem é um resumo de resultados (com muitos ✅/❌), um comentário sobre um jogo, ou um meme/GIF? - Se sim, responda `{"bet_type": "TRASH"}`.
2.  **É UMA ESCADA (LADDER)?** A mensagem mostra o mesmo mercado/jogador com linhas crescentes (ex: Chutes 2+, 3+, 4+)? - Se sim, responda `{"bet_type": "LADDER"}`.
3.  **É UM CRIAR APOSTA (BET BUILDER)?** A mensagem mostra múltiplas seleções diferentes para o MESMO JOGO, combinadas em uma odd final (ex: Rei do Pitaco)? - Se sim, responda `{"bet_type": "BET_BUILDER"}`.
4.  **É UMA DUPLA/TRIPLA SEM MÚLTIPLA?** A mensagem menciona "Dupla" ou "Tripla" mas NÃO contém uma aposta "Múltipla" no final? - Se sim, responda `{"bet_type": "BET_BUILDER"}` (será tratado como uma aposta de criar).
5.  **É UMA LISTA DE SIMPLES (MULTI_SIMPLE)?** A mensagem mostra uma lista de apostas para JOGOS DIFERENTES (pode incluir itens "Múltipla")? - Se sim, responda `{"bet_type": "MULTI_SIMPLE"}`.
6.  **SE NENHUM DOS ANTERIORES,** é uma aposta única e direta? - Se sim, responda `{"bet_type": "SIMPLE"}`.

NÃO responda nada além do JSON.
Conteúdo para análise:
Texto: "{message_text}"
"""

EXTRACTOR_RULES = """
CADA JSON DEVE TER TODAS as chaves: "is_bet", "dia_do_mes", "tipster", "casa_de_apostas", "tipo_de_aposta", "competicao", "jogos", "descricao_da_aposta", "entrada", "live_ou_pre_live", "esporte", "odd", "unidade".
REGRAS OBRIGATÓRIAS DE PREENCHIMENTO:
- `is_bet`: `true`.
- `tipster`: Se "Forwarded from", use o nome do canal original. Senão, use `{channel_name}`.
- `dia_do_mes`: Use a data do evento. Se ausente ou "Hoje", o valor DEVE ser `{today_date}`.
- `unidade`: É CRÍTICO. DEVE ser um número float. Se houver "Limite da aposta: R$X", a unidade é X. Senão, procure por '%' ou 'u'.
- `casa_de_apostas`: Procure no texto ou no link (Ex: "Rei do Pitaco"). Padrão: "N/A".
- `jogos`: DEVE ser um texto plano "Time A vs Time B".
- `live_ou_pre_live`: DEVE ser "PRÉ LIVE", a menos que o texto diga "LIVE".
- `SAÍDA`: APENAS a lista JSON pura, sem markdown.
"""

PROMPT_SIMPLE_EXTRACTOR = f"""
Você é um especialista em extrair UMA APOSTA SIMPLES. Retorne uma LISTA com UM ÚNICO objeto JSON.
{EXTRACTOR_RULES}
REGRAS PARA SIMPLES:
- `descricao_da_aposta`: O nome do mercado.
- `entrada`: A seleção específica.
- `tipo_de_aposta`: DEVE ser 'SIMPLES'.
Conteúdo:
Texto: \"{{message_text}}\"
"""

PROMPT_LADDER_EXTRACTOR = f"""
Você é um especialista em extrair APOSTAS EM ESCADA (LADDER). Trate cada linha da escada como um objeto JSON separado na lista.
{EXTRACTOR_RULES}
REGRAS PARA ESCADA:
- `descricao_da_aposta`: O mercado base.
- `entrada`: A linha específica (ex: '2+').
- `tipo_de_aposta`: DEVE ser 'SIMPLES' para cada degrau.
- Associe a unidade e odd corretas a cada linha.
Conteúdo:
Texto: \"{{message_text}}\"
"""

PROMPT_BET_BUILDER_EXTRACTOR = f"""
Você é um especialista em extrair UMA APOSTA "CRIAR APOSTA" (ou do tipo Rei do Pitaco, Dupla ou Tripla). Retorne uma LISTA com UM ÚNICO objeto JSON.
{EXTRACTOR_RULES}
REGRAS PARA CRIAR APOSTA:
- `tipo_de_aposta`: DEVE ser "CRIAR APOSTA", "DUPLA" ou "TRIPLA", conforme o contexto.
- `descricao_da_aposta`: Um resumo dos mercados. Ex: "Gols e Escanteios".
- `entrada`: A combinação de todas as seleções.
- `odd`: A odd final combinada.
Conteúdo:
Texto: \"{{message_text}}\"
"""

PROMPT_MULTI_SIMPLE_EXTRACTOR = f"""
Você é um especialista em extrair VÁRIAS APOSTAS SIMPLES de uma lista. Trate cada aposta da lista como um objeto JSON separado.
{EXTRACTOR_RULES}
REGRAS PARA MULTI-SIMPLES:
- Se um item da lista for uma 'Múltipla' genérica, extraia-a também, preenchendo os campos de `jogos`, `descricao_da_aposta` e `entrada` com 'Múltipla' e `tipo_de_aposta` como 'MÚLTIPLA'.
- Para os outros itens, o `tipo_de_aposta` DEVE ser 'SIMPLES'.
Conteúdo:
Texto: \"{{message_text}}\"
"""

PROMPT_QA_REFINER = """
Você é um especialista em Quality Assurance (QA). Sua tarefa é revisar um rascunho de JSON extraído por outra IA e corrigi-lo com base na mensagem original, garantindo que nenhum campo importante fique nulo se a informação estiver disponível. Se a mensagem NÃO for uma aposta acionável, sua resposta DEVE ser um JSON com `{"is_bet": false}`.
**Contexto:**
- **Mensagem Original:** ```{message_text}```
- **Rascunho do JSON:** ```{extra_data}```
**Sua Tarefa:**
1.  **Valide:** A mensagem original é uma recomendação de aposta real? Se for um comentário, aviso, etc., retorne `{"is_bet": false}`.
2.  **Corrija:** Compare o rascunho com a mensagem original e corrija CADA campo que esteja errado ou faltando (`null`). Preste **atenção máxima** em `unidade`, `casa_de_apostas`, `esporte` e `tipster`.
3.  **Responda:** Retorne apenas o objeto JSON final e perfeito, sem markdown.
"""

PROMPT_QA_REFINER_2 = """
Você é o Revisor Chefe. Esta é a prova real final. Verifique o JSON revisado contra a mensagem original para garantir 100% de precisão. Corrija qualquer detalhe restante. Sua resposta DEVE ser apenas o objeto JSON final e perfeito. Se você, em última análise, achar que não é uma aposta, retorne `{"is_bet": false}`.
**Mensagem Original:** ```{message_text}```
**JSON Revisado 1:** ```{extra_data}```
"""

PROMPT_MAP = {
    'SIMPLE': PROMPT_SIMPLE_EXTRACTOR,
    'LADDER': PROMPT_LADDER_EXTRACTOR,
    'BET_BUILDER': PROMPT_BET_BUILDER_EXTRACTOR,
    'MULTI_SIMPLE': PROMPT_MULTI_SIMPLE_EXTRACTOR,
}