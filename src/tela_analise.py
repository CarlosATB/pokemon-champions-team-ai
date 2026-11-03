"""
Seção "2. Análise" do site: a análise feita pela IA (src/modelo_nota.py e
src/dicas_ia.py), com gráficos, e os dados de apoio de src/analise.py.

Só exibição; a IA fica em modelo_nota.py e as regras em analise.py e validacao.py.
"""

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from src import config, dados
from src.analise import analisar, tipos_perigosos
from src.dicas import FUNCOES_ESSENCIAIS
from src.dicas_ia import dicas_da_ia, respostas_da_ia, texto_do_alerta
from src.funcoes_duplas import FUNCOES
from src.modelo_nota import ALERTA, PONTOS, analise_da_ia, carregar_modelo, pesos_do_modelo
from src.tipos import TIPOS_PT
from src.validacao import validar_time
from src.visual import etiqueta_tipo, etiquetas, foto, grade_de_tipos, imagem

TEXTO_DANO = {4: "4x", 2: "2x", 1: "", 0.5: "½", 0.25: "¼", 0: "0"}
CORES_DANO = {"4x": "#e74c3c", "2x": "#f5b7b1", "½": "#a9dfbf", "¼": "#52be80", "0": "#5dade2"}


def _lista_em_markdown(itens: list[str]) -> str:
    return "\n".join(f"- {item}" for item in itens)


def mostrar_problemas(problemas: list[dict]) -> None:
    """Erros das regras numa caixa vermelha, avisos numa amarela, o resto em azul."""
    caixas = [("erro", st.error, "⛔", "O time quebra as regras do formato:"),
              ("aviso", st.warning, "⚠️", "Vale conferir:"),
              ("info", st.info, "ℹ️", "")]
    for nivel, caixa, icone, titulo in caixas:
        mensagens = [p["mensagem"] for p in problemas if p["nivel"] == nivel]
        if len(mensagens) == 1:
            caixa(mensagens[0], icon=icone)
        elif mensagens:
            caixa(f"{titulo}\n\n{_lista_em_markdown(mensagens)}", icon=icone)


def _virgula(numero: float, casas: int = 1) -> str:
    return f"{numero:.{casas}f}".replace(".", ",")


def mostrar_resumo(resultado: dict, modelo: dict) -> None:
    """A análise da IA de relance: nota, chance de vencer e melhor/pior categoria.

    Melhor/pior olham só as categorias principais: as situacionais (clima,
    Fake Out, Screens) dependem do time e não dizem sozinhas se ele é bom.
    """
    categorias = sorted([c for c in resultado["categorias"] if c["principal"]], key=lambda c: c["nota"])
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Nota da IA", f"{_virgula(resultado['nota'])} / 10",
                help=f"Mais forte que {resultado['nota'] * 10:.0f}% dos times de "
                     f"{modelo['batalhas_treino'] + modelo['batalhas_teste']} batalhas reais, "
                     "segundo o que o modelo aprendeu.")
    col2.metric("Chance contra um time médio", f"{_virgula(resultado['chance'])}%",
                help="Chance de vencer um time típico do meta, só pela montagem do time "
                     "(sem contar a habilidade de quem joga).")
    col3.metric("Melhor categoria", categorias[-1]["nome"], f"nota {_virgula(categorias[-1]['nota'])}")
    col4.metric("Pior categoria", categorias[0]["nome"], f"nota {_virgula(categorias[0]['nota'])}",
                delta_color="inverse")


def mostrar_dicas(resultado: dict) -> None:
    """Dicas e respostas escritas a partir do que a IA aprendeu (src/dicas_ia.py)."""
    alerta = texto_do_alerta(resultado["alerta"])
    if alerta:
        st.warning(alerta, icon="⚠️")
    dicas = dicas_da_ia(resultado)
    col_ok, col_atencao = st.columns(2)
    for coluna, (nivel, titulo) in zip([col_ok, col_atencao],
                                       [("ok", "🟢 Ajuda a vencer"), ("atencao", "🟡 Pode melhorar")]):
        with coluna.container(border=True):
            st.markdown(f"**{titulo}**")
            textos = [d["texto"] for d in dicas if d["nivel"] == nivel]
            st.markdown(_lista_em_markdown(textos) if textos else "Nenhum.")
    st.markdown("**Situacionais** (só contam quando o time se beneficia deles)")
    for resposta in respostas_da_ia(resultado):
        icone = {1: "🟢", 0: "⚪", -1: "🔴"}[resposta["efeito"]]
        st.markdown(f"{icone} **{resposta['pergunta']}** {resposta['resposta']}")


