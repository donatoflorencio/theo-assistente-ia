# Theo Assistente IA

Assistente pessoal em português, construído com Flask, SQLite e Google Gemini.

## Requisitos

- Python 3.10 ou superior
- Chave de API do Google Gemini

## Configuração (PowerShell)

```powershell
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edite `.env` com seus valores reais. Não compartilhe nem faça commit desse arquivo. A aplicação carrega `.env` automaticamente.

## Execução

```powershell
python app.py
```

Abra http://127.0.0.1:5000. Configure `IA_SECRET_KEY`, `IA_PASSWORD` e `GEMINI_API_KEY` no `.env` antes de iniciar.

## Testes

```powershell
pytest -q
```

Os testes usam um banco temporário e não precisam fazer chamadas à API Gemini.
