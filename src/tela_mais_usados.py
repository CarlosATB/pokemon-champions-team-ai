"""
Aba "Mais usados": os 20 Pokémon mais usados no meta, com imagem e o que
cada um mais usa (dados do Smogon, src/dados.py -> uso.json).
"""

import streamlit as st

from src import config, dados
from src.recomendacao import nome_da_habilidade, nome_do_item, nome_do_pokemon
from src.visual import etiquetas, imagem

QUANTOS = 20


def mostrar_mais_usados() -> None:
    uso = dados.carregar_uso()
    pokemon = dados.carregar_pokemon()
    st.title("Os 20 Pokémon mais usados")
    st.caption(f"{config.REGULATION_NAME} · estatísticas de {config.STATS_MONTH} "
               f"({uso['batalhas']:,} batalhas)".replace(",", "."))

    colunas = st.columns(4)
    for posicao, (pokemon_id, info) in enumerate(list(uso["pokemon"].items())[:QUANTOS], start=1):
        with colunas[(posicao - 1) % 4].container(border=True):
            col_imagem, col_nome = st.columns([1, 2], vertical_alignment="center")
            if imagem(pokemon_id):
                col_imagem.image(imagem(pokemon_id), width=72)
            col_nome.markdown(f"**#{posicao} {info['nome']}**  \n{info['uso']:.1f}% dos times")
            st.markdown(etiquetas(pokemon.get(pokemon_id, {}).get("tipos", [])),
                        unsafe_allow_html=True)
            st.caption(
                f"Habilidade: {nome_da_habilidade(next(iter(info['habilidades']), '-'))}  \n"
                f"Item: {nome_do_item(next(iter(info['itens']), '-'))}  \n"
                f"Parceiro: {nome_do_pokemon(next(iter(info['parceiros']), '-'))}")
