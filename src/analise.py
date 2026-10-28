"""
Análise do time: a parte de "regras + dados" da IA.

Quatro perguntas, cada uma numa função:
1. matriz_defensiva   -> de quais tipos de golpe o time apanha muito?
2. cobertura_ofensiva -> quais tipos os golpes do time não acertam bem?
3. funcoes_do_time    -> o time tem as funções de duplas (Fake Out, Tailwind...)?
4. ameacas_do_meta    -> quais Pokémon mais usados nas batalhas reais são
                         um problema para este time?

Tudo é feito com a tabela de tipos (src/tipos.py) e as estatísticas de uso.
"""

from src import dados
from src.funcoes_duplas import FUNCOES, funcoes_do_pokemon
from src.nomes import to_id
from src.tipos import TIPOS, efetividade

# Habilidades que mudam o dano recebido de um tipo (as mais comuns no VGC).
# Ex.: Levitate deixa o Pokémon imune a golpes de Terra.
HABILIDADES_DEFENSIVAS = {
    "levitate": {"Ground": 0}, "eartheater": {"Ground": 0},
    "flashfire": {"Fire": 0}, "wellbakedbody": {"Fire": 0},
    "waterabsorb": {"Water": 0}, "stormdrain": {"Water": 0}, "dryskin": {"Water": 0},
    "voltabsorb": {"Electric": 0}, "lightningrod": {"Electric": 0}, "motordrive": {"Electric": 0},
    "sapsipper": {"Grass": 0},
    "thickfat": {"Fire": 0.5, "Ice": 0.5}, "heatproof": {"Fire": 0.5},
    "waterbubble": {"Fire": 0.5}, "purifyingsalt": {"Ghost": 0.5},
}

# Habilidades que transformam golpes do tipo Normal em outro tipo.
# Ex.: Hyper Voice de um Sylveon (Pixilate) vira um golpe de Fada.
HABILIDADES_ATE = {
    "pixilate": "Fairy", "aerilate": "Flying", "refrigerate": "Ice", "galvanize": "Electric",
}

QUANTOS_DO_META = 30        # quantos Pokémon mais usados olhar nas ameaças
USO_MINIMO_DO_GOLPE = 20.0  # % mínima para contar um golpe como "o que ele costuma usar"


# ---------------------------------------------------------------------------
# Informações de um Pokémon do time
# ---------------------------------------------------------------------------

def tipos_de(membro: dict) -> list[str]:
    """Tipos na batalha (os da Mega, se ele for Mega Evoluir)."""
    info = dados.carregar_pokemon().get(membro["forma"]) or dados.carregar_pokemon()[membro["id"]]
    return info["tipos"]


def habilidade_de(membro: dict) -> str:
    """Habilidade que vale na batalha.

    Mega: a habilidade da Mega. Senão: a escrita no time; se não foi escrita,
    a mais usada nas estatísticas (ou a única que ele tem).
    """
    pokemon = dados.carregar_pokemon()
    forma = pokemon.get(membro["forma"], {})
    if forma.get("mega"):
        return forma["habilidades"][0]
    if membro["habilidade"]:
        return to_id(membro["habilidade"])
    mais_usadas = dados.carregar_uso()["pokemon"].get(membro["id"], {}).get("habilidades", {})
    if mais_usadas:
        return next(iter(mais_usadas))
    return pokemon[membro["id"]]["habilidades"][0]


def golpes_de_ataque(golpes_ids: list[str], habilidade: str) -> list[tuple[str, str]]:
    """Golpes que causam dano, como (nome do golpe, tipo). Golpes de status não contam.

    O tipo já conta a habilidade: Hyper Voice com Pixilate vira um golpe de Fada.
    """
    golpes = dados.carregar_golpes()
    ataques = []
    for golpe_id in golpes_ids:
        golpe = golpes.get(golpe_id)
        if not golpe or golpe["categoria"] == "Status" or golpe["poder"] == 0:
            continue
        tipo = golpe["tipo"]
        if tipo == "Normal" and habilidade in HABILIDADES_ATE:
            tipo = HABILIDADES_ATE[habilidade]
        ataques.append((golpe["nome"], tipo))
    return ataques