def _sinal(numero: int) -> tuple[str, str]:
    """3 -> ("+3", "verde");  -2 -> ("-2", "vermelho");  0 -> ("0", "neutro")"""
    if numero > 0:
        return f"+{numero}", "verde"
    if numero < 0:
        return str(numero), "vermelho"
    return "0", "neutro"


def _tabela_de_quem(linhas: list[tuple[str, str, str]]) -> str:
    """Linhas (coluna da esquerda, nome do Pokémon, id) -> tabela HTML com fotinhas."""
    return "<table>" + "".join(
        f"<tr><td>{esquerda}</td><td>{nome} {foto(pid, 28)}</td></tr>"
        for esquerda, nome, pid in linhas) + "</table>"


def mostrar_fraquezas(analise: dict, time: list[dict]) -> None:
    perigosos = tipos_perigosos(analise)
    if perigosos:
        st.markdown("**Tipos perigosos para o seu time:** " + " ".join(
            f"{etiqueta_tipo(p['tipo'])} {p['fracos']} fracos · {p['seguram']} seguram &nbsp;"
            for p in perigosos), unsafe_allow_html=True)
    else:
        st.markdown("✅ Nenhum tipo de golpe acerta forte metade do time sem resposta.")
    st.caption("Número = quantos seguram (resistem ou são imunes) − quantos são fracos. "
               "Vermelho: mais fracos do que respostas. Passe o mouse num tipo para ver quem.")

    ids = {m["especie"]: m["forma"] for m in time}
    celulas = []
    for linha in analise["defesa"]:
        seguram = linha["resistem"] + linha["imunes"]
        numero, cor = _sinal(len(seguram) - len(linha["fracos"]))
        quem = ([(f"toma {TEXTO_DANO[linha['dano'][n]]}", n, ids[n]) for n in linha["fracos"]]
                + [(f"toma {TEXTO_DANO[linha['dano'][n]]}", n, ids[n]) for n in seguram])
        detalhe = (f"Golpes de {etiqueta_tipo(linha['tipo'])} contra o seu time:"
                   + (_tabela_de_quem(quem) if quem else "<br>Todos tomam dano normal."))
        celulas.append({"tipo": linha["tipo"], "numero": numero, "cor": cor, "detalhe": detalhe})
    st.markdown(grade_de_tipos(celulas), unsafe_allow_html=True)

    with st.expander("Ver a tabela completa"):
        nomes = [m["especie"] for m in time]
        linhas = []
        for linha in analise["defesa"]:
            celulas_tabela = {nome: TEXTO_DANO.get(x, f"{x}x") for nome, x in linha["dano"].items()}
            linhas.append({"Tipo do golpe": TIPOS_PT[linha["tipo"]], **celulas_tabela,
                           "Fracos": len(linha["fracos"]),
                           "Resistem/imunes": len(linha["resistem"]) + len(linha["imunes"])})
        tabela = pd.DataFrame(linhas).style.map(
            lambda v: f"background-color: {CORES_DANO[v]}; color: black" if v in CORES_DANO else "",
            subset=nomes)
        st.dataframe(tabela, hide_index=True, width="stretch", height=670)


def mostrar_cobertura(analise: dict, time: list[dict]) -> None:
    if analise["sem_ataques"]:
        st.warning(f"Sem golpes de ataque (não entram na conta): "
                   f"{', '.join(analise['sem_ataques'])}.")
    if len(analise["sem_ataques"]) == len(time):
        st.info("Escolha os golpes nos cards para ver a cobertura ofensiva.")
        return
    fracos = [c["tipo"] for c in analise["cobertura"] if not c["supereficazes"]]
    if fracos:
        st.markdown("**Nenhum golpe é supereficaz contra:** " + etiquetas(fracos),
                    unsafe_allow_html=True)
    else:
        st.markdown("✅ O time tem golpe supereficaz contra todos os tipos.")
    st.caption("Número = quantos golpes do time são supereficazes contra o tipo. "
               "Passe o mouse num tipo para ver os golpes e quem usa.")

    celulas = []
    for c in analise["cobertura"]:
        numero, cor = _sinal(len(c["supereficazes"]))
        quem = [(f"{etiqueta_tipo(g['tipo_golpe'], pequena=True)} {g['golpe']}", g["pokemon"], g["id"])
                for g in c["supereficazes"]]
        detalhe = (f"Supereficaz contra {etiqueta_tipo(c['tipo'])}:"
                   + (_tabela_de_quem(quem) if quem else "<br>Nenhum golpe do time."))
        celulas.append({"tipo": c["tipo"], "numero": numero, "cor": cor, "detalhe": detalhe})
    st.markdown(grade_de_tipos(celulas), unsafe_allow_html=True)


