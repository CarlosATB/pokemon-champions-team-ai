"""
Opções dos seletores da tela "Montar o time" (item, habilidade e golpes).

Cada lista vem ordenada pelo uso nas batalhas reais: primeiro o que os
jogadores mais usam com aquele Pokémon, depois o resto em ordem alfabética.
Assim a melhor escolha costuma ser uma das primeiras da lista.
"""

import random

from src import dados

QUANTOS_NO_SORTEIO = 60  # o dado sorteia entre os 60 Pokémon mais usados


def _uso_do_pokemon(pokemon_id: str) -> dict:
    return dados.carregar_uso()["pokemon"].get(pokemon_id, {})


def _ordenar(ids: list[str], mais_usados: dict, nome) -> list[str]:
    """Primeiro os mais usados (na ordem do uso), depois o resto por nome."""
    primeiros = [i for i in mais_usados if i in ids]
    resto = sorted((i for i in ids if i not in mais_usados), key=nome)
    return primeiros + resto


def pode_escolher(pokemon_id: str) -> bool:
    """Está na lista de Pokémon do card? (legal e não é forma que só existe na batalha)"""
    info = dados.carregar_pokemon().get(pokemon_id)
    return bool(info) and pokemon_id in dados.carregar_legais() and not info["forma_de_batalha"]


def pokemon_aleatorio(time: list[str], sorteio=random) -> str:
    """Botão do dado: um Pokémon do meta que ainda não está no time.

    Sorteia entre os mais usados, sem repetir espécie e sem uma 2ª Mega.
    """
    pokemon = dados.carregar_pokemon()
    especies = {pokemon[p]["especie_base"] for p in time}
    tem_mega = any(pokemon[p]["mega"] for p in time)
    candidatos = [p for p in list(dados.carregar_uso()["pokemon"])[:QUANTOS_NO_SORTEIO]
                  if pode_escolher(p) and pokemon[p]["especie_base"] not in especies
                  and not (tem_mega and pokemon[p]["mega"])]
    return sorteio.choice(candidatos)


def pedra_da_mega(pokemon_id: str) -> str | None:
    """Pedra Mega que esta forma Mega precisa segurar (None se não for Mega)."""
    for item_id, pedra in dados.carregar_itens()["pedras_mega"].items():
        if pokemon_id in pedra["megas"]:
            return item_id
    return None


def forma_normal(pokemon_id: str) -> str:
    """Forma que Mega Evolui nesta Mega (Charizard-Mega-Y -> Charizard).

    Quase sempre é a espécie base. A Floette-Mega é exceção: quem Mega Evolui
    é a Floette-Eternal, e a Floette comum nem existe no Champions.
    """
    info = dados.carregar_pokemon().get(pokemon_id, {})
    pedra = pedra_da_mega(pokemon_id)
    if pedra and info.get("especie_base") not in dados.carregar_pokemon():
        return dados.carregar_itens()["pedras_mega"][pedra]["pokemon"]
    return info.get("especie_base", pokemon_id)


def opcoes_de_itens(pokemon_id: str) -> list[str]:
    """ids dos itens legais, sem Pedras Mega de outros Pokémon.

    Uma Mega (ex.: Beedrill-Mega) só pode segurar a própria Pedra Mega.
    """
    pedra = pedra_da_mega(pokemon_id)
    if pedra:
        return [pedra]
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
    aprende = movepool.get(pokemon_id) or movepool.get(forma_normal(pokemon_id)) or []
    aprende = [g for g in aprende if g in golpes]
    return _ordenar(aprende, _uso_do_pokemon(pokemon_id).get("golpes", {}),
                    lambda g: golpes[g]["nome"])


def montagem_recomendada(pokemon_id: str, sugestao: dict) -> dict:
    """Item, habilidade, 4 golpes, natureza e EVs da recomendação, prontos para o card.

    Só entra o que existe nas opções daquele Pokémon (ex.: a habilidade da Mega
    não está entre as da forma normal, então a habilidade fica como está).
    """
    item = sugestao["item"]["melhor"]
    habilidade = sugestao["habilidade"]["id"]
    golpes_validos = opcoes_de_golpes(pokemon_id)
    golpes = [g["id"] for g in sugestao["golpes"]["lista"] if g["id"] in golpes_validos]
    return {
        "item": item["id"] if item and item["id"] in opcoes_de_itens(pokemon_id) else None,
        "habilidade": habilidade if habilidade in opcoes_de_habilidades(pokemon_id) else None,
        "golpes": golpes[:4],
        "natureza": sugestao["natureza_evs"]["natureza"] or None,
        "evs": sugestao["natureza_evs"]["pontos"],
    }
