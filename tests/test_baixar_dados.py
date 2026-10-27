"""Testes do tratamento dos dados (sem internet: usa exemplos pequenos)."""

import json
from pathlib import Path

from src.baixar_dados import (
    processar_golpes,
    processar_habilidades,
    processar_itens,
    processar_legais,
    processar_movepool,
    processar_pokeapi,
    processar_smogon,
)

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


def test_processar_golpes_aplica_o_mod_do_champions():
    base = (
        "export const Moves = {\n"
        "\tfakeout: {\n\t\tname: \"Fake Out\",\n\t\ttype: \"Normal\",\n\t\tcategory: \"Physical\",\n"
        "\t\tbasePower: 40,\n\t\tsecondary: {\n\t\t\tchance: 100,\n\t\t},\n\t\ttarget: \"normal\",\n\t},\n"
        "\theatwave: {\n\t\tname: \"Heat Wave\",\n\t\ttype: \"Fire\",\n\t\tcategory: \"Special\",\n"
        "\t\tbasePower: 95,\n\t\ttarget: \"allAdjacentFoes\",\n\t},\n"
        "};\n"
    )
    mod = "export const Moves = {\n\theatwave: {\n\t\tinherit: true,\n\t\tbasePower: 100,\n\t},\n};\n"
    golpes = processar_golpes(base, mod, {"fakeout", "heatwave"})
    assert golpes["fakeout"] == {"nome": "Fake Out", "tipo": "Normal", "categoria": "Physical",
                                 "poder": 40, "alvo": "normal"}
    assert golpes["heatwave"]["poder"] == 100  # o Champions mudou o poder


def test_processar_movepool():
    texto = (
        "export const Learnsets = {\n"
        "\tincineroar: {\n\t\tlearnset: {\n\t\t\tfakeout: [\"9M\"],\n\t\t\tprotect: [\"9M\"],\n\t\t},\n\t},\n"
        "};\n"
    )
    assert processar_movepool(texto) == {"incineroar": ["fakeout", "protect"]}


def test_processar_itens_e_pedras_mega():
    base = (
        "export const Items = {\n"
        "\tcharizarditey: {\n\t\tname: \"Charizardite Y\",\n"
        "\t\tmegaStone: { \"Charizard\": \"Charizard-Mega-Y\" },\n\t},\n"
        "\teviolite: {\n\t\tname: \"Eviolite\",\n\t},\n"
        "\tsitrusberry: {\n\t\tname: \"Sitrus Berry\",\n\t},\n"
        "\tmeowsticite: {\n\t\tname: \"Meowsticite\",\n\t\tmegaStone: {\n"
        "\t\t\t\"Meowstic\": \"Meowstic-M-Mega\",\n\t\t\t\"Meowstic-F\": \"Meowstic-F-Mega\",\n"
        "\t\t},\n\t},\n"
        "};\n"
    )
    mod = "export const Items = {\n\teviolite: {\n\t\tinherit: true,\n\t\tisNonstandard: \"Past\",\n\t},\n};\n"
    itens = processar_itens(base, mod)
    assert set(itens["legais"]) == {"charizarditey", "sitrusberry", "meowsticite"}
    assert itens["pedras_mega"]["charizarditey"] == {
        "pokemon": "charizard", "mega": "charizardmegay", "megas": ["charizardmegay"]}
    assert itens["pedras_mega"]["meowsticite"]["megas"] == ["meowsticmmega", "meowsticfmega"]


def test_processar_habilidades():
    texto = (
        "export const Abilities = {\n"
        "\tgrassysurge: {\n\t\tonStart(source) {},\n\t\tflags: {},\n"
        "\t\tname: \"Grassy Surge\",\n\t\trating: 4,\n\t},\n"
        "};\n"
    )
    assert processar_habilidades(texto) == {"grassysurge": "Grassy Surge"}
