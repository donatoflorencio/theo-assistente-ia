from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from google import genai
from google.genai import types
from functools import wraps
import os
import sqlite3
import secrets

app = Flask(__name__)

# Configurações de segurança
app.secret_key = os.getenv("IA_SECRET_KEY")

SENHA_IA = os.getenv("IA_PASSWORD")

if not app.secret_key or not SENHA_IA:
    raise RuntimeError("Configure as variáveis IA_SECRET_KEY e IA_PASSWORD.")

app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

# Configuração do Gemini
MODELO = "gemini-3.5-flash-lite"
CHAVE_API = os.getenv("GEMINI_API_KEY")

if not CHAVE_API:
    raise RuntimeError("GEMINI_API_KEY não encontrada.")

client = genai.Client(api_key=CHAVE_API)

# INSTRUÇÕES PRINCIPAIS DO THEO
INSTRUCAO_SISTEMA = """
Seu nome é Theo.

Você é um assistente pessoal de inteligência artificial.
Converse sempre em português brasileiro.

Seja educado, objetivo e profissional.
Explique assuntos técnicos de maneira didática.
Ao ensinar programação, avance passo a passo,
considerando que o usuário está aprendendo.

Você pode utilizar as informações de memória
fornecidas no contexto para personalizar suas respostas.

Não invente informações sobre o usuário.
Se não souber algo, seja transparente.
"""

# Banco de dados
BANCO_DADOS = os.path.join(app.root_path, "memoria.db")


