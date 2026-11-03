"""
Baixa batalhas reais (replays) do Pokémon Showdown e guarda os times e quem venceu.

É daqui que vem o "gabarito" do modelo de IA (src/modelo_nota.py): para cada
batalha sabemos os dois times e qual deles ganhou. O modelo aprende quais
pontos da análise (cobertura, velocidade, sinergia...) aparecem mais nos
times que VENCEM.

Rodar com internet (demora alguns minutos):

    python -m src.replays           # baixa ~3000 batalhas
    python -m src.replays 500       # baixa só 500 (teste rápido)

Salva em data/processed/replays.json. Se o arquivo já existir, só baixa as
batalhas novas (as que já estão lá são mantidas).
"""

import json
import sys
from concurrent.futures import ThreadPoolExecutor

import requests

from src import config
from src.nomes import to_id

TIMEOUT = 30          # segundos
QUANTAS_BATALHAS = 3000
DOWNLOADS_JUNTOS = 6  # baixa alguns replays ao mesmo tempo (sem exagerar com o site)


# ---------------------------------------------------------------------------
# 1. Ler o log de uma batalha
# ---------------------------------------------------------------------------

def _especie(detalhes: str) -> str:
    """'Basculegion-F, L50, M' -> 'basculegionf' (id do Pokémon)."""
    return to_id(detalhes.split(",")[0].replace("-*", ""))


def _lado(posicao: str) -> str:
    """'p1a: Apelido' -> 'p1'."""
    return posicao[:2]


def _apelido(posicao: str) -> str:
    """'p1a: Apelido' ou 'p1b: Apelido' -> 'p1: Apelido' (o mesmo Pokémon em qualquer lugar)."""
    return _lado(posicao) + ":" + posicao.split(":", 1)[-1]


def ler_log(log: str) -> dict | None:
    """Lê o texto do log do Showdown e devolve os dois times e o vencedor.

    Linhas usadas (o resto é ignorado):
        |player|p1|Nome|...          -> nome de cada jogador
        |poke|p1|Espécie, L50, M|    -> os 6 da prévia do time
        |switch|p1a: Apelido|Espécie, L50|...  -> liga apelido à espécie
        |move|p1a: Apelido|Golpe|... -> golpe que o Pokémon usou
        |-mega|p1a: Apelido|Espécie|Pedra  -> Mega Evolução (item = pedra)
        |-enditem|p1a: Apelido|Item  -> item revelado (consumido/derrubado)
        |-ability|p1a: Apelido|Habilidade -> habilidade revelada
        |win|Nome                    -> quem venceu
    Devolve None se a batalha não terminou com vencedor (empate, log quebrado).
    """
    jogadores, times, apelidos = {}, {"p1": {}, "p2": {}}, {}
    vencedor = None
    for linha in log.splitlines():
        partes = linha.split("|")
        if len(partes) < 3:
            continue
        tipo = partes[1]
        if tipo == "player" and len(partes) > 3 and partes[3]:
            jogadores[partes[2]] = partes[3]
        elif tipo == "poke" and partes[2] in times:
            especie = _especie(partes[3])
            times[partes[2]][especie] = {"especie": especie, "golpes": [], "item": "", "habilidade": ""}
        elif tipo in ("switch", "drag") and len(partes) > 3:
            lado, especie = _lado(partes[2]), _especie(partes[3])
            time = times.get(lado, {})
            # A prévia esconde algumas formas (ex.: "Urshifu-*"): troca pela forma real.
            if especie not in time:
                parecida = next((e for e in time if especie.startswith(e)), None)
                if parecida:
                    time = times[lado] = {(especie if e == parecida else e): m for e, m in time.items()}
                    time[especie]["especie"] = especie
            if especie in time:
                apelidos[_apelido(partes[2])] = especie
        elif tipo in ("move", "-mega", "-enditem", "-ability") and len(partes) > 3:
            if any("[from]" in p for p in partes[4:5]) and tipo != "-enditem":
                continue  # golpe/habilidade copiado de outro (ex.: Dancer, Trace)
            membro = times.get(_lado(partes[2]), {}).get(apelidos.get(_apelido(partes[2])))
            if membro is None:
                continue
            if tipo == "move":
                golpe = to_id(partes[3])
                if golpe != "struggle" and golpe not in membro["golpes"] and len(membro["golpes"]) < 4:
                    membro["golpes"].append(golpe)
            elif tipo == "-mega" and len(partes) > 4:
                membro["item"] = to_id(partes[4])
            elif tipo == "-enditem" and not membro["item"]:
                membro["item"] = to_id(partes[3])
            elif tipo == "-ability" and not membro["habilidade"]:
                membro["habilidade"] = to_id(partes[3])
        elif tipo == "win":
            vencedor = partes[2]
    if vencedor not in jogadores.values() or not all(len(t) >= 4 for t in times.values()):
        return None
    return {
        "vencedor": 1 if jogadores.get("p1") == vencedor else 2,
        "p1": list(times["p1"].values()),
        "p2": list(times["p2"].values()),
    }


