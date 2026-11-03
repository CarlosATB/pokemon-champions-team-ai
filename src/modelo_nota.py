"""
Análise do time com Machine Learning: a IA APRENDE com batalhas reais o que faz um time VENCER.

A ideia (aprendizado supervisionado):
- DADOS: milhares de batalhas reais do Pokémon Showdown (src/replays.py).
  Em cada uma temos os dois times e quem ganhou.
- ENTRADAS (pontos de análise): para cada time calculamos 12 números, em
  categorias com uma ORDEM DE IMPORTÂNCIA (a de quem joga VGC):
    1. Cobertura contra os 10 mais usados -> ataque e defesa
    2. Sinergia                           -> aparecem juntos, cobrem fraquezas um do outro
    3. Winrate                            -> quanto os Pokémon do time vencem nas batalhas
    4. Controle de velocidade             -> breakers rápidos, Trick Room, Tailwind
    5. Situacionais                       -> clima, Fake Out e Screens, que só contam
                                             quando o time se beneficia deles
  e um ponto de ALERTA: muitos atacantes físicos e pouco especial (sofre contra
  as ameaças do meta que são bulky).
- RÓTULO: o time 1 venceu? (1 = sim, 0 = não)
- MODELO: Regressão Logística feita só com numpy. Cada categoria ganha um PESO,
  aprendido com as batalhas, mas com uma regra: o peso de uma categoria é
  sempre maior que o da categoria de baixo (cobertura > sinergia > winrate >
  velocidade > situacionais) e o alerta só pode tirar força.
  "Força" do time = soma de peso × categoria. Na batalha, a chance do time 1
  vencer = sigmoide(força do time 1 - força do time 2).

A NOTA (0 a 10) de um time é a posição da força dele entre os times reais:
nota 8 = mais forte que 80% dos times das batalhas.

Para treinar (precisa de data/processed/replays.json; gera modelo_nota.json):
    python -m src.modelo_nota
"""

import json
from functools import lru_cache

import numpy as np

from src import config, dados
from src.analise import (ataques_do_membro, dano_recebido, golpes_mais_usados,
                         habilidade_de, tipos_de, tipos_de_ataque)
from src.leitor import montar_time
from src.nomes import to_id
from src.recomendacao import chave_de_uso
from src.tipos import TIPOS

TOP_DO_META = 10      # cobertura contra os 10 Pokémon mais usados
PARTE_DE_TESTE = 0.2  # 20% das batalhas ficam de fora do treino, para avaliar
SEMENTE = 42          # mesma semente = mesma divisão treino/teste = mesmo modelo
TAXA = 0.1            # tamanho do passo do gradiente descendente
PASSOS = 3000         # quantos passos de treino
REGULARIZACAO = 0.01  # força da regularização L2 (pesos menores = menos exagero)
# Só batalhas com rating a partir deste valor: entre jogadores com experiência,
# a montagem do time pesa mais no resultado (testamos 0, 1100, 1200, 1300 e 1400;
# 1200 deu a melhor acurácia na validação cruzada com dados suficientes).
RATING_MINIMO = 1200
# Winrate "suavizado": cada Pokémon começa com 20 batalhas imaginárias de 50%.
# Assim quem apareceu em 3 batalhas e venceu as 3 não vira "100% de vitória".
BATALHAS_IMAGINARIAS = 20
# Distância mínima entre o peso de uma categoria e o da de baixo. Sem ela os
# dados (fracos) deixam os pesos quase iguais; com 0,01 a ordem fica clara e a
# acurácia da validação cruzada quase não muda (52,0% -> 51,7%).
DEGRAU_MINIMO = 0.01

# As categorias, da MAIS importante para a menos importante (o treino respeita essa ordem).
CATEGORIAS = ["Cobertura (top 10)", "Sinergia", "Winrate", "Controle de velocidade", "Situacionais"]
PRINCIPAIS = CATEGORIAS[:4]  # as situacionais não entram em "melhor/pior categoria"
ALERTA = "Alerta"

