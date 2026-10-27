"""
Configuração central do projeto.

Tudo que depende da regulamentação atual do Pokémon Champions fica AQUI.
Quando a regulamentação mudar (ex.: M-C -> M-D), basta atualizar este arquivo
e baixar os dados novamente. Nenhum outro arquivo precisa ser alterado.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Regulamentação / formato
# ---------------------------------------------------------------------------

# Nome amigável, usado na interface.
REGULATION_NAME = "Regulamentação M-C"

# Código do formato no Pokémon Showdown / estatísticas do Smogon.
# Duplas (VGC) do Pokémon Champions, regulamentação M-C.
FORMAT_ID = "gen9championsvgc2026regmc"

# Mês das estatísticas de uso do Smogon (formato AAAA-MM).
STATS_MONTH = "2026-09"

# Corte de rating das estatísticas do Smogon.
# 0 = todas as batalhas | 1500 / 1630 / 1760 = só jogadores mais fortes.
# 1500 é um bom equilíbrio entre quantidade de dados e qualidade dos jogadores.
STATS_RATING = 1500

# ---------------------------------------------------------------------------
# Regras do formato (duplas do Pokémon Champions)
# ---------------------------------------------------------------------------

LEVEL = 50            # todos os Pokémon jogam no nível 50
TEAM_SIZE = 6         # leva 6 para a batalha...
PICK_SIZE = 4         # ...e escolhe 4
SPECIES_CLAUSE = True  # não pode repetir espécie
ITEM_CLAUSE = True     # não pode repetir item
MAX_MEGA_PER_BATTLE = 1  # só uma Mega Evolução por batalha
HAS_TERA = False       # o Champions não tem Terastalização

# ---------------------------------------------------------------------------
# Fontes de dados
# ---------------------------------------------------------------------------

SMOGON_STATS_BASE = "https://www.smogon.com/stats"
POKEAPI_BASE = "https://pokeapi.co/api/v2"


def smogon_chaos_url(
    month: str = STATS_MONTH,
    format_id: str = FORMAT_ID,
    rating: int = STATS_RATING,
) -> str:
    """URL do arquivo 'chaos' do Smogon: o JSON completo com uso, golpes,
    habilidades, itens, EVs e parceiros de cada Pokémon."""
    return f"{SMOGON_STATS_BASE}/{month}/chaos/{format_id}-{rating}.json"


# ---------------------------------------------------------------------------
# Pastas do projeto
# ---------------------------------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"              # dados baixados, sem tratamento
PROCESSED_DATA_DIR = DATA_DIR / "processed"  # dados limpos, usados pelo app
