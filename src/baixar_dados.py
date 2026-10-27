"""
Baixa os dados do projeto e salva em data/processed/ (cache em JSON).

Rodar UMA vez no computador (precisa de internet), e depois sempre que a
regulamentação ou o mês das estatísticas mudar em src/config.py:

    python -m src.baixar_dados            # baixa tudo
    python -m src.baixar_dados legais     # só a lista de Pokémon legais
    python -m src.baixar_dados pokeapi    # só tipos e status base
    python -m src.baixar_dados smogon     # só as estatísticas de uso

São três fontes:
1. Pokémon Showdown -> quais Pokémon (e Megas) são legais na regulamentação.
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
    print("Pronto!")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "tudo")