# Os pontos de análise: chave -> (categoria, nome bonito).
PONTOS = {
    "cobertura_ataque": ("Cobertura (top 10)", "Ataque: top 10 que o time acerta com dano dobrado"),
    "cobertura_defesa": ("Cobertura (top 10)", "Defesa: ataques do top 10 que alguém do time resiste"),
    "aparecem_juntos": ("Sinergia", "Aparecem juntos no meta"),
    "cobrem_fraquezas": ("Sinergia", "Cobrem as fraquezas um do outro"),
    "winrate": ("Winrate", "Winrate dos Pokémon do time nas batalhas (%)"),
    "breakers_rapidos": ("Controle de velocidade", "Breakers rápidos (rápidos e fortes)"),
    "trick_room": ("Controle de velocidade", "Trick Room (lentos com quem usa Trick Room)"),
    "tailwind": ("Controle de velocidade", "Tailwind (quem usa)"),
    "clima": ("Situacionais", "Clima: quem aproveita menos quem é prejudicado"),
    "fake_out": ("Situacionais", "Fake Out: +1 com setup no time, -1 com Psychic Terrain"),
    "screens": ("Situacionais", "Screens: +1 com setup ou Trick Room no time"),
    "fisicos_demais": (ALERTA, "Alerta: atacantes físicos a mais (e pouco especial)"),
}
# Pontos que valem 0 quando o time não usa aquilo: 0 = não muda a força
# (por isso não subtraímos a média deles, como fazemos com os outros).
SEM_MEDIA = {"clima", "fake_out", "screens", "fisicos_demais"}
# Que pontos formam cada coluna do modelo: as categorias, na ordem, e o alerta no fim.
COLUNAS = CATEGORIAS + [ALERTA]
GRUPOS = [[i for i, (cat, _) in enumerate(PONTOS.values()) if cat == coluna] for coluna in COLUNAS]

BREAKER_VELOCIDADE = 100  # base de Speed a partir da qual o Pokémon é "rápido"
BREAKER_ATAQUE = 110      # base de Attack ou Sp. Atk a partir da qual ele é "forte"
LENTO = 60                # base de Speed até onde o Pokémon gosta do Trick Room
BULKY = 100               # base de Defense a partir da qual uma ameaça segura golpes físicos
SCREENS = {"reflect", "lightscreen", "auroraveil"}
# Setup: golpes que aumentam os próprios status.
GOLPES_DE_SETUP = {"swordsdance", "nastyplot", "dragondance", "calmmind", "quiverdance", "bulkup",
                   "shellsmash", "bellydrum", "coil", "tidyup", "victorydance", "geomancy",
                   "irondefense", "curse", "growth", "shiftgear", "agility", "tailglow"}
# Preparar o campo: golpes que "settam" algo para o time.
GOLPES_DE_PREPARAR = {"trickroom", "tailwind", "raindance", "sunnyday", "sandstorm", "snowscape",
                      "reflect", "lightscreen", "auroraveil", "electricterrain", "grassyterrain",
                      "mistyterrain"}

# Climas: quem coloca, quem aproveita e quem sofre.
CLIMAS = {
    "chuva": {"habilidades": {"drizzle"}, "golpe": "raindance",
              "aproveitam": {"swiftswim", "raindish", "dryskin", "hydration"},
              "tipo_forte": "Water", "tipo_fraco": "Fire"},
    "sol": {"habilidades": {"drought", "orichalcumpulse"}, "golpe": "sunnyday",
            "aproveitam": {"chlorophyll", "solarpower", "protosynthesis", "flowergift", "leafguard"},
            "tipo_forte": "Fire", "tipo_fraco": "Water"},
    "areia": {"habilidades": {"sandstream"}, "golpe": "sandstorm",
              "aproveitam": {"sandrush", "sandforce", "sandveil"},
              "tipos_imunes": {"Rock", "Ground", "Steel"}, "tipo_que_ganha": "Rock"},
    "neve": {"habilidades": {"snowwarning"}, "golpe": "snowscape",
             "aproveitam": {"slushrush", "icebody", "snowcloak"}, "tipo_que_ganha": "Ice"},
}
IMUNES_A_AREIA = {"overcoat", "magicguard", "sandrush", "sandforce", "sandveil"}


# ---------------------------------------------------------------------------
# 1. Pontos de análise: o time virando números
# ---------------------------------------------------------------------------

def golpes_do_membro(membro: dict) -> set[str]:
    """Golpes escolhidos; sem nenhum, os mais usados com ele nas batalhas."""
    escolhidos = {to_id(g) for g in membro["golpes"] if g}
    return escolhidos or set(golpes_mais_usados(membro["forma"]) or golpes_mais_usados(membro["id"]))


def status_de(membro: dict) -> dict:
    """Status base na batalha (os da Mega, se ele for Mega Evoluir)."""
    pokemon = dados.carregar_pokemon()
    return (pokemon.get(membro["forma"]) or pokemon[membro["id"]])["status"]


@lru_cache
def top_do_meta(quantos: int = TOP_DO_META) -> list[dict]:
    """Os mais usados do meta: tipos, habilidade e tipos de ataque de cada um."""
    pokemon, uso = dados.carregar_pokemon(), dados.carregar_uso()["pokemon"]
    top = []
    for pokemon_id, info in uso.items():
        if pokemon_id not in pokemon or pokemon[pokemon_id]["forma_de_batalha"]:
            continue
        tipos = pokemon[pokemon_id]["tipos"]
        habilidade = next(iter(info["habilidades"]), "")
        ataques = tipos_de_ataque(golpes_mais_usados(pokemon_id), habilidade, tipos)
        top.append({"id": pokemon_id, "tipos": tipos, "habilidade": habilidade, "ataques": ataques})
        if len(top) == quantos:
            break
    return top


