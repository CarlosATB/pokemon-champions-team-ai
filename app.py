"""
Pokémon Champions Team AI — interface (Streamlit).

Para rodar localmente:
    streamlit run app.py

Fase 2: análise do time (colar do Showdown ou escolher na lista).
A recomendação (Fase 3) será ligada aqui depois.
"""

import pandas as pd
import streamlit as st

from src import config, dados
from src.analise import analisar
from src.dicas import gerar_dicas
from src.funcoes_duplas import FUNCOES
from src.leitor import ler_time, time_de_nomes
from src.tipos import TIPOS_PT
from src.times_exemplo import TIMES_EXEMPLO
from src.validacao import validar_time

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


# ---------------------------------------------------------------------------
# Entrada do time
# ---------------------------------------------------------------------------

st.header("1. Seu time")
aba_colar, aba_lista = st.tabs(["Colar do Showdown", "Escolher da lista"])

with aba_colar:
    exemplo = st.selectbox("Carregar um time de exemplo", ["(colar o meu)"] + list(TIMES_EXEMPLO))
    texto = st.text_area(
        "Cole aqui o time exportado do Pokémon Showdown (botão Export)",
        value=TIMES_EXEMPLO.get(exemplo, "").strip(),
        height=300,
    )

with aba_lista:
    uso_por_id = dados.carregar_uso()["pokemon"]
    # Nome como no Showdown quando existe ("Indeedee-F"); senão, o da PokéAPI.
    opcoes = sorted(uso_por_id.get(pid, info)["nome"] for pid, info in dados.carregar_pokemon().items()
                    if pid in dados.carregar_legais() and not info["forma_de_batalha"])
    escolhidos = st.multiselect("Escolha até 6 Pokémon", opcoes, max_selections=config.TEAM_SIZE)
    st.caption("Sem golpes, a análise usa só os tipos. Para ver funções de duplas e "
               "cobertura completa, cole o time com os golpes.")

# A lista tem prioridade se algo foi escolhido nela.
time = time_de_nomes(escolhidos) if escolhidos else ler_time(texto) if texto.strip() else []

# ---------------------------------------------------------------------------
# Resultado da análise
# ---------------------------------------------------------------------------

if time:
    st.header("2. Análise")

    problemas = validar_time(time)
    for problema in problemas:
        if problema["nivel"] == "erro":
            st.error(problema["mensagem"], icon="⛔")
        else:
            st.warning(problema["mensagem"], icon="⚠️")

    analise = analisar(time)
    time_ok = [m for m in time if m["id"] in dados.carregar_pokemon()]
    nomes = [m["especie"] for m in time_ok]

    st.subheader("Dicas")
    icones = {"alerta": "🔴", "atencao": "🟡", "ok": "🟢"}
    dicas = gerar_dicas(time_ok, analise)
    for nivel in ["alerta", "atencao", "ok"]:  # problemas primeiro
        for dica in dicas:
            if dica["nivel"] == nivel:
                st.markdown(f"{icones[nivel]} {dica['texto']}")

    texto_dano = {4: "4x", 2: "2x", 1: "", 0.5: "½", 0.25: "¼", 0: "0"}
    aba_def, aba_of, aba_func, aba_ameacas = st.tabs(
        ["Fraquezas e resistências", "Cobertura ofensiva", "Funções de duplas", "Ameaças do meta"])

    with aba_def:
        st.caption("Dano que cada Pokémon toma de cada tipo de golpe "
                   "(já contando habilidades como Levitate e a forma Mega).")
        cores = {"4x": "#e74c3c", "2x": "#f5b7b1", "½": "#a9dfbf", "¼": "#52be80", "0": "#5dade2"}
        linhas = []
        for linha in analise["defesa"]:
            celulas = {nome: texto_dano.get(x, f"{x}x") for nome, x in linha["dano"].items()}
            linhas.append({"Tipo do golpe": TIPOS_PT[linha["tipo"]], **celulas,
                           "Fracos": len(linha["fracos"]),
                           "Resistem/imunes": len(linha["resistem"]) + len(linha["imunes"])})
        tabela = pd.DataFrame(linhas).style.map(
            lambda v: f"background-color: {cores[v]}; color: black" if v in cores else "",
            subset=nomes)
        st.dataframe(tabela, hide_index=True, width="stretch", height=670)

    with aba_of:
        st.caption("O melhor dano que o time causa em cada tipo, com os golpes de ataque do time.")
        st.dataframe([{
            "Tipo do alvo": TIPOS_PT[c["tipo"]],
            "Melhor dano": texto_dano.get(c["melhor"], f"{c['melhor']}x") or "1x",
            "Quem acerta": ", ".join(c["quem"]) if c["melhor"] >= 2 else "-",
        } for c in analise["cobertura"]], hide_index=True, width="stretch", height=670)

    with aba_func:
        st.dataframe([{
            "Função": funcao["nome"],
            "Quem faz": ", ".join(analise["funcoes"][chave]) or "ninguém",
            "Para que serve": funcao["descricao"],
        } for chave, funcao in FUNCOES.items()], hide_index=True, width="stretch")

    with aba_ameacas:
        st.caption("Entre os 30 Pokémon mais usados: quem acerta muitos do seu time com dano "
                   "dobrado e quase não é acertado de volta. Nota = acerta − respostas.")
        st.dataframe([{
            "Pokémon": a["nome"],
            "Uso (%)": a["uso"],
            "Ataca com": ", ".join(TIPOS_PT[t] for t in a["tipos_ataque"]),
            "Acerta forte": ", ".join(a["acerta"]),
            "Suas respostas": ", ".join(a["respostas"]) or "nenhuma",
            "Nota": a["nota"],
        } for a in analise["ameacas"]], hide_index=True, width="stretch")

st.divider()
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
