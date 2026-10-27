"""
Opções dos seletores da tela "Montar o time" (item, habilidade e golpes).

Cada lista vem ordenada pelo uso nas batalhas reais: primeiro o que os
jogadores mais usam com aquele Pokémon, depois o resto em ordem alfabética.
Assim a melhor escolha costuma ser uma das primeiras da lista.
"""

from src import dados


def _uso_do_pokemon(pokemon_id: str) -> dict:
    return dados.carregar_uso()["pokemon"].get(pokemon_id, {})


def _ordenar(ids: list[str], mais_usados: dict, nome) -> list[str]:
    """Primeiro os mais usados (na ordem do uso), depois o resto por nome."""
    primeiros = [i for i in mais_usados if i in ids]
    resto = sorted((i for i in ids if i not in mais_usados), key=nome)
    return primeiros + resto


def opcoes_de_itens(pokemon_id: str) -> list[str]:
    """ids dos itens legais, sem Pedras Mega de outros Pokémon."""
    itens = dados.carregar_itens()
    especie = dados.carregar_pokemon().get(pokemon_id, {}).get("especie_base", pokemon_id)
    validos = [i for i in itens["legais"]
               if i not in itens["pedras_mega"]
               or itens["pedras_mega"][i]["pokemon"] in (pokemon_id, especie)]
    return _ordenar(validos, _uso_do_pokemon(pokemon_id).get("itens", {}),
                    lambda i: itens["legais"][i])


def opcoes_de_habilidades(pokemon_id: str) -> list[str]:
    """ids das habilidades que o Pokémon pode ter."""
    possiveis = dados.carregar_pokemon().get(pokemon_id, {}).get("habilidades", [])
    nomes = dados.carregar_habilidades()
    return _ordenar(possiveis, _uso_do_pokemon(pokemon_id).get("habilidades", {}),
                    lambda h: nomes.get(h, h))


def opcoes_de_golpes(pokemon_id: str) -> list[str]:
    """ids dos golpes que o Pokémon aprende no Champions (a Mega usa os da forma normal)."""
    movepool = dados.carregar_movepool()
    golpes = dados.carregar_golpes()
    especie = dados.carregar_pokemon().get(pokemon_id, {}).get("especie_base", pokemon_id)
    aprende = movepool.get(pokemon_id) or movepool.get(especie) or []
    aprende = [g for g in aprende if g in golpes]
    return _ordenar(aprende, _uso_do_pokemon(pokemon_id).get("golpes", {}),
                    lambda g: golpes[g]["nome"])