def cobertura_ataque(time: list[dict]) -> float:
    """Parte do top 10 que algum golpe do time acerta com dano dobrado (ou mais)."""
    ataques = set().union(*(ataques_do_membro(m) for m in time))
    top = top_do_meta()
    acertados = [any(dano_recebido(t, alvo["tipos"], alvo["habilidade"]) >= 2 for t in ataques)
                 for alvo in top]
    return sum(acertados) / len(top)


def cobertura_defesa(time: list[dict]) -> float:
    """Em média, que parte dos tipos de ataque de cada top 10 alguém do time resiste."""
    defensores = [(tipos_de(m), habilidade_de(m)) for m in time]
    partes = []
    for atacante in top_do_meta():
        resistidos = [any(dano_recebido(t, tipos, hab) <= 0.5 for tipos, hab in defensores)
                      for t in atacante["ataques"]]
        partes.append(sum(resistidos) / len(resistidos))
    return sum(partes) / len(partes)


def aparecem_juntos(time: list[dict]) -> float:
    """Média, entre todos os pares (A, B) do time, da % de times com A que também têm B.

    Usa os "parceiros" do uso.json (co-ocorrência). Ex.: 36,8 de Rillaboom ->
    Incineroar quer dizer que 36,8% dos times com Rillaboom têm Incineroar.
    """
    uso = dados.carregar_uso()["pokemon"]
    chaves = [chave_de_uso(m) for m in time]
    juntos = [uso[a]["parceiros"].get(b, 0.0) if a and b else 0.0
              for i, a in enumerate(chaves) for j, b in enumerate(chaves) if i != j]
    return sum(juntos) / len(juntos) if juntos else 0.0


def cobrem_fraquezas(time: list[dict]) -> float:
    """Das fraquezas de cada Pokémon, que parte um companheiro resiste (ou é imune).

    Ex.: Incineroar é fraco a Water; se outro do time resiste a Water, essa
    fraqueza está coberta. 1 = todas cobertas.
    """
    defensores = [(tipos_de(m), habilidade_de(m)) for m in time]
    cobertas, fraquezas = 0, 0
    for i, (tipos, hab) in enumerate(defensores):
        for tipo in TIPOS:
            if dano_recebido(tipo, tipos, hab) >= 2:
                fraquezas += 1
                cobertas += any(dano_recebido(tipo, t2, h2) <= 0.5
                                for j, (t2, h2) in enumerate(defensores) if j != i)
    return cobertas / fraquezas if fraquezas else 1.0


def winrate_suavizado(vitorias: float, batalhas: float) -> float:
    """Taxa de vitória com as batalhas imaginárias de 50% (0 a 1)."""
    return (vitorias + BATALHAS_IMAGINARIAS / 2) / (batalhas + BATALHAS_IMAGINARIAS)


def winrate_do_time(time: list[dict], winrates: dict[str, float]) -> float:
    """Média do winrate (%) dos Pokémon do time. Quem nunca apareceu conta como 50%."""
    return 100 * float(np.mean([winrates.get(m["id"], 0.5) for m in time]))


def efeito_do_clima(time: list[dict]) -> tuple[str | None, list[str], list[str]]:
    """(clima que o próprio time coloca, quem aproveita, quem é prejudicado)."""
    nome = None
    for membro in time:
        for clima_id, clima in CLIMAS.items():
            if habilidade_de(membro) in clima["habilidades"] or clima["golpe"] in golpes_do_membro(membro):
                nome = nome or clima_id
    if nome is None:
        return None, [], []
    clima = CLIMAS[nome]
    aproveitam, prejudicados = [], []
    for membro in time:
        habilidade, tipos, ataques = habilidade_de(membro), tipos_de(membro), ataques_do_membro(membro)
        if (habilidade in clima["aproveitam"] or clima.get("tipo_forte") in ataques
                or clima.get("tipo_que_ganha") in tipos):
            aproveitam.append(membro["especie"])
        elif "tipo_fraco" in clima and clima["tipo_fraco"] in ataques:
            prejudicados.append(membro["especie"])  # ataque enfraquecido (Fire na chuva, Water no sol)
        elif "tipos_imunes" in clima and not (set(tipos) & clima["tipos_imunes"]) \
                and habilidade not in IMUNES_A_AREIA:
            prejudicados.append(membro["especie"])  # toma dano da areia todo turno
    return nome, aproveitam, prejudicados


