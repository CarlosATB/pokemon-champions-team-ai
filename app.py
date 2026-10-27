"""
Pokémon Champions Team AI — interface (Streamlit).

Para rodar localmente:
    streamlit run app.py

Por enquanto esta é só a página inicial. As partes de análise e recomendação
serão ligadas aqui nas próximas fases.
"""

import streamlit as st

from src import config

st.set_page_config(
    page_title="Pokémon Champions Team AI",
    page_icon="⚔️",
    layout="wide",
)

st.title("Pokémon Champions Team AI")
st.caption(
    f"Analisador e recomendador de times para duplas (VGC) · "
    f"{config.REGULATION_NAME} · dados de uso de {config.STATS_MONTH}"
)

st.info("🚧 Em construção. As próximas versões vão trazer a análise do time e as recomendações.")

st.subheader("O que esta IA vai fazer")
st.markdown(
    """
- **Analisar o seu time:** fraquezas por tipo, cobertura ofensiva e funções de duplas
  (controle de velocidade, Fake Out, Intimidate, redirecionamento, proteção).
- **Recomendar melhorias:** habilidades, itens, golpes e parceiros com base em dados
  reais de milhares de batalhas.
- **Explicar o porquê** de cada sugestão.
"""
)

with st.expander("Regras do formato consideradas"):
    st.markdown(
        f"""
- Nível {config.LEVEL}; leva {config.TEAM_SIZE} e escolhe {config.PICK_SIZE}.
- Não pode repetir espécie nem item.
- Até {config.MAX_MEGA_PER_BATTLE} Mega Evolução por batalha. Sem Terastalização.
- Formato no Showdown: `{config.FORMAT_ID}`
"""
    )
