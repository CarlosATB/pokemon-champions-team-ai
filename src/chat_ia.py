"""
Chat com um agente de IA (modelo de linguagem da Groq).

1ª parte (esta): um chat genérico que responde perguntas sobre Pokémon e VGC.
    papel do agente + tabela de tipos + fatos dos Pokémon citados (prompt de sistema)
    + histórico + pergunta -> API da Groq -> resposta

Modelos de linguagem às vezes "alucinam" (ex.: dizer que Fada toma 4x de Dragão,
quando Fada é imune). Para evitar isso, o próprio código calcula os fatos e
manda junto: a tabela de tipos do projeto (src/tipos.py) e, para cada Pokémon
citado na conversa, os tipos, status base, habilidades e fraquezas/resistências
calculadas. O agente é instruído a confiar nesses fatos e não na memória dele.
2ª parte (depois): ligar o chat ao time montado e às análises do site
    (ex.: "quero um time com Umbreon" -> o agente devolve um time).

A interface (a bolinha no canto inferior direito) fica em src/tela_chat.py.
Este arquivo não usa o Streamlit, para poder ser testado sem o site.
"""

import os
import re

import requests

from src import config, dados
from src.tipos import TIPOS, TIPOS_PT, efetividade, multiplicador

PAPEL_DO_AGENTE = f"""Você é o assistente do site "Pokémon Champions Team AI", um trabalho de \
Inteligência Artificial (CEUB). Responda sempre em português do Brasil, de forma curta e clara \
(no máximo uns 3 parágrafos ou uma lista curta).

Formato do jogo: Pokémon Champions, duplas (VGC), {config.REGULATION_NAME}. Nível {config.LEVEL}; \
leva {config.TEAM_SIZE} e escolhe {config.PICK_SIZE}. Não pode repetir espécie nem item. \
Só {config.MAX_MEGA_PER_BATTLE} Mega Evolução por batalha. Não existe Terastalização. \
Pontos de status (EVs do Champions): até {config.EV_MAX} por status e {config.EV_TOTAL} no total.

Se não souber algo do Champions, diga que não tem certeza em vez de inventar. \
Não sugira Tera nem Pokémon/itens repetidos.

REGRA IMPORTANTE: para tipos, fraquezas, resistências, imunidades e status base, use SOMENTE \
a tabela de tipos e os fatos abaixo (calculados pelo código do site), nunca a sua memória. \
Para um Pokémon de dois tipos, multiplique os dois valores da tabela (0 em qualquer um = imune). \
Se um Pokémon citado não aparece nos fatos, ele não está nos dados da regulamentação atual \
(ou o nome foi escrito diferente): avise isso em vez de inventar."""

MAX_POKEMON_NOS_FATOS = 6  # quantos Pokémon citados entram nos fatos (para o prompt não crescer demais)


def _pt(tipos) -> str:
    return ", ".join(TIPOS_PT[t] for t in tipos) or "nenhum"


def tabela_de_tipos_em_texto() -> str:
    """A tabela 18 × 18 de src/tipos.py, só com o que não é dano normal."""
    linhas = ["Tabela de tipos (tipo do GOLPE -> efeito no tipo do ALVO; o resto é 1x):"]
    for golpe in TIPOS:
        partes = []
        for valor, rotulo in ((2.0, "2x"), (0.5, "0,5x"), (0.0, "0x/imune")):
            alvos = [alvo for alvo in TIPOS if multiplicador(golpe, alvo) == valor]
            if alvos:
                partes.append(f"{rotulo} em {_pt(alvos)}")
        linhas.append(f"- {TIPOS_PT[golpe]}: " + "; ".join(partes))
    return "\n".join(linhas)


