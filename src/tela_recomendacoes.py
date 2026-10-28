"""
Seção "3. Recomendações" do site: mostra o resultado de src/recomendacao.py.

Os botões usam preencher_card (src/tela_montar.py) para levar a sugestão
direto para os cards do time.
"""

import streamlit as st

from src.opcoes import montagem_recomendada
from src.recomendacao import (PESO_FRAQUEZAS, PESO_FUNCOES, PESO_PARCERIA, recomendar_time,
                              sugerir_parceiros, sugerir_substitutos)
from src.tela_montar import VAGAS, card_recomendado, preencher_card
from src.visual import imagem


def _marca(voce_usa: bool) -> str:
    return " ✅" if voce_usa else ""


def _itens_ocupados(time: list[dict], menos: dict | None = None) -> dict:
    """{item_id: quem segura}, para a recomendação não repetir item."""
    return {m["item_id"]: m["especie"] for m in time if m["item_id"] and m is not menos}


def _colocar_no_time(vaga: int, pokemon_id: str, ocupados: dict) -> None:
    preencher_card(vaga, card_recomendado(pokemon_id, ocupados))


def mostrar_por_pokemon(time: list[dict]) -> None:
    abas = st.tabs([m["especie"] for m in time])
    for aba, membro, sugestao in zip(abas, time, recomendar_time(time)):
        with aba:
            col_imagem, col1, col2 = st.columns([2, 4, 4])
            if imagem(membro["forma"]) or imagem(membro["id"]):
                col_imagem.image(imagem(membro["forma"]) or imagem(membro["id"]), width=96)
            if not sugestao["tem_dados"]:
                col1.info(sugestao["porque"])
                continue
            montagem = montagem_recomendada(membro["id"], sugestao)
            col_imagem.button("Montar com esta recomendação", key=f"montar_{membro['vaga']}",
                              on_click=preencher_card,
                              args=(membro["vaga"], {"pokemon": membro["id"], **montagem}),
                              help="Preenche o card deste Pokémon com o item, a habilidade, "
                                   "os 4 golpes, a natureza e os pontos de status mais usados.")
            hab, item, golpes, spread = (sugestao["habilidade"], sugestao["item"],
                                         sugestao["golpes"], sugestao["natureza_evs"])
            with col1:
                st.markdown(f"**Habilidade:** {hab['nome']}{_marca(hab['voce_usa'])}")
                st.caption(hab["porque"])
                melhor = item["melhor"]["nome"] if item["melhor"] else "-"
                st.markdown(f"**Item:** {melhor}{_marca(item['voce_usa'])}")
                st.caption(item["porque"])
                st.markdown(f"**Natureza:** {spread['natureza']}{_marca(spread['voce_usa'])}  \n"
                            f"**EVs:** {spread['evs']}")
                st.caption(spread["porque"])
            with col2:
                st.markdown("**Golpes mais usados**")
                st.dataframe([{"Golpe": g["nome"] + _marca(g["voce_usa"]), "Uso (%)": g["uso"]}
                              for g in golpes["lista"]], hide_index=True, width="stretch")
                st.caption(golpes["porque"])


def mostrar_parceiros(time: list[dict]) -> None:
    st.caption("Quem mais aparece junto com o seu time. Confiança = % dos times com os "
               "seus Pokémon que também têm ele (média). Lift > 1 = combinam mais que o acaso.")
    vagas_livres = [v for v in VAGAS if v not in {m["vaga"] for m in time}]
    colunas = st.columns(4)
    for n, parceiro in enumerate(sugerir_parceiros(time, quantos=8)):
        with colunas[n % 4].container(border=True):
            if imagem(parceiro["id"]):
                st.image(imagem(parceiro["id"]), width=80)
            st.markdown(f"**{parceiro['nome']}**  \n"
                        f"Confiança {parceiro['confianca']}% · Lift {parceiro['lift']}")
            st.caption(parceiro["porque"])
            st.button("Adicionar ao time", key=f"parceiro_{parceiro['id']}",
                      disabled=not vagas_livres, width="stretch",
                      on_click=_colocar_no_time,
                      args=(vagas_livres[0] if vagas_livres else 0, parceiro["id"],
                            _itens_ocupados(time)),
                      help="Coloca no primeiro card vazio, já montado com a recomendação."
                      if vagas_livres else "O time já tem 6. Use 'Trocar um Pokémon'.")


def mostrar_trocas(time: list[dict]) -> None:
    if len(time) < 2:
        st.info("Coloque pelo menos 2 Pokémon para sugerir trocas.")
        return
    automatico = "(a IA escolhe)"
    escolha = st.selectbox("Quem sai do time?", [automatico] + [m["especie"] for m in time])
    sai = None if escolha == automatico else next(m for m in time if m["especie"] == escolha)
    trocas = sugerir_substitutos(time, sai)
    membro_que_sai = next(m for m in time if m["especie"] == trocas["sai"])
    st.markdown(f"**Sai: {trocas['sai']}.** {trocas['motivo']}")
    if trocas["fraquezas"]:
        st.markdown("Fraquezas do time sem ele: " + ", ".join(trocas["fraquezas"]))
    if trocas["faltam"]:
        st.markdown("Funções de duplas que faltam sem ele: " + ", ".join(trocas["faltam"]))
    st.caption(f"Nota (0 a 100) = {PESO_PARCERIA:.0%} co-ocorrência com quem fica + "
               f"{PESO_FRAQUEZAS:.0%} quantas dessas fraquezas ele resiste + "
               f"{PESO_FUNCOES:.0%} quantas dessas funções ele traz (com os golpes mais "
               "usados com ele). Pelo menos 1 sugerido traz cada função essencial que falta.")
    for substituto in trocas["substitutos"]:
        with st.container(border=True):
            col_imagem, col_texto, col_botao = st.columns([1, 5, 2], vertical_alignment="center")
            if imagem(substituto["id"]):
                col_imagem.image(imagem(substituto["id"]), width=80)
            col_texto.markdown(
                f"**{substituto['nome']}** · nota **{substituto['nota']}**  \n"
                f"Traz: {', '.join(substituto['traz']) or '-'} · "
                f"Resiste a: {', '.join(substituto['cobre']) or '-'}")
            col_texto.caption(substituto["porque"])
            col_botao.button(f"Colocar no lugar de {trocas['sai']}",
                             key=f"trocar_{substituto['id']}", width="stretch",
                             on_click=_colocar_no_time,
                             args=(membro_que_sai["vaga"], substituto["id"],
                                   _itens_ocupados(time, menos=membro_que_sai)))


def mostrar_recomendacoes(time: list[dict]) -> None:
    st.caption("Baseadas no que os jogadores mais usam nas batalhas reais "
               "(\"quem usa X também usa Y\"). ✅ = você já usa.")
    aba_pokemon, aba_parceiros, aba_trocas = st.tabs(
        ["Por Pokémon", "Parceiros", "Trocar um Pokémon"])
    with aba_pokemon:
        mostrar_por_pokemon(time)
    with aba_parceiros:
        mostrar_parceiros(time)
    with aba_trocas:
        mostrar_trocas(time)
