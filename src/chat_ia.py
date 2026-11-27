"""
Chat com um agente de IA (modelo de linguagem da Groq).

1ª parte (esta): um chat genérico que responde perguntas sobre Pokémon e VGC.
    papel do agente (prompt de sistema) + histórico + pergunta -> API da Groq -> resposta
2ª parte (depois): ligar o chat ao time montado e às análises do site
    (ex.: "quero um time com Umbreon" -> o agente devolve um time).

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

Se não souber algo do Champions, diga que não tem certeza em vez de inventar. \
Não sugira Tera nem Pokémon/itens repetidos."""


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


def montar_mensagens(historico: list[dict]) -> list[dict]:
    """[prompt de sistema com o papel do agente] + as últimas mensagens da conversa."""
    recentes = historico[-config.CHAT_MAX_MENSAGENS:]
    return [{"role": "system", "content": PAPEL_DO_AGENTE}] + [
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
