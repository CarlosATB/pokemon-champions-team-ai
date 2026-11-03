"""
Visões "Análise da IA" e "Detalhes" do site (ver src/navegacao.py).

- Análise da IA: veredito (nota), alerta, um card por categoria com os motivos,
  as ameaças do meta e o próximo passo (src/modelo_nota.py, src/dicas_ia.py, src/analise.py).
- Detalhes: gráficos e tabelas da IA e os dados de apoio de src/analise.py.

Só exibição; a IA fica em modelo_nota.py e as regras em analise.py e validacao.py.
"""

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from src import config, dados
from src.analise import analisar, tipos_perigosos
from src.dicas import FUNCOES_ESSENCIAIS
from src.dicas_ia import IMPACTO_MINIMO, respostas_da_ia, texto_do_alerta
from src.funcoes_duplas import FUNCOES
from src.modelo_nota import ALERTA, PONTOS, analise_da_ia, carregar_modelo, pesos_do_modelo
from src.navegacao import MELHORAR, botao_ir_para
from src.tipos import TIPOS_PT
from src.validacao import validar_time
from src.visual import etiqueta_tipo, etiquetas, foto, grade_de_tipos, icone

TEXTO_DANO = {4: "4x", 2: "2x", 1: "", 0.5: "½", 0.25: "¼", 0: "0"}
CORES_DANO = {"4x": "#e74c3c", "2x": "#f5b7b1", "½": "#a9dfbf", "¼": "#52be80", "0": "#5dade2"}


def _lista_em_markdown(itens: list[str]) -> str:
    return "\n".join(f"- {item}" for item in itens)


def mostrar_problemas(problemas: list[dict]) -> None:
    """Erros das regras numa caixa vermelha, avisos numa amarela, o resto em azul."""
    caixas = [("erro", st.error, ":material/block:", "O time quebra as regras do formato:"),
              ("aviso", st.warning, ":material/warning:", "Vale conferir:"),
              ("info", st.info, ":material/info:", "")]
    for nivel, caixa, icone, titulo in caixas:
        mensagens = [p["mensagem"] for p in problemas if p["nivel"] == nivel]
        if len(mensagens) == 1:
            caixa(mensagens[0], icon=icone)
        elif mensagens:
            caixa(f"{titulo}\n\n{_lista_em_markdown(mensagens)}", icon=icone)


def _virgula(numero: float, casas: int = 1) -> str:
    return f"{numero:.{casas}f}".replace(".", ",")


def _cor(nota: float) -> str:
    """Verde = bom, amarelo = na média, vermelho = fraco (nota de 0 a 10)."""
    return "#34D399" if nota >= 7 else "#FBBF24" if nota >= 4 else "#F87171"


def _numero(valor: float) -> str:
    return f"{valor:.2f}".rstrip("0").rstrip(".").replace(".", ",")


def mostrar_veredito(resultado: dict, modelo: dict) -> None:
    """O resultado da IA de relance: nota num anel colorido e uma frase."""
    nota = resultado["nota"]
    titulo = ("Time forte" if nota >= 7 else "Time na média" if nota >= 4 else "Time precisa de ajustes")
    total = modelo["batalhas_treino"] + modelo["batalhas_teste"]
    st.markdown(f"""
<div class="veredito">
  <div class="anel" style="--cor:{_cor(nota)}; --pct:{nota * 10:.0f}%">
    <div><b>{_virgula(nota)}</b><small>/ 10</small></div>
  </div>
  <div>
    <div class="rotulo">{icone("auto_awesome")} Veredito da IA</div>
    <div class="titulo" style="color:{_cor(nota)}">{titulo}</div>
    <div>Mais forte que <b>{nota * 10:.0f}%</b> dos times de {total} batalhas reais.</div>
    <div>Chance de vencer um time médio do meta: <b>{_virgula(resultado['chance'])}%</b>
      <span class="apagado">(só pela montagem; quem joga também pesa)</span></div>
  </div>
</div>""", unsafe_allow_html=True)


DESCRICOES = {
    "Cobertura (top 10)": "Acerta e aguenta os 10 Pokémon mais usados?",
    "Sinergia": "Os Pokémon costumam jogar juntos e cobrem as fraquezas um do outro?",
    "Winrate": "Quanto esses Pokémon vencem nas batalhas reais?",
    "Controle de velocidade": "Breakers rápidos, Trick Room e Tailwind.",
    "Situacionais": "Fake Out, Screens e clima: só contam se o time aproveita.",
}
ICONES_CATEGORIAS = {
    "Cobertura (top 10)": "shield", "Sinergia": "hub", "Winrate": "emoji_events",
    "Controle de velocidade": "speed", "Situacionais": "tune",
}
SETAS = {1: ("trending_up", "verde"), 0: ("remove", "neutro"), -1: ("trending_down", "vermelho")}


