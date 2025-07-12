import re
import json
from .gemini_analyzer import run_gemini_request

PROMPT_READER = (
    "Você é um parser de apostas que recebe um texto e deve retornar um JSON válido com os campos: "
    "tipo_de_aposta, jogador, competicao, jogo, mercado, linha, odd, stake e opcoes. "
    "Exemplos:\n"
    '{"tipo_de_aposta":"CHUTES_JOGADOR","jogador":"X","mercado":"Finalizações Totais","linha":"Mais de 2.5","odd":3.0,"stake":1.0}\n'
    '{"tipo_de_aposta":"ESCADA","jogador":"Y","mercado":"Finalizações Totais","opcoes":[{"linha":"Mais de 1.5","odd":3.0,"stake":1.0},{"linha":"Mais de 2.5","odd":7.0,"stake":0.5}]}\n'
    "Se nenhum regex aplicar, use o fallback para gerar JSON."
)

def parse_chutes_jogador(text: str) -> dict | None:
    pattern = re.compile(
        r'([\w\. ]+)[–-]\s*Finalizações Totais[:\-]\s*Mais de\s*'
        r'(\d+(?:\.\d+)?)\s*\(odd\s*(\d+\.\d+)\)\s*stake\s*(\d+\.?\d*)u',
        re.IGNORECASE
    )
    m = pattern.search(text)
    if not m:
        return None

    return {
        "tipo_de_aposta": "CHUTES_JOGADOR",
        "jogador": m.group(1).strip(),
        "mercado": "Finalizações Totais",
        "linha": f"Mais de {m.group(2)}",
        "odd": float(m.group(3)),
        "stake": float(m.group(4))
    }

def parse_escada(text: str) -> dict | None:
    lines = text.splitlines()
    if not lines or not lines[0].lower().startswith("escadinha"):
        return None

    head = lines[0]
    m_head = re.search(r'Escadinha\s+(.+?)\s+Finalizações', head, re.IGNORECASE)
    jogador = m_head.group(1).strip() if m_head else None
    item_pattern = re.compile(
        r'\d+\)\s*Mais de\s*(\d+(?:\.\d+)?)\s*@([\d\.]+)\s*stake\s*(\d+\.?\d*)u',
        re.IGNORECASE
    )

    opcoes = []
    for line in lines[1:]:
        m = item_pattern.search(line)
        if m:
            opcoes.append({
                "linha": f"Mais de {m.group(1)}",
                "odd": float(m.group(2)),
                "stake": float(m.group(3))
            })

    if not opcoes:
        return None
    return {
        "tipo_de_aposta": "ESCADA",
        "jogador": jogador,
        "mercado": "Finalizações Totais",
        "opcoes": opcoes
    }

async def generic_parse(text: str) -> dict:
    for fn in (parse_chutes_jogador, parse_escada):
        out = fn(text)
        if out:
            return out
    # fallback para IA
    return await run_gemini_request(PROMPT_READER, text, None, "parser")
