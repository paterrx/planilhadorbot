# app/main.py - Teste de Conexão do Telegram (v-debug-2)

import logging
import asyncio
import sys
from telethon import TelegramClient
from telethon.sessions import StringSession

# Importa as configurações de forma segura
# Adicionamos o caminho do projeto para garantir que a importação funcione na nuvem
sys.path.insert(0, '/app')
from app import config

# Configuração de logging para garantir que veremos a mensagem
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

async def main():
    logging.info("--- INICIANDO TESTE DE CONEXÃO DO TELEGRAM ---")

    # Verifica se a string de sessão existe
    if not config.TELETHON_SESSION_STRING:
        logging.error("ERRO CRÍTICO: A variável de ambiente TELETHON_SESSION_STRING não foi encontrada!")
        return

    logging.info("String de Sessão encontrada. Tentando criar o cliente...")

    session = StringSession(config.TELETHON_SESSION_STRING)
    client = TelegramClient(session, config.TELEGRAM_API_ID, config.TELEGRAM_API_HASH)

    logging.info("Cliente criado. Tentando conectar ao Telegram com client.start()...")

    try:
        await client.start()
        # Se chegarmos aqui, a conexão foi um sucesso
        logging.info("✅ SUCESSO! Conexão com o Telegram estabelecida!")

        me = await client.get_me()
        logging.info(f"✅ Bot logado como: {me.first_name} (@{me.username})")

        logging.info("--- BOT FICARÁ ONLINE AGORA ---")

        # Mantém o bot conectado e ocioso
        await client.run_until_disconnected()

    except Exception as e:
        logging.error(f"❌ FALHA AO CONECTAR: Ocorreu um erro durante o client.start(): {e}")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Teste de conexão encerrado.")