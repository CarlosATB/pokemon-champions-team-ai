"""Leitura dos replays do Pokémon Showdown (src/replays.py). Não precisa de internet."""

from src.replays import ler_log

LOG = """|j|☆Ana
|player|p1|Ana|1|1300
|player|p2|Bia|2|1280
|poke|p1|Incineroar, L50, M|
|poke|p1|Rillaboom, L50, F|
|poke|p1|Urshifu-*, L50, M|
|poke|p1|Garchomp, L50, M|
|poke|p2|Pelipper, L50, M|
|poke|p2|Basculegion-F, L50, F|
|poke|p2|Charizard, L50, M|
|poke|p2|Amoonguss, L50, M|
|start
|switch|p1a: Gato|Incineroar, L50, M|100/100
|switch|p1b: Urshifu|Urshifu-Rapid-Strike, L50, M|100/100
|switch|p2a: Pelipper|Pelipper, L50, M|100/100
|switch|p2b: Zard|Charizard, L50, M|100/100
|-weather|RainDance|[from] ability: Drizzle|[of] p2a: Pelipper
|-ability|p1a: Gato|Intimidate|boost
|detailschange|p2b: Zard|Charizard-Mega-Y, L50, M
|-mega|p2b: Zard|Charizard|Charizardite Y
|move|p1a: Gato|Fake Out|p2a: Pelipper
|move|p1b: Urshifu|Surging Strikes|p2b: Zard
|move|p2a: Pelipper|Tailwind|p2a: Pelipper
|move|p1a: Gato|Fake Out|p2a: Pelipper
|-enditem|p1b: Urshifu|Focus Sash
|move|p2b: Zard|Heat Wave|p1a: Gato|[spread] p1a,p1b
|win|Ana
"""


def test_le_vencedor_e_times():
    batalha = ler_log(LOG)
    assert batalha["vencedor"] == 1
    assert [m["especie"] for m in batalha["p1"]] == [
        "incineroar", "rillaboom", "urshifurapidstrike", "garchomp"]
    assert [m["especie"] for m in batalha["p2"]][1] == "basculegionf"


def test_le_golpes_item_habilidade_e_mega():
    batalha = ler_log(LOG)
    gato, _, urshifu, _ = batalha["p1"]
    assert gato["golpes"] == ["fakeout"]  # repetido conta uma vez só
    assert gato["habilidade"] == "intimidate"
    assert urshifu["item"] == "focussash"
    zard = batalha["p2"][2]
    assert zard["item"] == "charizarditey"
    assert zard["golpes"] == ["heatwave"]


def test_sem_vencedor_devolve_none():
    assert ler_log(LOG.replace("|win|Ana", "|tie")) is None
    assert ler_log("") is None
