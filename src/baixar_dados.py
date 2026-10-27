"""
Baixa os dados do projeto e salva em data/processed/ (cache em JSON).

Rodar UMA vez no computador (precisa de internet), e depois sempre que a
regulamentação ou o mês das estatísticas mudar em src/config.py:

    python -m src.baixar_dados            # baixa tudo
    python -m src.baixar_dados legais     # só a lista de Pokémon legais
    python -m src.baixar_dados pokeapi    # só tipos e status base
    python -m src.baixar_dados smogon     # só as estatísticas de uso
    python -m src.baixar_dados golpes     # só golpes, movepool, itens e habilidades

São três fontes:
1. Pokémon Showdown -> quais Pokémon (e Megas) são legais na regulamentação,
                       e também golpes, movepool, itens e nomes das habilidades do Champions.
2. PokéAPI          -> tipos, status base e habilidades de cada Pokémon legal.
3. Smogon           -> estatísticas de uso: habilidades, itens, golpes,
                       EVs e parceiros mais usados por cada Pokémon.

O site só lê os JSON gerados aqui; ele nunca baixa nada ao vivo.
"""

import json
import re
import sys
import time

import requests

from src import config
from src.nomes import FORMAS_DE_BATALHA, nome_pokeapi, to_id

TIMEOUT = 60  # segundos


def baixar_json(url: str) -> dict:
    resposta = requests.get(url, timeout=TIMEOUT)
    resposta.raise_for_status()
    return resposta.json()


def salvar_json(dados, caminho) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=1)
    print(f"  salvo: {caminho.relative_to(config.ROOT_DIR)}")


# ---------------------------------------------------------------------------
# 1. Lista de Pokémon legais (Pokémon Showdown)
# ---------------------------------------------------------------------------

def processar_legais(texto_ts: str) -> list[str]:
    """Lê o arquivo formats-data.ts do Showdown e devolve os ids legais.

    O arquivo tem um bloco por Pokémon, por exemplo:
        bulbasaur: {
            isNonstandard: "Past",     <- não está no jogo
            tier: "Illegal",
        },
    Um Pokémon é legal quando o bloco não tem "isNonstandard" nem "Illegal".
    """
    blocos = re.findall(r"^\t(\w+): \{(.*?)^\t\},", texto_ts, re.MULTILINE | re.DOTALL)
    return [
        pokemon_id
        for pokemon_id, conteudo in blocos
        if "isNonstandard" not in conteudo and "Illegal" not in conteudo
    ]


def baixar_legais() -> list[str]:
    print("Baixando a lista de Pokémon legais (Showdown)...")
    resposta = requests.get(config.showdown_legalidade_url(), timeout=TIMEOUT)
    resposta.raise_for_status()
    legais = processar_legais(resposta.text)
    salvar_json(
        {"regulamentacao": config.REGULATION_NAME, "mod": config.SHOWDOWN_MOD, "legais": legais},
        config.LEGAIS_FILE,
    )
    print(f"  {len(legais)} Pokémon/formas legais")
    return legais


# ---------------------------------------------------------------------------
# 2. Tipos e status base (PokéAPI)
# ---------------------------------------------------------------------------

# Nome do status na PokéAPI -> sigla usada no projeto (igual ao Showdown).
STATUS = {
    "hp": "hp", "attack": "atk", "defense": "def",
    "special-attack": "spa", "special-defense": "spd", "speed": "spe",
}


def processar_pokeapi(pokemon_id: str, dados: dict) -> dict:
    """Pega só o que interessa da resposta da PokéAPI para um Pokémon."""
    nome = dados["name"]
    return {
        "id": pokemon_id,
        "nome": nome.title(),  # "charizard-mega-y" -> "Charizard-Mega-Y"
        "tipos": [t["type"]["name"].capitalize() for t in dados["types"]],
        "status": {STATUS[s["stat"]["name"]]: s["base_stat"] for s in dados["stats"]},
        "habilidades": [to_id(h["ability"]["name"]) for h in dados["abilities"]],
        "especie_base": to_id(dados["species"]["name"]),
        "mega": "-mega" in nome,
        "forma_de_batalha": pokemon_id in FORMAS_DE_BATALHA,
    }


def baixar_pokeapi(legais: list[str]) -> dict:
    print(f"Baixando tipos e status base de {len(legais)} Pokémon (PokéAPI)...")
    lista = baixar_json(f"{config.POKEAPI_BASE}/pokemon?limit=3000")
    nomes_pokeapi = [p["name"] for p in lista["results"]]

    pokemon = {}
    nao_encontrados = []
    for i, pokemon_id in enumerate(legais, start=1):
        nome = nome_pokeapi(pokemon_id, nomes_pokeapi)
        if nome is None:
            nao_encontrados.append(pokemon_id)
            continue
        dados = baixar_json(f"{config.POKEAPI_BASE}/pokemon/{nome}")
        pokemon[pokemon_id] = processar_pokeapi(pokemon_id, dados)
        if i % 50 == 0:
            print(f"  {i}/{len(legais)}")
        time.sleep(0.1)  # educação com a API gratuita

    salvar_json(pokemon, config.POKEMON_FILE)
    if nao_encontrados:
        print(f"  ATENÇÃO, sem par na PokéAPI (adicionar em src/nomes.py): {nao_encontrados}")
    return pokemon


