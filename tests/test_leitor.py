"""Leitura do time no formato de exportação do Showdown."""

from apoio import precisa_dados, time_exemplo

from src.leitor import ler_bloco, ler_time, time_de_nomes

pytestmark = precisa_dados


def test_le_um_pokemon_completo():
    membro = ler_bloco(
        "Incineroar @ Sitrus Berry\nAbility: Intimidate\nLevel: 50\n"
        "EVs: 32 HP / 32 SpD\nCareful Nature\n- Fake Out\n- Parting Shot\n- Flare Blitz\n- Protect"
    )
    assert membro["especie"] == "Incineroar"
    assert membro["id"] == "incineroar"
    assert membro["item"] == "Sitrus Berry"
    assert membro["habilidade"] == "Intimidate"
    assert membro["natureza"] == "Careful"
    assert membro["evs"] == {"HP": 32, "SpD": 32}
    assert membro["golpes"] == ["Fake Out", "Parting Shot", "Flare Blitz", "Protect"]


def test_apelido_e_genero_sao_ignorados():
    membro = ler_bloco("Gato (Incineroar) (M) @ Sitrus Berry\n- Fake Out")
    assert membro["especie"] == "Incineroar"


def test_pedra_mega_vira_a_forma_mega():
    assert ler_bloco("Charizard @ Charizardite Y\n- Heat Wave")["forma"] == "charizardmegay"
    assert ler_bloco("Charizard @ Charizardite X\n- Heat Wave")["forma"] == "charizardmegax"
    assert ler_bloco("Charizard @ Sitrus Berry\n- Heat Wave")["forma"] == "charizard"
    # Pedra de outro Pokémon não faz Mega Evoluir.
    assert ler_bloco("Charizard @ Salamencite\n- Heat Wave")["forma"] == "charizard"


def test_le_o_time_inteiro():
    time = time_exemplo("Meta")
    assert [m["especie"] for m in time] == [
        "Rillaboom", "Incineroar", "Sneasler", "Salamence", "Indeedee-F", "Kingambit"]
    assert time[3]["forma"] == "salamencemega"


def test_time_so_com_nomes():
    time = time_de_nomes(["Rillaboom", "Incineroar"])
    assert [m["id"] for m in time] == ["rillaboom", "incineroar"]
    assert time[0]["golpes"] == []


def test_especie_repetida_ganha_numero():
    time = ler_time("Garchomp\n- Earthquake\n\nGarchomp\n- Rock Slide")
    assert [m["especie"] for m in time] == ["Garchomp", "Garchomp (2)"]
    assert time[1]["id"] == "garchomp"


def test_aceita_nome_da_pokeapi():
    assert ler_bloco("Indeedee-Female @ Rocky Helmet\n- Follow Me")["id"] == "indeedeef"
    assert ler_bloco("Pyroar-Male\n- Hyper Voice")["id"] == "pyroar"
