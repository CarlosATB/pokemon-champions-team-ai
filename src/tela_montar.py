"""
Tela "Montar o time": os 6 cards no estilo do teambuilder do Showdown,
com os botões Importar/Exportar, o dado (Pokémon aleatório) e os ajustes
(natureza e pontos de status).

Cada seletor guarda o valor em st.session_state com uma chave própria:
    especie_{vaga}                 -> qual Pokémon está no card (vaga = 0 a 5)
    item_{vaga}_{pokemon}          -> item       (a chave inclui o Pokémon: ao
    habilidade_{vaga}_{pokemon}    -> habilidade  trocar de Pokémon, o card
    golpe_{vaga}_{n}_{pokemon}     -> golpe n     recomeça vazio)
    natureza_{vaga}_{pokemon}, ev_{vaga}_{status}_{pokemon}
Importar, o dado e "Montar com esta recomendação" só escrevem nessas chaves.
"""

import streamlit as st

from src import config, dados
from src.importar_exportar import NATUREZAS, exportar, importar
from src.leitor import completar
from src.opcoes import (
    montagem_recomendada, opcoes_de_golpes, opcoes_de_habilidades, opcoes_de_itens,
    pedra_da_mega, pode_escolher, pokemon_aleatorio,
)
from src.recomendacao import NOMES_EVS, sugerir_para_pokemon
from src.times_exemplo import TIMES_EXEMPLO
from src.visual import CATEGORIAS, etiqueta_tipo, etiquetas

VAGAS = range(config.TEAM_SIZE)


# ---------------------------------------------------------------------------
# Escrever nos cards (usado por Importar, pelo dado e pelas recomendações)
# ---------------------------------------------------------------------------

def preencher_card(vaga: int, card: dict) -> None:
    """Coloca um Pokémon e o que ele usa nos seletores de um card.

    card = {pokemon, item, habilidade, golpes, natureza, evs} (ids, como em importar()).
    """
    pid = card["pokemon"]
    estado = st.session_state
    estado[f"especie_{vaga}"] = pid
    estado[f"item_{vaga}_{pid}"] = card.get("item")
    if card.get("habilidade"):
        estado[f"habilidade_{vaga}_{pid}"] = card["habilidade"]
    else:  # sem habilidade: o seletor volta para a mais usada
        estado.pop(f"habilidade_{vaga}_{pid}", None)
    golpes = card.get("golpes", [])
    for n in range(4):
        estado[f"golpe_{vaga}_{n}_{pid}"] = golpes[n] if n < len(golpes) else None
    estado[f"natureza_{vaga}_{pid}"] = card.get("natureza")
    for status in NOMES_EVS:
        estado[f"ev_{vaga}_{status}_{pid}"] = card.get("evs", {}).get(status, 0)


def card_recomendado(pid: str, itens_ocupados: dict | None = None) -> dict:
    """O Pokémon montado com o que a maioria dos jogadores usa (Sistema de Recomendação)."""
    nome = dados.carregar_pokemon()[pid]["nome"]
    membro = completar({"especie": nome, "item": "", "habilidade": "", "natureza": "",
                        "golpes": []})
    sugestao = sugerir_para_pokemon(membro, itens_ocupados)
    if not sugestao["tem_dados"]:
        return {"pokemon": pid}
    return {"pokemon": pid, **montagem_recomendada(pid, sugestao)}


def _importar_texto(texto: str) -> None:
    cards, avisos = importar(texto)
    for vaga in VAGAS:
        if vaga < len(cards):
            preencher_card(vaga, cards[vaga])
        else:
            st.session_state[f"especie_{vaga}"] = None
    st.session_state["avisos_importar"] = avisos
    if not cards:
        st.session_state["avisos_importar"] = avisos + [
            "Nenhum Pokémon foi reconhecido. Cole o texto do botão Export do Showdown."]


def _ao_importar() -> None:
    _importar_texto(st.session_state["texto_importar"])


def _ao_carregar_exemplo() -> None:
    _importar_texto(TIMES_EXEMPLO[st.session_state["exemplo_escolhido"]])


def _ao_limpar() -> None:
    for vaga in VAGAS:
        st.session_state[f"especie_{vaga}"] = None
    st.session_state["avisos_importar"] = []


