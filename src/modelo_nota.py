"""
Análise do time com Machine Learning: a IA APRENDE com batalhas reais o que faz um time VENCER.

A ideia (aprendizado supervisionado):
- DADOS: milhares de batalhas reais do Pokémon Showdown (src/replays.py).
  Em cada uma temos os dois times e quem ganhou.
- ENTRADAS (pontos de análise): para cada time calculamos 11 números,
  agrupados em 5 categorias:
    Cobertura contra os 10 mais usados -> ataque e defesa
    Controle de velocidade             -> breakers rápidos, Trick Room, Tailwind
    Sinergia                           -> aparecem juntos, cobrem fraquezas um do outro
    Fake Out, Screens e Clima          -> (a favor e contra)
- RÓTULO: o time 1 venceu? (1 = sim, 0 = não)
- MODELO: Regressão Logística feita só com numpy. Cada ponto ganha um PESO.
  "Força" do time = soma de peso × ponto. Na batalha, a chance do time 1
  vencer = sigmoide(força do time 1 - força do time 2).
  Peso positivo = ter mais daquilo ajuda a vencer; negativo = atrapalha.

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

# Os pontos de análise: chave -> (categoria, nome bonito).
CATEGORIAS = ["Cobertura (top 10)", "Controle de velocidade", "Sinergia", "Fake Out", "Screens", "Clima"]
PONTOS = {
    "cobertura_ataque": ("Cobertura (top 10)", "Ataque: top 10 que o time acerta com dano dobrado"),
    "cobertura_defesa": ("Cobertura (top 10)", "Defesa: ataques do top 10 que alguém do time resiste"),
    "breakers_rapidos": ("Controle de velocidade", "Breakers rápidos (rápidos e fortes)"),
    "trick_room": ("Controle de velocidade", "Trick Room (lentos com quem usa Trick Room)"),
    "tailwind": ("Controle de velocidade", "Tailwind (quem usa)"),
    "aparecem_juntos": ("Sinergia", "Aparecem juntos no meta"),
    "cobrem_fraquezas": ("Sinergia", "Cobrem as fraquezas um do outro"),
    "fake_out": ("Fake Out", "Fake Out (quem usa)"),
    "screens": ("Screens", "Screens: Reflect, Light Screen, Aurora Veil"),
    "clima_a_favor": ("Clima", "Clima a favor (quem aproveita o clima do time)"),
    "clima_contra": ("Clima", "Clima contra (quem é prejudicado pelo clima do time)"),
}

BREAKER_VELOCIDADE = 100  # base de Speed a partir da qual o Pokémon é "rápido"
BREAKER_ATAQUE = 110      # base de Attack ou Sp. Atk a partir da qual ele é "forte"
LENTO = 60                # base de Speed até onde o Pokémon gosta do Trick Room
SCREENS = {"reflect", "lightscreen", "auroraveil"}

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


def clima_do_time(time: list[dict]) -> str | None:
    """Qual clima o time coloca (pela habilidade ou pelo golpe), ou None."""
    for membro in time:
        for nome, clima in CLIMAS.items():
            if habilidade_de(membro) in clima["habilidades"] or clima["golpe"] in golpes_do_membro(membro):
                return nome
    return None


def efeito_do_clima(time: list[dict]) -> tuple[int, int]:
    """(quantos aproveitam, quantos são prejudicados) pelo clima que o próprio time coloca."""
    nome = clima_do_time(time)
    if nome is None:
        return 0, 0
    clima = CLIMAS[nome]
    a_favor, contra = 0, 0
    for membro in time:
        habilidade, tipos, ataques = habilidade_de(membro), tipos_de(membro), ataques_do_membro(membro)
        if (habilidade in clima["aproveitam"] or clima.get("tipo_forte") in ataques
                or clima.get("tipo_que_ganha") in tipos):
            a_favor += 1
        elif "tipo_fraco" in clima and clima["tipo_fraco"] in ataques:
            contra += 1  # ataque enfraquecido (Fire na chuva, Water no sol)
        elif "tipos_imunes" in clima and not (set(tipos) & clima["tipos_imunes"]) \
                and habilidade not in IMUNES_A_AREIA:
            contra += 1  # toma dano da areia todo turno
    return a_favor, contra


def pontos_de_analise(time: list[dict]) -> dict[str, float]:
    """Os 11 pontos de análise do time (as entradas do modelo)."""
    golpes = [golpes_do_membro(m) for m in time]
    velocidades = [status_de(m) for m in time]
    breakers = sum(s["spe"] >= BREAKER_VELOCIDADE and max(s["atk"], s["spa"]) >= BREAKER_ATAQUE
                   for s in velocidades)
    usa_trick_room = any("trickroom" in g for g in golpes)
    lentos = sum(s["spe"] <= LENTO for s in velocidades)
    a_favor, contra = efeito_do_clima(time)
    numeros = {
        "cobertura_ataque": cobertura_ataque(time),
        "cobertura_defesa": cobertura_defesa(time),
        # Até 3 / 2: ter mais do que isso não muda muito na batalha.
        "breakers_rapidos": min(breakers, 3),
        "trick_room": lentos if usa_trick_room else 0,
        "tailwind": min(sum("tailwind" in g for g in golpes), 2),
        "aparecem_juntos": aparecem_juntos(time),
        "cobrem_fraquezas": cobrem_fraquezas(time),
        "fake_out": min(sum("fakeout" in g for g in golpes), 2),
        "screens": min(sum(bool(g & SCREENS) for g in golpes), 2),
        "clima_a_favor": a_favor,
        "clima_contra": contra,
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

    {A: pontos do time 1, B: pontos do time 2, y: 1 se o time 1 venceu}
    """
    A, B, y = [], [], []
    for batalha in batalhas:
        time1, time2 = time_do_replay(batalha["p1"]), time_do_replay(batalha["p2"])
        if not time1 or not time2:
            continue
        A.append(list(pontos_de_analise(time1).values()))
        B.append(list(pontos_de_analise(time2).values()))
        y.append(1.0 if batalha["vencedor"] == 1 else 0.0)
    return {"A": np.array(A), "B": np.array(B), "y": np.array(y)}