# ---------------------------------------------------------------------------
# 3. Estatísticas de uso (Smogon)
# ---------------------------------------------------------------------------

def _porcentagens(contagens: dict, total: float, minimo: float, usar_id: bool = False) -> dict:
    """Converte contagens em % do total, ordena e corta o que for < minimo%."""
    resultado = {}
    for chave, valor in sorted(contagens.items(), key=lambda kv: kv[1], reverse=True):
        porcentagem = round(100 * valor / total, 1)
        if chave and porcentagem >= minimo:
            resultado[to_id(chave) if usar_id else chave] = porcentagem
    return resultado


def processar_smogon(chaos: dict, minimo: float = 1.0) -> dict:
    """Resume o arquivo 'chaos' do Smogon.

    Para cada Pokémon, guarda a % de uso no formato e, entre os times que
    usam esse Pokémon, a % que usa cada habilidade, item, golpe, EVs e
    parceiro. Ex.: parceiros["rillaboom"] = 40.0 quer dizer que 40% dos
    times com este Pokémon também têm Rillaboom (co-ocorrência).
    """
    pokemon = {}
    for nome, dados in chaos["data"].items():
        # Cada time com o Pokémon conta uma habilidade, então a soma das
        # habilidades é o "total" de vezes que ele foi usado (com peso).
        total = sum(dados["Abilities"].values()) or 1
        pokemon[to_id(nome)] = {
            "nome": nome,
            "uso": round(100 * dados["usage"], 2),
            "habilidades": _porcentagens(dados["Abilities"], total, minimo),
            "itens": _porcentagens(dados["Items"], total, minimo),
            "golpes": _porcentagens(dados["Moves"], total, minimo),
            "spreads": _porcentagens(dados["Spreads"], total, minimo),
            "parceiros": _porcentagens(dados["Teammates"], total, minimo, usar_id=True),
        }

    # Do mais usado para o menos usado.
    pokemon = dict(sorted(pokemon.items(), key=lambda kv: kv[1]["uso"], reverse=True))
    return {
        "formato": config.FORMAT_ID,
        "mes": config.STATS_MONTH,
        "rating": config.STATS_RATING,
        "batalhas": chaos["info"].get("number of battles"),
        "pokemon": pokemon,
    }


def baixar_smogon() -> dict:
    url = config.smogon_chaos_url()
    print(f"Baixando estatísticas de uso (Smogon): {url}")
    try:
        chaos = baixar_json(url)
    except requests.HTTPError as erro:
        print(
            f"  ERRO: {erro}. Talvez o mês {config.STATS_MONTH} ainda não foi publicado "
            "ou o formato mudou. Confira em https://www.smogon.com/stats/ e ajuste src/config.py."
        )
        raise
    salvar_json(chaos, config.RAW_DATA_DIR / f"{config.FORMAT_ID}-{config.STATS_MONTH}-{config.STATS_RATING}.json")
    uso = processar_smogon(chaos)
    salvar_json(uso, config.USO_FILE)
    print(f"  {len(uso['pokemon'])} Pokémon, {uso['batalhas']} batalhas")
    return uso


# ---------------------------------------------------------------------------
# 4. Golpes, movepool e itens (Pokémon Showdown)
# ---------------------------------------------------------------------------
# Os arquivos do Showdown são código TypeScript, com um bloco por golpe/item:
#     fakeout: {
#         name: "Fake Out",
#         type: "Normal",
#         ...
#     },
# O mod do Champions só lista o que MUDA em relação ao jogo base
# (ex.: um golpe com outro poder). Então lemos o base e aplicamos o mod por cima.

def _blocos_ts(texto_ts: str) -> dict[str, str]:
    """{id: conteúdo do bloco} de um arquivo .ts do Showdown."""
    blocos = re.findall(r'^\t"?(\w+)"?: \{(.*?)^\t\},', texto_ts, re.MULTILINE | re.DOTALL)
    return dict(blocos)


def _campo(bloco: str, nome: str) -> str | None:
    """Valor de um campo do primeiro nível do bloco (ex.: type: "Fire" -> "Fire")."""
    achado = re.search(rf"^\t\t{nome}: (.*?),$", bloco, re.MULTILINE)
    return achado.group(1).strip('"') if achado else None


def processar_movepool(learnsets_ts: str) -> dict[str, list[str]]:
    """Lê o learnsets.ts do mod: {pokemon_id: [golpes que ele aprende]}.

    Megas não têm lista própria: usam a da forma normal (ver src/analise).
    """
    blocos = re.findall(
        r"^\t(\w+): \{\n\t\tlearnset: \{(.*?)^\t\t\}", learnsets_ts, re.MULTILINE | re.DOTALL
    )
    return {pokemon_id: re.findall(r"^\t\t\t(\w+):", golpes, re.MULTILINE)
            for pokemon_id, golpes in blocos}