def tipos_de_ataque(golpes_ids: list[str], habilidade: str, tipos_proprios: list[str]) -> set[str]:
    """Tipos dos golpes que causam dano.

    Se não sabemos os golpes, supomos que ele ataca com os próprios tipos
    (o STAB, que é o golpe mais forte que quase todo Pokémon carrega).
    """
    tipos = {tipo for _, tipo in golpes_de_ataque(golpes_ids, habilidade)}
    return tipos or set(tipos_proprios)


def dano_recebido(tipo_golpe: str, tipos: list[str], habilidade: str) -> float:
    """Multiplicador de dano de um tipo de golpe, já contando a habilidade."""
    multiplicador = efetividade(tipo_golpe, tipos)
    ajuste = HABILIDADES_DEFENSIVAS.get(habilidade, {}).get(tipo_golpe)
    if ajuste is not None:
        multiplicador *= ajuste
    return multiplicador


def golpes_mais_usados(pokemon_id: str) -> list[str]:
    """Golpes que pelo menos USO_MINIMO_DO_GOLPE % dos jogadores usam com ele."""
    info = dados.carregar_uso()["pokemon"].get(pokemon_id, {})
    return [g for g, porcentagem in info.get("golpes", {}).items()
            if porcentagem >= USO_MINIMO_DO_GOLPE]


def ataques_do_membro(membro: dict) -> set[str]:
    """Tipos de ataque do Pokémon. Sem golpes de ataque escolhidos, supomos os
    golpes mais usados com ele nas batalhas (a Mega, se ele segura a Pedra Mega)."""
    golpes_ids = [to_id(g) for g in membro["golpes"]]
    if not golpes_de_ataque(golpes_ids, habilidade_de(membro)):
        golpes_ids = golpes_mais_usados(membro["forma"]) or golpes_mais_usados(membro["id"])
    return tipos_de_ataque(golpes_ids, habilidade_de(membro), tipos_de(membro))


def golpes_de_ataque_do_membro(membro: dict) -> list[tuple[str, str]]:
    golpes_ids = [to_id(g) for g in membro["golpes"]]
    return golpes_de_ataque(golpes_ids, habilidade_de(membro))


# ---------------------------------------------------------------------------
# 1. Fraquezas e resistências
# ---------------------------------------------------------------------------

def matriz_defensiva(time: list[dict]) -> list[dict]:
    """Para cada tipo de golpe: quanto dano cada Pokémon toma e o resumo.

    [{tipo, dano: {nome: 2.0, ...}, fracos: [...], resistem: [...], imunes: [...]}]
    """
    linhas = []
    for tipo in TIPOS:
        dano = {m["especie"]: dano_recebido(tipo, tipos_de(m), habilidade_de(m)) for m in time}
        linhas.append({
            "tipo": tipo,
            "dano": dano,
            "fracos": [nome for nome, x in dano.items() if x > 1],
            "resistem": [nome for nome, x in dano.items() if 0 < x < 1],
            "imunes": [nome for nome, x in dano.items() if x == 0],
        })
    return linhas


# ---------------------------------------------------------------------------
# 2. Cobertura ofensiva
# ---------------------------------------------------------------------------

def cobertura_ofensiva(time: list[dict]) -> list[dict]:
    """Para cada tipo de Pokémon: o melhor dano que os golpes de ataque do time causam.

    [{tipo, melhor: 2.0, quem: ["Poison Jab (Beedrill)"],
      supereficazes: [{golpe, tipo_golpe, pokemon, id}]}]
    melhor = maior multiplicador; supereficazes = todos os golpes que dão dano dobrado (ou mais).
    Só contam os golpes escolhidos: um Pokémon sem golpes de ataque não entra na conta.
    """
    # Todos os golpes de ataque do time, como (golpe, tipo do golpe, Pokémon que usa).
    golpes = [(golpe, tipo, m)
              for m in time for golpe, tipo in golpes_de_ataque_do_membro(m)]
    linhas = []
    for tipo_alvo in TIPOS:
        melhor = 0.0
        quem = []
        supereficazes = []
        for golpe, tipo, membro in golpes:
            dano = efetividade(tipo, [tipo_alvo])
            if dano > melhor:
                melhor, quem = dano, [f"{golpe} ({membro['especie']})"]
            elif dano == melhor:
                quem.append(f"{golpe} ({membro['especie']})")
            if dano >= 2:
                supereficazes.append({"golpe": golpe, "tipo_golpe": tipo,
                                      "pokemon": membro["especie"], "id": membro["forma"]})
        linhas.append({"tipo": tipo_alvo, "melhor": melhor, "quem": quem,
                       "supereficazes": supereficazes})
    return linhas


