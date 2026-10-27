"""
Pokémon Champions Team AI — interface (Streamlit).

Para rodar localmente:
    streamlit run app.py

Fase 2: análise do time (colar do Showdown ou escolher na lista).
Fase 3: recomendações (habilidade, item, golpes, EVs, parceiros e substitutos).
"""

import pandas as pd
import streamlit as st

from src import config, dados
from src.analise import analisar
from src.dicas import gerar_dicas
from src.funcoes_duplas import FUNCOES
from src.leitor import ler_time, montar_time
from src.opcoes import (
    montagem_recomendada, opcoes_de_golpes, opcoes_de_habilidades, opcoes_de_itens, pedra_da_mega,
)
from src.recomendacao import (PESO_FRAQUEZAS, PESO_FUNCOES, PESO_PARCERIA, recomendar_time,
                              sugerir_parceiros,
                              sugerir_substitutos)
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
aba_montar, aba_colar = st.tabs(["Montar o time", "Colar do Showdown"])

with aba_montar:
    uso_por_id = dados.carregar_uso()["pokemon"]
    pokemon_por_id = dados.carregar_pokemon()
    # Nome como no Showdown quando existe ("Indeedee-F"); senão, o da PokéAPI.
    nome_por_id = {pid: uso_por_id.get(pid, info)["nome"] for pid, info in pokemon_por_id.items()
                   if pid in dados.carregar_legais() and not info["forma_de_batalha"]}
    ids_ordenados = sorted(nome_por_id, key=nome_por_id.get)
    itens_por_id = dados.carregar_itens()["legais"]
    golpes_por_id = dados.carregar_golpes()
    habilidades_por_id = dados.carregar_habilidades()

    def nome_do_golpe(golpe_id):
        golpe = golpes_por_id[golpe_id]
        return f"{golpe['nome']} · {TIPOS_PT[golpe['tipo']]}"

    st.caption("As opções de item, habilidade e golpes vêm ordenadas pelo uso: "
               "as primeiras são as que os jogadores mais usam com aquele Pokémon.")
    montados = []
    for vaga in range(config.TEAM_SIZE):
        if vaga % 2 == 0:  # uma linha com 2 cards: grade de 2 colunas x 3 linhas
            colunas = st.columns(2)
        with colunas[vaga % 2].container(border=True):
            pid = st.selectbox(f"Pokémon {vaga + 1}", [None] + ids_ordenados, key=f"especie_{vaga}",
                               format_func=lambda p: "(vazio)" if p is None else nome_por_id[p])
            if pid is None:
                continue
            st.caption(" / ".join(TIPOS_PT[t] for t in pokemon_por_id[pid]["tipos"]))
            esquerda, direita = st.columns(2)
            with esquerda:
                # A chave inclui o Pokémon: ao trocar de Pokémon, os seletores recomeçam.
                pedra = pedra_da_mega(pid)
                if pedra:  # a Mega já vem com a Pedra Mega dela, travada
                    item = st.selectbox("Item", [pedra], key=f"item_{vaga}_{pid}", disabled=True,
                                        format_func=itens_por_id.get,
                                        help="Para Mega Evoluir, ela precisa segurar esta pedra.")
                else:
                    item = st.selectbox(
                        "Item", [None] + opcoes_de_itens(pid), key=f"item_{vaga}_{pid}",
                        format_func=lambda i: "(nenhum)" if i is None else itens_por_id[i])
                habilidade = st.selectbox("Habilidade", opcoes_de_habilidades(pid),
                                          key=f"habilidade_{vaga}_{pid}",
                                          format_func=lambda h: habilidades_por_id.get(h, h))
            with direita:
                golpes = [st.selectbox(f"Golpe {n + 1}", [None] + opcoes_de_golpes(pid),
                                       key=f"golpe_{vaga}_{n}_{pid}",
                                       format_func=lambda g: "(nenhum)" if g is None else nome_do_golpe(g))
                          for n in range(4)]
            montados.append({
                "vaga": vaga,  # qual card: o botão das recomendações preenche este card
                "especie": nome_por_id[pid],
                "item": itens_por_id[item] if item else "",
                "habilidade": habilidades_por_id.get(habilidade, habilidade or ""),
                "natureza": "",
                "golpes": [golpes_por_id[g]["nome"] for g in golpes if g],
            })

