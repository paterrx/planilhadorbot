# app/gemini_analyzer.py
import asyncio
import json
import logging
from datetime import datetime
import google.generativeai as genai
from . import config

async def run_gemini_request(prompt, message_text, image_path, channel_name, extra_data=""):
    try:
        genai.configure(api_key=config.GEMINI_API_KEY)
        model = genai.GenerativeModel(config.GEMINI_MODEL)
        today_date = datetime.now().strftime('%d/%m/%Y')
        
        casas_context = ", ".join(config.LIST_CASAS)
        tipsters_context = ", ".join(config.LIST_TIPSTERS)
        tipos_aposta_context = ", ".join(config.LIST_TIPOS_APOSTA)

        final_prompt = prompt.replace("{today_date}", today_date) \
                             .replace("{message_text}", message_text) \
                             .replace("{channel_name}", channel_name) \
                             .replace("{extra_data}", extra_data) \
                             .replace("{casas_context}", casas_context) \
                             .replace("{tipsters_context}", tipsters_context) \
                             .replace("{tipos_aposta_context}", tipos_aposta_context)

        content_to_send = [final_prompt]
        if image_path:
            loop = asyncio.get_running_loop()
            image_part = await loop.run_in_executor(None, lambda: genai.upload_file(image_path))
            content_to_send.append(image_part)
        
        response = await model.generate_content_async(content_to_send, request_options={"timeout": 180})
        
        logging.info(f"--- RESPOSTA BRUTA DA IA (MODELO: {prompt[:25]}...) ---\n{response.text}\n--------------------------")
        
        clean_text = response.text.strip().replace('\u00a0', ' ')
        start_char, end_char = ('[', ']') if '[' in clean_text else ('{', '}')
        start_index, end_index = clean_text.find(start_char), clean_text.rfind(end_char) + 1
        if start_index != -1 and end_index > start_index:
            json_str = clean_text[start_index:end_index]
            return json.loads(json_str)
        return None
    except Exception as e:
        logging.error(f"❌ Erro crítico na função run_gemini_request: {e}"); return None

PROMPT_CLASSIFIER = """
Você é um Classificador Mestre. Sua tarefa é analisar o propósito da mensagem. Responda com um JSON: {"bet_type": "VALOR"}.
- Se for um resumo de resultados, balanço, ou um **comentário sobre um jogo sem uma aposta clara e acionável**, classifique como "TRASH".
- Se for uma recomendação de aposta nova, classifique como: "SIMPLE", "BET_BUILDER", "LADDER", "DUPLA", "TRIPLA", "MULTI_SIMPLE".
Conteúdo:
Texto: "{message_text}"
"""

PROMPT_TRASH_EVALUATOR = """
Você é um especialista em analisar comentários sobre apostas. Sua tarefa é determinar se a mensagem contém uma instrução importante sobre uma aposta já feita.
Responda com um único JSON com as chaves: "is_important", "instruction", "game_reference".
- `is_important`: `true` se a mensagem contiver uma instrução como "cashout", "aumentar stake", "cobrir aposta", "proteger". `false` caso contrário.
- `instruction`: Se for importante, descreva a instrução. Ex: "Fazer cashout", "Aumentar 1% na stake".
- `game_reference`: Se for importante, identifique o jogo a que se refere. Ex: "PSG vs Real Madrid".
Se não for uma instrução importante, retorne `{"is_important": false, "instruction": null, "game_reference": null}`.
NÃO responda nada além do JSON.
Conteúdo para análise:
Texto: "{message_text}"
"""

EXTRACTOR_RULES = """
CADA JSON DEVE TER TODAS as chaves: "is_bet", "dia_do_mes", "tipster", "casa_de_apostas", "tipo_de_aposta", "competicao", "jogos", "descricao_da_aposta", "entrada", "live_ou_pre_live", "esporte", "odd", "unidade".
REGRAS OBRIGATÓRIAS DE PREENCHIMENTO:
- `is_bet`: `true`.
- **PADRONIZAÇÃO:** Para os campos `tipster`, `casa_de_apostas` e `tipo_de_aposta`, você DEVE usar um dos valores EXATOS das listas de contexto fornecidas.
- `unidade`: É CRÍTICO. DEVE ser um número float. Se houver "Limite da aposta: R$X", a unidade é X. Senão, procure por '%' ou 'u'.
- `jogos`: DEVE ser um texto plano "Time A vs Time B".
- `live_ou_pre_live`: DEVE ser "PRÉ LIVE", a menos que o texto diga "LIVE".
- `SAÍDA`: APENAS a lista JSON pura, sem markdown.
**FONTES DA VERDADE:**
- Casas de Apostas Válidas: {casas_context}
- Tipsters Válidos: {tipsters_context}
- Tipos de Aposta Válidos: {tipos_aposta_context}
"""

