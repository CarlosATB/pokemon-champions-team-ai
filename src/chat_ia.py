"""
Chat com um agente de IA (modelo de linguagem da Groq) que conversa sobre o time.

Intuição: o agente NÃO faz a análise. Quem analisa são os nossos algoritmos
(regras, recomendação por co-ocorrência e o modelo de ML). O agente recebe,
escondido no "prompt de sistema", um resumo do que esses algoritmos acharam
do time montado, e usa isso para responder em linguagem natural.

    time montado -> analisar() + analise_da_ia() -> texto de contexto
    contexto + histórico + pergunta -> API da Groq -> resposta

A interface (a bolinha no canto inferior direito) fica em src/tela_chat.py.
Este arquivo não usa o Streamlit, para poder ser testado sem o site.
"""

import os

import requests

from src import config

PAPEL_DO_AGENTE = f"""Você é o assistente do site "Pokémon Champions Team AI", um trabalho de \
Inteligência Artificial (CEUB). Responda sempre em português do Brasil, de forma curta e clara \
(no máximo uns 3 parágrafos ou uma lista curta).

Formato do jogo: Pokémon Champions, duplas (VGC), {config.REGULATION_NAME}. Nível {config.LEVEL}; \
leva {config.TEAM_SIZE} e escolhe {config.PICK_SIZE}. Não pode repetir espécie nem item. \
Só {config.MAX_MEGA_PER_BATTLE} Mega Evolução por batalha. Não existe Terastalização. \
Pontos de status (EVs do Champions): até {config.EV_MAX} por status e {config.EV_TOTAL} no total.

Use os dados do site (abaixo) como fonte principal. Se não souber algo do Champions, diga que \
não tem certeza em vez de inventar. Não sugira Tera nem Pokémon/itens repetidos. Para mudar o \
time, explique o que fazer nos cards da aba "Montar o time" (você não consegue mexer neles).
Se perguntarem como o site funciona: a análise vem de regras de tipos e funções de duplas, a \
recomendação vem de estatísticas de uso do Smogon ("quem usa X também usa Y") e a nota vem de \
uma regressão logística treinada com batalhas reais do Showdown. Você (o chat) só explica os \
resultados."""


def chave_da_api(secrets=None) -> str | None:
    """A chave vem dos Secrets do Streamlit (site publicado) ou de uma variável de
    ambiente (no PC). Nunca fica no repositório."""
    nome = config.CHAT_NOME_DA_CHAVE
    try:
        if secrets is not None and nome in secrets:
            return str(secrets[nome]).strip() or None
    except Exception:  # sem arquivo de secrets, o Streamlit dá erro ao ler
        pass
    return os.environ.get(nome, "").strip() or None


def _membro_em_texto(membro: dict) -> str:
    partes = [membro["especie"]]
    if membro.get("item"):
        partes.append(f"@ {membro['item']}")
    linha = " ".join(partes)
    detalhes = []
    if membro.get("habilidade"):
        detalhes.append(f"habilidade {membro['habilidade']}")
    if membro.get("natureza"):
        detalhes.append(f"natureza {membro['natureza']}")
    evs = {s: v for s, v in (membro.get("evs") or {}).items() if v}
    if evs:
        detalhes.append("EVs " + ", ".join(f"{v} {s}" for s, v in evs.items()))
    golpes = membro.get("golpes") or []
    detalhes.append("golpes: " + (", ".join(golpes) if golpes else "nenhum escolhido"))
    return f"- {linha} ({'; '.join(detalhes)})"


