"""
Pokémon Champions Team AI — interface (Streamlit).

Para rodar localmente:
    streamlit run app.py

O site tem três abas no topo:
- Montar o time -> as três partes principais, cada uma desenhada por um arquivo de src/:
    1. Seu time      -> tela_montar.py        (6 cards, dado, Importar/Exportar do Showdown)
    2. Análise       -> tela_analise.py       (usa analise.py, dicas.py e validacao.py)
    3. Recomendações -> tela_recomendacoes.py (usa recomendacao.py: o Sistema de Recomendação)
- Mais usados   -> tela_mais_usados.py (os 20 mais usados no meta)
- Sobre         -> tela_sobre.py
"""

import streamlit as st

from src import config
from src.leitor import montar_time
from src.tela_analise import mostrar_analise
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
    st.title("Pokémon Champions Team AI")
    st.caption(f"Analisador e recomendador de times para duplas (VGC) · "
               f"{config.REGULATION_NAME} · dados de uso de {config.STATS_MONTH}")

    st.header("1. Seu time")
    time = montar_time(tela_montar_o_time())
    if not time:
        st.info("Monte o time nos cards acima (ou use 📥 Importar → Time de exemplo) "
                "para ver a análise e as recomendações.")
        return
    st.header("2. Análise")
    time_ok = mostrar_analise(time)
    if time_ok:
        st.header("3. Recomendações")
        mostrar_recomendacoes(time_ok)


st.set_page_config(page_title="Pokémon Champions Team AI", page_icon="⚔️", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
manter_o_time()
pagina = st.navigation([
    st.Page(pagina_montar_o_time, title="Montar o time", icon="🛠️", default=True),
    st.Page(mostrar_mais_usados, title="Mais usados", icon="📊", url_path="mais-usados"),
    st.Page(mostrar_sobre, title="Sobre", icon="ℹ️", url_path="sobre"),
], position="top")
pagina.run()
