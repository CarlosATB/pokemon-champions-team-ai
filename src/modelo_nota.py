"""
Nota do time com Machine Learning: a IA APRENDE a dar nota a partir do meta.

A ideia (aprendizado supervisionado):
- ENTRADAS (características): os números que a análise do time já calcula
  (src/analise.py): tipos perigosos, fraquezas, resistências, cobertura
  ofensiva, Pokémon sem ataques, funções de duplas e ameaças do meta.
- RÓTULO (o que o modelo aprende a prever): a "coesão no meta" do time,
  tirada do USO REAL (uso.json do Smogon): em média, que % dos times com um
  Pokémon do nosso time também têm cada um dos outros (os "parceiros").
  Times que os jogadores de verdade montam juntos têm coesão alta; times
  aleatórios, baixa.
- MODELO: Regressão Linear com regularização (Ridge), feita só com numpy.
  Cada característica ganha um PESO; nota = soma dos pesos × características.
  Por ser linear, dá para explicar a nota: quanto cada característica somou
  ou tirou.

Para treinar (gera data/processed/modelo_nota.json):
    python -m src.modelo_nota
"""

import json
import random
from functools import lru_cache

import numpy as np

from src import config, dados
from src.analise import analisar, tipos_perigosos
from src.funcoes_duplas import FUNCOES
from src.leitor import montar_time
from src.opcoes import forma_normal, pedra_da_mega
from src.recomendacao import chave_de_uso
from src.tipos import TIPOS

POOL_DO_META = 120   # times de treino usam os 120 Pokémon mais usados
TIMES_POR_GRUPO = 400  # quantos times de cada tipo (meta, perturbado, aleatório)
ALPHA = 1.0          # força da regularização do Ridge (pesos menores = menos exagero)
PARTE_DE_TESTE = 0.2  # 20% dos times ficam de fora do treino, para avaliar
SEMENTE = 42         # mesma semente = mesmo dataset e mesmo modelo

# Nome bonito de cada característica (na ordem em que entram no modelo).
CARACTERISTICAS = {
    "tipos_perigosos": "Tipos perigosos (2+ fracos, poucos seguram)",
    "fraquezas_por_pokemon": "Fraquezas por Pokémon",
    "fraquezas_4x": "Fraquezas 4x",
    "resistencias_por_pokemon": "Resistências/imunidades por Pokémon",
    "tipos_sem_resposta": "Tipos que ninguém do time segura",
    "cobertura_2x": "Tipos acertados com dano dobrado",
    "sem_ataques": "Parte do time sem golpes de ataque",
    **{f"funcao_{chave}": f"Função: {funcao['nome']}" for chave, funcao in FUNCOES.items()},
    "ameacas": "Ameaças do meta",
    "pior_ameaca": "Nota da pior ameaça do meta",
}


# ---------------------------------------------------------------------------
# 1. Características: a análise do time virando números
# ---------------------------------------------------------------------------

def caracteristicas(time: list[dict], analise: dict | None = None) -> dict[str, float]:
    """Transforma o resultado de analisar() em números (as entradas do modelo).

    Quando faz sentido, divide pelo tamanho do time, para um time de 4 poder
    ser comparado com um de 6.
    """
    analise = analise or analisar(time)
    tamanho = max(len(time), 1)
    defesa = analise["defesa"]
    numeros = {
        "tipos_perigosos": len(tipos_perigosos(analise)),
        "fraquezas_por_pokemon": sum(len(l["fracos"]) for l in defesa) / tamanho,
        "fraquezas_4x": sum(x >= 4 for l in defesa for x in l["dano"].values()),
        "resistencias_por_pokemon": sum(len(l["resistem"]) + len(l["imunes"]) for l in defesa) / tamanho,
        "tipos_sem_resposta": sum(bool(l["fracos"]) and not (l["resistem"] or l["imunes"])
                                  for l in defesa),
        "cobertura_2x": sum(c["melhor"] >= 2 for c in analise["cobertura"]),
        "sem_ataques": len(analise["sem_ataques"]) / tamanho,
        "ameacas": len(analise["ameacas"]),
        "pior_ameaca": max((a["nota"] for a in analise["ameacas"]), default=0),
    }
    for chave in FUNCOES:
        # Até 3: ter a função em 4 Pokémon não é melhor do que em 3.
        numeros[f"funcao_{chave}"] = min(len(analise["funcoes"][chave]), 3)
    return {chave: float(numeros[chave]) for chave in CARACTERISTICAS}


