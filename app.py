"""
Pokémon Champions Team AI — interface (Streamlit).

Para rodar localmente:
    streamlit run app.py

O site tem três abas no topo:
- Montar o time -> 1. Seu time (tela_montar.py: 6 cards, dado, Importar/Exportar do Showdown)
                   2. O que a IA achou, com um seletor de 3 visões (navegacao.py):
                      Análise da IA   -> tela_analise.py       (nota, categorias, ameaças, próximo passo)
                      Melhorar o time -> tela_recomendacoes.py (trocas da IA, parceiros, montagem)
                      Detalhes        -> tela_analise.py       (gráficos, tabelas, como a IA aprendeu)
- Mais usados   -> tela_mais_usados.py (os 20 mais usados no meta)
- Sobre         -> tela_sobre.py
"""

import streamlit as st

from src import config
from src.leitor import montar_time
from src.navegacao import ANALISE, MELHORAR, escolher_visao
from src.tela_analise import mostrar_analise, mostrar_detalhes, mostrar_validacao, reconhecidos
from src.tela_mais_usados import mostrar_mais_usados
from src.tela_montar import tela_montar_o_time
from src.tela_recomendacoes import mostrar_recomendacoes
from src.tela_sobre import mostrar_sobre
from src.visual import CSS

# Prefixos das chaves dos seletores dos cards (ver src/tela_montar.py).
CHAVES_DO_TIME = ("especie_", "item_", "habilidade_", "golpe_", "natureza_", "ev_")


def manter_o_time() -> None:
    """O Streamlit apaga o valor de um seletor que não aparece na tela. Ao ir para
    outra aba, os cards somem; regravar os valores faz o time continuar lá na volta."""
    for chave in list(st.session_state):
        if chave.startswith(CHAVES_DO_TIME):
            st.session_state[chave] = st.session_state[chave]


def pagina_montar_o_time() -> None:
    st.caption(f"Analisador e recomendador de times para duplas (VGC) · "
               f"{config.REGULATION_NAME} · dados de uso de {config.STATS_MONTH}")

    st.header("1. Seu time")
    time = montar_time(tela_montar_o_time())
    if not time:
        st.info("Monte o time nos cards acima (ou use **Importar → Time de exemplo**) "
                "para ver o que a IA acha dele.", icon=":material/info:")
        return
    st.header("2. O que a IA achou")
    mostrar_validacao(time)
    time_ok = reconhecidos(time)
    if not time_ok:
        return
    visao = escolher_visao()
    if visao == ANALISE:
        mostrar_analise(time_ok)
    elif visao == MELHORAR:
        mostrar_recomendacoes(time_ok)
    else:
        mostrar_detalhes(time_ok)


st.set_page_config(page_title="Pokémon Champions Team AI", page_icon=":material/sports_esports:", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
st.logo("static/logo.svg", size="large")  # o nome do site vira logo na barra de cima
manter_o_time()
pagina = st.navigation([
    st.Page(pagina_montar_o_time, title="Montar o time", icon=":material/groups:", default=True),
    st.Page(mostrar_mais_usados, title="Mais usados", icon=":material/leaderboard:", url_path="mais-usados"),
    st.Page(mostrar_sobre, title="Sobre", icon=":material/info:", url_path="sobre"),
], position="top")
pagina.run()
