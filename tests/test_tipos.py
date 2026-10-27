"""Testes da tabela de tipos."""

from src.tipos import TIPOS, TIPOS_PT, efetividade, multiplicador, tabela_completa


def test_tabela_tem_18_por_18():
    tabela = tabela_completa()
    assert len(TIPOS) == 18
    assert len(tabela) == 18
    assert all(len(linha) == 18 for linha in tabela.values())
    assert set(TIPOS_PT) == set(TIPOS)


def test_casos_conhecidos():
    assert multiplicador("Water", "Fire") == 2
    assert multiplicador("Fire", "Water") == 0.5
    assert multiplicador("Normal", "Ghost") == 0
    assert multiplicador("Ground", "Flying") == 0
    assert multiplicador("Dragon", "Fairy") == 0
    assert multiplicador("Normal", "Normal") == 1


def test_dois_tipos_multiplicam():
    assert efetividade("Ice", ["Dragon", "Flying"]) == 4      # ex.: Dragonite
    assert efetividade("Fire", ["Water", "Dragon"]) == 0.25
    assert efetividade("Electric", ["Water", "Ground"]) == 0
