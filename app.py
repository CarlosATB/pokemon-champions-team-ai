"""
Pokémon Champions Team AI — interface (Streamlit).

Para rodar localmente:
    streamlit run app.py

A página tem três partes, cada uma desenhada por um arquivo de src/:
1. Seu time      -> tela_montar.py        (6 cards, dado, Importar/Exportar do Showdown)
2. Análise       -> tela_analise.py       (usa analise.py, dicas.py e validacao.py)
3. Recomendações -> tela_recomendacoes.py (usa recomendacao.py: o Sistema de Recomendação)
"""

import streamlit as st

from src import config, dados
from src.leitor import montar_time
from src.recomendacao import nome_da_habilidade, nome_do_item, nome_do_pokemon
from src.tela_analise import mostrar_analise
from src.tela_montar import tela_montar_o_time
from src.tela_recomendacoes import mostrar_recomendacoes
from src.tipos import TIPOS_PT
from src.visual import CSS

st.set_page_config(
    page_title="Pokémon Champions Team AI",
    page_icon="⚔️",
    layout="wide",
)

st.markdown(CSS, unsafe_allow_html=True)
st.title("Pokémon Champions Team AI")
st.caption(
    f"Analisador e recomendador de times para duplas (VGC) · "
    f"{config.REGULATION_NAME} · dados de uso de {config.STATS_MONTH}"
)

st.header("1. Seu time")
time = montar_time(tela_montar_o_time())

if time:
    st.header("2. Análise")
    time_ok = mostrar_analise(time)
    if time_ok:
        st.header("3. Recomendações")
        mostrar_recomendacoes(time_ok)
else:
    st.info("Monte o time nos cards acima (ou use 📥 Importar → Time de exemplo) "
            "para ver a análise e as recomendações.")

# ---------------------------------------------------------------------------
# Sobre os dados
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Sobre os dados")
uso = dados.carregar_uso()
col1, col2, col3 = st.columns(3)
col1.metric("Batalhas analisadas", f"{uso['batalhas']:,}".replace(",", "."))
col2.metric("Pokémon com estatísticas", len(uso["pokemon"]))
col3.metric("Pokémon/formas legais", len(dados.carregar_legais()))

with st.expander("Os 20 Pokémon mais usados"):
    pokemon = dados.carregar_pokemon()
    st.dataframe([{
        "Pokémon": info["nome"],
        "Uso (%)": info["uso"],
        "Tipos": " / ".join(TIPOS_PT[t] for t in pokemon.get(pokemon_id, {}).get("tipos", [])),
        "Habilidade mais usada": nome_da_habilidade(next(iter(info["habilidades"]), "-")),
        "Item mais usado": nome_do_item(next(iter(info["itens"]), "-")),
        "Parceiro mais comum": nome_do_pokemon(next(iter(info["parceiros"]), "-")),
    } for pokemon_id, info in list(uso["pokemon"].items())[:20]], hide_index=True, width="stretch")

with st.expander("Regras do formato consideradas"):
    st.markdown(
        f"""
- Nível {config.LEVEL}; leva {config.TEAM_SIZE} e escolhe {config.PICK_SIZE}.
- Não pode repetir espécie nem item.
- Até {config.MAX_MEGA_PER_BATTLE} Mega Evolução por batalha. Sem Terastalização.
- Pontos de status (EVs): até {config.EV_MAX} em cada, {config.EV_TOTAL} no total.
- Formato no Showdown: `{config.FORMAT_ID}`
"""
    )