# ---------------------------------------------------------------------------
# 3. Modelo: Regressão Logística (feita à mão com numpy)
# ---------------------------------------------------------------------------

def sigmoide(z):
    """Transforma qualquer número numa chance entre 0 e 1."""
    return 1 / (1 + np.exp(-z))


def treinar_logistica(X: np.ndarray, y: np.ndarray, taxa: float = TAXA,
                      passos: int = PASSOS, regularizacao: float = REGULARIZACAO) -> np.ndarray:
    """Acha os pesos com gradiente descendente.

    chance = sigmoide(X · pesos). A cada passo, mexe um pouquinho nos pesos
    na direção que diminui o erro (log-loss) + regularização L2.
    """
    pesos = np.zeros(X.shape[1])
    for _ in range(passos):
        erro = sigmoide(X @ pesos) - y
        gradiente = X.T @ erro / len(y) + regularizacao * pesos
        pesos -= taxa * gradiente
    return pesos


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


def validacao_cruzada(X: np.ndarray, y: np.ndarray, partes: int = 5, semente: int = SEMENTE) -> dict:
    """Divide as batalhas em 5 partes; treina com 4 e testa na que sobrou, 5 vezes.
    A média das 5 acurácias é mais confiável que um teste só."""
    ordem = np.random.default_rng(semente).permutation(len(y))
    acuracias = []
    for teste in np.array_split(ordem, partes):
        treino = np.setdiff1d(ordem, teste)
        pesos = treinar_logistica(*_espelhar(X[treino], y[treino]))
        acuracias.append(avaliar(y[teste], sigmoide(X[teste] @ pesos))["acuracia"])
    return {"media": round(float(np.mean(acuracias)), 3), "desvio": round(float(np.std(acuracias)), 3),
            "acuracias": acuracias}


def treinar(batalhas: list[dict], semente: int = SEMENTE, rating_minimo: int = RATING_MINIMO) -> dict:
    """Monta o dataset, separa treino/teste, treina, avalia e devolve o modelo."""
    batalhas = [b for b in batalhas if b.get("rating", 0) >= rating_minimo]
    base = montar_dataset(batalhas)
    A, B, y = base["A"], base["B"], base["y"]
    # Padroniza cada ponto (média 0, desvio 1) com todos os times, para os
    # pesos serem comparáveis entre si.
    todos = np.vstack([A, B])
    medias, desvios = todos.mean(axis=0), todos.std(axis=0)
    desvios[desvios == 0] = 1.0
    zA, zB = (A - medias) / desvios, (B - medias) / desvios
    X = zA - zB  # a batalha é a diferença entre os dois times

    ordem = np.random.default_rng(semente).permutation(len(y))
    corte = int(len(y) * (1 - PARTE_DE_TESTE))
    treino, teste = ordem[:corte], ordem[corte:]
    pesos = treinar_logistica(*_espelhar(X[treino], y[treino]))

    # Força de cada time real: base da nota (percentil) e dos gráficos.
    forca_A, forca_B = zA @ pesos, zB @ pesos
    forcas = np.concatenate([forca_A, forca_B])
    venceu = np.concatenate([y, 1 - y]) == 1
    pontos_categoria = {cat: np.concatenate([zA, zB])[:, _indices(cat)] @ pesos[_indices(cat)]
                        for cat in CATEGORIAS}
    quantis = np.linspace(0, 100, 101)
    return {
        "pontos": list(PONTOS),
        "medias": medias.tolist(),
        "desvios": desvios.tolist(),
        "pesos": pesos.tolist(),
        "rating_minimo": rating_minimo,
        "batalhas_treino": int(len(treino)),
        "batalhas_teste": int(len(teste)),
        "treino": avaliar(y[treino], sigmoide(X[treino] @ pesos)),
        "teste": avaliar(y[teste], sigmoide(X[teste] @ pesos)),
        "baseline": {"acuracia": 0.5, "log_loss": round(float(np.log(2)), 3)},  # chutar 50% sempre
        "validacao_cruzada": validacao_cruzada(X, y, semente=semente),
        # Percentis da força (e de cada categoria) entre os times reais.
        "quantis_forca": np.percentile(forcas, quantis).tolist(),
        "quantis_categoria": {cat: np.percentile(v, quantis).tolist() for cat, v in pontos_categoria.items()},
        # Para os gráficos de treino.
        "forca_vencedores": np.round(forcas[venceu], 3).tolist(),
        "forca_perdedores": np.round(forcas[~venceu], 3).tolist(),
        "media_vencedores": np.round(np.vstack([A, B])[venceu].mean(axis=0), 3).tolist(),
        "media_perdedores": np.round(np.vstack([A, B])[~venceu].mean(axis=0), 3).tolist(),
    }