def sem_golpes_de_ataque(time: list[dict]) -> list[str]:
    """Pokémon do time que ainda não têm nenhum golpe de ataque escolhido."""
    return [m["especie"] for m in time if not golpes_de_ataque_do_membro(m)]


# ---------------------------------------------------------------------------
# 3. Funções de duplas
# ---------------------------------------------------------------------------

def funcoes_do_time(time: list[dict]) -> dict[str, list[str]]:
    """{função: [Pokémon do time que cumprem]} para todas as funções."""
    resultado = {chave: [] for chave in FUNCOES}
    for membro in time:
        for chave in funcoes_do_pokemon(membro["golpes"], habilidade_de(membro)):
            resultado[chave].append(membro["especie"])
    return resultado


# ---------------------------------------------------------------------------
# 4. Ameaças do meta
# ---------------------------------------------------------------------------

def ameacas_do_meta(time: list[dict], quantos: int = 5) -> list[dict]:
    """Os Pokémon mais usados que mais atrapalham este time.

    Para cada um dos Pokémon mais usados (com os golpes que ele costuma usar):
      - acerta: quantos do nosso time ele acerta com dano dobrado (ou mais);
      - respostas: quantos do nosso time acertam ELE com dano dobrado
        (quem ainda não tem golpes conta com os golpes mais usados com ele).
    Nota da ameaça = acerta - respostas. Quanto maior, pior para nós.
    """
    pokemon = dados.carregar_pokemon()
    uso = dados.carregar_uso()["pokemon"]
    nossas_especies = {pokemon[m["id"]]["especie_base"] for m in time if m["id"] in pokemon}
    nossos_ataques = {m["especie"]: ataques_do_membro(m) for m in time}

    ameacas = []
    for meta_id, info in list(uso.items())[:QUANTOS_DO_META]:
        if meta_id not in pokemon or pokemon[meta_id]["especie_base"] in nossas_especies:
            continue
        tipos_meta = pokemon[meta_id]["tipos"]
        habilidade_meta = next(iter(info["habilidades"]), "")
        golpes_meta = golpes_mais_usados(meta_id)
        ataques_meta = tipos_de_ataque(golpes_meta, habilidade_meta, tipos_meta)

        acerta = [m["especie"] for m in time
                  if max(dano_recebido(t, tipos_de(m), habilidade_de(m)) for t in ataques_meta) >= 2]
        respostas = [nome for nome, tipos in nossos_ataques.items()
                     if max(dano_recebido(t, tipos_meta, habilidade_meta) for t in tipos) >= 2]
        ameacas.append({
            "id": meta_id,
            "nome": info["nome"],
            "uso": info["uso"],
            "tipos_ataque": sorted(ataques_meta),
            "acerta": acerta,
            "respostas": respostas,
            "nota": len(acerta) - len(respostas),
        })

    # Maior nota primeiro; no empate, o mais usado.
    ameacas.sort(key=lambda a: (a["nota"], a["uso"]), reverse=True)
    return [a for a in ameacas if a["nota"] > 0][:quantos]


def tipos_perigosos(analise: dict) -> list[dict]:
    """Tipos de golpe a que 2 ou mais são fracos e que poucos seguram."""
    perigosos = []
    for linha in analise["defesa"]:
        fracos = len(linha["fracos"])
        seguram = len(linha["resistem"]) + len(linha["imunes"])
        if fracos >= 2 and fracos > seguram:
            perigosos.append({"tipo": linha["tipo"], "fracos": fracos, "seguram": seguram})
    return sorted(perigosos, key=lambda p: p["fracos"] - p["seguram"], reverse=True)


def analisar(time: list[dict]) -> dict:
    """Roda as quatro análises de uma vez (só com os Pokémon reconhecidos)."""
    time = [m for m in time if m["id"] in dados.carregar_pokemon()]
    return {
        "defesa": matriz_defensiva(time),
        "cobertura": cobertura_ofensiva(time),
        "sem_ataques": sem_golpes_de_ataque(time),
        "funcoes": funcoes_do_time(time),
        "ameacas": ameacas_do_meta(time),
    }
