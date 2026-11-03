"""
Navegação da página "Montar o time": depois dos cards, o usuário escolhe o que ver.

    📊 Análise da IA  -> o veredito da IA, categoria por categoria (tela_analise.py)
    🛠️ Melhorar o time -> trocas, parceiros e montagem de cada Pokémon (tela_recomendacoes.py)
    🔎 Detalhes        -> gráficos, tabelas e como a IA aprendeu (tela_analise.py)

Os botões de "próximo passo" usam ir_para para trocar de visão.
"""

import streamlit as st

ANALISE, MELHORAR, DETALHES = "📊 Análise da IA", "🛠️ Melhorar o time", "🔎 Detalhes"
VISOES = [ANALISE, MELHORAR, DETALHES]
CHAVE = "visao"


def ir_para(visao: str) -> None:
    """Usado no on_click dos botões: muda a visão escolhida no seletor."""
    st.session_state[CHAVE] = visao


def escolher_visao() -> str:
    """O seletor das 3 visões. Se o usuário desmarcar, volta para a Análise."""
    visao = st.segmented_control("O que você quer ver?", VISOES, key=CHAVE, default=ANALISE,
                                 label_visibility="collapsed")
    return visao or ANALISE


def botao_ir_para(texto: str, visao: str, chave: str) -> None:
    st.button(texto, key=chave, on_click=ir_para, args=(visao,), type="primary")
