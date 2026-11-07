from __future__ import annotations

from google import genai
from google.genai import types

from config import Config
from services.memory_service import buscar_memorias_relevantes, carregar_historico

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

client = genai.Client(api_key=Config.GEMINI_API_KEY)


def gerar_resposta(pergunta, conversa_id):
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
            role="user",
            parts=[types.Part(text=contexto_memorias + pergunta)],
        )
    )

    resposta = client.models.generate_content(
        model=Config.GEMINI_MODEL,
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

    return texto_resposta
