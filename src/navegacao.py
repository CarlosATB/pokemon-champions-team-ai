"""
Navegação da página "Montar o time": depois dos cards, o usuário escolhe o que ver.

    Análise da IA   -> veredito, categoria por categoria e ameaças do meta (tela_analise.py)
    Melhorar o time -> trocas, parceiros e montagem de cada Pokémon (tela_recomendacoes.py)
    Detalhes        -> gráficos, tabelas e como a IA aprendeu (tela_analise.py)

Os ícones são da biblioteca Material Symbols (":material/nome:" no Streamlit).

Os botões de "próximo passo" usam ir_para para trocar de visão.
"""

import streamlit as st

ANALISE, MELHORAR, DETALHES = "Análise da IA", "Melhorar o time", "Detalhes"
VISOES = [ANALISE, MELHORAR, DETALHES]
ICONES = {ANALISE: ":material/insights:", MELHORAR: ":material/auto_fix_high:",
          DETALHES: ":material/query_stats:"}
CHAVE = "visao"


def ir_para(visao: str) -> None:
    """Usado no on_click dos botões: muda a visão escolhida no seletor."""
    st.session_state[CHAVE] = visao


def escolher_visao() -> str:
    """O seletor das 3 visões. Se o usuário desmarcar, volta para a Análise."""
    visao = st.segmented_control("O que você quer ver?", VISOES, key=CHAVE, default=ANALISE,
                                 format_func=lambda v: f"{ICONES[v]} {v}",
                                 label_visibility="collapsed")
    return visao or ANALISE


def botao_ir_para(texto: str, visao: str, chave: str) -> None:
    st.button(texto, key=chave, on_click=ir_para, args=(visao,), type="primary",
              icon=":material/arrow_forward:", width="stretch")