def situacionais_do_time(time: list[dict]) -> dict:
    """Clima, Fake Out e Screens: quem usa e se o time se BENEFICIA deles.

    - Fake Out ajuda quando outro Pokémon do time faz setup ou prepara o campo
      (Trick Room, Tailwind, clima...) no turno ganho. Mas o Psychic Terrain
      bloqueia golpes de prioridade contra quem está no chão: aí ele atrapalha.
    - Screens ajudam quando alguém do time faz setup ou usa Trick Room.
    - Clima: quem aproveita menos quem é prejudicado.
    """
    golpes = [golpes_do_membro(m) for m in time]
    nomes = [m["especie"] for m in time]

    def quem_usa(alvo: set[str]) -> list[str]:
        return [nome for nome, g in zip(nomes, golpes) if g & alvo]

    fake_out = quem_usa({"fakeout"})
    psychic_terrain = [nome for nome, m, g in zip(nomes, time, golpes)
                       if habilidade_de(m) == "psychicsurge" or "psychicterrain" in g]
    setup_para_fake_out = [n for n in quem_usa(GOLPES_DE_SETUP | GOLPES_DE_PREPARAR) if n not in fake_out]
    screens = quem_usa(SCREENS)
    setup_para_screens = [n for n in quem_usa(GOLPES_DE_SETUP | {"trickroom"}) if n not in screens]
    clima, aproveitam, prejudicados = efeito_do_clima(time)

    if not fake_out:
        valor_fake_out = 0
    elif psychic_terrain:
        valor_fake_out = -1
    else:
        valor_fake_out = 1 if setup_para_fake_out else 0
    return {
        "fake_out": fake_out, "psychic_terrain": psychic_terrain, "setup_para_fake_out": setup_para_fake_out,
        "screens": screens, "setup_para_screens": setup_para_screens,
        "clima": clima, "aproveitam": aproveitam, "prejudicados": prejudicados,
        "valores": {"clima": len(aproveitam) - len(prejudicados), "fake_out": valor_fake_out,
                    "screens": 1 if screens and setup_para_screens else 0},
    }


def tipo_de_atacante(membro: dict) -> str | None:
    """'fisico', 'especial' ou None (sem golpes de dano), pelos golpes que ele usa.

    Fake Out não conta: é um golpe de apoio. Empate: decide pelo maior status de ataque.
    """
    golpes = dados.carregar_golpes()
    fisicos, especiais = 0, 0
    for golpe_id in golpes_do_membro(membro) - {"fakeout"}:
        golpe = golpes.get(golpe_id)
        if golpe and golpe["poder"] > 0:
            fisicos += golpe["categoria"] == "Physical"
            especiais += golpe["categoria"] == "Special"
    if fisicos == especiais == 0:
        return None
    if fisicos != especiais:
        return "fisico" if fisicos > especiais else "especial"
    status = status_de(membro)
    return "fisico" if status["atk"] >= status["spa"] else "especial"


def atacantes_do_time(time: list[dict]) -> dict[str, list[str]]:
    tipos = [tipo_de_atacante(m) for m in time]
    return {"fisicos": [m["especie"] for m, t in zip(time, tipos) if t == "fisico"],
            "especiais": [m["especie"] for m, t in zip(time, tipos) if t == "especial"]}


@lru_cache
def ameacas_bulky() -> tuple[str, ...]:
    """Os do top 10 com muita Defense: seguram bem golpes físicos."""
    pokemon = dados.carregar_pokemon()
    return tuple(pokemon[a["id"]]["nome"] for a in top_do_meta() if pokemon[a["id"]]["status"]["def"] >= BULKY)


def pontos_de_analise(time: list[dict], winrates: dict[str, float] | None = None) -> dict[str, float]:
    """Os 12 pontos de análise do time (as entradas do modelo)."""
    golpes = [golpes_do_membro(m) for m in time]
    velocidades = [status_de(m) for m in time]
    breakers = sum(s["spe"] >= BREAKER_VELOCIDADE and max(s["atk"], s["spa"]) >= BREAKER_ATAQUE
                   for s in velocidades)
    usa_trick_room = any("trickroom" in g for g in golpes)
    lentos = sum(s["spe"] <= LENTO for s in velocidades)
    situacionais = situacionais_do_time(time)["valores"]
    atacantes = atacantes_do_time(time)
    numeros = {
        "cobertura_ataque": cobertura_ataque(time),
        "cobertura_defesa": cobertura_defesa(time),
        "aparecem_juntos": aparecem_juntos(time),
        "cobrem_fraquezas": cobrem_fraquezas(time),
        "winrate": winrate_do_time(time, winrates or {}),
        # Até 3 / 2: ter mais do que isso não muda muito na batalha.
        "breakers_rapidos": min(breakers, 3),
        "trick_room": lentos if usa_trick_room else 0,
        "tailwind": min(sum("tailwind" in g for g in golpes), 2),
        **situacionais,
        # Ex.: 5 físicos e 1 especial -> 2; 4 físicos e 2 especiais -> 0 (equilibrado).
        "fisicos_demais": max(0, len(atacantes["fisicos"]) - len(atacantes["especiais"]) - 2),
    }
    return {chave: float(numeros[chave]) for chave in PONTOS}