def pokemon_citados(texto: str) -> list[str]:
    """Ids dos Pokémon (dos dados do site) cujo nome aparece no texto.
    Citar a forma normal (ex.: "Charizard") traz também as Megas dela."""
    pokemon = dados.carregar_pokemon()
    texto = texto.lower()
    citados = []
    for pid, info in pokemon.items():
        if re.search(rf"(?<![\w-]){re.escape(info['nome'].lower())}(?![\w-])", texto):
            citados.append(pid)
    # As Megas e formas da mesma espécie de quem foi citado
    especies = {pokemon[pid]["especie_base"] for pid in citados}
    extras = [pid for pid, info in pokemon.items() if info["especie_base"] in especies
              and info["mega"] and pid not in citados]
    return (citados + extras)[:MAX_POKEMON_NOS_FATOS]


def fatos_do_pokemon(pid: str) -> str:
    """Tipos, status, habilidades e o que cada tipo de golpe faz nele (calculado pela tabela)."""
    info = dados.carregar_pokemon()[pid]
    habilidades = dados.carregar_habilidades()
    dano = {golpe: efetividade(golpe, info["tipos"]) for golpe in TIPOS}
    grupos = [("toma 4x de", [t for t, x in dano.items() if x == 4]),
              ("toma 2x de", [t for t, x in dano.items() if x == 2]),
              ("resiste (0,5x ou 0,25x) a", [t for t, x in dano.items() if 0 < x < 1]),
              ("é IMUNE (0x) a", [t for t, x in dano.items() if x == 0])]
    status = info["status"]
    from src.analise import HABILIDADES_DEFENSIVAS  # ex.: Levitate = imune a Terrestre
    notas_habilidade = [
        f"com {habilidades.get(h, h)}: " + ", ".join(
            f"{TIPOS_PT[t]} vira {str(dano[t] * x).replace('.', ',').removesuffix(',0')}x"
            for t, x in HABILIDADES_DEFENSIVAS[h].items())
        for h in info["habilidades"] if h in HABILIDADES_DEFENSIVAS]
    return (f"- {info['nome']}: tipo {_pt(info['tipos'])}; status base HP {status['hp']}, "
            f"Atk {status['atk']}, Def {status['def']}, SpA {status['spa']}, SpD {status['spd']}, "
            f"Spe {status['spe']}; habilidades possíveis: "
            f"{', '.join(habilidades.get(h, h) for h in info['habilidades'])}. "
            + "; ".join(f"{rotulo} {_pt(tipos)}" for rotulo, tipos in grupos if tipos)
            + (f". Habilidade muda: {'; '.join(notas_habilidade)}" if notas_habilidade else "") + ".")


def fatos_da_conversa(historico: list[dict]) -> str:
    """Fatos calculados pelo código sobre os Pokémon citados nas últimas mensagens."""
    texto = " ".join(m["content"] for m in historico[-config.CHAT_MAX_MENSAGENS:])
    try:
        citados = pokemon_citados(texto)
        linhas = [fatos_do_pokemon(pid) for pid in citados]
    except Exception:  # sem os dados, o chat continua só com a tabela
        linhas = []
    if not linhas:
        return "Fatos dos Pokémon citados: nenhum Pokémon dos dados do site foi citado."
    return "Fatos dos Pokémon citados (calculados pelo código do site):\n" + "\n".join(linhas)


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
    """[prompt de sistema: papel do agente + tabela de tipos + fatos] + as últimas mensagens."""
    recentes = historico[-config.CHAT_MAX_MENSAGENS:]
    sistema = "\n\n".join([PAPEL_DO_AGENTE, tabela_de_tipos_em_texto(), fatos_da_conversa(recentes)])
    return [{"role": "system", "content": sistema}] + [
        {"role": m["role"], "content": m["content"]} for m in recentes]


class ErroDoChat(Exception):
    """Erro com uma mensagem amigável para mostrar no chat."""


def _pedir(mensagens: list[dict], chave: str, modelo: str, post) -> requests.Response:
    corpo = {"model": modelo, "messages": mensagens, "temperature": config.CHAT_TEMPERATURA,
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
