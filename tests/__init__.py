# Theo Assistente IA

Assistente pessoal de inteligência artificial em Python com Flask e Gemini.

## Visão geral

Este projeto oferece uma interface web simples para conversar com uma IA pessoal, guardar memórias e manter contexto por conversa. A autenticação é feita por senha local e a integração com Gemini é feita por meio da biblioteca `google-genai`.

## Requisitos

- Python 3.10+
- Uma chave da API do Google Gemini

## Configuração

1. Crie um ambiente virtual:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente:

```bash
cp .env.example .env
```

Edite o arquivo `.env` com os valores reais.

## Execução

```bash
python app.py
```

A aplicação sobe em:

```text
http://127.0.0.1:5000
```

## Estrutura principal

- `app.py`: configuração do app Flask e rotas
- `db.py`: criação e acesso ao banco SQLite
- `services/`: lógica de memória e integração com Gemini
- `templates/`: páginas HTML
- `static/`: CSS do frontend
- `tests/`: testes iniciais

## Observações

- O banco de dados local é salvo em `memoria.db`.
- A memória segue uma política simples de confirmação e deduplicação.
- A autenticação ainda é por senha local, com `IA_PASSWORD` como ambiente.

## Próximos passos sugeridos

- separar melhor as rotas em módulos
- expandir testes de autenticação e chat
- criar política mais robusta para persistência de memória
- preparar o app para deploy em produção