def mostrar_funcoes(analise: dict) -> None:
    st.caption("✅ = alguém do time faz · ❌ = ninguém faz. As marcadas com ⭐ quase "
               "todo time de duplas precisa.")
    colunas = st.columns(4)
    for n, (chave, funcao) in enumerate(FUNCOES.items()):
        quem = analise["funcoes"][chave]
        estrela = " ⭐" if chave in FUNCOES_ESSENCIAIS else ""
        with colunas[n % 4].container(border=True):
            st.markdown(f"{'✅' if quem else '❌'} **{funcao['nome']}**{estrela}")
            st.markdown(", ".join(quem) if quem else "ninguém")
            st.caption(funcao["descricao"])


def mostrar_ameacas(analise: dict) -> None:
    st.caption("Entre os 30 Pokémon mais usados: quem acerta muitos do seu time com dano "
               "dobrado e quase não é acertado de volta. Pokémon sem golpes contam com "
               "os golpes mais usados com ele.")
    if not analise["ameacas"]:
        st.success("Nenhum dos mais usados leva vantagem clara contra o seu time.")
        return
    colunas = st.columns(3)
    for n, ameaca in enumerate(analise["ameacas"][:6]):
        with colunas[n % 3].container(border=True):
            col_imagem, col_texto = st.columns([1, 2])
            if imagem(ameaca["id"]):
                col_imagem.image(imagem(ameaca["id"]), width=80)
            col_texto.markdown(f"**{ameaca['nome']}**  \n{ameaca['uso']:.0f}% dos times")
            st.markdown("Ataca com: " + etiquetas(ameaca["tipos_ataque"]),
                        unsafe_allow_html=True)
            st.markdown(f"**Acerta forte:** {', '.join(ameaca['acerta'])}  \n"
                        f"**Suas respostas:** {', '.join(ameaca['respostas']) or 'nenhuma'}")


def mostrar_pontos_ia(resultado: dict) -> None:
    """A análise da IA por categoria e por ponto, em tabela."""
    st.caption("Cada ponto foi calculado para o seu time e pesado pelo que o modelo aprendeu "
               "com batalhas reais. Impacto = quanto o ponto deixa o time mais forte (+) ou "
               "mais fraco (-) que um time médio. Nota da categoria = mais forte que X% dos times reais (÷10). "
               "As categorias estão na ordem de importância.")
    blocos = [(c["nome"], f" · nota {_virgula(c['nota'])} / 10") for c in resultado["categorias"]]
    for nome, nota in blocos + [(ALERTA, "")]:
        pontos = [p for p in resultado["pontos"] if p["categoria"] == nome]
        st.markdown(f"**{nome}**{nota}")
        st.dataframe(pd.DataFrame([
            {"Ponto": p["nome"], "Seu time": p["valor"], "Média dos vencedores": p["media_vencedores"],
             "Impacto": p["impacto"]} for p in pontos]).style.map(
                lambda v: f"color: {'#52be80' if v > 0 else '#e74c3c' if v < 0 else 'inherit'}",
                subset=["Impacto"]).format(
                {"Seu time": "{:.2f}", "Média dos vencedores": "{:.2f}", "Impacto": "{:+.3f}"}),
            hide_index=True, width="stretch")


def _barras(tabela: pd.DataFrame, x: str, y: str, titulo: str, cor: str | None = None,
            dominio: list | None = None) -> alt.Chart:
    """Gráfico de barras deitadas (verde = positivo, vermelho = negativo)."""
    escala = alt.Scale(domain=dominio) if dominio else alt.Undefined
    cores = (alt.Color(cor, legend=None) if cor else
             alt.condition(f"datum['{x}'] >= 0", alt.value("#52be80"), alt.value("#e74c3c")))
    return alt.Chart(tabela, title=titulo).mark_bar().encode(
        x=alt.X(x, scale=escala), y=alt.Y(y, sort=None, title=None, axis=alt.Axis(labelLimit=320)),
        color=cores, tooltip=list(tabela.columns))


