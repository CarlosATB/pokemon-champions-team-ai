"""Os dados baixados carregam e os nomes batem entre as fontes.

Se os arquivos ainda não foram gerados (python -m src.baixar_dados),
os testes são pulados.
"""

import pytest

from src import config, dados
from src.tipos import TIPOS

precisa_legais_e_pokemon = pytest.mark.skipif(
    not (config.LEGAIS_FILE.exists() and config.POKEMON_FILE.exists()),
    reason="dados da PokéAPI/Showdown ainda não baixados",
)
precisa_uso = pytest.mark.skipif(
    not config.USO_FILE.exists(), reason="estatísticas do Smogon ainda não baixadas"
)


@precisa_legais_e_pokemon
def test_todo_legal_tem_tipos_e_status():
    pokemon = dados.carregar_pokemon()
    for pokemon_id in dados.carregar_legais():
        assert pokemon_id in pokemon, f"{pokemon_id} sem dados da PokéAPI"
        info = pokemon[pokemon_id]
        assert 1 <= len(info["tipos"]) <= 2
        assert all(t in TIPOS for t in info["tipos"])
        assert len(info["status"]) == 6


@precisa_legais_e_pokemon
def test_busca_por_nome_em_qualquer_grafia():
    assert dados.buscar_pokemon("Charizard-Mega-Y")["tipos"] == ["Fire", "Flying"]
    assert dados.buscar_pokemon("indeedee f")["tipos"] == ["Psychic", "Normal"]
    assert dados.eh_legal("Incineroar")
    assert not dados.eh_legal("Bulbasaur")


@precisa_legais_e_pokemon
def test_megas_apontam_para_especie_legal():
    pokemon = dados.carregar_pokemon()
    nao_megas = [pokemon_id for pokemon_id, info in pokemon.items() if not info["mega"]]
    for info in pokemon.values():
        if info["mega"]:
            # startswith: Floette-Mega vem da forma legal Floette-Eternal
            assert any(p.startswith(info["especie_base"]) for p in nao_megas), info["id"]


@precisa_uso
@precisa_legais_e_pokemon
def test_nomes_do_smogon_batem_com_os_legais():
    legais = set(dados.carregar_legais())
    uso = dados.carregar_uso()["pokemon"]
    assert uso, "estatísticas vazias"
    for pokemon_id, info in uso.items():
        assert pokemon_id in legais, f"{info['nome']} (Smogon) não está na lista de legais"
        for parceiro in info["parceiros"]:
            assert parceiro in legais, f"parceiro {parceiro} não está na lista de legais"
