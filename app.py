from functools import wraps
import secrets

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from config import Config
from db import inicializar_banco
from services.gemini_service import gerar_resposta
from services.memory_service import (
    apagar_memoria, atualizar_memoria, buscar_memorias_relacionadas,
    identificar_memoria, listar_memorias, memoria_ja_existe,
    pode_salvar_memoria, salvar_memoria, salvar_mensagens,
)


def create_app(test_config=None):
    Config.validate()
    app = Flask(__name__)
    app.secret_key = Config.SECRET_KEY
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE=Config.SESSION_COOKIE_SAMESITE,
        SESSION_COOKIE_SECURE=Config.SESSION_COOKIE_SECURE,
    )
    if test_config:
        app.config.update(test_config)
    inicializar_banco()

    def exige_login(funcao):
        @wraps(funcao)
        def verificar(*args, **kwargs):
            if not session.get("autenticado"):
                return jsonify({"error": "Acesso não autorizado."}), 401
            return funcao(*args, **kwargs)
        return verificar

    @app.get("/")
    def inicio():
        return render_template("index.html" if session.get("autenticado") else "login.html")

    @app.post("/login")
    def login():
        dados = request.get_json(silent=True) or {}
        senha = dados.get("password", "")
        if not isinstance(senha, str) or not secrets.compare_digest(senha, Config.IA_PASSWORD):
            return jsonify({"error": "Senha incorreta."}), 401
        session.clear()
        session["autenticado"] = True
        return jsonify({"success": True})

    @app.post("/logout")
    def logout():
        session.clear()
        return redirect(url_for("inicio"))

    @app.post("/chat")
    @exige_login
    def chat():
        dados = request.get_json(silent=True) or {}
        pergunta = dados.get("message", "")
        conversa_id = dados.get("conversation_id", "principal")
        if not isinstance(pergunta, str) or not pergunta.strip():
            return jsonify({"error": "Mensagem vazia."}), 400
        pergunta = pergunta.strip()
        if not isinstance(conversa_id, str) or not conversa_id.strip() or len(conversa_id) > 100:
            return jsonify({"error": "Identificador de conversa inválido."}), 400

        try:
            lower = pergunta.casefold()
            if lower.startswith("theo, lembre-se:"):
                conteudo = pergunta[len("theo, lembre-se:"):].strip()
                if not pode_salvar_memoria(conteudo):
                    return jsonify({"response": "Essa informação não parece adequada para memória de longo prazo."})
                salvar_memoria("geral", conteudo)
                return jsonify({"response": "Informação salva na minha memória de longo prazo."})

            if lower.startswith("theo, atualize a memória "):
                partes = pergunta[len("theo, atualize a memória "):].split(":", 1)
                if len(partes) != 2 or not partes[0].strip().isdigit() or not partes[1].strip():
                    return jsonify({"response": "Use: Theo, atualize a memória 1: novo conteúdo."})
                memoria_id = int(partes[0].strip())
                if not any(m["id"] == memoria_id for m in listar_memorias()):
                    return jsonify({"response": "Não encontrei essa memória."})
                atualizar_memoria(memoria_id, partes[1].strip())
                return jsonify({"response": f"Memória {memoria_id} atualizada."})

            if lower.rstrip(" ?!") in ("theo, quais são minhas memórias", "quais são minhas memórias"):
                memorias = listar_memorias()
                texto = "Ainda não tenho memórias salvas." if not memorias else "Estas são minhas memórias:\n\n" + "".join(
                    f"Memória {m['id']} ({m['categoria']}): {m['conteudo']}\n\n" for m in memorias
                )
                return jsonify({"response": texto})

            if lower.startswith("theo, esqueça a memória "):
                identificador = pergunta[len("theo, esqueça a memória "):].strip()
                if not identificador.isdigit():
                    return jsonify({"response": "Informe o número da memória que deseja apagar."})
                apagar_memoria(int(identificador))
                return jsonify({"response": "Solicitação de exclusão processada."})

            if lower in ("cancelar", "não", "nao", "cancelar operação", "cancelar operacao"):
                for chave in ("memoria_pendente", "memorias_relacionadas", "memoria_id_complementar"):
                    session.pop(chave, None)
                return jsonify({"response": "Operação cancelada. Nenhuma memória foi alterada."})

            if lower in ("sim", "sim, pode salvar", "pode salvar", "salve"):
                pendente = session.get("memoria_pendente")
                if pendente and pode_salvar_memoria(pendente):
                    salvar_memoria("geral", pendente)
                    session.pop("memoria_pendente", None)
                    return jsonify({"response": "Informação salva na minha memória."})

            if identificar_memoria(pergunta):
                if memoria_ja_existe(pergunta):
                    return jsonify({"response": "Essa informação já está registrada na minha memória."})
                relacionadas = buscar_memorias_relacionadas(pergunta)
                session["memoria_pendente"] = pergunta
                if relacionadas:
                    session["memorias_relacionadas"] = [m["id"] for m in relacionadas]
                    lista = "\n".join(f"Memória {m['id']}: {m['conteudo']}" for m in relacionadas)
                    return jsonify({"response": f"Encontrei memórias relacionadas:\n\n{lista}\n\nDeseja complementar ou salvar como nova memória?"})
                return jsonify({"response": "Essa informação pode ser útil. Deseja que eu salve na memória?", "sugerir_memoria": pergunta})

            resposta = gerar_resposta(pergunta, conversa_id)
            salvar_mensagens(conversa_id, pergunta, resposta)
            return jsonify({"response": resposta})
        except Exception:
            app.logger.exception("Falha ao processar mensagem de chat")
            return jsonify({"error": "Não foi possível processar sua mensagem."}), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