def _motivo(seta: int, texto: str) -> str:
    simbolo, classe = SETAS[seta]
    return f'<li class="{classe}">{icone(simbolo)} {texto}</li>'


def _motivos(resultado: dict, categoria: dict) -> list[str]:
    """As linhas do card: os pontos da categoria (ou as respostas, nas situacionais)."""
    if not categoria["principal"]:
        return [_motivo(r["efeito"], f"<b>{r['pergunta']}</b> {r['resposta']}")
                for r in respostas_da_ia(resultado)]
    linhas = []
    for p in resultado["pontos"]:
        if p["categoria"] != categoria["nome"]:
            continue
        seta = (p["impacto"] >= IMPACTO_MINIMO) - (p["impacto"] <= -IMPACTO_MINIMO)
        linhas.append(_motivo(seta, f"{p['nome']}: <b>{_numero(p['valor'])}</b> "
                                    f'<span class="apagado">(vencedores: '
                                    f"{_numero(p['media_vencedores'])})</span>"))
    return linhas


def mostrar_categorias(resultado: dict) -> None:
    """Um card por categoria, na ordem de importância, com barra e os motivos da nota."""
    st.markdown("#### :material/category: Categoria por categoria")
    st.caption("Em ordem de importância para a IA. Nota = mais forte que X% dos times reais (÷10). "
               ":green[:material/trending_up:] ajuda a vencer · :red[:material/trending_down:] puxa "
               "para baixo · :gray[:material/remove:] quase não muda.")
    cards = []
    for ordem, categoria in enumerate(resultado["categorias"], start=1):
        nota, cor = categoria["nota"], _cor(categoria["nota"])
        selo = "" if categoria["principal"] else '<span class="selo">situacional</span>'
        cards.append(f"""
<div class="categoria">
  <div class="cabecalho"><span class="ordem">{ordem}</span>{icone(ICONES_CATEGORIAS.get(categoria['nome'], 'label'))}<b>{categoria['nome']}</b>{selo}
    <span class="nota" style="color:{cor}">{_virgula(nota)}</span></div>
  <div class="barra"><div style="width:{nota * 10:.0f}%; background:{cor}"></div></div>
  <div class="apagado">{DESCRICOES[categoria['nome']]}</div>
  <ul class="motivos">{''.join(_motivos(resultado, categoria))}</ul>
</div>""")
    st.markdown(f'<div class="categorias">{"".join(cards)}</div>', unsafe_allow_html=True)


def mostrar_proximo_passo(resultado: dict) -> None:
    """Liga a análise às recomendações: qual o ponto mais fraco e onde melhorar."""
    pior = min((c for c in resultado["categorias"] if c["principal"]), key=lambda c: c["nota"])
    with st.container(key="vidro_proximo_passo"):
        col_texto, col_botao = st.columns([3, 1], vertical_alignment="center")
        col_texto.markdown(f":blue[:material/lightbulb:] **Próximo passo:** o ponto mais fraco é "
                           f"**{pior['nome']}** (nota {_virgula(pior['nota'])}). A IA já testou "
                           "trocas de Pokémon para deixar o time mais forte.")
        with col_botao:
            botao_ir_para("Ver trocas sugeridas", MELHORAR, "ir_para_trocas")


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
        st.markdown(":green[:material/check_circle:] Nenhum tipo de golpe acerta forte metade do time sem resposta.")
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
        st.markdown(":green[:material/check_circle:] O time tem golpe supereficaz contra todos os tipos.")
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
    st.caption(":green[:material/check_circle:] = alguém do time faz · :red[:material/cancel:] = ninguém "
               "faz. As marcadas com :orange[:material/star:] quase todo time de duplas precisa.")
    colunas = st.columns(4)
    for n, (chave, funcao) in enumerate(FUNCOES.items()):
        quem = analise["funcoes"][chave]
        estrela = " :orange[:material/star:]" if chave in FUNCOES_ESSENCIAIS else ""
        marca = ":green[:material/check_circle:]" if quem else ":red[:material/cancel:]"
        with colunas[n % 4].container(key=f"vidro_funcao_{chave}"):
            st.markdown(f"{marca} **{funcao['nome']}**{estrela}")
            st.markdown(", ".join(quem) if quem else "ninguém")
            st.caption(funcao["descricao"])


