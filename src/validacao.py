"""
Validação das regras do formato (duplas do Pokémon Champions).

Cada problema vira uma mensagem com um nível:
    "erro"  -> o time não pode ser usado assim (ex.: item repetido);
    "aviso" -> pode ser usado, mas vale conferir (ex.: duas Pedras Mega);
    "info"  -> só informação (ex.: o time ainda não tem 6 Pokémon).
"""

import difflib

from src import config, dados
from src.nomes import to_id


def sugestao_de_nome(nome_id: str) -> str:
    """"incinerar" -> ' Você quis dizer "Incineroar"?'"""
    pokemon = dados.carregar_pokemon()
    parecidos = difflib.get_close_matches(nome_id, dados.carregar_legais(), n=1)
    return f' Você quis dizer "{pokemon[parecidos[0]]["nome"]}"?' if parecidos else ""


def validar_time(time: list[dict]) -> list[dict]:
    """Confere o time contra as regras. Devolve [{nivel, mensagem}]."""
    pokemon = dados.carregar_pokemon()
    legais = set(dados.carregar_legais())
    itens = dados.carregar_itens()
    movepool = dados.carregar_movepool()
    golpes = dados.carregar_golpes()
    problemas = []

    def erro(mensagem):
        problemas.append({"nivel": "erro", "mensagem": mensagem})

    def aviso(mensagem):
        problemas.append({"nivel": "aviso", "mensagem": mensagem})

    # Tamanho do time: leva 6, escolhe 4.
    if len(time) > config.TEAM_SIZE:
        erro(f"O time tem {len(time)} Pokémon; o máximo é {config.TEAM_SIZE}.")
    elif len(time) < config.TEAM_SIZE:  # não é erro: o time ainda está sendo montado
        problemas.append({"nivel": "info", "mensagem":
                          f"O time tem {len(time)} de {config.TEAM_SIZE} Pokémon: a análise "
                          "considera só estes. Complete os cards para ela ficar completa."})

    especies_vistas = {}
    itens_vistos = {}
    megas = []
    for membro in time:
        nome = membro["especie"]
        info = pokemon.get(membro["id"])

        # 1. O Pokémon existe e é legal nesta regulamentação?
        if info is None:
            erro(f'"{nome}" não foi reconhecido.{sugestao_de_nome(membro["id"])}')
            continue
        if membro["id"] not in legais or info["forma_de_batalha"]:
            erro(f"{nome} não é permitido na {config.REGULATION_NAME}.")

        # 2. Espécie repetida (Charizard e Charizard-Mega-Y contam como a mesma).
        especie = info["especie_base"]
        if config.SPECIES_CLAUSE and especie in especies_vistas:
            erro(f"Espécie repetida: {especies_vistas[especie]} e {nome}.")
        especies_vistas[especie] = nome

        # 3. Item repetido e item fora do jogo.
        item_id = membro["item_id"]
        if item_id:
            if config.ITEM_CLAUSE and item_id in itens_vistos:
                erro(f"Item repetido: {itens_vistos[item_id]} e {nome} seguram {membro['item']}.")
            itens_vistos[item_id] = nome
            if item_id not in itens["legais"]:
                erro(f"O item {membro['item']} ({nome}) não existe no Pokémon Champions.")
            pedra = itens["pedras_mega"].get(item_id)
            if pedra and membro["forma"] not in pedra["megas"]:
                aviso(f"{nome} segura {membro['item']}, que é a Pedra Mega de outro Pokémon.")
        if pokemon.get(membro["forma"], {}).get("mega"):
            megas.append(nome)

        # 4. Golpes: no máximo 4, e que o Pokémon aprenda no Champions.
        if len(membro["golpes"]) > 4:
            erro(f"{nome} tem {len(membro['golpes'])} golpes; o máximo é 4.")
        aprende = movepool.get(membro["id"]) or movepool.get(especie)
        for golpe in membro["golpes"]:
            golpe_id = to_id(golpe)
            if golpe_id not in golpes:
                aviso(f'Golpe "{golpe}" ({nome}) não reconhecido no Champions.')
            elif aprende and golpe_id not in aprende:
                aviso(f"{nome} não aprende {golpe} no Champions.")

        # 5. Habilidade: precisa ser uma das habilidades do Pokémon.
        habilidade_id = to_id(membro["habilidade"])
        if habilidade_id and habilidade_id not in info["habilidades"]:
            aviso(f"{nome} normalmente não tem a habilidade {membro['habilidade']}.")

    # 6. Só uma Mega Evolução por batalha.
    if len(megas) > config.MAX_MEGA_PER_BATTLE:
        aviso(f"O time tem {len(megas)} Megas ({', '.join(megas)}), mas só "
              f"{config.MAX_MEGA_PER_BATTLE} pode Mega Evoluir por batalha.")
    return problemas


def tem_erro(problemas: list[dict]) -> bool:
    return any(p["nivel"] == "erro" for p in problemas)
