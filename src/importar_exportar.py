"""
Botões Importar e Exportar da tela "Montar o time" (formato do Pokémon Showdown).

- Importar: o texto colado vira o conteúdo dos 6 cards (ids que os seletores usam).
  O que não existe no Champions não entra no card e vira um aviso em português.
- Exportar: os cards viram o texto que o Showdown aceita em "Import from text".
"""

from src import config, dados
from src.leitor import ler_time
from src.nomes import to_id
from src.opcoes import (opcoes_de_golpes, opcoes_de_habilidades, opcoes_de_itens,
                        pedra_da_mega, pode_escolher)
from src.recomendacao import NOMES_EVS
from src.validacao import sugestao_de_nome

NATUREZAS = [
    "Adamant", "Bashful", "Bold", "Brave", "Calm", "Careful", "Docile", "Gentle", "Hardy",
    "Hasty", "Impish", "Jolly", "Lax", "Lonely", "Mild", "Modest", "Naive", "Naughty",
    "Quiet", "Quirky", "Rash", "Relaxed", "Sassy", "Serious", "Timid",
]


# ---------------------------------------------------------------------------
# Importar: texto do Showdown -> cards
# ---------------------------------------------------------------------------

def card_do_membro(membro: dict) -> tuple[dict | None, list[str]]:
    """Um Pokémon lido do texto -> conteúdo de um card + avisos do que ficou de fora."""
    nome = membro["especie"]
    pid = membro["id"]
    if not pode_escolher(pid):
        if pid in dados.carregar_pokemon():
            return None, [f"{nome} não é permitido na {config.REGULATION_NAME}."]
        return None, [f'"{nome}" não foi reconhecido.{sugestao_de_nome(pid)}']

    avisos = []
    card = {"pokemon": pid, "item": None, "habilidade": None, "golpes": [],
            "natureza": None, "evs": {}}

    item_id = membro["item_id"]
    if item_id in opcoes_de_itens(pid):
        card["item"] = item_id
    elif item_id:
        avisos.append(f"{nome}: o item {membro['item']} não existe no Champions "
                      "ou é a Pedra Mega de outro Pokémon.")
    if pedra_da_mega(pid):  # a forma Mega segura sempre a própria pedra
        card["item"] = pedra_da_mega(pid)

    habilidade_id = to_id(membro["habilidade"])
    if habilidade_id in opcoes_de_habilidades(pid):
        card["habilidade"] = habilidade_id
    elif habilidade_id:
        avisos.append(f"{nome} não pode ter a habilidade {membro['habilidade']}.")

    podem = opcoes_de_golpes(pid)
    for golpe in membro["golpes"][:4]:
        if to_id(golpe) in podem:
            card["golpes"].append(to_id(golpe))
        else:
            avisos.append(f"{nome} não aprende {golpe} no Champions.")
    if len(membro["golpes"]) > 4:
        avisos.append(f"{nome} tinha {len(membro['golpes'])} golpes; ficaram só os 4 primeiros.")

    natureza = membro["natureza"].capitalize()
    card["natureza"] = natureza if natureza in NATUREZAS else None
    card["evs"] = {status: min(valor, config.EV_MAX)
                   for status, valor in membro.get("evs", {}).items() if status in NOMES_EVS}
    return card, avisos


def importar(texto: str) -> tuple[list[dict], list[str]]:
    """Texto exportado do Showdown -> (cards, avisos). No máximo 6 cards."""
    cards, avisos = [], []
    for membro in ler_time(texto):
        card, problemas = card_do_membro(membro)
        avisos += problemas
        if card:
            cards.append(card)
    if len(cards) > config.TEAM_SIZE:
        avisos.append(f"O texto tinha {len(cards)} Pokémon; ficaram só os "
                      f"{config.TEAM_SIZE} primeiros.")
    return cards[:config.TEAM_SIZE], avisos


# ---------------------------------------------------------------------------
# Exportar: cards -> texto do Showdown
# ---------------------------------------------------------------------------

def exportar(cards: list[dict]) -> str:
    """Os cards montados -> texto para colar no Showdown ("Import from text").

    Uma forma Mega (ex.: Beedrill-Mega) sai como a forma normal segurando a
    Pedra Mega: é assim que o Showdown monta o time. A habilidade da Mega só
    existe depois de Mega Evoluir, então vai a habilidade mais usada da normal.
    """
    pokemon = dados.carregar_pokemon()
    uso = dados.carregar_uso()["pokemon"]
    itens = dados.carregar_itens()["legais"]
    habilidades = dados.carregar_habilidades()
    golpes = dados.carregar_golpes()

    def nome(pid):  # nome como no Showdown ("Indeedee-F") quando existe
        return uso.get(pid, pokemon[pid])["nome"]

    blocos = []
    for card in cards:
        pid, habilidade = card["pokemon"], card["habilidade"]
        if pokemon[pid]["mega"]:
            pid = pokemon[pid]["especie_base"]
            habilidade = (opcoes_de_habilidades(pid) or [None])[0]
        linhas = [nome(pid) + (f" @ {itens[card['item']]}" if card["item"] else "")]
        if habilidade:
            linhas.append(f"Ability: {habilidades.get(habilidade, habilidade)}")
        linhas.append(f"Level: {config.LEVEL}")
        evs = [f"{card['evs'][s]} {s}" for s in NOMES_EVS if card["evs"].get(s)]
        if evs:
            linhas.append("EVs: " + " / ".join(evs))
        if card["natureza"]:
            linhas.append(f"{card['natureza']} Nature")
        linhas += [f"- {golpes[g]['nome']}" for g in card["golpes"] if g]
        blocos.append("\n".join(linhas))
    return "\n\n".join(blocos) + "\n"
