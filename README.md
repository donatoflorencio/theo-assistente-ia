from services.memory_service import buscar_memorias_relevantes, identificar_memoria, salvar_memoria


def test_identificar_memoria():
    texto = "Meu nome é Ana e estou estudando Python."
    assert identificar_memoria(texto) is True


def test_buscar_memorias_relevantes():
    salvar_memoria("geral", "Eu estudo Python e quero aprender Flask.")
    relevantes = buscar_memorias_relevantes("quero aprender python")
    assert any("Python" in memoria["conteudo"] for memoria in relevantes)
