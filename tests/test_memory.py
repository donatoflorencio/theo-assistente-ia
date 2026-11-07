from services.memory_service import (
    buscar_memorias_relevantes, identificar_memoria, pode_salvar_memoria, salvar_memoria,
)


def test_identificar_memoria():
    assert identificar_memoria("Meu nome é Ana e estou estudando Python.")


def test_memory_save_policy():
    assert pode_salvar_memoria("Meu nome é Ana e estou estudando Python.")
    assert not pode_salvar_memoria("sim")
    assert not pode_salvar_memoria("!!!")


def test_relevant_memory_search():
    assert salvar_memoria("geral", "Estou estudando Python e quero aprender Flask.")
    result = buscar_memorias_relevantes("quero aprender Python")
    assert any("Python" in item["conteudo"] for item in result)
