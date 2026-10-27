"""
Padronização de nomes entre as fontes de dados.

Cada fonte escreve o mesmo Pokémon de um jeito:
    Smogon / Showdown:  "Charizard-Mega-Y", "Indeedee-F"
    PokéAPI:            "charizard-mega-y", "indeedee-female"

A solução é transformar todo nome num "id": só letras minúsculas e números.
    "Charizard-Mega-Y"  -> "charizardmegay"
    "charizard-mega-y"  -> "charizardmegay"
O id é a chave usada em todo o projeto. Quando o id da PokéAPI não bate com
o do Showdown, usamos a tabela de exceções abaixo.
"""

import re


def to_id(nome: str) -> str:
    """Transforma qualquer nome (Pokémon, golpe, item, habilidade) em id."""
    return re.sub(r"[^a-z0-9]", "", nome.lower())


# id do Showdown -> nome na PokéAPI, só para os casos em que to_id não basta.
# (Em geral a PokéAPI coloca a forma "padrão" no nome, ex.: "aegislash-shield".)
POKEAPI_EXCECOES = {
    "taurospaldeacombat": "tauros-paldea-combat-breed",
    "taurospaldeablaze": "tauros-paldea-blaze-breed",
    "taurospaldeaaqua": "tauros-paldea-aqua-breed",
    "basculegion": "basculegion-male",
    "basculegionf": "basculegion-female",
    "pyroar": "pyroar-male",
    "meowstic": "meowstic-male",
    "meowsticmmega": "meowstic-male-mega",
    "meowsticfmega": "meowstic-female-mega",
    "aegislash": "aegislash-shield",
    "gourgeist": "gourgeist-average",
    "lycanroc": "lycanroc-midday",
    "mimikyu": "mimikyu-disguised",
    "toxtricity": "toxtricity-amped",
    "indeedee": "indeedee-male",
    "indeedeef": "indeedee-female",
    "morpeko": "morpeko-full-belly",
    "palafin": "palafin-zero",
    "maushold": "maushold-family-of-four",
    "squawkabilly": "squawkabilly-green-plumage",
    "squawkabillyblue": "squawkabilly-blue-plumage",
    "squawkabillyyellow": "squawkabilly-yellow-plumage",
    "squawkabillywhite": "squawkabilly-white-plumage",
}

# Formas que só existem durante a batalha: não dá para escolher no time.
FORMAS_DE_BATALHA = {
    "castformsunny", "castformrainy", "castformsnowy",
    "aegislashblade",
}


def nome_pokeapi(pokemon_id: str, nomes_pokeapi: list[str]) -> str | None:
    """Acha o nome que a PokéAPI usa para um id do Showdown.

    `nomes_pokeapi` é a lista com todos os nomes da PokéAPI.
    Devolve None se não encontrar.
    """
    if pokemon_id in POKEAPI_EXCECOES:
        return POKEAPI_EXCECOES[pokemon_id]
    for nome in nomes_pokeapi:
        if to_id(nome) == pokemon_id:
            return nome
    return None