def mostrar_ameacas(analise: dict) -> None:
    """Cards dos Pokémon do meta que levam vantagem contra o time (parte da Análise da IA)."""
    st.markdown("#### :material/crisis_alert: Ameaças do meta")
    st.caption("Entre os 30 Pokémon mais usados: quem acerta muitos do seu time com dano "
               "dobrado e quase não é acertado de volta. Pokémon sem golpes contam com "
               "os golpes mais usados com ele.")
    if not analise["ameacas"]:
        st.success("Nenhum dos mais usados leva vantagem clara contra o seu time.",
                   icon=":material/verified:")
        return
    cards = []
    for ameaca in analise["ameacas"][:6]:
        respostas = ", ".join(ameaca["respostas"]) or "nenhuma"
        classe = "verde" if ameaca["respostas"] else "vermelho"
        cards.append(f"""
<div class="ameaca">
  <div class="cabecalho">{foto(ameaca['id'], 56)}<div><b>{ameaca['nome']}</b>
    <div class="apagado">{etiquetas(ameaca['tipos_ataque'])}</div></div>
    <span class="selo">{ameaca['uso']:.0f}% dos times</span></div>
  <ul class="motivos">
    <li class="vermelho">{icone("bolt")} <b>Acerta forte:</b> {', '.join(ameaca['acerta'])}</li>
    <li class="{classe}">{icone("shield")} <b>Suas respostas:</b> {respostas}</li>
  </ul>
</div>""")
    st.markdown(f'<div class="ameacas">{"".join(cards)}</div>', unsafe_allow_html=True)


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


def mostrar_validacao(time: list[dict]) -> None:
    """Erros e avisos das regras do formato (src/validacao.py)."""
    mostrar_problemas(validar_time(time))


def reconhecidos(time: list[dict]) -> list[dict]:
    """Só os Pokémon que existem nos dados (os outros não entram na análise)."""
    return [m for m in time if m["id"] in dados.carregar_pokemon()]


def _resultado_da_ia(time: list[dict]) -> tuple[dict | None, dict | None]:
    """(resultado, modelo) da IA, ou (None, modelo) quando ela ainda não pode dar a nota."""
    modelo = carregar_modelo()
    if modelo is None or len(time) < config.TEAM_SIZE:
        return None, modelo
    return analise_da_ia(time, modelo), modelo


def _sem_nota(time: list[dict], modelo: dict | None) -> None:
    if modelo is None:
        st.info("A IA ainda não foi treinada. Rode: python -m src.replays e python -m src.modelo_nota",
                icon=":material/model_training:")
        return
    # A IA aprendeu com times completos: com menos Pokémon as contagens caem e a nota não vale.
    faltam = config.TEAM_SIZE - len(time)
    with st.container(key="vidro_sem_nota"):
        col_texto, col_botao = st.columns([3, 1], vertical_alignment="center")
        col_texto.markdown(f":blue[:material/group_add:] **Faltam {faltam} Pokémon.** A IA dá a nota "
                           f"com o time completo ({config.TEAM_SIZE}), porque aprendeu com times "
                           "completos de batalhas reais. Veja quem combina com o seu time:")
        with col_botao:
            botao_ir_para("Ver parceiros sugeridos", MELHORAR, "ir_para_parceiros")


def mostrar_analise(time: list[dict]) -> None:
    """Visão "Análise da IA": veredito, alerta, categorias, ameaças do meta e o próximo passo."""
    resultado, modelo = _resultado_da_ia(time)
    if resultado is None:
        _sem_nota(time, modelo)
        mostrar_ameacas(analisar(time))
        return
    mostrar_veredito(resultado, modelo)
    alerta = texto_do_alerta(resultado["alerta"])
    if alerta:
        st.warning(alerta, icon=":material/warning:")
    mostrar_categorias(resultado)
    mostrar_ameacas(analisar(time))
    mostrar_proximo_passo(resultado)


ABA_GRAFICOS, ABA_PONTOS, ABA_MODELO = (":material/bar_chart: Gráficos", ":material/table_chart: Pontos da análise",
                                        ":material/school: Como a IA aprendeu")
ABA_FRAQUEZAS, ABA_COBERTURA, ABA_FUNCOES = (":material/shield: Fraquezas", ":material/swords: Cobertura ofensiva",
                                             ":material/groups: Funções de duplas")


def mostrar_detalhes(time: list[dict]) -> None:
    """Visão "Detalhes": gráficos e tabelas da IA e os dados de apoio da análise."""
    resultado, modelo = _resultado_da_ia(time)
    analise = analisar(time)
    abas = [ABA_FRAQUEZAS, ABA_COBERTURA, ABA_FUNCOES]
    if resultado is not None:
        abas = [ABA_GRAFICOS, ABA_PONTOS, *abas, ABA_MODELO]
    aba = dict(zip(abas, st.tabs(abas)))
    if resultado is not None:
        with aba[ABA_GRAFICOS]:
            mostrar_graficos(resultado, modelo)
        with aba[ABA_PONTOS]:
            mostrar_pontos_ia(resultado)
        with aba[ABA_MODELO]:
            mostrar_sobre_o_modelo(modelo)
    with aba[ABA_FRAQUEZAS]:
        mostrar_fraquezas(analise, time)
    with aba[ABA_COBERTURA]:
        mostrar_cobertura(analise, time)
    with aba[ABA_FUNCOES]:
        mostrar_funcoes(analise)
