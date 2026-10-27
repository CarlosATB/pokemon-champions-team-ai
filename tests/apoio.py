"""Funções de apoio para os testes da Fase 2 (análise do time)."""

import pytest

from src import config
from src.leitor import ler_time
from src.times_exemplo import TIMES_EXEMPLO

# A análise precisa de todos os arquivos de data/processed.
precisa_dados = pytest.mark.skipif(
    not all(arquivo.exists() for arquivo in [
        config.LEGAIS_FILE, config.POKEMON_FILE, config.USO_FILE,
        config.GOLPES_FILE, config.MOVEPOOL_FILE, config.ITENS_FILE,
    ]),
    reason="dados ainda não baixados (python -m src.baixar_dados)",
)


def time_exemplo(inicio_do_nome: str) -> list[dict]:
    """Lê um dos times de src/times_exemplo.py pelo começo do nome."""
    for nome, texto in TIMES_EXEMPLO.items():
        if nome.startswith(inicio_do_nome):
            return ler_time(texto)
    raise KeyError(inicio_do_nome)
