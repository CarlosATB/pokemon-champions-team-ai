"""Testes do tratamento dos dados (sem internet: usa exemplos pequenos)."""

import json
from pathlib import Path

from src.baixar_dados import processar_legais, processar_pokeapi, processar_smogon

FIXTURES = Path(__file__).parent / "fixtures"


def test_processar_legais():
    texto = (
        "export const FormatsData = {\n"
        "\tbulbasaur: {\n\t\tisNonstandard: \"Past\",\n\t\ttier: \"Illegal\",\n\t},\n"
        "\tvenusaur: {\n\t\ttier: \"RU\",\n\t\tdoublesTier: \"DOU\",\n\t},\n"
        "\tvenusaurmega: {\n\t\ttier: \"UU\",\n\t},\n"
        "};\n"
    )
    assert processar_legais(texto) == ["venusaur", "venusaurmega"]


def test_processar_pokeapi():
    resposta = {
        "name": "charizard-mega-y",
        "species": {"name": "charizard"},
        "types": [{"type": {"name": "fire"}}, {"type": {"name": "flying"}}],
        "stats": [{"stat": {"name": "speed"}, "base_stat": 100}],
        "abilities": [{"ability": {"name": "drought"}}],
    }
    pokemon = processar_pokeapi("charizardmegay", resposta)
    assert pokemon["nome"] == "Charizard-Mega-Y"
    assert pokemon["tipos"] == ["Fire", "Flying"]
    assert pokemon["status"] == {"spe": 100}
    assert pokemon["especie_base"] == "charizard"
    assert pokemon["mega"] is True


def test_processar_smogon():
    with open(FIXTURES / "chaos_exemplo.json", encoding="utf-8") as arquivo:
        uso = processar_smogon(json.load(arquivo))

    assert uso["batalhas"] == 1000
    assert list(uso["pokemon"]) == ["incineroar", "indeedeef"]  # mais usado primeiro

    incineroar = uso["pokemon"]["incineroar"]
    assert incineroar["uso"] == 50.0
    assert incineroar["habilidades"] == {"intimidate": 95.0, "blaze": 5.0}
    assert "nothing" not in incineroar["itens"]   # < 1% é cortado
    assert "" not in incineroar["golpes"]         # slot vazio é ignorado
    # Parceiros viram id, para bater com o resto dos dados.
    assert incineroar["parceiros"] == {"rillaboom": 40.0, "indeedeef": 10.0}