def contexto_do_time(time: list[dict]) -> str:
    """Resumo do time e do que os algoritmos do site acharam dele, em texto."""
    if not time:
        return "O usuário ainda não montou nenhum Pokémon no time."

    linhas = [f"Time montado agora ({len(time)} de {config.TEAM_SIZE}):"]
    linhas += [_membro_em_texto(m) for m in time]

    # Cada parte é opcional: se uma análise falhar, o chat continua funcionando.
    try:
        from src.analise import analisar, tipos_perigosos
        analise = analisar(time)
        perigosos = tipos_perigosos(analise)
        if perigosos:
            linhas.append("Tipos perigosos (muitos fracos, poucos seguram): " + ", ".join(
                f"{p['tipo']} ({p['fracos']} fracos, {p['seguram']} seguram)" for p in perigosos))
        sem_2x = [c["tipo"] for c in analise["cobertura"] if not c.get("supereficazes")]
        if sem_2x and not len(sem_2x) == len(analise["cobertura"]):
            linhas.append("Tipos que o time não acerta com dano dobrado: " + ", ".join(sem_2x))
        if analise["sem_ataques"]:
            linhas.append("Sem golpes de ataque escolhidos: " + ", ".join(analise["sem_ataques"]))
        funcoes = [f"{nome}: {', '.join(quem) if quem else 'ninguém'}"
                   for nome, quem in analise["funcoes"].items()]
        linhas.append("Funções de duplas -> " + "; ".join(funcoes))
        if analise["ameacas"]:
            linhas.append("Ameaças do meta: " + "; ".join(
                f"{a['nome']} (acerta forte {', '.join(a['acerta'])})" for a in analise["ameacas"]))
    except Exception:
        pass

    try:
        if len(time) == config.TEAM_SIZE:
            from src.modelo_nota import analise_da_ia
            ia = analise_da_ia(time)
            if ia:
                linhas.append(f"Nota da IA do site: {ia['nota']}/10; chance de vencer um time "
                              f"médio do meta: {ia['chance']}%.")
                linhas.append("Notas por categoria: " + ", ".join(
                    f"{c['nome']} {c['nota']}" for c in ia["categorias"]))
        else:
            linhas.append("A nota da IA do site só sai com o time completo (6 Pokémon).")
            from src.recomendacao import sugerir_parceiros
            parceiros = sugerir_parceiros(time)
            if parceiros:
                linhas.append("Parceiros que a recomendação do site sugere (co-ocorrência no meta): "
                              + "; ".join(f"{p['nome']} ({p['confianca']}% dos times com o seu)"
                                          for p in parceiros))
    except Exception:
        pass
    return "\n".join(linhas)


def montar_mensagens(historico: list[dict], contexto: str) -> list[dict]:
    """[prompt de sistema com o contexto] + as últimas mensagens da conversa."""
    sistema = f"{PAPEL_DO_AGENTE}\n\nDados do site neste momento:\n{contexto}"
    recentes = historico[-config.CHAT_MAX_MENSAGENS:]
    return [{"role": "system", "content": sistema}] + [
        {"role": m["role"], "content": m["content"]} for m in recentes]


class ErroDoChat(Exception):
    """Erro com uma mensagem amigável para mostrar no chat."""


def _pedir(mensagens: list[dict], chave: str, modelo: str, post) -> requests.Response:
    corpo = {"model": modelo, "messages": mensagens, "temperature": 0.5,
             "max_tokens": config.CHAT_MAX_TOKENS}
    if modelo.startswith("openai/gpt-oss"):
        corpo["reasoning_effort"] = "low"  # pensa pouco: responde mais rápido
    return post(config.CHAT_API_URL, json=corpo, timeout=30,
                headers={"Authorization": f"Bearer {chave}"})


def perguntar(mensagens: list[dict], chave: str, post=None) -> str:
    """Manda a conversa para a API e devolve o texto da resposta.
    Se o modelo principal não existir mais, tenta o reserva.
    (post pode ser trocado por uma função falsa nos testes.)"""
    post = post or requests.post
    try:
        resposta = _pedir(mensagens, chave, config.CHAT_MODELO, post)
        if resposta.status_code in (400, 404) and "model" in resposta.text.lower():
            resposta = _pedir(mensagens, chave, config.CHAT_MODELO_RESERVA, post)
    except requests.RequestException as erro:
        raise ErroDoChat("Não consegui falar com o agente agora (sem conexão). "
                         "Tente de novo em instantes.") from erro

    if resposta.status_code == 401:
        raise ErroDoChat("A chave da API foi recusada. Confira o GROQ_API_KEY nos Secrets.")
    if resposta.status_code == 429:
        raise ErroDoChat("O limite gratuito da API foi atingido. Espere um pouco e tente de novo.")
    if resposta.status_code != 200:
        raise ErroDoChat(f"O agente respondeu com erro ({resposta.status_code}). Tente de novo.")
    try:
        texto = resposta.json()["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as erro:
        raise ErroDoChat("O agente mandou uma resposta que não entendi. Tente de novo.") from erro
    return (texto or "").strip() or "(o agente não respondeu nada; tente perguntar de outro jeito)"