# ---------------------------------------------------------------------------
# 2. Rótulo: a coesão do time no meta (uso real)
# ---------------------------------------------------------------------------

def coesao_no_meta(time: list[dict]) -> float:
    """Média, entre todos os pares (A, B) do time, da % de times com A que também têm B.

    Usa os "parceiros" do uso.json (co-ocorrência). Ex.: 36,8 de Rillaboom ->
    Incineroar quer dizer que 36,8% dos times com Rillaboom têm Incineroar.
    Pokémon sem estatísticas contam como 0 (ninguém usa com ele).
    """
    uso = dados.carregar_uso()["pokemon"]
    chaves = [chave_de_uso(m) for m in time]
    confiancas = []
    for i, a in enumerate(chaves):
        for j, b in enumerate(chaves):
            if i != j:
                confiancas.append(uso[a]["parceiros"].get(b, 0.0) if a and b else 0.0)
    return sum(confiancas) / len(confiancas) if confiancas else 0.0


# ---------------------------------------------------------------------------
# 3. Dataset: times do meta, times "estragados" e times aleatórios
# ---------------------------------------------------------------------------

def pool_do_meta(quantos: int = POOL_DO_META) -> list[str]:
    """Os Pokémon mais usados que podem entrar num time (ids das estatísticas)."""
    pokemon = dados.carregar_pokemon()
    return [p for p in list(dados.carregar_uso()["pokemon"])[:quantos]
            if p in pokemon and not pokemon[p]["forma_de_batalha"]]


def membro_do_meta(pokemon_id: str) -> dict:
    """Monta um Pokémon como os jogadores costumam usar: habilidade, item e os
    4 golpes mais usados. Mega -> a forma normal segurando a Pedra Mega."""
    info = dados.carregar_uso()["pokemon"][pokemon_id]
    pedra = pedra_da_mega(pokemon_id)
    especie = forma_normal(pokemon_id) if pedra else pokemon_id
    return {
        "especie": dados.carregar_pokemon()[especie]["nome"],
        "item": pedra or next(iter(info["itens"]), ""),
        "habilidade": "" if pedra else next(iter(info["habilidades"]), ""),
        "natureza": "",
        "golpes": list(info["golpes"])[:4],
    }


def _pode_entrar(candidato: str, time_ids: list[str]) -> bool:
    """Sem repetir espécie e no máximo uma Mega (regras do formato)."""
    pokemon = dados.carregar_pokemon()
    especies = {pokemon[p]["especie_base"] for p in time_ids}
    tem_mega = any(pokemon[p]["mega"] for p in time_ids)
    return (pokemon[candidato]["especie_base"] not in especies
            and not (tem_mega and pokemon[candidato]["mega"]))


def time_do_meta(sorteio: random.Random, pool: list[str]) -> list[str]:
    """Time "de verdade": começa por um Pokémon popular e vai chamando os
    parceiros com que ele mais aparece (sorteio com peso = co-ocorrência)."""
    uso = dados.carregar_uso()["pokemon"]
    time_ids = [sorteio.choices(pool, weights=[uso[p]["uso"] for p in pool])[0]]
    while len(time_ids) < config.TEAM_SIZE:
        candidatos = [p for p in pool if _pode_entrar(p, time_ids)]
        pesos = [sum(uso[t]["parceiros"].get(c, 0.0) for t in time_ids) ** 2 + 0.01
                 for c in candidatos]
        time_ids.append(sorteio.choices(candidatos, weights=pesos)[0])
    return time_ids


def time_aleatorio(sorteio: random.Random, pool: list[str]) -> list[str]:
    """Time sem critério nenhum (só respeitando as regras)."""
    time_ids = []
    while len(time_ids) < config.TEAM_SIZE:
        candidato = sorteio.choice(pool)
        if _pode_entrar(candidato, time_ids):
            time_ids.append(candidato)
    return time_ids