with aba_colar:
    exemplo = st.selectbox("Carregar um time de exemplo", ["(colar o meu)"] + list(TIMES_EXEMPLO))
    texto = st.text_area(
        "Cole aqui o time exportado do Pokémon Showdown (botão Export)",
        value=TIMES_EXEMPLO.get(exemplo, "").strip(),
        height=300,
    )

# O time montado tem prioridade se algo foi escolhido nele.
time = montar_time(montados) if montados else ler_time(texto) if texto.strip() else []

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
        st.caption("O melhor dano que o time causa em cada tipo, só com os golpes de ataque "
                   "escolhidos. Em cada linha: o golpe e quem usa.")
        if analise["sem_ataques"]:
            st.warning(f"Sem golpes de ataque (não entram na conta): "
                       f"{', '.join(analise['sem_ataques'])}.")
        if len(analise["sem_ataques"]) < len(time_ok):
            st.dataframe([{
                "Tipo do alvo": TIPOS_PT[c["tipo"]],
                "Melhor dano": texto_dano.get(c["melhor"], f"{c['melhor']}x") or "1x",
                "Golpes (quem usa)": ", ".join(c["quem"]) if c["melhor"] >= 2 else "-",
            } for c in analise["cobertura"]], hide_index=True, width="stretch", height=670)

    with aba_func:
        st.dataframe([{
            "Função": funcao["nome"],
            "Quem faz": ", ".join(analise["funcoes"][chave]) or "ninguém",
            "Para que serve": funcao["descricao"],
        } for chave, funcao in FUNCOES.items()], hide_index=True, width="stretch")

    with aba_ameacas:
        st.caption("Entre os 30 Pokémon mais usados: quem acerta muitos do seu time com dano "
                   "dobrado e quase não é acertado de volta. Nota = acerta − respostas. "
                   "Pokémon sem golpes contam com os golpes mais usados com ele.")
        st.dataframe([{
            "Pokémon": a["nome"],
            "Uso (%)": a["uso"],
            "Ataca com": ", ".join(TIPOS_PT[t] for t in a["tipos_ataque"]),
            "Acerta forte": ", ".join(a["acerta"]),
            "Suas respostas": ", ".join(a["respostas"]) or "nenhuma",
            "Nota": a["nota"],
        } for a in analise["ameacas"]], hide_index=True, width="stretch")

# ---------------------------------------------------------------------------
# Recomendações (Fase 3)
# ---------------------------------------------------------------------------