# ---------------------------------------------------------------------------
# 2. Dataset: os times das batalhas reais
# ---------------------------------------------------------------------------

def especie_conhecida(especie: str) -> str | None:
    """Id que existe no pokemon.json. Formas só de aparência viram a espécie
    base: 'vivillonpokeball' -> 'vivillon', 'mausholdfour' -> 'maushold'."""
    pokemon = dados.carregar_pokemon()
    for fim in range(len(especie), 3, -1):
        if especie[:fim] in pokemon:
            return especie[:fim]
    return None


def membro_do_replay(revelado: dict) -> dict | None:
    """Monta um Pokémon da batalha: o que apareceu no replay (golpes, item,
    habilidade) e, no que não apareceu, o mais usado nas estatísticas."""
    pokemon = dados.carregar_pokemon()
    especie = especie_conhecida(revelado["especie"])
    if especie is None:
        return None
    info = dados.carregar_uso()["pokemon"].get(especie, {})
    golpes = list(revelado["golpes"])
    for golpe in info.get("golpes", {}):
        if len(golpes) >= 4:
            break
        if golpe not in golpes:
            golpes.append(golpe)
    return {
        "especie": pokemon[especie]["nome"],
        "item": revelado["item"] or next(iter(info.get("itens", {})), ""),
        "habilidade": revelado["habilidade"] or next(iter(info.get("habilidades", {})), ""),
        "natureza": "",
        "golpes": golpes,
    }


def time_do_replay(revelados: list[dict]) -> list[dict] | None:
    membros = [membro_do_replay(r) for r in revelados]
    if any(m is None for m in membros):
        return None
    return montar_time(membros)


def montar_dataset(batalhas: list[dict]) -> dict:
    """Pontos de análise dos dois times de cada batalha + quem venceu.

    {A: pontos do time 1, B: pontos do time 2, ids_A/ids_B: Pokémon de cada
     time, y: 1 se o time 1 venceu}. O winrate fica em 50% por enquanto: ele
    depende de quais batalhas são de treino (veja preencher_winrate).
    """
    A, B, ids_A, ids_B, y = [], [], [], [], []
    for batalha in batalhas:
        time1, time2 = time_do_replay(batalha["p1"]), time_do_replay(batalha["p2"])
        if not time1 or not time2:
            continue
        A.append(list(pontos_de_analise(time1).values()))
        B.append(list(pontos_de_analise(time2).values()))
        ids_A.append([m["id"] for m in time1])
        ids_B.append([m["id"] for m in time2])
        y.append(1.0 if batalha["vencedor"] == 1 else 0.0)
    return {"A": np.array(A), "B": np.array(B), "ids_A": ids_A, "ids_B": ids_B, "y": np.array(y)}


def contar_vitorias(base: dict, batalhas: np.ndarray) -> dict[str, tuple[float, int]]:
    """{pokemon_id: (vitórias, batalhas)} contando só as batalhas indicadas."""
    contagem = {}
    for i in batalhas:
        for ids, venceu in ((base["ids_A"][i], base["y"][i]), (base["ids_B"][i], 1 - base["y"][i])):
            for pokemon_id in ids:
                vitorias, jogos = contagem.get(pokemon_id, (0.0, 0))
                contagem[pokemon_id] = (vitorias + venceu, jogos + 1)
    return contagem


