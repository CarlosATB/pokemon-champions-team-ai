"""
Leitura dos dados já baixados (data/processed/*.json).

O resto do projeto usa só estas funções; ninguém precisa saber de onde
os dados vieram. Para gerar os arquivos: python -m src.baixar_dados
"""

import json
from functools import lru_cache

from src import config
from src.nomes import to_id


def _ler(caminho) -> dict:
    if not caminho.exists():
        raise FileNotFoundError(
            f"{caminho.name} não encontrado. Rode antes: python -m src.baixar_dados"
        )
    with open(caminho, encoding="utf-8") as arquivo:
        return json.load(arquivo)


@lru_cache  # lê o arquivo do disco só uma vez
def carregar_legais() -> list[str]:
    """ids de todos os Pokémon e Megas legais na regulamentação."""
    return _ler(config.LEGAIS_FILE)["legais"]


@lru_cache
def carregar_pokemon() -> dict:
    """id -> {nome, tipos, status, habilidades, especie_base, mega, forma_de_batalha}"""
    return _ler(config.POKEMON_FILE)


@lru_cache
def carregar_uso() -> dict:
    """Estatísticas de uso do Smogon: {formato, mes, batalhas, pokemon: {id: ...}}"""
    return _ler(config.USO_FILE)


def buscar_pokemon(nome: str) -> dict | None:
    """Acha um Pokémon pelo nome, em qualquer grafia: "Indeedee-F", "indeedee f"..."""
    return carregar_pokemon().get(to_id(nome))


def eh_legal(nome: str) -> bool:
    return to_id(nome) in carregar_legais()