if time and time_ok:
    st.header("3. Recomendações")
    st.caption("Baseadas no que os jogadores mais usam nas batalhas reais "
               "(\"quem usa X também usa Y\"). ✅ = você já usa.")
    aba_pokemon, aba_parceiros, aba_trocas = st.tabs(
        ["Por Pokémon", "Parceiros", "Trocar um Pokémon"])

    def marca(voce_usa):
        return " ✅" if voce_usa else ""

    def montar_com_a_recomendacao(vaga, pid, montagem):
        """Coloca item, habilidade e golpes recomendados nos seletores do card."""
        if montagem["item"]:
            st.session_state[f"item_{vaga}_{pid}"] = montagem["item"]
        if montagem["habilidade"]:
            st.session_state[f"habilidade_{vaga}_{pid}"] = montagem["habilidade"]
        for n in range(4):
            golpe = montagem["golpes"][n] if n < len(montagem["golpes"]) else None
            st.session_state[f"golpe_{vaga}_{n}_{pid}"] = golpe

    with aba_pokemon:
        for membro, sugestao in zip(time_ok, recomendar_time(time_ok)):
            with st.expander(sugestao["especie"]):
                if not sugestao["tem_dados"]:
                    st.info(sugestao["porque"])
                    continue
                if "vaga" in membro:  # só para o time da aba "Montar o time"
                    st.button("Montar com esta recomendação", key=f"montar_{membro['vaga']}",
                              on_click=montar_com_a_recomendacao,
                              args=(membro["vaga"], membro["id"],
                                    montagem_recomendada(membro["id"], sugestao)),
                              help="Preenche o card deste Pokémon com o item, a habilidade "
                                   "e os 4 golpes mais usados.")
                hab, item, golpes, spread = (sugestao["habilidade"], sugestao["item"],
                                             sugestao["golpes"], sugestao["natureza_evs"])
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Habilidade:** {hab['nome']}{marca(hab['voce_usa'])}")
                    st.caption(hab["porque"])
                    melhor = item["melhor"]["nome"] if item["melhor"] else "-"
                    st.markdown(f"**Item:** {melhor}{marca(item['voce_usa'])}")
                    st.caption(item["porque"])
                    st.markdown(f"**Natureza:** {spread['natureza']}{marca(spread['voce_usa'])}  \n"
                                f"**EVs:** {spread['evs']}")
                    st.caption(spread["porque"])
                with col2:
                    st.markdown("**Golpes mais usados**")
                    st.dataframe([{"Golpe": g["nome"] + marca(g["voce_usa"]), "Uso (%)": g["uso"]}
                                  for g in golpes["lista"]], hide_index=True, width="stretch")
                    st.caption(golpes["porque"])

    with aba_parceiros:
        st.caption("Quem mais aparece junto com o seu time. Confiança = % dos times com os "
                   "seus Pokémon que também têm ele (média). Lift > 1 = combinam mais que o acaso.")
        st.dataframe([{
            "Pokémon": p["nome"],
            "Confiança (%)": p["confianca"],
            "Uso geral (%)": p["suporte"],
            "Lift": p["lift"],
            "Por quê": p["porque"],
        } for p in sugerir_parceiros(time_ok, quantos=8)], hide_index=True, width="stretch")

    with aba_trocas:
        if len(time_ok) < 2:
            st.info("Coloque pelo menos 2 Pokémon para sugerir trocas.")
        else:
            automatico = "(a IA escolhe)"
            escolha = st.selectbox("Quem sai do time?", [automatico] + [m["especie"] for m in time_ok])
            sai = None if escolha == automatico else next(m for m in time_ok if m["especie"] == escolha)
            trocas = sugerir_substitutos(time_ok, sai)
            st.markdown(f"**Sai: {trocas['sai']}.** {trocas['motivo']}")
            if trocas["fraquezas"]:
                st.markdown("Fraquezas do time sem ele: " + ", ".join(trocas["fraquezas"]))
            if trocas["faltam"]:
                st.markdown("Funções de duplas que faltam sem ele: " + ", ".join(trocas["faltam"]))
            st.caption(f"Nota (0 a 100) = {PESO_PARCERIA:.0%} co-ocorrência com quem fica + "
                       f"{PESO_FRAQUEZAS:.0%} quantas dessas fraquezas ele resiste + "
                       f"{PESO_FUNCOES:.0%} quantas dessas funções ele traz (com os golpes mais "
                       "usados com ele). Pelo menos 1 sugerido traz cada função essencial que falta.")
            st.dataframe([{
                "Pokémon": s["nome"],
                "Nota": s["nota"],
                "Traz": ", ".join(s["traz"]) or "-",
                "Resiste a": ", ".join(s["cobre"]) or "-",
                "Por quê": s["porque"],
            } for s in trocas["substitutos"]], hide_index=True, width="stretch")

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
