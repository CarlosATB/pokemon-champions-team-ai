"""
Seção "2. Análise" do site: mostra o resultado de src/analise.py e src/dicas.py.

Só exibição; as regras ficam em analise.py, dicas.py e validacao.py.
"""

import pandas as pd
import streamlit as st

from src import dados
from src.analise import analisar, tipos_perigosos
from src.dicas import FUNCOES_ESSENCIAIS, gerar_dicas
from src.funcoes_duplas import FUNCOES
from src.tipos import TIPOS, TIPOS_PT
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


def mostrar_resumo(time: list[dict], analise: dict) -> None:
    """Quatro números grandes para ver o time de relance."""
    alguem_ataca = len(analise["sem_ataques"]) < len(time)
    acerta_forte = sum(c["melhor"] >= 2 for c in analise["cobertura"])
    funcoes = sum(bool(quem) for quem in analise["funcoes"].values())
    ameaca = analise["ameacas"][0]["nome"] if analise["ameacas"] else "nenhuma"
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tipos perigosos", len(tipos_perigosos(analise)),
                help="Tipos de golpe a que 2 ou mais do time são fracos e poucos resistem.")
    col2.metric("Acerta com dano dobrado",
                f"{acerta_forte} de {len(TIPOS)} tipos" if alguem_ataca else "sem golpes",
                help="Quantos tipos os golpes de ataque do time acertam com dano dobrado.")
    col3.metric("Funções de duplas", f"{funcoes} de {len(FUNCOES)}",
                help="Controle de velocidade, Fake Out, Intimidate, redirecionamento...")
    col4.metric("Maior ameaça do meta", ameaca,
                help="O Pokémon muito usado que mais atrapalha o seu time.")


def mostrar_dicas(time: list[dict], analise: dict) -> None:
    dicas = gerar_dicas(time, analise)
    colunas = st.columns(3)
    grupos = [("alerta", "🔴 Problemas"), ("atencao", "🟡 Pode melhorar"), ("ok", "🟢 Pontos fortes")]
    for coluna, (nivel, titulo) in zip(colunas, grupos):
        with coluna.container(border=True):
            st.markdown(f"**{titulo}**")
            textos = [d["texto"] for d in dicas if d["nivel"] == nivel]
            st.markdown(_lista_em_markdown(textos) if textos else "Nenhum.")


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


def mostrar_analise(time: list[dict]) -> list[dict]:
    """Desenha a seção inteira. Devolve só os Pokémon reconhecidos (para as recomendações)."""
    mostrar_problemas(validar_time(time))
    time_ok = [m for m in time if m["id"] in dados.carregar_pokemon()]
    if not time_ok:
        return []
    analise = analisar(time_ok)
    mostrar_resumo(time_ok, analise)
    st.subheader("Dicas")
    mostrar_dicas(time_ok, analise)
    aba_def, aba_of, aba_func, aba_ameacas = st.tabs(
        ["Fraquezas e resistências", "Cobertura ofensiva", "Funções de duplas", "Ameaças do meta"])
    with aba_def:
        mostrar_fraquezas(analise, time_ok)
    with aba_of:
        mostrar_cobertura(analise, time_ok)
    with aba_func:
        mostrar_funcoes(analise)
    with aba_ameacas:
        mostrar_ameacas(analise)
    return time_ok
