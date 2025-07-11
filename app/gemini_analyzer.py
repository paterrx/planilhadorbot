# app/gemini_analyzer.py

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
        model = genai.GenerativeModel(config.GEMINI_MODEL)
        
        today_date = datetime.now().strftime('%d/%m/%Y')
        final_prompt = prompt.replace("{today_date}", today_date).replace("{message_text}", message_text).replace("{channel_name}", channel_name).replace("{extra_data}", extra_data)

        content_to_send = [final_prompt]
        if image_path:
            loop = asyncio.get_running_loop()
            image_part = await loop.run_in_executor(None, lambda: genai.upload_file(image_path))
            content_to_send.append(image_part)
        
        response = await model.generate_content_async(content_to_send, request_options={"timeout": 180})
        
        logging.info(f"--- RESPOSTA BRUTA DA IA (MODELO: {prompt[:30]}...) ---\n{response.text}\n--------------------------")
        
        clean_text = response.text.strip().replace('\u00a0', ' ').replace("```json", "").replace("```", "")
        
        # Tenta carregar o JSON diretamente
        return json.loads(clean_text)

    except json.JSONDecodeError:
        logging.error(f"Erro de decodificação de JSON. A IA não retornou um JSON válido. Resposta: {clean_text}")
        return None
    except Exception as e:
        logging.error(f"❌ Erro crítico na função run_gemini_request: {e}")
        return None

# --- ARQUITETURA DEBATE DE IAS ---

# IA 1: O LEITOR
PROMPT_READER = """
Sua única tarefa é "ler" o conteúdo da mensagem e extrair os dados brutos em uma estrutura JSON única. NÃO tente interpretar ou formatar as apostas ainda.
- Se for uma aposta de jogador em escada, extraia o nome do jogador, o mercado e uma lista de 'opcoes' com cada linha, odd e stake.
- Se for uma múltipla ou bet builder, extraia cada seleção em uma lista de 'selecoes'.
- Se for uma aposta simples, extraia os campos diretamente.
- Se não for uma aposta, retorne `{"is_bet": false}`.

**Exemplo de Escada:**
{"jogador": "B. Zeneli", "mercado": "Finalizações Totais", "opcoes": [{"linha": "Mais de 1.5", "odd": 3.00, "stake": 2.0}, {"linha": "Mais de 2.5", "odd": 7.00, "stake": 0.5}]}

**Exemplo de Criar Aposta:**
{"tipo_de_aposta": "CRIAR APOSTA", "odd_total": 3.00, "unidade_total": 1.75, "selecoes": ["Mais de 0.5 gols de LDU Quito", "LDU Quito com a maioria dos escanteios"]}

**Conteúdo para Análise:**
{message_text}
"""

# IA 2: O ANALISTA MESTRE
PROMPT_ANALYZER = """
Você é um Analista Mestre. Sua tarefa é receber os dados brutos extraídos por um "Leitor" e transformá-los em uma lista final de apostas no formato padrão.

**REGRAS DE NEGÓCIO:**
- Se os dados brutos contiverem uma lista de 'opcoes' (uma escada), você DEVE criar um objeto JSON separado para CADA opção na lista, tratando cada uma como uma aposta 'SIMPLES'.
- Se os dados brutos forem do tipo 'CRIAR APOSTA', você DEVE criar um ÚNICO objeto JSON, combinando as 'selecoes' no campo 'entrada'.
- Para todas as outras, formate para o padrão.

**MANUAL DE PREENCHIMENTO FINAL (SEJA RIGOROSO):**
- CADA JSON na lista final DEVE ter TODAS as chaves: "is_bet", "dia_do_mes", "tipster", "casa_de_apostas", "tipo_de_aposta", "competicao", "jogos", "descricao_da_aposta", "entrada", "live_ou_pre_live", "esporte", "odd", "unidade".
- `unidade`: DEVE ser um número float. Se houver "Limite da aposta: R$X", a unidade é X. Senão, procure por '%' ou 'u'.
- `SAÍDA`: APENAS a lista JSON final, sem markdown.

**Dados Brutos do Leitor:**
```json
{extra_data}
"""
