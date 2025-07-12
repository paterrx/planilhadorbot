import json
import logging
import google.generativeai as genai  # type: ignore
from .config import GEMINI_API_KEY, GEMINI_MODEL

PROMPT_REFINER = (
    "Você é um Analista Mestre especializado em apostas esportivas. Recebe a descrição original "
    "da aposta e um JSON preliminar com os campos: tipo_de_aposta, jogador (se aplicável), competicao, "
    "jogo, mercado, linha, odd, stake e opcoes (para escadinha). Valide e ajuste todos os campos. "
    "Se algum campo estiver ausente ou inválido, corrija com base no texto original. "
    "Retorne apenas um JSON no formato de uma lista de objetos."
)

async def run_gemini_request(
    prompt_template,    # str
    message_text,       # str
    image_path,         # str or None
    channel_name,       # str
    extra_data=""       # str
):
    # configura chave
    genai.configure(api_key=GEMINI_API_KEY)
    # monta conteúdo do usuário
    user_input = (
        f"CANAL: {channel_name}\n"
        f"MENSAGEM: {message_text}\n"
        f"DADOS_PRELIMINARES: {extra_data}\n"
    )
    # escolhe modelo base
    model = GEMINI_MODEL
    payload = {
        "model": model,
        "temperature": 0.2,
        "prompt": prompt_template,
        "user": user_input
    }
    # adiciona imagem e muda para versão vision, se houver
    if image_path:
        with open(image_path, "rb") as f:
            img = f.read()
        payload["image"] = img
        payload["model"] = f"{GEMINI_MODEL}-vision"

    # envia requisição
    resp = await genai.chat.completions.create(**payload)  # type: ignore[attr-defined]
    text = resp.choices[0].message  # type: ignore[attr-defined]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logging.error("Gemini retornou JSON inválido: %s", text)
        raise
