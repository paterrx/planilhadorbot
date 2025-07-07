# 🤖 Planilhador de Apostas para Telegram

Este é um bot de Python avançado projetado para monitorar canais de apostas no Telegram, extrair informações de apostas de mensagens (texto e imagens) usando a IA Generativa do Google (Gemini), e catalogar tudo automaticamente em uma planilha do Google Sheets.

O projeto foi desenvolvido para ser robusto, inteligente e capaz de entender uma vasta gama de formatos de apostas, desde simples e múltiplas até estruturas complexas como "Escadas" (Ladder) e "Criar Aposta" (Bet Builder).

---

## ✨ Funcionalidades Principais

-   **Monitoramento Ativo 24/7:** Ouve múltiplos canais do Telegram simultaneamente.
-   **Análise com IA Generativa:** Utiliza a API do Google Gemini para interpretar texto e imagens, extraindo dados detalhados das apostas.
-   **Arquitetura Inteligente (Classificador + Especialistas):**
    -   Um **Classificador** primeiro identifica o tipo de aposta (Simples, Escada, Criar Aposta, etc.) ou se a mensagem deve ser ignorada (resumo de resultados, memes).
    -   **Especialistas** focados e altamente treinados são chamados para extrair os dados de cada tipo de aposta com máxima precisão.
-   **Memória Persistente:** Usa um banco de dados SQLite para se "lembrar" das apostas já processadas, evitando duplicatas.
-   **Lógica de Negócios:** Implementa regras de prioridade para "tipsters carro-chefe", permitindo a atualização de stakes caso uma aposta de maior confiança apareça.
-   **Planilhamento Automático:** Conecta-se de forma segura à API do Google Sheets para adicionar cada aposta extraída em uma nova linha, pronta para a análise do usuário.
-   **Interface de Controle (Opcional):** O projeto inclui um módulo de interface web construído com Streamlit para gerenciar os canais monitorados e visualizar a atividade do bot.

---

## 🛠️ Tecnologias Utilizadas

-   **Linguagem:** Python 3
-   **Telegram API:** Telethon
-   **Inteligência Artificial:** Google Gemini Pro
-   **Planilhas:** Google Sheets API & gspread
-   **Banco de Dados:** SQLite3
-   **Interface Web (Opcional):** Streamlit
-   **Gerenciamento de Segredos:** python-dotenv

---

## 🚀 Configuração e Uso

Para rodar este projeto localmente, siga os passos:

1.  **Clonar o Repositório:**
    ```bash
    git clone [https://github.com/paterrx/planilhadorbot.git](https://github.com/paterrx/planilhadorbot.git)
    cd planilhador-telegram-bot
    ```

2.  **Criar Ambiente Virtual:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Instalar Dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurar Arquivos de Contexto:**
    - Preencha os arquivos `.txt` (`casas.txt`, `esporte.txt`, `tiposDeAposta.txt`) com as suas categorias preferidas.

5.  **Configurar Credenciais e Segredos:**
    - Coloque seu arquivo `credentials.json` (da Google Cloud Service Account) na pasta raiz.
    - Crie um arquivo `.env` na raiz e preencha com suas chaves de API, seguindo o modelo:
      ```
      TELEGRAM_API_ID=...
      TELEGRAM_API_HASH=...
      GEMINI_API_KEY=...
      SPREADSHEET_ID=...
      MAIN_TIPSTER_NAME="Nome do Canal Principal"
      ```

6.  **Configurar Canais Alvo:**
    - Edite o arquivo `config.json` para incluir os IDs dos canais do Telegram a serem monitorados.

7.  **Inicializar o Banco de Dados:**
    - Rode o script de setup uma vez para criar o banco de dados de memória:
      ```bash
      python database_setup.py
      ```

8.  **Executar o Bot:**
    - Inicie o bot com o seguinte comando:
      ```bash
      python -m app.main
      ```