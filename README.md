# 🤖 Planilhador de Apostas Inteligente com IA

Este é um ecossistema de bots em Python avançado, projetado para automatizar completamente o processo de catalogação de apostas esportivas a partir de canais do Telegram. O sistema utiliza a IA Generativa do Google (Gemini) para análise de conteúdo, um banco de dados local para gerenciamento de estado e se integra diretamente com o Google Sheets para a criação de planilhas.

O projeto foi desenvolvido com foco em robustez, precisão e automação, transformando um processo manual e demorado em um fluxo de trabalho inteligente e eficiente.

---

## ✨ Funcionalidades Principais

-   **Monitoramento Ativo 24/7:** Ouve múltiplos canais do Telegram simultaneamente através da API do Telethon.
-   **Análise com IA Generativa:** Utiliza a API do Google Gemini para interpretar texto e imagens, extraindo dados detalhados das apostas.
-   **Arquitetura Inteligente (Classificador + Especialistas):**
    -   Um **Classificador** primeiro identifica o tipo de aposta (Simples, Escada, Criar Aposta, Múltiplas Simples) ou se a mensagem deve ser ignorada (resumo de resultados, comentários, memes).
    -   **Especialistas** focados e altamente treinados são chamados para extrair os dados de cada tipo de aposta com máxima precisão.
-   **Camada de Validação "Duplo-Check":** Uma segunda chamada de IA atua como um **Revisor de Qualidade (QA)**, que analisa o trabalho da primeira extração, corrige erros e preenche campos faltantes, garantindo uma taxa de acerto extremamente alta.
-   **Memória Persistente:** Usa um banco de dados SQLite para se "lembrar" das apostas já processadas, implementando uma lógica anti-duplicata inteligente que diferencia apostas pela partida, mercado, entrada e casa de apostas.
-   **Lógica de Negócios:** Implementa regras de prioridade para "tipsters carro-chefe", permitindo a atualização de stakes caso uma aposta de maior confiança apareça.
-   **Guardião da Planilha (`monitor.py`):** Um segundo bot que roda em paralelo, monitorando a planilha do Google Sheets para detectar alterações manuais (edições e exclusões) e sincronizá-las com o banco de dados do bot principal.
-   **Configuração Segura:** Utiliza variáveis de ambiente (`.env`) para gerenciar todas as chaves de API e informações sensíveis, garantindo a segurança do projeto.

---

## 🛠️ Tecnologias Utilizadas

-   **Linguagem:** Python 3
-   **Telegram API:** Telethon
-   **Inteligência Artificial:** Google Gemini Pro
-   **Planilhas:** Google Sheets API & gspread
-   **Banco de Dados:** SQLite3
-   **Gerenciamento de Dados:** Pandas
-   **Gerenciamento de Segredos:** python-dotenv

---

## 🚀 Configuração e Uso

Para rodar este projeto, siga os passos:

1.  **Clonar o Repositório:**
    ```bash
    git clone [https://github.com/paterrx/planilhadorbot.git](https://github.com/paterrx/planilhadorbot.git)
    cd planilhadorbot
    ```

2.  **Criar Ambiente Virtual:**
    ```bash
    python -m venv venv
    # No Windows
    .\venv\Scripts\activate
    # No Linux/Mac
    source venv/bin/activate
    ```

3.  **Instalar Dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurar Arquivos de Contexto e Canais:**
    - Preencha os arquivos `.txt` (`casas.txt`, `esporte.txt`, etc.) com suas categorias.
    - Edite o `config.json` com os IDs dos canais do Telegram a serem monitorados.

5.  **Configurar Segredos (`.env`):**
    - Crie um arquivo `.env` na raiz e preencha com suas chaves de API, seguindo o modelo:
      ```
      TELEGRAM_API_ID=...
      TELEGRAM_API_HASH=...
      GEMINI_API_KEY=...
      SPREADSHEET_ID=...
      MAIN_TIPSTER_NAME="Nome do Canal Principal"
      TELETHON_SESSION_STRING=...
      GOOGLE_CREDENTIALS_JSON="..." 
      ```

6.  **Inicializar o Banco de Dados:**
    - Rode o script de setup uma vez para criar o banco de dados:
      ```bash
      python database_setup.py
      ```

---
## ▶️ Executando a Aplicação

A aplicação consiste em dois serviços que rodam em paralelo. Abra dois terminais na pasta do projeto (com o `venv` ativo).

-   **No Terminal 1 (O Bot Principal):**
    ```bash
    python -m app.main
    ```

-   **No Terminal 2 (O Guardião da Planilha):**
    ```bash
    python monitor.py
    ```

Para implantação na nuvem (ex: Railway), o `Procfile` já está configurado para iniciar os dois serviços (`worker` e `monitor`) automaticamente.