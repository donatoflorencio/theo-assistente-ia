from google import genai
from google.genai import types

from config import Config
from services.memory_service import buscar_memorias_relevantes, carregar_historico

INSTRUCAO_SISTEMA = """
Seu nome é Theo. Você é um assistente pessoal de inteligência artificial.
Converse sempre em português brasileiro. Seja educado, objetivo e profissional.
Explique assuntos técnicos de maneira didática. Não invente informações sobre o usuário.
Se não souber algo, seja transparente.
"""

client = genai.Client(api_key=Config.GEMINI_API_KEY) if Config.GEMINI_API_KEY else None


def gerar_resposta(pergunta, conversa_id):
    if client is None:
        raise RuntimeError("GEMINI_API_KEY não configurada.")
    historico = carregar_historico(conversa_id)
    memórias = buscar_memorias_relevantes(pergunta)
    contexto = ""
    if memórias:
        contexto = "\n\nInformações importantes sobre o usuário:\n" + "".join(
            f"- {memoria['conteudo']}\n" for memoria in memórias
        )
    conteudos = [
        types.Content(
            role="model" if item["role"] == "assistant" else "user",
            parts=[types.Part(text=item["content"])],
        )
        for item in historico
    ]
    conteudos.append(types.Content(role="user", parts=[types.Part(text=contexto + pergunta)]))
    resposta = client.models.generate_content(
        model=Config.GEMINI_MODEL,
        contents=conteudos,
        config=types.GenerateContentConfig(
            system_instruction=INSTRUCAO_SISTEMA,
            temperature=0.7,
            max_output_tokens=1000,
        ),
    )
    if not resposta.text:
        raise RuntimeError("O Gemini não retornou texto.")
    return resposta.text