PROMPT_SIMPLE_EXTRACTOR = f"Você é um especialista em extrair UMA APOSTA SIMPLES. Retorne uma LISTA com UM ÚNICO objeto JSON.\n{EXTRACTOR_RULES}\nREGRAS PARA SIMPLES:\n- `descricao_da_aposta`: O nome do mercado.\n- `entrada`: A seleção específica.\n- `tipo_de_aposta`: DEVE ser 'SIMPLES'.\nConteúdo:\nTexto: \"{{message_text}}\""
PROMPT_LADDER_EXTRACTOR = f"Você é um especialista em extrair APOSTAS EM ESCADA (LADDER). Trate cada linha da escada como um objeto JSON separado na lista.\n{EXTRACTOR_RULES}\nREGRAS PARA ESCADA:\n- `descricao_da_aposta`: O mercado base.\n- `entrada`: A linha específica (ex: '2+').\n- `tipo_de_aposta`: DEVE ser 'SIMPLES' para cada degrau.\n- Associe a unidade e odd corretas a cada linha.\nConteúdo:\nTexto: \"{{message_text}}\""
PROMPT_BET_BUILDER_EXTRACTOR = f"Você é um especialista em extrair UMA APOSTA 'CRIAR APOSTA' (ou do tipo Rei do Pitaco, Dupla ou Tripla). Retorne uma LISTA com UM ÚNICO objeto JSON.\n{EXTRACTOR_RULES}\nREGRAS PARA CRIAR APOSTA:\n- `tipo_de_aposta`: DEVE ser 'CRIAR APOSTA', 'DUPLA' ou 'TRIPLA', conforme o contexto.\n- `descricao_da_aposta`: Um resumo dos mercados.\n- `entrada`: A combinação das seleções.\n- `odd`: A odd final combinada.\nConteúdo:\nTexto: \"{{message_text}}\""
PROMPT_MULTI_SIMPLE_EXTRACTOR = f"Você é um especialista em extrair VÁRIAS APOSTAS SIMPLES de uma lista. Trate cada aposta da lista como um objeto JSON separado.\n{EXTRACTOR_RULES}\nREGRAS PARA MULTI-SIMPLES:\n- `tipo_de_aposta`: DEVE ser 'SIMPLES' para cada item, a menos que esteja escrito 'Múltipla'.\nConteúdo:\nTexto: \"{{message_text}}\""
PROMPT_DUPLA_EXTRACTOR = f"Você é um especialista em extrair uma APOSTA DUPLA. Retorne uma LISTA com UM ÚNICO objeto JSON.\n{EXTRACTOR_RULES}\nREGRAS PARA DUPLA:\n- `tipo_de_aposta`: DEVE ser 'DUPLA'.\n- `entrada`: A combinação das duas seleções.\nConteúdo:\nTexto: \"{{message_text}}\""
PROMPT_TRIPLA_EXTRACTOR = f"Você é um especialista em extrair uma APOSTA TRIPLA. Retorne uma LISTA com UM ÚNICO objeto JSON.\n{EXTRACTOR_RULES}\nREGRAS PARA TRIPLA:\n- `tipo_de_aposta`: DEVE ser 'TRIPLA'.\n- `entrada`: A combinação das três seleções.\nConteúdo:\nTexto: \"{{message_text}}\""

PROMPT_QA_REFINER = """
Você é um especialista em Quality Assurance (QA). Sua tarefa é revisar um rascunho de JSON extraído por outra IA e corrigi-lo com base na mensagem original. Se a mensagem NÃO for uma aposta acionável, sua resposta DEVE ser um JSON com `{"is_bet": false}`.
**Contexto:**
- **Mensagem Original:** ```{message_text}```
- **Rascunho do JSON:** ```{extra_data}```
**Sua Tarefa:**
1.  **Valide:** A mensagem original é uma recomendação de aposta real? Se for um comentário, retorne `{"is_bet": false}`.
2.  **Corrija:** Compare o rascunho com a mensagem original e corrija CADA campo. Preste **atenção máxima** em `unidade`, `casa_de_apostas`, `esporte` e `tipster`.
3.  **Responda:** Retorne apenas o objeto JSON final e perfeito, sem markdown.
"""
PROMPT_QA_REFINER_2 = """
Você é o Revisor Chefe. Esta é a prova real final. Verifique o JSON revisado contra a mensagem original para garantir 100% de precisão. Corrija qualquer detalhe restante. Se, em última análise, achar que não é uma aposta, retorne `{"is_bet": false}`.
**Mensagem Original:** ```{message_text}```
**JSON Revisado 1:** ```{extra_data}```
"""

PROMPT_ERROR_DETECTOR = """
Você é um Detetive de Dados. Sua tarefa é analisar uma linha de planilha que contém um erro e, com base no contexto da extração original, propor uma correção.
Sua resposta deve ser um JSON com a chave "correcao_sugerida" e o valor correto. Ex: `{"correcao_sugerida": 0.5}`.

**CENÁRIO:**
- **Linha com Erro (da planilha principal):** `{extra_data}`
- **Contexto (da extração original do bot):** A mensagem original continha o texto: `"{message_text}"`

**SUA MISSÃO:**
1.  Identifique o campo com erro óbvio na "Linha com Erro". O erro mais comum é uma `unidade` vazia ou com um valor claramente errado (ex: 100.0).
2.  Analise o "Contexto" da mensagem original para encontrar o valor correto.
3.  Retorne a correção no formato JSON especificado. Se não encontrar uma correção clara, retorne `{"correcao_sugerida": null}`.
"""

PROMPT_MAP = {
    'SIMPLE': PROMPT_SIMPLE_EXTRACTOR, 'LADDER': PROMPT_LADDER_EXTRACTOR,
    'BET_BUILDER': PROMPT_BET_BUILDER_EXTRACTOR, 'MULTI_SIMPLE': PROMPT_MULTI_SIMPLE_EXTRACTOR,
    'DUPLA': PROMPT_DUPLA_EXTRACTOR, 'TRIPLA': PROMPT_TRIPLA_EXTRACTOR
}