def _ao_sortear(vaga: int) -> None:
    """Dado: um Pokémon do meta que não está no time, já montado com a recomendação."""
    outros = {v: st.session_state.get(f"especie_{v}") for v in VAGAS if v != vaga}
    outros = {v: p for v, p in outros.items() if p}
    ocupados = {st.session_state.get(f"item_{v}_{p}"): p for v, p in outros.items()}
    preencher_card(vaga, card_recomendado(pokemon_aleatorio(list(outros.values())), ocupados))


# ---------------------------------------------------------------------------
# Desenho da tela
# ---------------------------------------------------------------------------

def _barra_de_botoes(cards: list[dict]) -> None:
    importar_, exportar_, limpar_ = st.columns([1, 1, 1])
    with importar_.popover("📥 Importar", width="stretch"):
        st.selectbox("Time de exemplo", list(TIMES_EXEMPLO), key="exemplo_escolhido")
        st.button("Carregar este exemplo", on_click=_ao_carregar_exemplo, width="stretch")
        st.divider()
        st.text_area("Ou cole o time exportado do Pokémon Showdown (botão Export)",
                     key="texto_importar", height=250,
                     placeholder="Incineroar @ Sitrus Berry\nAbility: Intimidate\n- Fake Out\n...")
        st.button("Importar", type="primary", on_click=_ao_importar, width="stretch")
    with exportar_.popover("📤 Exportar", width="stretch"):
        if cards:
            st.caption("Copie (botão no canto) e cole no Showdown: Teambuilder → "
                       "New Team → Import from text.")
            st.code(exportar(cards), language=None)
        else:
            st.info("Escolha pelo menos um Pokémon para exportar.")
    limpar_.button("🗑️ Limpar o time", on_click=_ao_limpar, width="stretch")
    avisos = st.session_state.get("avisos_importar", [])
    if avisos:
        st.warning("Algumas coisas do texto não entraram no time:\n\n"
                   + "\n".join(f"- {aviso}" for aviso in avisos), icon="⚠️")


def _ajustes(vaga: int, pid: str) -> None:
    """Botão de ajustes do card: natureza e pontos de status (os "EVs" do Champions)."""
    with st.popover("⚙️", help="Natureza e pontos de status (EVs)"):
        st.selectbox("Natureza", [None] + NATUREZAS, key=f"natureza_{vaga}_{pid}",
                     placeholder="(nenhuma)",
                     format_func=lambda n: "(nenhuma)" if n is None else n)
        st.caption(f"Pontos de status: até {config.EV_MAX} em cada, "
                   f"{config.EV_TOTAL} no total.")
        colunas = st.columns(3)
        total = sum(
            colunas[i % 3].number_input(status, 0, config.EV_MAX, step=1,
                                        key=f"ev_{vaga}_{status}_{pid}")
            for i, status in enumerate(NOMES_EVS))
        if total > config.EV_TOTAL:
            st.error(f"Total {total}: passou de {config.EV_TOTAL}. Tire {total - config.EV_TOTAL}.")
        else:
            st.caption(f"Total: {total} de {config.EV_TOTAL}")


