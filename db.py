import sqlite3

from config import Config


def get_connection():
    return sqlite3.connect(str(Config.DB_PATH))


def inicializar_banco():
    with get_connection() as conexao:
        conexao.execute("""
            CREATE TABLE IF NOT EXISTS mensagens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL
            )
        """)
        conexao.execute("""
            CREATE TABLE IF NOT EXISTS memorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                categoria TEXT NOT NULL,
                conteudo TEXT NOT NULL,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conexao.execute("""
            CREATE TABLE IF NOT EXISTS projetos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                descricao TEXT,
                status TEXT DEFAULT 'em andamento',
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