# ---------------------------------------------------------------------------
# 2. Baixar do site
# ---------------------------------------------------------------------------

def buscar_ids(quantas: int, formato: str = config.FORMAT_ID) -> list[dict]:
    """Lista os replays mais recentes do formato (página por página, 51 por vez)."""
    encontrados, antes = [], None
    while len(encontrados) < quantas:
        url = f"{config.REPLAYS_BASE}/search.json?format={formato}"
        if antes:
            url += f"&before={antes}"
        pagina = requests.get(url, timeout=TIMEOUT).json()
        if not pagina:
            break
        encontrados += [r for r in pagina if not r.get("private")]
        antes = pagina[-1]["uploadtime"]
        if len(pagina) < 51:  # última página
            break
    return encontrados[:quantas]


def baixar_batalha(resumo: dict) -> dict | None:
    """Baixa o log de um replay e lê os times. None se der erro."""
    try:
        resposta = requests.get(f"{config.REPLAYS_BASE}/{resumo['id']}.json", timeout=TIMEOUT)
        resposta.raise_for_status()
        batalha = ler_log(resposta.json().get("log", ""))
    except (requests.RequestException, ValueError):
        return None
    if batalha:
        batalha = {"id": resumo["id"], "rating": resumo.get("rating") or 0, **batalha}
    return batalha


def carregar_replays(caminho=config.REPLAYS_FILE) -> list[dict]:
    if not caminho.exists():
        return []
    with open(caminho, encoding="utf-8") as arquivo:
        return json.load(arquivo)["batalhas"]


def baixar(quantas: int = QUANTAS_BATALHAS, caminho=config.REPLAYS_FILE) -> list[dict]:
    batalhas = carregar_replays(caminho)
    ja_tem = {b["id"] for b in batalhas}
    print(f"Procurando {quantas} replays de {config.FORMAT_ID}...")
    novos = [r for r in buscar_ids(quantas) if r["id"] not in ja_tem]
    print(f"  {len(novos)} replays novos para baixar")
    with ThreadPoolExecutor(DOWNLOADS_JUNTOS) as grupo:
        for i, batalha in enumerate(grupo.map(baixar_batalha, novos), 1):
            if batalha:
                batalhas.append(batalha)
            if i % 250 == 0:
                print(f"  {i}/{len(novos)}")
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump({"formato": config.FORMAT_ID, "batalhas": batalhas}, arquivo,
                  ensure_ascii=False, separators=(",", ":"))
    print(f"  salvo: {caminho.name} ({len(batalhas)} batalhas)")
    return batalhas


if __name__ == "__main__":
    baixar(int(sys.argv[1]) if len(sys.argv) > 1 else QUANTAS_BATALHAS)