def _card(vaga: int, nomes: dict, ids_ordenados: list[str]) -> dict | None:
    """Desenha um card e devolve o que foi escolhido nele (ou None se está vazio)."""
    pokemon = dados.carregar_pokemon()
    itens = dados.carregar_itens()["legais"]
    golpes = dados.carregar_golpes()
    habilidades = dados.carregar_habilidades()

    esquerda, direita = st.columns(2)
    with esquerda:
        pid = st.selectbox("Pokémon", [None] + ids_ordenados, key=f"especie_{vaga}",
                           label_visibility="collapsed", placeholder="Escolha um Pokémon",
                           format_func=lambda p: "Escolha um Pokémon" if p is None else nomes[p])
    if pid is None:
        with direita:
            st.markdown('<div class="vazio">Escolha na lista ou jogue o dado 🎲</div>',
                        unsafe_allow_html=True)
        esquerda.button("🎲", key=f"dado_{vaga}", on_click=_ao_sortear, args=(vaga,),
                        help="Pokémon aleatório do meta, já montado")
        return None

    with esquerda:
        # Tipos ao lado da imagem
        col_tipos, col_imagem = st.columns([1, 2], vertical_alignment="center")
        col_tipos.markdown(etiquetas(pokemon[pid]["tipos"]), unsafe_allow_html=True)
        imagem = config.SPRITES_DIR / f"{pid}.png"
        if imagem.exists():
            col_imagem.image(str(imagem), width=120)
        # Dado e ajustes embaixo da imagem
        col_dado, col_ajustes = st.columns(2)
        col_dado.button("🎲", key=f"dado_{vaga}", on_click=_ao_sortear, args=(vaga,),
                        help="Trocar por um Pokémon aleatório do meta, já montado")
        with col_ajustes:
            _ajustes(vaga, pid)
        # Item, com o ícone ao lado
        col_icone, col_item = st.columns([1, 6], vertical_alignment="center")
        pedra = pedra_da_mega(pid)
        with col_item:
            if pedra:  # a Mega já vem com a Pedra Mega dela, travada
                item = st.selectbox("Item", [pedra], key=f"item_{vaga}_{pid}", disabled=True,
                                    label_visibility="collapsed", format_func=itens.get,
                                    help="Para Mega Evoluir, ela precisa segurar esta pedra.")
            else:
                item = st.selectbox("Item", [None] + opcoes_de_itens(pid), key=f"item_{vaga}_{pid}",
                                    label_visibility="collapsed", placeholder="Sem item",
                                    format_func=lambda i: "Sem item" if i is None else itens[i])
        icone = config.ITEM_SPRITES_DIR / f"{item}.png"
        if item and icone.exists():
            col_icone.image(str(icone), width=28)

    with direita:
        escolhidos = []
        for n in range(4):
            col_tipo, col_golpe = st.columns([1, 3], vertical_alignment="center")
            golpe = col_golpe.selectbox(
                f"Golpe {n + 1}", [None] + opcoes_de_golpes(pid), key=f"golpe_{vaga}_{n}_{pid}",
                label_visibility="collapsed", placeholder=f"Golpe {n + 1}",
                format_func=lambda g: f"Golpe {n + 1}" if g is None else (
                    f"{golpes[g]['nome']} · {CATEGORIAS.get(golpes[g]['categoria'], '')}"))
            if golpe:
                col_tipo.markdown(etiqueta_tipo(golpes[golpe]["tipo"], pequena=True),
                                  unsafe_allow_html=True)
            escolhidos.append(golpe)
        habilidade = st.selectbox("Habilidade", opcoes_de_habilidades(pid),
                                  key=f"habilidade_{vaga}_{pid}", label_visibility="collapsed",
                                  format_func=lambda h: habilidades.get(h, h))

    return {
        "pokemon": pid,
        "item": item,
        "habilidade": habilidade,
        "golpes": [g for g in escolhidos if g],
        "natureza": st.session_state.get(f"natureza_{vaga}_{pid}"),
        "evs": {s: st.session_state.get(f"ev_{vaga}_{s}_{pid}", 0) for s in NOMES_EVS},
    }


def tela_montar_o_time() -> list[dict]:
    """Desenha a tela inteira. Devolve o time montado no formato do leitor
    (espécie, item, habilidade, natureza e golpes com os nomes do Showdown)."""
    uso = dados.carregar_uso()["pokemon"]
    pokemon = dados.carregar_pokemon()
    # Nome como no Showdown quando existe ("Indeedee-F"); senão, o da PokéAPI.
    nomes = {pid: uso.get(pid, info)["nome"] for pid, info in pokemon.items() if pode_escolher(pid)}
    ids_ordenados = sorted(nomes, key=nomes.get)

    # Os botões ficam em cima, mas o Exportar precisa dos cards: guardamos um
    # lugar para eles e desenhamos depois.
    barra = st.container()
    st.caption("As opções de item, habilidade e golpes vêm ordenadas pelo uso: "
               "as primeiras são as que os jogadores mais usam com aquele Pokémon.")
    cards = []
    for vaga in VAGAS:
        if vaga % 2 == 0:  # uma linha com 2 cards: grade de 2 colunas x 3 linhas
            colunas = st.columns(2)
        with colunas[vaga % 2].container(key=f"card_{vaga}"):
            card = _card(vaga, nomes, ids_ordenados)
        if card:
            cards.append({**card, "vaga": vaga})
    with barra:
        _barra_de_botoes(cards)

    itens = dados.carregar_itens()["legais"]
    golpes = dados.carregar_golpes()
    habilidades = dados.carregar_habilidades()
    return [{
        "vaga": card["vaga"],  # qual card: o botão das recomendações preenche este card
        "especie": nomes[card["pokemon"]],
        "item": itens[card["item"]] if card["item"] else "",
        "habilidade": habilidades.get(card["habilidade"], card["habilidade"] or ""),
        "natureza": card["natureza"] or "",
        "evs": card["evs"],
        "golpes": [golpes[g]["nome"] for g in card["golpes"]],
    } for card in cards]