def mostrar_graficos(resultado: dict, modelo: dict) -> None:
    """Gráficos do seu time e do treinamento do modelo."""
    st.markdown("#### Seu time")
    col1, col2 = st.columns(2)
    categorias = pd.DataFrame([{"Categoria": c["nome"], "Nota": c["nota"]} for c in resultado["categorias"]])
    col1.altair_chart(_barras(categorias, "Nota", "Categoria", "Nota por categoria (0 a 10)",
                              cor="Categoria", dominio=[0, 10]), width="stretch")
    impactos = pd.DataFrame([{"Ponto": p["nome"], "Impacto": p["impacto"]} for p in resultado["pontos"]])
    col2.altair_chart(_barras(impactos, "Impacto", "Ponto", "Impacto de cada ponto na força do time"),
                      width="stretch")

    # Seu time x vencedores x perdedores, em desvios da média (para caber tudo no mesmo eixo).
    medias, desvios = np.array(modelo["medias"]), np.array(modelo["desvios"])
    grupos = {"Seu time": [p["valor"] for p in resultado["pontos"]],
              "Média dos vencedores": modelo["media_vencedores"],
              "Média dos perdedores": modelo["media_perdedores"]}
    comparacao = pd.DataFrame([
        {"Ponto": PONTOS[chave][1], "Grupo": grupo, "Desvios da média": round(float(z), 2)}
        for grupo, valores in grupos.items()
        for chave, z in zip(modelo["pontos"], (np.array(valores) - medias) / desvios)])
    ordem = list(grupos)
    st.altair_chart(alt.Chart(comparacao, title="Seu time comparado aos vencedores e perdedores").mark_bar()
                    .encode(x="Desvios da média",
                            y=alt.Y("Ponto", sort=None, title=None, axis=alt.Axis(labelLimit=320)),
                            yOffset=alt.YOffset("Grupo", sort=ordem),
                            color=alt.Color("Grupo", sort=ordem, legend=alt.Legend(orient="top", title=None)),
                            tooltip=["Ponto", "Grupo", "Desvios da média"])
                    .properties(height=len(PONTOS) * 36), width="stretch")
    st.caption("Desvios da média: 0 = time comum; positivo = tem mais disso que a maioria dos times.")

    st.markdown("#### Treinamento do modelo")
    col1, col2 = st.columns(2)
    pesos = pd.DataFrame([{"Categoria": p["categoria"], "Peso": p["peso"]} for p in pesos_do_modelo(modelo)])
    col1.altair_chart(_barras(pesos, "Peso", "Categoria", "O que o modelo aprendeu (peso de cada categoria)"),
                      width="stretch")
    cruzada = modelo["validacao_cruzada"]
    acuracias = pd.DataFrame([
        {"Avaliação": "Chute (50%)", "Acurácia": 50.0},
        {"Avaliação": "Treino", "Acurácia": 100 * modelo["treino"]["acuracia"]},
        {"Avaliação": "Teste", "Acurácia": 100 * modelo["teste"]["acuracia"]},
        {"Avaliação": "Validação cruzada", "Acurácia": 100 * cruzada["media"]}])
    col2.altair_chart(_barras(acuracias, "Acurácia", "Avaliação", "Acertou quem venceu? (%)",
                              cor="Avaliação", dominio=[0, 100]), width="stretch")
    col1.caption("O treino é obrigado a manter a ordem: cada categoria pesa mais que a de baixo. "
                 "O alerta só pode tirar força.")

    forcas = pd.DataFrame([{"Força": f, "Resultado": "Venceu"} for f in modelo["forca_vencedores"]]
                          + [{"Força": f, "Resultado": "Perdeu"} for f in modelo["forca_perdedores"]])
    histograma = alt.Chart(forcas, title="Força dos times reais: vencedores x perdedores").mark_bar(
        opacity=0.5).encode(x=alt.X("Força", bin=alt.Bin(maxbins=40), title="Força"),
                            y=alt.Y("count()", stack=None, title="Times"),
                            color=alt.Color("Resultado", scale=alt.Scale(domain=["Perdeu", "Venceu"],
                                                                         range=["#e74c3c", "#52be80"])))
    seu_time = alt.Chart(pd.DataFrame([{"Força": resultado["forca"]}])).mark_rule(
        color="#f1c40f", strokeWidth=3).encode(x="Força")
    st.altair_chart(histograma + seu_time, width="stretch")
    st.caption("A linha amarela é o seu time. Quanto mais à direita, mais o modelo acha que o time vence.")


