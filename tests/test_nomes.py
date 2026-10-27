"""Testes da padronização de nomes."""

from src.nomes import POKEAPI_EXCECOES, nome_pokeapi, to_id


def test_to_id():
    assert to_id("Charizard-Mega-Y") == "charizardmegay"
    assert to_id("charizard-mega-y") == "charizardmegay"
    assert to_id("Fake Out") == "fakeout"
    assert to_id("King's Shield") == "kingsshield"


def test_nome_pokeapi_caso_normal():
    nomes = ["charizard", "charizard-mega-x", "charizard-mega-y"]
    assert nome_pokeapi("charizardmegay", nomes) == "charizard-mega-y"
    assert nome_pokeapi("pikachu", nomes) is None


def test_nome_pokeapi_excecoes():
    assert nome_pokeapi("indeedeef", []) == "indeedee-female"
    assert nome_pokeapi("aegislash", []) == "aegislash-shield"
    # As chaves de exceção já estão no formato id.
    assert all(chave == to_id(chave) for chave in POKEAPI_EXCECOES)
