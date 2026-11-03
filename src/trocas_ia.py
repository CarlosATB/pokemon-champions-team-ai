"""
"Trocar um Pokémon" feito pela IA (o modelo de src/modelo_nota.py).

Em vez de uma fórmula escrita à mão, a IA TESTA as trocas:
  1. para cada candidato do meta, monta o time com ele no lugar de quem sai
     (com os golpes, o item e a habilidade mais usados com ele);
  2. calcula a força do novo time (o que o modelo aprendeu com as batalhas reais);
  3. as melhores trocas são as que mais aumentam a força, ou seja, a chance de vencer.
Se ninguém for escolhido para sair, a IA testa trocar cada um e fica com a troca
que mais ajuda.
"""

from src import config, dados
from src.leitor import montar_time
from src.modelo_nota import analise_da_ia, carregar_modelo, membro_do_replay
from src.recomendacao import candidatos, nome_do_pokemon

QUANTOS = 5               # quantas trocas mostrar
MUDANCA_MINIMA = 0.005    # mudanças de impacto menores que isso não entram na explicação


def membro_candidato(pokemon_id: str) -> dict:
    """O candidato montado com o que os jogadores mais usam com ele."""
    vazio = {"especie": pokemon_id, "golpes": [], "item": "", "habilidade": ""}
    return montar_time([membro_do_replay(vazio)])[0]


def _numero(valor: float) -> str:
    return f"{valor:.2f}".rstrip("0").rstrip(".").replace(".", ",")


def _mudancas(antes: dict, depois: dict) -> tuple[list[dict], list[dict]]:
    """Pontos da análise que melhoram e que pioram com a troca (maior mudança primeiro)."""
    mudancas = []
    for p_antes, p_depois in zip(antes["pontos"], depois["pontos"]):
        diferenca = p_depois["impacto"] - p_antes["impacto"]
        if abs(diferenca) >= MUDANCA_MINIMA:
            mudancas.append({"nome": p_antes["nome"], "categoria": p_antes["categoria"],
                             "antes": p_antes["valor"], "depois": p_depois["valor"],
                             "mudanca": round(diferenca, 3)})
    mudancas.sort(key=lambda m: abs(m["mudanca"]), reverse=True)
    return ([m for m in mudancas if m["mudanca"] > 0], [m for m in mudancas if m["mudanca"] < 0])


def _porque(troca: dict, atual: dict) -> str:
    """Explica a troca com os pontos da análise que mais mudam."""
    frases = [f"Nota do time: {_numero(atual['nota'])} → {_numero(troca['nota'])}; chance contra "
              f"um time médio: {_numero(atual['chance'])}% → {_numero(troca['chance'])}%."]
    if troca["melhora"]:
        partes = [f"{m['nome']} ({_numero(m['antes'])} → {_numero(m['depois'])})" for m in troca["melhora"][:2]]
        frases.append("Segundo a IA, ganha força em: " + "; ".join(partes) + ".")
    if troca["piora"]:
        m = troca["piora"][0]
        frases.append(f"Perde força em: {m['nome']} ({_numero(m['antes'])} → {_numero(m['depois'])}).")
    return " ".join(frases)


def testar_trocas(time: list[dict], sai: dict, modelo: dict) -> list[dict]:
    """Todas as trocas de `sai` por um candidato do meta, da que mais ajuda para a que menos."""
    pokemon = dados.carregar_pokemon()
    resto = [m for m in time if m is not sai]
    atual = analise_da_ia(time, modelo)
    trocas = []
    for candidato in candidatos(resto):
        if pokemon[candidato]["especie_base"] == pokemon.get(sai["id"], {}).get("especie_base"):
            continue  # sugerir outro Pokémon, não o mesmo
        depois = analise_da_ia(resto + [membro_candidato(candidato)], modelo)
        melhora, piora = _mudancas(atual, depois)
        troca = {"id": candidato, "nome": nome_do_pokemon(candidato), "nota": depois["nota"],
                 "chance": depois["chance"], "ganho": round(depois["forca"] - atual["forca"], 3),
                 "melhora": melhora, "piora": piora}
        troca["porque"] = _porque(troca, atual)
        trocas.append(troca)
    trocas.sort(key=lambda t: t["ganho"], reverse=True)
    return trocas


def trocas_da_ia(time: list[dict], sai: dict | None = None, quantos: int = QUANTOS,
                 modelo: dict | None = None) -> dict | None:
    """Quem colocar no lugar de `sai` (se não vier, a IA escolhe quem sai).

    {sai, motivo, atual: {nota, chance}, substitutos: [{id, nome, nota, chance,
     ganho, melhora, piora, porque}]}. None se a IA não foi treinada ou o time
    não está completo (o modelo aprendeu com times de 6).
    """
    modelo = modelo or carregar_modelo()
    if modelo is None or len(time) < config.TEAM_SIZE:
        return None
    atual = analise_da_ia(time, modelo)
    if sai is None:
        # Testa trocar cada um e fica com quem tem a melhor troca.
        testes = {id(m): testar_trocas(time, m, modelo) for m in time}
        sai = max(time, key=lambda m: testes[id(m)][0]["ganho"] if testes[id(m)] else -1)
        trocas = testes[id(sai)]
        melhor = trocas[0] if trocas else None
        if melhor and melhor["ganho"] > 0:
            motivo = (f"A IA testou trocar cada Pokémon do time: trocar {sai['especie']} é o que "
                      f"mais aumenta a chance de vencer (a melhor troca leva a nota de "
                      f"{_numero(atual['nota'])} para {_numero(melhor['nota'])}).")
        else:
            motivo = (f"A IA testou trocar cada Pokémon e nenhuma troca melhora o time; "
                      f"trocar {sai['especie']} é a que menos piora.")
    else:
        trocas = testar_trocas(time, sai, modelo)
        motivo = "Escolhido por você."
    return {"sai": sai["especie"], "motivo": motivo,
            "atual": {"nota": atual["nota"], "chance": atual["chance"]},
            "substitutos": trocas[:quantos]}