def time_perturbado(sorteio: random.Random, pool: list[str]) -> list[str]:
    """Time do meta com 1 a 3 Pokémon trocados por outros aleatórios."""
    time_ids = time_do_meta(sorteio, pool)
    for _ in range(sorteio.randint(1, 3)):
        time_ids.pop(sorteio.randrange(len(time_ids)))
        candidato = sorteio.choice(pool)
        while not _pode_entrar(candidato, time_ids):
            candidato = sorteio.choice(pool)
        time_ids.append(candidato)
    return time_ids


def gerar_dataset(times_por_grupo: int = TIMES_POR_GRUPO, semente: int = SEMENTE) -> dict:
    """{X: características, y: coesão, grupos: "meta"/"perturbado"/"aleatorio"}"""
    sorteio = random.Random(semente)
    pool = pool_do_meta()
    linhas, rotulos, grupos = [], [], []
    for grupo, gerar in [("meta", time_do_meta), ("perturbado", time_perturbado),
                         ("aleatorio", time_aleatorio)]:
        for _ in range(times_por_grupo):
            time = montar_time([membro_do_meta(p) for p in gerar(sorteio, pool)])
            linhas.append(list(caracteristicas(time).values()))
            rotulos.append(coesao_no_meta(time))
            grupos.append(grupo)
    return {"X": np.array(linhas), "y": np.array(rotulos), "grupos": np.array(grupos)}


# ---------------------------------------------------------------------------
# 4. Modelo: Regressão Ridge (feita à mão com numpy)
# ---------------------------------------------------------------------------

def treinar_ridge(X: np.ndarray, y: np.ndarray, alpha: float = ALPHA) -> dict:
    """Acha os pesos que minimizam  erro² + alpha × pesos².

    1. Padroniza cada característica (média 0, desvio 1), para os pesos
       serem comparáveis entre si.
    2. Fórmula fechada do Ridge:  pesos = (XᵀX + alpha·I)⁻¹ Xᵀ (y - média de y)
    """
    medias = X.mean(axis=0)
    desvios = X.std(axis=0)
    desvios[desvios == 0] = 1.0  # característica que nunca muda não atrapalha
    Xp = (X - medias) / desvios
    pesos = np.linalg.solve(Xp.T @ Xp + alpha * np.eye(X.shape[1]), Xp.T @ (y - y.mean()))
    return {"medias": medias, "desvios": desvios, "pesos": pesos, "intercepto": float(y.mean())}


def prever(modelo: dict, X: np.ndarray) -> np.ndarray:
    Xp = (np.asarray(X) - np.asarray(modelo["medias"])) / np.asarray(modelo["desvios"])
    return Xp @ np.asarray(modelo["pesos"]) + modelo["intercepto"]


def avaliar(y_real: np.ndarray, y_previsto: np.ndarray) -> dict:
    """R² (1 = acerta tudo, 0 = igual a chutar a média) e erro médio absoluto."""
    erro = y_real - y_previsto
    r2 = 1 - (erro ** 2).sum() / ((y_real - y_real.mean()) ** 2).sum()
    return {"r2": round(float(r2), 3), "mae": round(float(np.abs(erro).mean()), 3)}


def treinar(times_por_grupo: int = TIMES_POR_GRUPO, semente: int = SEMENTE) -> dict:
    """Gera o dataset, separa treino/teste, treina, avalia e devolve o modelo."""
    base = gerar_dataset(times_por_grupo, semente)
    X, y, grupos = base["X"], base["y"], base["grupos"]
    ordem = np.random.default_rng(semente).permutation(len(y))
    corte = int(len(y) * (1 - PARTE_DE_TESTE))
    treino, teste = ordem[:corte], ordem[corte:]

    modelo = treinar_ridge(X[treino], y[treino])
    previsto = prever(modelo, X[teste])
    chute_da_media = np.full(len(teste), y[treino].mean())
    # A nota de 0 a 10 vai do 5º ao 95º percentil da coesão vista no treino.
    minimo, maximo = np.percentile(y[treino], [5, 95])
    modelo.update({
        "caracteristicas": list(CARACTERISTICAS),
        "nota_min": float(minimo),
        "nota_max": float(maximo),
        "alpha": ALPHA,
        "times_treino": int(len(treino)),
        "times_teste": int(len(teste)),
        "teste": avaliar(y[teste], previsto),
        "baseline_media": avaliar(y[teste], chute_da_media),
        "coesao_media_por_grupo": {g: round(float(y[grupos == g].mean()), 2)
                                   for g in ("meta", "perturbado", "aleatorio")},
    })
    return modelo