def mostrar_sobre_o_modelo(modelo: dict) -> None:
    cruzada = modelo["validacao_cruzada"]
    with st.expander("Como a IA aprendeu (e o quanto ela acerta)"):
        st.markdown(
            f"- **Dados:** {modelo['batalhas_treino'] + modelo['batalhas_teste']} batalhas reais do "
            f"Pokémon Showdown (replays públicos, rating {modelo['rating_minimo']}+), com os dois "
            "times e quem venceu.\n"
            "- **Modelo:** Regressão Logística (feita com numpy). Para cada batalha, olha a diferença "
            "entre as categorias dos dois times e aprende um peso para cada categoria.\n"
            "- **Ordem de importância:** Cobertura > Sinergia > Winrate > Controle de velocidade > "
            "Situacionais. O treino é obrigado a manter essa ordem (o valor de cada peso vem das "
            "batalhas). Clima, Fake Out e Screens só contam quando o time se beneficia deles. "
            "Atacantes físicos demais são um alerta que só tira força.\n"
            "- **Winrate:** quanto cada Pokémon vence nas batalhas de treino (sem contar a própria "
            "batalha, para o modelo não colar a resposta).\n"
            f"- **Avaliação:** acertou quem venceu em {_virgula(100 * modelo['teste']['acuracia'])}% de "
            f"{modelo['batalhas_teste']} batalhas que não viu no treino; na validação cruzada "
            f"(5 partes), {_virgula(100 * cruzada['media'])}% ± {_virgula(100 * cruzada['desvio'])}%. "
            "Chutar daria 50%.\n"
            "- **Limite:** quem joga melhor costuma vencer, com qualquer time. Por isso a montagem do "
            "time explica só uma parte do resultado, e a acurácia fica perto de 50%. Os pesos mostram "
            "tendências, não garantias.")


def mostrar_analise(time: list[dict]) -> list[dict]:
    """Desenha a seção inteira. Devolve só os Pokémon reconhecidos (para as recomendações)."""
    mostrar_problemas(validar_time(time))
    time_ok = [m for m in time if m["id"] in dados.carregar_pokemon()]
    if not time_ok:
        return []
    analise = analisar(time_ok)
    modelo = carregar_modelo()
    resultado = analise_da_ia(time_ok, modelo)
    abas_de_dados = ["Fraquezas e resistências", "Cobertura ofensiva", "Funções de duplas", "Ameaças do meta"]
    if resultado is None:
        st.info("A IA ainda não foi treinada. Rode: python -m src.replays e python -m src.modelo_nota")
        abas = st.tabs(abas_de_dados)
    elif len(time_ok) < config.TEAM_SIZE:
        # A IA aprendeu com times completos: com menos Pokémon as contagens caem e a nota não vale.
        st.info(f"A análise da IA aparece com o time completo ({config.TEAM_SIZE} Pokémon), porque ela "
                "aprendeu com times completos de batalhas reais.")
        abas = st.tabs(abas_de_dados)
    else:
        mostrar_resumo(resultado, modelo)
        st.subheader("Análise da IA")
        mostrar_dicas(resultado)
        mostrar_sobre_o_modelo(modelo)
        aba_ia, aba_graficos, *abas = st.tabs(["Pontos da análise", "Gráficos", *abas_de_dados])
        with aba_ia:
            mostrar_pontos_ia(resultado)
        with aba_graficos:
            mostrar_graficos(resultado, modelo)
    aba_def, aba_of, aba_func, aba_ameacas = abas
    with aba_def:
        mostrar_fraquezas(analise, time_ok)
    with aba_of:
        mostrar_cobertura(analise, time_ok)
    with aba_func:
        mostrar_funcoes(analise)
    with aba_ameacas:
        mostrar_ameacas(analise)
    return time_ok
