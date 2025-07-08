# app/main.py - Teste de Pulso (v-debug-1)
import logging
import time
import sys

# Configuração de logging para garantir que veremos a mensagem
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout  # Força o log a sair no console do Railway
)

logging.info("Iniciando o Teste de Pulso...")
print("PRINT: Iniciando o Teste de Pulso...") # Adicionando um print para garantir a saída

count = 0
while True:
    message = f"PULSO: O container está vivo. Contagem: {count}"
    logging.info(message)
    print(f"PRINT: {message}")
    count += 1
    time.sleep(10) # Pisca a cada 10 segundos