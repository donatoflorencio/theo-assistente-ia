import difflib
import re
import sqlite3
import unicodedata

from db import get_connection


def pode_salvar_memoria(conteudo):
    texto = (conteudo or "").strip()
    if len(texto) < 8 or len(texto) > 280 or re.fullmatch(r"[\W_]+", texto):
        return False
    indicadores = (
        "meu nome", "meu objetivo", "meu projeto", "minha preferência",
        "eu gosto", "eu prefiro", "estou estudando", "estou aprendendo",
        "estou trabalhando", "quero aprender", "quero trabalhar", "moro em",
        "tenho interesse", "pretendo",
    )
    return any(indicador in texto.casefold() for indicador in indicadores)


def carregar_historico(conversa_id):
    with get_connection() as conexao:
        rows = conexao.execute(
            "SELECT role, content FROM mensagens WHERE conversation_id = ? ORDER BY id DESC LIMIT 10",
            (conversa_id,),
        ).fetchall()
    rows.reverse()
    return [{"role": role, "content": content} for role, content in rows]


def salvar_mensagens(conversa_id, pergunta, resposta):
    with get_connection() as conexao:
        conexao.executemany(
            "INSERT INTO mensagens (conversation_id, role, content) VALUES (?, ?, ?)",
            [(conversa_id, "user", pergunta), (conversa_id, "assistant", resposta)],
        )


def salvar_memoria(categoria, conteudo):
    if not pode_salvar_memoria(conteudo):
        return False
    with get_connection() as conexao:
        conexao.execute(
            "INSERT INTO memorias (categoria, conteudo) VALUES (?, ?)",
            (categoria, conteudo.strip()),
        )
    return True


def atualizar_memoria(memoria_id, novo_conteudo):
    with get_connection() as conexao:
        conexao.execute("UPDATE memorias SET conteudo = ? WHERE id = ?", (novo_conteudo, memoria_id))


def listar_memorias():
    with get_connection() as conexao:
        conexao.row_factory = sqlite3.Row
        rows = conexao.execute(
            "SELECT id, categoria, conteudo, criado_em FROM memorias ORDER BY id DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def buscar_memoria_por_categoria(categoria):
    with get_connection() as conexao:
        conexao.row_factory = sqlite3.Row
        row = conexao.execute(
            "SELECT * FROM memorias WHERE categoria = ? ORDER BY id DESC LIMIT 1",
            (categoria,),
        ).fetchone()
    return dict(row) if row else None


def identificar_tema_memoria(texto):
    texto = texto.casefold()
    temas = {
        "estudos": ("estud", "aprend", "curso", "python", "javascript", "html", "css", "programação", "desenvolvimento"),
        "trabalho": ("trabalho", "empresa", "profissão", "emprego", "cargo"),
        "projetos": ("projeto", "desenvolvendo", "criando", "construindo"),
        "preferencias": ("prefiro", "gosto", "não gosto", "preferência"),
        "objetivos": ("objetivo", "pretendo", "quero me tornar", "quero trabalhar"),
    }
    return [tema for tema, palavras in temas.items() if any(p in texto for p in palavras)]


def buscar_memorias_relacionadas(texto):
    temas = set(identificar_tema_memoria(texto))
    return [m for m in listar_memorias() if temas.intersection(identificar_tema_memoria(m["conteudo"]))]


def normalizar_texto_memoria(texto):
    texto = unicodedata.normalize("NFKD", texto.casefold().strip())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", texto)).strip()


def memoria_ja_existe(conteudo):
    novo = normalizar_texto_memoria(conteudo)
    if not novo:
        return False
    for memoria in listar_memorias():
        existente = normalizar_texto_memoria(memoria["conteudo"])
        if novo == existente or difflib.SequenceMatcher(None, novo, existente).ratio() >= 0.85:
            return True
    return False


def buscar_memorias_relevantes(pergunta):
    termos = ("nome", "chamo", "estudo", "estudando", "aprender", "python", "javascript", "html", "css", "programação")
    pergunta = pergunta.casefold()
    relacionados = []
    for memoria in listar_memorias():
        conteudo = memoria["conteudo"].casefold()
        pontos = sum(1 for termo in termos if termo in pergunta and termo in conteudo)
        if pontos:
            relacionados.append((pontos, memoria))
    relacionados.sort(key=lambda item: item[0], reverse=True)
    return [memoria for _, memoria in relacionados[:5]]


def identificar_memoria(pergunta):
    indicadores = (
        "estou estudando", "estou aprendendo", "quero aprender", "estou fazendo um curso",
        "eu gosto de", "eu prefiro", "não gosto de", "minha preferência é", "meu objetivo é",
        "meu sonho é", "pretendo", "quero trabalhar com", "quero me tornar", "estou trabalhando",
        "eu trabalho com", "minha profissão é", "minha função é", "meu projeto é",
        "estou desenvolvendo", "estou criando", "estou construindo", "meu nome é", "moro em",
        "tenho interesse em",
    )
    return any(i in pergunta.casefold() for i in indicadores)


def apagar_memoria(memoria_id):
    with get_connection() as conexao:
        conexao.execute("DELETE FROM memorias WHERE id = ?", (memoria_id,))
