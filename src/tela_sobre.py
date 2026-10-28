"""
Aba "Sobre": o que é o projeto e as regras consideradas.
(Primeira versão; o texto vai ser desenvolvido na Fase 7.)
"""

import streamlit as st

from src import config, dados


def mostrar_sobre() -> None:
    st.title("Sobre")
    st.markdown(
        "Trabalho da disciplina de Inteligência Artificial (CEUB). Uma IA que analisa um time "
        "de Pokémon Champions (duplas) e recomenda melhorias usando estatísticas de batalhas "
        "reais: \"quem usa X também usa Y\".")
    st.info("Esta página ainda vai ser desenvolvida.", icon="🚧")

    uso = dados.carregar_uso()
    col1, col2, col3 = st.columns(3)
    col1.metric("Batalhas analisadas", f"{uso['batalhas']:,}".replace(",", "."))
    col2.metric("Pokémon com estatísticas", len(uso["pokemon"]))
    col3.metric("Pokémon/formas legais", len(dados.carregar_legais()))

    st.subheader("Regras do formato consideradas")
    st.markdown(
        f"""
- Nível {config.LEVEL}; leva {config.TEAM_SIZE} e escolhe {config.PICK_SIZE}.
- Não pode repetir espécie nem item.
- Até {config.MAX_MEGA_PER_BATTLE} Mega Evolução por batalha. Sem Terastalização.
- Pontos de status (EVs): até {config.EV_MAX} em cada, {config.EV_TOTAL} no total.
- Formato no Showdown: `{config.FORMAT_ID}`
"""
    )