def _indices(categoria: str) -> list[int]:
    return [i for i, (cat, _) in enumerate(PONTOS.values()) if cat == categoria]


def salvar(modelo: dict, caminho=config.MODELO_FILE) -> None:
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(modelo, arquivo, ensure_ascii=False, separators=(",", ":"))


@lru_cache
def carregar_modelo() -> dict | None:
    """O modelo salvo (None se ainda não foi treinado)."""
    if not config.MODELO_FILE.exists():
        return None
    with open(config.MODELO_FILE, encoding="utf-8") as arquivo:
        return json.load(arquivo)


# ---------------------------------------------------------------------------
# 4. Usar o modelo: nota, chance de vencer e explicação
# ---------------------------------------------------------------------------

def percentil(quantis: list[float], valor: float) -> float:
    """Que % dos times reais têm valor menor que este (0 a 100)."""
    return float(np.interp(valor, quantis, np.linspace(0, 100, len(quantis))))


def analise_da_ia(time: list[dict], modelo: dict | None = None) -> dict | None:
    """A análise completa do time feita pelo modelo.

    {nota: 0-10, chance: % de vencer um time médio do meta,
     pontos: [{chave, categoria, nome, valor, media_vencedores, peso, impacto}],
     categorias: [{nome, impacto, nota}]}
    impacto = peso × (ponto padronizado): quanto aquele ponto deixou o time
    mais forte (+) ou mais fraco (-) que um time médio das batalhas.
    """
    modelo = modelo or carregar_modelo()
    if modelo is None or not time:
        return None
    valores = pontos_de_analise(time)
    x = np.array([valores[p] for p in modelo["pontos"]])
    z = (x - np.array(modelo["medias"])) / np.array(modelo["desvios"])
    impactos = z * np.array(modelo["pesos"])
    forca = float(impactos.sum())
    pontos = [
        {"chave": chave, "categoria": PONTOS[chave][0], "nome": PONTOS[chave][1],
         "valor": round(float(valor), 2), "media_vencedores": venc,
         "peso": round(float(peso), 3), "impacto": round(float(impacto), 3)}
        for chave, valor, venc, peso, impacto in zip(
            modelo["pontos"], x, modelo["media_vencedores"], modelo["pesos"], impactos)
    ]
    categorias = []
    for cat in CATEGORIAS:
        impacto = sum(p["impacto"] for p in pontos if p["categoria"] == cat)
        nota = percentil(modelo["quantis_categoria"][cat], impacto) / 10
        categorias.append({"nome": cat, "impacto": round(impacto, 3), "nota": round(nota, 1)})
    return {
        "nota": round(percentil(modelo["quantis_forca"], forca) / 10, 1),
        "forca": round(forca, 3),
        "chance": round(100 * float(sigmoide(forca)), 1),
        "pontos": pontos,
        "categorias": categorias,
    }


def pesos_do_modelo(modelo: dict | None = None) -> list[dict]:
    """O que o modelo aprendeu: o peso de cada ponto (maior impacto primeiro)."""
    modelo = modelo or carregar_modelo()
    pesos = [{"chave": c, "categoria": PONTOS[c][0], "nome": PONTOS[c][1], "peso": round(p, 3)}
             for c, p in zip(modelo["pontos"], modelo["pesos"])]
    return sorted(pesos, key=lambda p: abs(p["peso"]), reverse=True)


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
    print("Pesos (o que ajuda a vencer):")
    for p in pesos_do_modelo(modelo):
        print(f"  {p['peso']:+6.3f}  {p['nome']}")