def processar_golpes(base_ts: str, mod_ts: str, aprendiveis: set[str]) -> dict:
    """{golpe_id: {nome, tipo, categoria, poder, alvo}} dos golpes do Champions.

    Só entram os golpes que algum Pokémon aprende (`aprendiveis`).
    """
    base = _blocos_ts(base_ts)
    mod = _blocos_ts(mod_ts)
    golpes = {}
    for golpe_id in sorted(aprendiveis):
        if golpe_id not in base:
            continue
        info = {}
        for campo, chave in [("name", "nome"), ("type", "tipo"), ("category", "categoria"),
                             ("basePower", "poder"), ("target", "alvo")]:
            valor = _campo(base[golpe_id], campo)
            if golpe_id in mod and _campo(mod[golpe_id], campo) is not None:
                valor = _campo(mod[golpe_id], campo)  # o Champions mudou este campo
            info[chave] = valor
        info["poder"] = int(info["poder"] or 0)
        golpes[golpe_id] = info
    return golpes


def processar_itens(base_ts: str, mod_ts: str) -> dict:
    """Itens legais no Champions e as Pedras Mega (item -> Pokémon e Mega).

    Um item é legal quando não está marcado como isNonstandard (ou o mod
    do Champions tira essa marca com isNonstandard: null).
    """
    base = _blocos_ts(base_ts)
    mod = _blocos_ts(mod_ts)
    legais = {}
    pedras_mega = {}
    for item_id, bloco in base.items():
        fora = _campo(bloco, "isNonstandard")
        if item_id in mod and _campo(mod[item_id], "isNonstandard") is not None:
            fora = _campo(mod[item_id], "isNonstandard")
        if fora not in (None, "null"):
            continue
        nome = _campo(bloco, "name")
        legais[item_id] = nome
        pedra = re.search(r'megaStone: \{ "(.+?)": "(.+?)" \}', bloco)
        if pedra:
            pedras_mega[item_id] = {"pokemon": to_id(pedra.group(1)), "mega": to_id(pedra.group(2))}
    return {"legais": legais, "pedras_mega": pedras_mega}


def processar_habilidades(base_ts: str) -> dict[str, str]:
    """{habilidade_id: nome}, só para mostrar o nome bonito ("Grassy Surge")."""
    return {habilidade_id: _campo(bloco, "name")
            for habilidade_id, bloco in _blocos_ts(base_ts).items() if _campo(bloco, "name")}


def baixar_golpes() -> None:
    print("Baixando golpes, movepool, itens e habilidades do Champions (Showdown)...")

    def texto(url):
        resposta = requests.get(url, timeout=TIMEOUT)
        resposta.raise_for_status()
        return resposta.text

    movepool = processar_movepool(texto(config.showdown_url("learnsets.ts")))
    salvar_json(movepool, config.MOVEPOOL_FILE)

    aprendiveis = {golpe for golpes in movepool.values() for golpe in golpes}
    if config.USO_FILE.exists():
        # Golpes que aparecem nas batalhas mas faltam no movepool (ex.: golpes de
        # evento, como o Light of Ruin da Floette Eterna) também precisam de dados.
        with open(config.USO_FILE, encoding="utf-8") as arquivo:
            uso = json.load(arquivo)
        aprendiveis |= {golpe for info in uso["pokemon"].values() for golpe in info["golpes"]}
    golpes = processar_golpes(
        texto(config.showdown_url("moves.ts", mod=None)),
        texto(config.showdown_url("moves.ts")),
        aprendiveis,
    )
    salvar_json(golpes, config.GOLPES_FILE)

    itens = processar_itens(
        texto(config.showdown_url("items.ts", mod=None)),
        texto(config.showdown_url("items.ts")),
    )
    salvar_json(itens, config.ITENS_FILE)

    habilidades = processar_habilidades(texto(config.showdown_url("abilities.ts", mod=None)))
    salvar_json(habilidades, config.HABILIDADES_FILE)
    print(f"  {len(movepool)} Pokémon com movepool, {len(golpes)} golpes, "
          f"{len(itens['legais'])} itens ({len(itens['pedras_mega'])} Pedras Mega), "
          f"{len(habilidades)} habilidades")


# ---------------------------------------------------------------------------

def main(etapa: str = "tudo") -> None:
    if etapa in ("legais", "tudo"):
        legais = baixar_legais()
    if etapa in ("pokeapi", "tudo"):
        if etapa == "pokeapi":
            with open(config.LEGAIS_FILE, encoding="utf-8") as arquivo:
                legais = json.load(arquivo)["legais"]
        baixar_pokeapi(legais)
    if etapa in ("smogon", "tudo"):
        baixar_smogon()
    if etapa in ("golpes", "tudo"):
        baixar_golpes()
    print("Pronto!")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "tudo")