def preencher_winrate(base: dict, contagem: dict, treino: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Coloca o winrate de cada time nas batalhas.

    Nas batalhas de treino, a própria batalha é tirada da conta: senão o modelo
    "cola" (o winrate já teria o resultado que ele precisa adivinhar).
    """
    coluna = list(PONTOS).index("winrate")
    A, B = base["A"].copy(), base["B"].copy()
    de_treino = set(treino.tolist())
    for i in range(len(base["y"])):
        for pontos, ids, venceu in ((A, base["ids_A"][i], base["y"][i]),
                                    (B, base["ids_B"][i], 1 - base["y"][i])):
            taxas = []
            for pokemon_id in ids:
                vitorias, jogos = contagem.get(pokemon_id, (0.0, 0))
                if i in de_treino:
                    vitorias, jogos = vitorias - venceu, jogos - 1
                taxas.append(winrate_suavizado(vitorias, jogos))
            pontos[i, coluna] = 100 * np.mean(taxas)
    return A, B


# ---------------------------------------------------------------------------
# 3. Modelo: Regressão Logística com a ordem das categorias (numpy)
# ---------------------------------------------------------------------------

def pontuar_categorias(P: np.ndarray, medias, desvios, desvios_categoria=None) -> np.ndarray:
    """Pontos (um time por linha) -> uma coluna por categoria (COLUNAS).

    Cada ponto é padronizado (quantos desvios acima da média) e a categoria é
    a média dos seus pontos, dividida pelo desvio da categoria. Assim todas as
    colunas ficam na mesma escala e os pesos podem ser comparados.
    """
    Z = (P - np.array(medias)) / np.array(desvios)
    C = np.column_stack([Z[:, grupo].mean(axis=1) for grupo in GRUPOS])
    return C if desvios_categoria is None else C / np.array(desvios_categoria)


def ajustar_escalas(P: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Médias e desvios dos pontos e das categorias (só com os times de treino)."""
    medias, desvios = P.mean(axis=0), P.std(axis=0)
    medias[[i for i, chave in enumerate(PONTOS) if chave in SEM_MEDIA]] = 0.0
    desvios[desvios == 0] = 1.0
    desvios_categoria = pontuar_categorias(P, medias, desvios).std(axis=0)
    desvios_categoria[desvios_categoria == 0] = 1.0
    return medias, desvios, desvios_categoria


def preparar(base: dict, treino: np.ndarray) -> dict:
    """Tudo o que depende das batalhas de treino: winrates, escalas e as categorias de cada time."""
    contagem = contar_vitorias(base, treino)
    A, B = preencher_winrate(base, contagem, treino)
    medias, desvios, desvios_categoria = ajustar_escalas(np.vstack([A[treino], B[treino]]))
    return {"A": A, "B": B, "contagem": contagem, "medias": medias, "desvios": desvios,
            "desvios_categoria": desvios_categoria,
            "SA": pontuar_categorias(A, medias, desvios, desvios_categoria),
            "SB": pontuar_categorias(B, medias, desvios, desvios_categoria)}


def sigmoide(z):
    """Transforma qualquer número numa chance entre 0 e 1."""
    return 1 / (1 + np.exp(-z))


def pesos_em_ordem(degraus: np.ndarray, alerta: float) -> np.ndarray:
    """Degraus (todos >= 0) -> pesos em ordem decrescente, e o peso do alerta no fim.

    O peso da última categoria é o último degrau; o de cada categoria acima é o
    da de baixo + o seu degrau. Ex.: degraus [0.1, 0, 0.2, 0.05, 0.01] ->
    pesos [0.36, 0.26, 0.26, 0.06, 0.01]. Como degrau nunca é negativo, a ordem
    nunca quebra.
    """
    return np.append(np.cumsum(degraus[::-1])[::-1], alerta)


def treinar_em_ordem(X: np.ndarray, y: np.ndarray, taxa: float = TAXA, passos: int = PASSOS,
                     regularizacao: float = REGULARIZACAO, degrau_minimo: float = DEGRAU_MINIMO) -> np.ndarray:
    """Acha os pesos com gradiente descendente, respeitando a ordem das categorias.

    X: uma coluna por categoria (na ordem de CATEGORIAS) e o alerta na última.
    chance = sigmoide(X · pesos). A cada passo, mexe um pouquinho nos degraus
    na direção que diminui o erro (log-loss) + regularização L2. Depois do
    passo, os degraus voltam para o mínimo permitido (degrau_minimo entre as
    categorias; 0 na última) e o peso do alerta não pode passar de 0.
    """
    minimos = np.full(X.shape[1] - 1, degrau_minimo)
    minimos[-1] = 0.0  # a última categoria só não pode ter peso negativo
    degraus, alerta = minimos.copy(), 0.0
    for _ in range(passos):
        pesos = pesos_em_ordem(degraus, alerta)
        erro = sigmoide(X @ pesos) - y
        gradiente = X.T @ erro / len(y) + regularizacao * pesos
        # Um degrau entra no peso da sua categoria e de todas as de cima:
        # o gradiente dele é a soma dos gradientes desses pesos.
        degraus = np.maximum(degraus - taxa * np.cumsum(gradiente[:-1]), minimos)
        alerta = min(alerta - taxa * gradiente[-1], 0.0)
    return pesos_em_ordem(degraus, alerta)


def avaliar(y_real: np.ndarray, chance: np.ndarray) -> dict:
    """Acurácia (acertou quem venceu?) e log-loss (erro das chances; menor é melhor)."""
    chance = np.clip(chance, 1e-9, 1 - 1e-9)
    log_loss = -np.mean(y_real * np.log(chance) + (1 - y_real) * np.log(1 - chance))
    return {"acuracia": round(float(np.mean((chance > 0.5) == (y_real == 1))), 3),
            "log_loss": round(float(log_loss), 3)}


def _espelhar(X: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Espelho: trocar os lados (time 2 vira time 1) inverte o resultado.
    Assim o modelo não aprende que "o time 1 ganha mais"."""
    return np.vstack([X, -X]), np.concatenate([y, 1 - y])


def validacao_cruzada(base: dict, partes: int = 5, semente: int = SEMENTE) -> dict:
    """Divide as batalhas em 5 partes; treina com 4 e testa na que sobrou, 5 vezes.
    A média das 5 acurácias é mais confiável que um teste só."""
    y = base["y"]
    ordem = np.random.default_rng(semente).permutation(len(y))
    acuracias = []
    for teste in np.array_split(ordem, partes):
        treino = np.setdiff1d(ordem, teste)
        preparo = preparar(base, treino)
        X = preparo["SA"] - preparo["SB"]
        pesos = treinar_em_ordem(*_espelhar(X[treino], y[treino]))
        acuracias.append(avaliar(y[teste], sigmoide(X[teste] @ pesos))["acuracia"])
    return {"media": round(float(np.mean(acuracias)), 3), "desvio": round(float(np.std(acuracias)), 3),
            "acuracias": acuracias}


def treinar(batalhas: list[dict], semente: int = SEMENTE, rating_minimo: int = RATING_MINIMO) -> dict:
    """Monta o dataset, separa treino/teste, treina, avalia e devolve o modelo."""
    batalhas = [b for b in batalhas if b.get("rating", 0) >= rating_minimo]
    base = montar_dataset(batalhas)
    y = base["y"]
    ordem = np.random.default_rng(semente).permutation(len(y))
    corte = int(len(y) * (1 - PARTE_DE_TESTE))
    treino, teste = ordem[:corte], ordem[corte:]
    preparo = preparar(base, treino)
    X = preparo["SA"] - preparo["SB"]  # a batalha é a diferença entre os dois times
    pesos = treinar_em_ordem(*_espelhar(X[treino], y[treino]))

    # Força de cada time real: base da nota (percentil) e dos gráficos.
    S = np.vstack([preparo["SA"], preparo["SB"]])
    P = np.vstack([preparo["A"], preparo["B"]])
    forcas = S @ pesos
    venceu = np.concatenate([y, 1 - y]) == 1
    quantis = np.linspace(0, 100, 101)
    return {
        "pontos": list(PONTOS),
        "colunas": COLUNAS,
        "medias": preparo["medias"].tolist(),
        "desvios": preparo["desvios"].tolist(),
        "desvios_categoria": preparo["desvios_categoria"].tolist(),
        "pesos": pesos.tolist(),
        "winrates": {p: round(winrate_suavizado(v, j), 4) for p, (v, j) in sorted(preparo["contagem"].items())},
        "rating_minimo": rating_minimo,
        "batalhas_treino": int(len(treino)),
        "batalhas_teste": int(len(teste)),
        "treino": avaliar(y[treino], sigmoide(X[treino] @ pesos)),
        "teste": avaliar(y[teste], sigmoide(X[teste] @ pesos)),
        "baseline": {"acuracia": 0.5, "log_loss": round(float(np.log(2)), 3)},  # chutar 50% sempre
        "validacao_cruzada": validacao_cruzada(base, semente=semente),
        # Percentis da força (e de cada categoria) entre os times reais.
        "quantis_forca": np.percentile(forcas, quantis).tolist(),
        "quantis_categoria": {cat: np.percentile(S[:, k] * pesos[k], quantis).tolist()
                              for k, cat in enumerate(CATEGORIAS)},
        # Para os gráficos de treino.
        "forca_vencedores": np.round(forcas[venceu], 3).tolist(),
        "forca_perdedores": np.round(forcas[~venceu], 3).tolist(),
        "media_vencedores": np.round(P[venceu].mean(axis=0), 3).tolist(),
        "media_perdedores": np.round(P[~venceu].mean(axis=0), 3).tolist(),
    }


def salvar(modelo: dict, caminho=config.MODELO_FILE) -> None:
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(modelo, arquivo, ensure_ascii=False, separators=(",", ":"))


@lru_cache
def carregar_modelo() -> dict | None:
    """O modelo salvo (None se ainda não foi treinado ou é de uma versão antiga)."""
    if not config.MODELO_FILE.exists():
        return None
    with open(config.MODELO_FILE, encoding="utf-8") as arquivo:
        modelo = json.load(arquivo)
    return modelo if modelo.get("pontos") == list(PONTOS) else None


# ---------------------------------------------------------------------------
# 4. Usar o modelo: nota, chance de vencer e explicação
# ---------------------------------------------------------------------------

def percentil(quantis: list[float], valor: float) -> float:
    """Que % dos times reais têm valor menor que este (0 a 100)."""
    return float(np.interp(valor, quantis, np.linspace(0, 100, len(quantis))))


def pesos_dos_pontos(modelo: dict) -> np.ndarray:
    """Peso de cada ponto: o da categoria dividido entre os pontos dela."""
    pesos = np.zeros(len(PONTOS))
    for k, grupo in enumerate(GRUPOS):
        pesos[grupo] = modelo["pesos"][k] / (len(grupo) * modelo["desvios_categoria"][k])
    return pesos


def analise_da_ia(time: list[dict], modelo: dict | None = None) -> dict | None:
    """A análise completa do time feita pelo modelo.

    {nota: 0-10, chance: % de vencer um time médio do meta, forca,
     pontos: [{chave, categoria, nome, valor, media_vencedores, peso, impacto}],
     categorias: [{nome, impacto, nota, principal}],
     situacionais: quem usa clima/Fake Out/Screens e quem se beneficia,
     alerta: {ativo, fisicos, especiais, bulky, impacto}}
    impacto = peso × (ponto padronizado): quanto aquele ponto deixou o time
    mais forte (+) ou mais fraco (-) que um time médio das batalhas.
    """
    modelo = modelo or carregar_modelo()
    if modelo is None or not time:
        return None
    valores = pontos_de_analise(time, modelo["winrates"])
    x = np.array([valores[p] for p in modelo["pontos"]])
    z = (x - np.array(modelo["medias"])) / np.array(modelo["desvios"])
    pesos = pesos_dos_pontos(modelo)
    impactos = z * pesos
    forca = float(impactos.sum())
    pontos = [
        {"chave": chave, "categoria": PONTOS[chave][0], "nome": PONTOS[chave][1],
         "valor": round(float(valor), 2), "media_vencedores": venc,
         "peso": round(float(peso), 3), "impacto": round(float(impacto), 3)}
        for chave, valor, venc, peso, impacto in zip(
            modelo["pontos"], x, modelo["media_vencedores"], pesos, impactos)
    ]
    categorias = []
    for cat in CATEGORIAS:
        impacto = sum(p["impacto"] for p in pontos if p["categoria"] == cat)
        nota = percentil(modelo["quantis_categoria"][cat], impacto) / 10
        categorias.append({"nome": cat, "impacto": round(impacto, 3), "nota": round(nota, 1),
                           "principal": cat in PRINCIPAIS})
    atacantes = atacantes_do_time(time)
    return {
        "nota": round(percentil(modelo["quantis_forca"], forca) / 10, 1),
        "forca": round(forca, 3),
        "chance": round(100 * float(sigmoide(forca)), 1),
        "pontos": pontos,
        "categorias": categorias,
        "situacionais": situacionais_do_time(time),
        "alerta": {"ativo": valores["fisicos_demais"] > 0, **atacantes, "bulky": list(ameacas_bulky()),
                   "impacto": next(p["impacto"] for p in pontos if p["categoria"] == ALERTA)},
    }


def pesos_do_modelo(modelo: dict | None = None) -> list[dict]:
    """O que o modelo aprendeu: o peso de cada categoria, na ordem de importância (e o alerta)."""
    modelo = modelo or carregar_modelo()
    return [{"categoria": c, "peso": round(p, 3)} for c, p in zip(modelo["colunas"], modelo["pesos"])]


if __name__ == "__main__":
    from src.replays import carregar_replays

    batalhas = carregar_replays()
    if not batalhas:
        raise SystemExit("Baixe as batalhas antes: python -m src.replays")
    print(f"Treinando com as batalhas de rating {RATING_MINIMO}+ (de {len(batalhas)} baixadas)...")
    modelo = treinar(batalhas)
    salvar(modelo)
    print(f"Modelo salvo em {config.MODELO_FILE}")
    print(f"Treino: {modelo['batalhas_treino']} batalhas · teste: {modelo['batalhas_teste']}")
    print(f"Teste    -> acurácia {modelo['teste']['acuracia']:.1%} · log-loss {modelo['teste']['log_loss']}")
    print(f"Baseline -> acurácia 50% · log-loss {modelo['baseline']['log_loss']} (chutar 50% sempre)")
    cruzada = modelo["validacao_cruzada"]
    print(f"Validação cruzada (5 partes) -> acurácia {cruzada['media']:.1%} ± {cruzada['desvio']:.1%}")
    print("Pesos (na ordem de importância; o alerta só tira força):")
    for p in pesos_do_modelo(modelo):
        print(f"  {p['peso']:+6.3f}  {p['categoria']}")