def salvar(modelo: dict, caminho=config.MODELO_FILE) -> None:
    pronto = {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in modelo.items()}
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(pronto, arquivo, ensure_ascii=False, indent=1)


@lru_cache
def carregar_modelo() -> dict | None:
    """O modelo salvo (None se ainda não foi treinado)."""
    if not config.MODELO_FILE.exists():
        return None
    with open(config.MODELO_FILE, encoding="utf-8") as arquivo:
        return json.load(arquivo)


# ---------------------------------------------------------------------------
# 5. Usar o modelo: nota de 0 a 10 com explicação
# ---------------------------------------------------------------------------

def _para_nota(modelo: dict, coesao: float) -> float:
    escala = (coesao - modelo["nota_min"]) / (modelo["nota_max"] - modelo["nota_min"])
    return round(float(np.clip(10 * escala, 0, 10)), 1)


def nota_do_time(time: list[dict], analise: dict | None = None, modelo: dict | None = None) -> dict | None:
    """A nota que o modelo dá ao time, e o porquê.

    {nota: 0-10, coesao_prevista, coesao_real,
     contribuicoes: [{chave, nome, valor, pontos}]}  (maior impacto primeiro)
    pontos = quanto aquela característica subiu (+) ou desceu (-) a nota,
    comparando com um time médio do treino.
    """
    modelo = modelo or carregar_modelo()
    if modelo is None or not time:
        return None
    numeros = caracteristicas(time, analise)
    x = np.array([numeros[c] for c in modelo["caracteristicas"]])
    coesao = float(prever(modelo, x[None, :])[0])
    por_ponto = 10 / (modelo["nota_max"] - modelo["nota_min"])
    padronizado = (x - np.array(modelo["medias"])) / np.array(modelo["desvios"])
    contribuicoes = [
        {"chave": chave, "nome": CARACTERISTICAS[chave], "valor": round(float(valor), 2),
         "pontos": round(float(peso * z * por_ponto), 2)}
        for chave, valor, peso, z in zip(modelo["caracteristicas"], x, modelo["pesos"], padronizado)
    ]
    contribuicoes.sort(key=lambda c: abs(c["pontos"]), reverse=True)
    return {"nota": _para_nota(modelo, coesao), "coesao_prevista": round(coesao, 2),
            "coesao_real": round(coesao_no_meta(time), 2), "contribuicoes": contribuicoes}


def pesos_do_modelo(modelo: dict | None = None) -> list[dict]:
    """Importância de cada característica: o peso (em pontos de nota por desvio padrão)."""
    modelo = modelo or carregar_modelo()
    por_ponto = 10 / (modelo["nota_max"] - modelo["nota_min"])
    pesos = [{"nome": CARACTERISTICAS[c], "peso": round(p * por_ponto, 2)}
             for c, p in zip(modelo["caracteristicas"], modelo["pesos"])]
    return sorted(pesos, key=lambda p: abs(p["peso"]), reverse=True)


if __name__ == "__main__":
    print("Gerando times e treinando o modelo...")
    modelo = treinar()
    salvar(modelo)
    print(f"Modelo salvo em {config.MODELO_FILE}")
    print(f"Treino: {modelo['times_treino']} times · teste: {modelo['times_teste']} times")
    print(f"Teste    -> R² {modelo['teste']['r2']} · erro médio {modelo['teste']['mae']}")
    print(f"Baseline -> R² {modelo['baseline_media']['r2']} · erro médio "
          f"{modelo['baseline_media']['mae']} (chutar sempre a média)")
    print(f"Coesão média por grupo: {modelo['coesao_media_por_grupo']}")
    print("Pesos (pontos de nota):")
    for p in pesos_do_modelo(modelo):
        print(f"  {p['peso']:+6.2f}  {p['nome']}")
