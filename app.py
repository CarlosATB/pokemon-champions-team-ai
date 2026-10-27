"""
Pokémon Champions Team AI — interface (Streamlit).

Para rodar localmente:
    streamlit run app.py

Por enquanto esta é só a página inicial. As partes de análise e recomendação
serão ligadas aqui nas próximas fases.
"""

import streamlit as st

from src import config, dados
from src.tipos import TIPOS_PT

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

st.subheader("Dados carregados")
try:
    uso = dados.carregar_uso()
    pokemon = dados.carregar_pokemon()
except FileNotFoundError as erro:
    st.warning(str(erro))
else:
    col1, col2, col3 = st.columns(3)
    col1.metric("Batalhas analisadas", f"{uso['batalhas']:,}".replace(",", "."))
    col2.metric("Pokémon com estatísticas", len(uso["pokemon"]))
    col3.metric("Pokémon/formas legais", len(dados.carregar_legais()))

    def nome_de(pokemon_id):
        return uso["pokemon"].get(pokemon_id, {}).get("nome", pokemon_id)

    st.markdown("**Os 20 Pokémon mais usados**")
    linhas = []
    for pokemon_id, info in list(uso["pokemon"].items())[:20]:
        tipos = pokemon.get(pokemon_id, {}).get("tipos", [])
        linhas.append({
            "Pokémon": info["nome"],
            "Uso (%)": info["uso"],
            "Tipos": " / ".join(TIPOS_PT[t] for t in tipos),
            "Habilidade mais usada": next(iter(info["habilidades"]), "-"),
            "Item mais usado": next(iter(info["itens"]), "-"),
            "Parceiro mais comum": nome_de(next(iter(info["parceiros"]), "-")),
        })
    st.dataframe(linhas, hide_index=True, width="stretch")

with st.expander("Regras do formato consideradas"):
    st.markdown(
        f"""
- Nível {config.LEVEL}; leva {config.TEAM_SIZE} e escolhe {config.PICK_SIZE}.
- Não pode repetir espécie nem item.
- Até {config.MAX_MEGA_PER_BATTLE} Mega Evolução por batalha. Sem Terastalização.
- Formato no Showdown: `{config.FORMAT_ID}`
"""
    )