def inicializar_banco():
    with sqlite3.connect(BANCO_DADOS) as conexao:

        # Histórico de conversas existente
        conexao.execute("""
            CREATE TABLE IF NOT EXISTS mensagens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL
            )
        """)

        # Memória de longo prazo
        conexao.execute("""
            CREATE TABLE IF NOT EXISTS memorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                categoria TEXT NOT NULL,
                conteudo TEXT NOT NULL,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Memória de projetos
        conexao.execute("""
            CREATE TABLE IF NOT EXISTS projetos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                descricao TEXT,
                status TEXT DEFAULT 'em andamento',
                atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def carregar_historico(conversa_id):
    with sqlite3.connect(BANCO_DADOS) as conexao:
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
    with sqlite3.connect(BANCO_DADOS) as conexao:
        conexao.executemany(
            """
            INSERT INTO mensagens
            (conversation_id, role, content)
            VALUES (?, ?, ?)
        """,
            [(conversa_id, "user", pergunta), (conversa_id, "assistant", resposta)],
        )


def salvar_memoria(categoria, conteudo):
    with sqlite3.connect(BANCO_DADOS) as conexao:
        conexao.execute(
            """
            INSERT INTO memorias (categoria, conteudo)
            VALUES (?, ?)
        """,
            (categoria, conteudo),
        )


def atualizar_memoria(memoria_id, novo_conteudo):
    with sqlite3.connect(BANCO_DADOS) as conexao:
        conexao.execute(
            """
            UPDATE memorias
            SET conteudo = ?
            WHERE id = ?
        """,
            (novo_conteudo, memoria_id),
        )


def buscar_memoria_por_categoria(categoria):
    with sqlite3.connect(BANCO_DADOS) as conexao:
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
    with sqlite3.connect(BANCO_DADOS) as conexao:
        conexao.row_factory = sqlite3.Row

        memorias = conexao.execute("""
            SELECT id, categoria, conteudo, criado_em
            FROM memorias
            ORDER BY id DESC
        """).fetchall()

        return [dict(memoria) for memoria in memorias]

def normalizar_texto_memoria(texto):
    import re
    import unicodedata

    texto = texto.casefold().strip()

    texto = unicodedata.normalize("NFKD", texto)

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    texto = re.sub(r"[^\w\s]", "", texto)
    texto = re.sub(r"\s+", " ", texto)

    return texto


def memoria_ja_existe(conteudo):
    import difflib

    novo_conteudo = normalizar_texto_memoria(conteudo)

    if not novo_conteudo:
        return False

    for memoria in listar_memorias():
        conteudo_salvo = normalizar_texto_memoria(
            memoria["conteudo"]
        )

        if novo_conteudo == conteudo_salvo:
            return True

        similaridade = difflib.SequenceMatcher(
            None,
            novo_conteudo,
            conteudo_salvo
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

    return [memoria for pontuacao, memoria in relevantes[:5]]


def identificar_memoria(pergunta):
    pergunta = pergunta.lower().strip()

    indicadores = [
        # Estudos
        "estou estudando",
        "estou aprendendo",
        "quero aprender",
        "estou fazendo um curso",
        "estou estudando para",
        # Preferências
        "eu gosto de",
        "eu prefiro",
        "não gosto de",
        "minha preferência é",
        "prefiro utilizar",
        # Objetivos
        "meu objetivo é",
        "meu sonho é",
        "pretendo",
        "quero trabalhar com",
        "quero me tornar",
        # Trabalho e carreira
        "estou trabalhando",
        "eu trabalho com",
        "minha profissão é",
        "trabalho na empresa",
        "minha função é",
        # Projetos
        "meu projeto é",
        "estou desenvolvendo",
        "estou criando",
        "estou construindo",
        "estou trabalhando no projeto",
        # Informações pessoais
        "meu nome é",
        "moro em",
        "tenho interesse em",
    ]

    return any(indicador in pergunta for indicador in indicadores)


def apagar_memoria(memoria_id):
    with sqlite3.connect(BANCO_DADOS) as conexao:
        conexao.execute(
            """
            DELETE FROM memorias
            WHERE id = ?
        """,
            (memoria_id,),
        )


def exige_login(funcao):
    @wraps(funcao)
    def verificar(*args, **kwargs):
        if not session.get("autenticado"):
            return jsonify({"error": "Acesso não autorizado."}), 401
        return funcao(*args, **kwargs)

    return verificar


@app.route("/", methods=["GET"])
def inicio():
    if session.get("autenticado"):
        return render_template("index.html")

    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    dados = request.get_json(silent=True) or {}
    senha = dados.get("password", "")

    if not secrets.compare_digest(senha, SENHA_IA):
        return jsonify({"error": "Senha incorreta."}), 401

    session["autenticado"] = True
    return jsonify({"success": True})


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("inicio"))


@app.route("/chat", methods=["POST"])
@exige_login
def chat():
    dados = request.get_json(silent=True) or {}

    pergunta = dados.get("message", "").strip()
    conversa_id = dados.get("conversation_id", "principal")

    if not pergunta:
        return jsonify({"error": "Mensagem vazia."}), 400

    try:
        # COMANDO: SALVAR MEMÓRIA
        prefixo = "theo, lembre-se:"

        if pergunta.lower().startswith(prefixo):
            conteudo = pergunta[len(prefixo) :].strip()

            if not conteudo:
                return jsonify({"response": "Informe o que devo guardar."})

            salvar_memoria("geral", conteudo)

            return jsonify(
                {"response": "Informação salva na minha memória de longo prazo."}
            )

        # COMANDO: ATUALIZAR MEMÓRIA
        prefixo_atualizar = "theo, atualize a memória "

        if pergunta.lower().startswith(prefixo_atualizar):
            dados = pergunta[len(prefixo_atualizar) :].split(":", 1)

            if len(dados) != 2 or not dados[0].strip().isdigit():
                return jsonify(
                    {"response": "Use: Theo, atualize a memória 1: novo conteúdo."}
                )

            memoria_id = int(dados[0].strip())
            novo_conteudo = dados[1].strip()

            if not novo_conteudo:
                return jsonify({"response": "Informe o novo conteúdo."})

            if not any(memoria["id"] == memoria_id for memoria in listar_memorias()):
                return jsonify({"response": "Não encontrei essa memória."})

            atualizar_memoria(memoria_id, novo_conteudo)

            return jsonify({"response": f"Memória {memoria_id} atualizada."})

        # CONFIRMAR COMPLEMENTAÇÃO DE MEMÓRIA
        if pergunta.lower().strip() in [
            "sim",
            "sim, pode complementar",
            "pode complementar",
        ]:

            memoria_id = session.get("memoria_id_complementar")
            memoria_pendente = session.get("memoria_pendente")

            if memoria_id and memoria_pendente:

                memoria = next(
                    (m for m in listar_memorias() if m["id"] == memoria_id), None
                )

                if memoria:
                    novo_conteudo = memoria["conteudo"] + " " + memoria_pendente

                    atualizar_memoria(memoria_id, novo_conteudo)

                    session.pop("memoria_id_complementar", None)
                    session.pop("memoria_pendente", None)
                    session.pop("memorias_relacionadas", None)

                    return jsonify({"response": "Memória complementada com sucesso."})
                # SALVAR COMO NOVA MEMÓRIA
        if pergunta.lower().strip() in [
            "salvar como nova memória",
            "salvar como nova memoria",
            "nova memória",
            "nova memoria",
        ]:

            memoria_pendente = session.get("memoria_pendente")

            if memoria_pendente:

                if memoria_ja_existe(memoria_pendente):
                    session.pop("memoria_pendente", None)
                    session.pop("memorias_relacionadas", None)
                    session.pop("memoria_id_complementar", None)

                    return jsonify({
                        "response": "Essa informação já está registrada na minha memória."
                    })

                salvar_memoria("geral", memoria_pendente)

                session.pop("memoria_pendente", None)
                session.pop("memorias_relacionadas", None)
                session.pop("memoria_id_complementar", None)

                return jsonify({"response": "Nova memória salva com sucesso."})

        # CONFIRMAR SALVAMENTO DE MEMÓRIA
        if pergunta.lower().strip() in [
            "sim",
            "sim, pode salvar",
            "pode salvar",
            "salve",
        ]:

            memoria_pendente = session.get("memoria_pendente")

            if memoria_pendente:
                salvar_memoria("geral", memoria_pendente)

                session.pop("memoria_pendente", None)

                return jsonify({"response": "Informação salva na minha memória."})

        # CANCELAR OPERAÇÃO DE MEMÓRIA
        if pergunta.lower().strip() in [
            "cancelar",
            "cancelar operação",
            "cancelar operacao",
            "não",
            "nao"
        ]:

            session.pop("memoria_pendente", None)
            session.pop("memorias_relacionadas", None)
            session.pop("memoria_id_complementar", None)

            return jsonify({
                "response": "Operação cancelada. Nenhuma memória foi alterada."
            })

        # COMPLEMENTAR MEMÓRIA EXISTENTE
        if pergunta.lower().startswith("complementar a memória"):

            import re

            resultado = re.search(r"memória\s+(\d+)", pergunta.lower())

            if resultado:
                memoria_id = int(resultado.group(1))

                memorias_relacionadas = session.get("memorias_relacionadas", [])

                if memoria_id not in memorias_relacionadas:
                    return jsonify(
                        {
                            "response": "Esse número não corresponde a uma memória relacionada."
                        }
                    )

                session["memoria_id_complementar"] = memoria_id

                return jsonify(
                    {
                        "response": (
                            f"Você escolheu complementar a memória {memoria_id}. "
                            "Deseja acrescentar a informação que acabou de enviar?"
                        )
                    }
                )

        # COMANDO: LISTAR MEMÓRIAS
        if pergunta.lower().rstrip(" ?!") in [
            "theo, quais são minhas memórias",
            "quais são minhas memórias",
        ]:
            memorias = listar_memorias()

            if not memorias:
                texto = "Ainda não tenho memórias salvas."
            else:
                texto = "Estas são minhas memórias:\n\n"

                for memoria in memorias:
                    texto += (
                        f"**Memória {memoria['id']}** "
                        f"({memoria['categoria']}): "
                        f"{memoria['conteudo']}\n\n"
                    )

            return jsonify({"response": texto})

        # COMANDO: APAGAR MEMÓRIA
        prefixo_apagar = "theo, esqueça a memória "

        if pergunta.lower().startswith(prefixo_apagar):
            identificador = pergunta[len(prefixo_apagar) :].strip()

            if not identificador.isdigit():
                return jsonify(
                    {"response": "Informe o número da memória que deseja apagar."}
                )

            memoria_id = int(identificador)
            apagar_memoria(memoria_id)

            return jsonify(
                {
                    "response": f"Solicitação de exclusão da memória {memoria_id} processada."
                }
            )

        # IDENTIFICAÇÃO DE POSSÍVEIS MEMÓRIAS

        if identificar_memoria(pergunta):
            print("DEBUG: IDENTIFICAÇÃO DE MEMÓRIA ATIVADA:", repr(pergunta))
            memoria_ja_salva = memoria_ja_existe(pergunta)
            print("DEBUG: MEMÓRIA JÁ EXISTE:", memoria_ja_salva)

            if memoria_ja_salva:
                return jsonify({
                "response": "Essa informação já está registrada na minha memória."
    })

            if not memoria_ja_salva:

                relacionadas = buscar_memorias_relacionadas(pergunta)

                if relacionadas:
                    session["memoria_pendente"] = pergunta
                    session["memorias_relacionadas"] = [
                        memoria["id"] for memoria in relacionadas
                    ]
                    session["memoria_id_complementar"] = None

                    lista = "\n".join(
                        f"Memória {memoria['id']}: {memoria['conteudo']}"
                        for memoria in relacionadas
                    )

                    return jsonify(
                        {
                            "response": (
                                "Encontrei memórias sobre assuntos relacionados:\n\n"
                                f"{lista}\n\n"
                                "Deseja complementar essas informações "
                                "ou salvar como uma nova memória?"
                            )
                        }
                    )

                session["memoria_pendente"] = pergunta

                return jsonify(
                    {
                        "response": (
                            "Essa informação pode ser útil "
                            "nas próximas conversas. "
                            "Deseja que eu salve isso na minha memória?"
                        ),
                        "sugerir_memoria": pergunta,
                    }
                )

        # CONVERSA NORMAL COM O GEMINI
        historico = carregar_historico(conversa_id)

        memorias_relevantes = buscar_memorias_relevantes(pergunta)

        contexto_memorias = ""

        if memorias_relevantes:
            contexto_memorias = "\n\nInformações importantes sobre o usuário:\n"

            for memoria in memorias_relevantes:
                contexto_memorias += f"- {memoria['conteudo']}\n"

        conteudos = []

        for mensagem in historico:
            papel = "model" if mensagem["role"] == "assistant" else "user"

            conteudos.append(
                types.Content(role=papel, parts=[types.Part(text=mensagem["content"])])
            )

        conteudos.append(
            types.Content(
                role="user", parts=[types.Part(text=contexto_memorias + pergunta)]
            )
        )

        resposta = client.models.generate_content(
            model=MODELO,
            contents=conteudos,
            config=types.GenerateContentConfig(
                system_instruction=INSTRUCAO_SISTEMA,
                temperature=0.7,
                max_output_tokens=1000,
            ),
        )

        texto_resposta = resposta.text

        if not texto_resposta:
            raise RuntimeError("O Gemini não retornou texto.")

        salvar_mensagens(conversa_id, pergunta, texto_resposta)

        return jsonify({"response": texto_resposta})

    except Exception as erro:
        print("Erro no chat:", str(erro))
        return jsonify({"error": "Não foi possível processar sua mensagem."}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
