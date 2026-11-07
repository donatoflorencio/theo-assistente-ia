import difflib
import re
import sqlite3
import unicodedata

from db import get_connection


def carregar_historico(conversa_id):
    with get_connection() as conexao:
        registros = conexao.execute(
            """
            SELECT role, content
            FROM mensagens
            WHERE conversation_id = ?
            ORDER BY id DESC
            LIMIT 10
            """,
            (conversa_id,),
        ).fetchall()

    registros.reverse()
    return [{"role": role, "content": content} for role, content in registros]


def salvar_mensagens(conversa_id, pergunta, resposta):
    with get_connection() as conexao:
        conexao.executemany(
            """
            INSERT INTO mensagens (conversation_id, role, content)
            VALUES (?, ?, ?)
            """,
            [(conversa_id, "user", pergunta), (conversa_id, "assistant", resposta)],
        )


def salvar_memoria(categoria, conteudo):
    with get_connection() as conexao:
        conexao.execute(
            """
            INSERT INTO memorias (categoria, conteudo)
            VALUES (?, ?)
            """,
            (categoria, conteudo),
        )


def atualizar_memoria(memoria_id, novo_conteudo):
    with get_connection() as conexao:
        conexao.execute(
            """
            UPDATE memorias
            SET conteudo = ?
            WHERE id = ?
            """,
            (novo_conteudo, memoria_id),
        )


def buscar_memoria_por_categoria(categoria):
    with get_connection() as conexao:
        conexao.row_factory = sqlite3.Row

        resultado = conexao.execute(
            """
            SELECT * FROM memorias
            WHERE categoria = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (categoria,),
        ).fetchone()

        return dict(resultado) if resultado else None


def identificar_tema_memoria(texto):
    texto = texto.lower()

    temas = {
        "estudos": [
            "estud",
            "aprend",
            "curso",
            "python",
            "javascript",
            "html",
            "css",
            "programação",
            "desenvolvimento",
        ],
        "trabalho": ["trabalho", "empresa", "profissão", "emprego", "cargo"],
        "projetos": ["projeto", "desenvolvendo", "criando", "construindo"],
        "preferencias": ["prefiro", "gosto", "não gosto", "preferência"],
        "objetivos": ["objetivo", "pretendo", "quero me tornar", "quero trabalhar"],
    }

    encontrados = []
    for tema, palavras in temas.items():
        if any(palavra in texto for palavra in palavras):
            encontrados.append(tema)

    return encontrados


def buscar_memorias_relacionadas(texto):
    temas_novos = identificar_tema_memoria(texto)
    if not temas_novos:
        return []

    memorias = listar_memorias()
    relacionadas = []

    for memoria in memorias:
        temas_existentes = identificar_tema_memoria(memoria["conteudo"])
        if any(tema in temas_existentes for tema in temas_novos):
            relacionadas.append(memoria)

    return relacionadas


def listar_memorias():
    with get_connection() as conexao:
        conexao.row_factory = sqlite3.Row
        memorias = conexao.execute(
            """
            SELECT id, categoria, conteudo, criado_em
            FROM memorias
            ORDER BY id DESC
            """
        ).fetchall()
        return [dict(memoria) for memoria in memorias]


def normalizar_texto_memoria(texto):
    texto = texto.casefold().strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        caractere for caractere in texto if not unicodedata.combining(caractere)
    )
    texto = re.sub(r"[^\w\s]", "", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto


def memoria_ja_existe(conteudo):
    novo_conteudo = normalizar_texto_memoria(conteudo)

    if not novo_conteudo:
        return False

    for memoria in listar_memorias():
        conteudo_salvo = normalizar_texto_memoria(memoria["conteudo"])

        if novo_conteudo == conteudo_salvo:
            return True

        similaridade = difflib.SequenceMatcher(
            None,
            novo_conteudo,
            conteudo_salvo,
        ).ratio()

        if similaridade >= 0.85:
            return True

    return False


def buscar_memorias_relevantes(pergunta):
    pergunta = pergunta.casefold()

    palavras_chave = {
        "nome": ["nome", "chamo", "chamar"],
        "estudo": ["estudo", "estudando", "estudar", "aprendendo", "aprendo"],
        "programacao": [
            "programacao",
            "programação",
            "python",
            "javascript",
            "html",
            "css",
        ],
    }

    termos_relevantes = []
    for palavras in palavras_chave.values():
        if any(palavra in pergunta for palavra in palavras):
            termos_relevantes.extend(palavras)

    if not termos_relevantes:
        return []

    memorias = listar_memorias()
    relevantes = []

    for memoria in memorias:
        conteudo = memoria["conteudo"].casefold()
        pontuacao = sum(1 for termo in set(termos_relevantes) if termo in conteudo)

        if pontuacao > 0:
            relevantes.append((pontuacao, memoria))

    relevantes.sort(key=lambda item: item[0], reverse=True)
    return [memoria for _, memoria in relevantes[:5]]


def identificar_memoria(pergunta):
    pergunta = pergunta.lower().strip()

    indicadores = [
        "estou estudando",
        "estou aprendendo",
        "quero aprender",
        "estou fazendo um curso",
        "estou estudando para",
        "eu gosto de",
        "eu prefiro",
        "não gosto de",
        "minha preferência é",
        "prefiro utilizar",
        "meu objetivo é",
        "meu sonho é",
        "pretendo",
        "quero trabalhar com",
        "quero me tornar",
        "estou trabalhando",
        "eu trabalho com",
        "minha profissão é",
        "trabalho na empresa",
        "minha função é",
        "meu projeto é",
        "estou desenvolvendo",
        "estou criando",
        "estou construindo",
        "estou trabalhando no projeto",
        "meu nome é",
        "moro em",
        "tenho interesse em",
    ]

    return any(indicador in pergunta for indicador in indicadores)


def apagar_memoria(memoria_id):
    with get_connection() as conexao:
        conexao.execute(
            """
            DELETE FROM memorias
            WHERE id = ?
            """,
            (memoria_id,),
        )
