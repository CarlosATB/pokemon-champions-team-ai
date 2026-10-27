"""
Sistema de Recomendação: a parte "quem usa X também usa Y" da IA.

Funciona como a recomendação de uma loja online ("quem comprou este livro
também comprou..."), usando as estatísticas de milhares de batalhas reais
(src/dados.py -> uso.json). Em termos de regras de associação:

    suporte(Y)       = % dos times que têm Y                 -> uso[Y]["uso"]
    confiança(X -> Y) = % dos times com X que também têm Y   -> uso[X]["parceiros"][Y]
    lift(X -> Y)      = confiança(X -> Y) / suporte(Y)
                        (> 1: X e Y aparecem juntos MAIS do que o acaso)

Três perguntas, cada uma numa função:
1. sugerir_para_pokemon -> qual habilidade, item, golpes e natureza/EVs usar?
                           (o que a maioria dos jogadores usa com ele)
2. sugerir_parceiros    -> quem combina com o time? (co-ocorrência)
3. sugerir_substitutos  -> se eu trocar um Pokémon, por quem?
                           nota = co-ocorrência + cobrir as fraquezas da Fase 2
"""

from src import dados
from src.analise import dano_recebido, habilidade_de, matriz_defensiva, tipos_de
from src.dicas import _lista
from src.nomes import to_id
from src.tipos import TIPOS_PT

QUANTOS_GOLPES = 6         # quantos golpes mais usados mostrar
GOLPE_RARO = 5.0           # % abaixo da qual um golpe do time é "pouco usado"
CANDIDATOS_DO_META = 80    # quantos Pokémon mais usados entram como candidatos
PESO_PARCERIA = 0.5        # peso da co-ocorrência na nota do substituto
PESO_FRAQUEZAS = 0.5       # peso de cobrir as fraquezas na nota do substituto
NOMES_EVS = ["HP", "Atk", "Def", "SpA", "SpD", "Spe"]


# ---------------------------------------------------------------------------
# Apoio: estatísticas e nomes bonitos
# ---------------------------------------------------------------------------

def chave_de_uso(membro: dict) -> str | None:
    """Com que nome o Pokémon aparece nas estatísticas: a Mega, se ele segura
    a Pedra Mega ("salamencemega"); senão, ele mesmo. None se não tem dados."""
    uso = dados.carregar_uso()["pokemon"]
    for chave in (membro["forma"], membro["id"]):
        if chave in uso:
            return chave
    return None


def nome_do_pokemon(pokemon_id: str) -> str:
    uso = dados.carregar_uso()["pokemon"]
    if pokemon_id in uso:
        return uso[pokemon_id]["nome"]
    return dados.carregar_pokemon().get(pokemon_id, {}).get("nome", pokemon_id)


def nome_do_item(item_id: str) -> str:
    return dados.carregar_itens()["legais"].get(item_id, item_id)


def nome_do_golpe(golpe_id: str) -> str:
    return dados.carregar_golpes().get(golpe_id, {}).get("nome", golpe_id)


def nome_da_habilidade(habilidade_id: str) -> str:
    return dados.carregar_habilidades().get(habilidade_id, habilidade_id)


def ler_spread(spread: str) -> tuple[str, str]:
    """"Adamant:32/32/0/0/2/0" -> ("Adamant", "32 HP / 32 Atk / 2 SpD")

    No Champions os EVs são "pontos de status" (0 a 32 em cada um).
    """
    natureza, _, numeros = spread.partition(":")
    evs = [f"{valor} {nome}" for valor, nome in zip(numeros.split("/"), NOMES_EVS) if valor != "0"]
    return natureza, " / ".join(evs)


def _pct(valor: float) -> str:
    """42.96 -> "43%";  0.4 -> "0,4%" """
    return f"{valor:.0f}%" if valor >= 10 else f"{valor:.1f}%".replace(".", ",")


# ---------------------------------------------------------------------------
# 1. Habilidade, item, golpes e natureza/EVs de cada Pokémon
# ---------------------------------------------------------------------------

def sugerir_para_pokemon(membro: dict, itens_ocupados: dict[str, str] | None = None) -> dict:
    """O que a maioria dos jogadores usa com este Pokémon (frequência de uso).

    itens_ocupados: {item_id: quem do time já usa}. Como o time não pode
    repetir item, a sugestão de item é o mais usado que ainda está livre.
    """
    itens_ocupados = itens_ocupados or {}
    chave = chave_de_uso(membro)
    if chave is None:
        return {"especie": membro["especie"], "tem_dados": False,
                "porque": f"{membro['especie']} quase não aparece nas batalhas, então não há "
                          "estatísticas suficientes para recomendar."}

    info = dados.carregar_uso()["pokemon"][chave]
    nome = info["nome"]
    eh_mega = dados.carregar_pokemon().get(chave, {}).get("mega", False)

    # Habilidade: a mais usada. A Mega tem habilidade fixa.
    habilidade_id, habilidade_pct = next(iter(info["habilidades"].items()))
    if eh_mega:
        porque = f"Ao Mega Evoluir, a habilidade vira {nome_da_habilidade(habilidade_id)}."
    else:
        porque = f"{_pct(habilidade_pct)} dos {nome} usam {nome_da_habilidade(habilidade_id)}."
    habilidade = {
        "nome": nome_da_habilidade(habilidade_id),
        "uso": habilidade_pct,
        "voce_usa": eh_mega or to_id(membro["habilidade"]) == habilidade_id,
        "porque": porque,
    }

    # Item: o mais usado que ninguém do time está usando.
    itens = []
    for item_id, porcentagem in info["itens"].items():
        dono = itens_ocupados.get(item_id)
        itens.append({"id": item_id, "nome": nome_do_item(item_id), "uso": porcentagem,
                      "ocupado_por": dono if dono != membro["especie"] else None})
    livres = [i for i in itens if not i["ocupado_por"]]
    melhor_item = livres[0] if livres else None
    if melhor_item is None:
        porque = "Os itens mais usados por ele já estão com outros Pokémon do time."
    elif melhor_item is itens[0]:
        porque = f"{_pct(melhor_item['uso'])} dos {nome} usam {melhor_item['nome']}."
    else:
        porque = (f"O mais usado é {itens[0]['nome']} ({_pct(itens[0]['uso'])}), mas ele já está "
                  f"com {itens[0]['ocupado_por']} e o time não pode repetir item. "
                  f"A melhor opção livre é {melhor_item['nome']} ({_pct(melhor_item['uso'])}).")
    item = {
        "melhor": melhor_item,
        "opcoes": itens[:5],
        "voce_usa": melhor_item is not None and membro["item_id"] == melhor_item["id"],
        "porque": porque,
    }

    # Golpes: os mais usados; e os do time que quase ninguém usa.
    golpes_do_time = {to_id(g) for g in membro["golpes"]}
    golpes = [{"nome": nome_do_golpe(g), "uso": p, "voce_usa": g in golpes_do_time}
              for g, p in list(info["golpes"].items())[:QUANTOS_GOLPES]]
    raros = [nome_do_golpe(g) for g in golpes_do_time
             if info["golpes"].get(g, 0) < GOLPE_RARO and g in dados.carregar_golpes()]
    top4 = ", ".join(f"{g['nome']} ({_pct(g['uso'])})" for g in golpes[:4])
    porque = f"Os 4 golpes mais usados pelos {nome}: {top4}."
    if raros:
        porque += (f" Menos de {GOLPE_RARO:.0f}% dos jogadores usam {', '.join(sorted(raros))}: "
                   "vale conferir se compensa.")

    # Natureza e EVs: o spread (natureza + EVs) mais usado.
    spread, spread_pct = next(iter(info["spreads"].items()), ("", 0))
    natureza, evs = ler_spread(spread)

    return {
        "especie": membro["especie"],
        "tem_dados": True,
        "nome_nas_estatisticas": nome,
        "habilidade": habilidade,
        "item": item,
        "golpes": {"lista": golpes, "raros": sorted(raros), "porque": porque},
        "natureza_evs": {
            "natureza": natureza,
            "evs": evs,
            "uso": spread_pct,
            "voce_usa": membro["natureza"].lower() == natureza.lower(),
            "porque": f"É a combinação mais comum ({_pct(spread_pct)} dos {nome}). "
                      "Os EVs variam muito entre jogadores, então use como ponto de partida.",
        },
    }


def recomendar_time(time: list[dict]) -> list[dict]:
    """Sugestões para cada Pokémon do time, sem repetir item.

    Quem já tem item "reserva" o dele. Quem não tem recebe o melhor item
    livre, e esse item passa a ficar reservado para os próximos.
    """
    ocupados = {m["item_id"]: m["especie"] for m in time if m["item_id"]}
    sugestoes = []
    for membro in time:
        sugestao = sugerir_para_pokemon(membro, ocupados)
        if sugestao["tem_dados"] and not membro["item_id"] and sugestao["item"]["melhor"]:
            ocupados[sugestao["item"]["melhor"]["id"]] = membro["especie"]
        sugestoes.append(sugestao)
    return sugestoes


# ---------------------------------------------------------------------------
# 2. Parceiros (co-ocorrência)
# ---------------------------------------------------------------------------

def _especies(time: list[dict]) -> set[str]:
    pokemon = dados.carregar_pokemon()
    return {pokemon[m["id"]]["especie_base"] for m in time if m["id"] in pokemon}


def _tem_mega(time: list[dict]) -> bool:
    pokemon = dados.carregar_pokemon()
    return any(pokemon.get(m["forma"], {}).get("mega") for m in time)


def candidatos(time: list[dict]) -> list[str]:
    """Pokémon do meta que podem entrar no time: legais, de espécie que o time
    ainda não tem, e sem Mega se o time já tem uma (só uma Mega por batalha)."""
    pokemon = dados.carregar_pokemon()
    legais = set(dados.carregar_legais())
    especies = _especies(time)
    sem_mega = _tem_mega(time)
    lista = []
    for pokemon_id in list(dados.carregar_uso()["pokemon"])[:CANDIDATOS_DO_META]:
        info = pokemon.get(pokemon_id)
        if (info is None or pokemon_id not in legais or info["especie_base"] in especies
                or (sem_mega and info["mega"])):
            continue
        lista.append(pokemon_id)
    return lista


def confianca_com_o_time(time: list[dict], candidato: str) -> dict[str, float]:
    """{membro: confiança(membro -> candidato)}: % dos times com aquele
    membro que também têm o candidato."""
    uso = dados.carregar_uso()["pokemon"]
    resultado = {}
    vistos = set()
    for membro in time:
        chave = chave_de_uso(membro)
        if chave and chave not in vistos:  # espécie repetida conta uma vez só
            vistos.add(chave)
            resultado[membro["especie"]] = uso[chave]["parceiros"].get(candidato, 0.0)
    return resultado


def sugerir_parceiros(time: list[dict], quantos: int = 5) -> list[dict]:
    """Quem mais aparece junto com os Pokémon do time.

    Nota = confiança média (média, entre os membros do time, da % de times
    com aquele membro que também têm o candidato). O lift mostra se isso é
    só porque o candidato é popular (lift ~1) ou se ele combina de verdade.
    """
    uso = dados.carregar_uso()["pokemon"]
    resultado = []
    for candidato in candidatos(time):
        confiancas = confianca_com_o_time(time, candidato)
        if not confiancas:
            continue
        media = sum(confiancas.values()) / len(confiancas)
        if media == 0:
            continue
        lift = media / uso[candidato]["uso"]
        principais = sorted(confiancas.items(), key=lambda kv: kv[1], reverse=True)[:2]
        explicacao = " e ".join(f"{_pct(c)} dos times com {nome}" for nome, c in principais if c > 0)
        lift_texto = f"{lift:.2f}".replace(".", ",")
        if lift >= 1.1:
            leitura = "combina com o seu time mais do que com um time qualquer"
        elif lift <= 0.9:
            leitura = "é popular em geral, mas aparece menos com o seu time do que com um time qualquer"
        else:
            leitura = "aparece com o seu time tanto quanto com um time qualquer (é popular em geral)"
        resultado.append({
            "id": candidato,
            "nome": nome_do_pokemon(candidato),
            "confianca": round(media, 1),
            "suporte": uso[candidato]["uso"],
            "lift": round(lift, 2),
            "porque": f"Aparece em {explicacao}. Lift {lift_texto}: {leitura}.",
        })
    resultado.sort(key=lambda p: p["confianca"], reverse=True)
    return resultado[:quantos]


# ---------------------------------------------------------------------------
# 3. Substitutos: co-ocorrência + cobrir as fraquezas da Fase 2
# ---------------------------------------------------------------------------

def fraquezas_do_time(time: list[dict]) -> list[str]:
    """Tipos de golpe que preocupam: 2+ Pokémon tomam dano dobrado e são
    mais os fracos do que os que resistem (mesma matriz da Fase 2)."""
    return [linha["tipo"] for linha in matriz_defensiva(time)
            if len(linha["fracos"]) >= 2
            and len(linha["fracos"]) > len(linha["resistem"]) + len(linha["imunes"])]


def escolher_quem_sai(time: list[dict]) -> tuple[dict, str]:
    """Sugere quem trocar: quem é fraco a mais tipos que preocupam o time;
    no empate, quem menos aparece junto com os outros (menor confiança)."""
    fraquezas = fraquezas_do_time(time)

    def fraco_a(membro):
        return [t for t in fraquezas if dano_recebido(t, tipos_de(membro), habilidade_de(membro)) > 1]

    def combina(membro):
        resto = [m for m in time if m is not membro]
        chave = chave_de_uso(membro)
        valores = confianca_com_o_time(resto, chave).values() if chave else []
        return sum(valores) / len(valores) if valores else 0.0

    sai = max(time, key=lambda m: (len(fraco_a(m)), -combina(m)))
    tipos = [TIPOS_PT[t] for t in fraco_a(sai)]
    empatados = [m for m in time if len(fraco_a(m)) == len(tipos)]
    if tipos:
        motivo = f"{sai['especie']} é fraco a {_lista(tipos)}, que já preocupam o time."
        if len(empatados) > 1:
            motivo += " Entre os empatados, é o que menos aparece junto com os outros nas batalhas."
    else:
        motivo = f"{sai['especie']} é o que menos aparece junto com os outros nas batalhas."
    return sai, motivo


def sugerir_substitutos(time: list[dict], sai: dict | None = None, quantos: int = 5) -> dict:
    """Quem colocar no lugar de `sai` (se não vier, a IA escolhe).

    Para cada candidato do meta:
      parceria = confiança média com os 5 que ficam (0 a 1, dividindo pela maior);
      cobertura = fração das fraquezas do time que ele resiste (0 a 1).
      nota = PESO_PARCERIA * parceria + PESO_FRAQUEZAS * cobertura   (0 a 100)
    """
    motivo = "Escolhido por você."
    if sai is None:
        sai, motivo = escolher_quem_sai(time)
    resto = [m for m in time if m is not sai]
    fraquezas = fraquezas_do_time(resto)
    pokemon = dados.carregar_pokemon()
    uso = dados.carregar_uso()["pokemon"]

    linhas = []
    for candidato in candidatos(resto):
        if pokemon[candidato]["especie_base"] == pokemon.get(sai["id"], {}).get("especie_base"):
            continue  # sugerir outro Pokémon, não o mesmo
        confiancas = confianca_com_o_time(resto, candidato)
        media = sum(confiancas.values()) / len(confiancas) if confiancas else 0.0
        habilidade = next(iter(uso[candidato]["habilidades"]), "")
        cobre = [t for t in fraquezas
                 if dano_recebido(t, pokemon[candidato]["tipos"], habilidade) < 1]
        linhas.append({"id": candidato, "nome": nome_do_pokemon(candidato),
                       "confianca": round(media, 1), "cobre": cobre})

    maior = max((l["confianca"] for l in linhas), default=0) or 1
    for linha in linhas:
        parceria = linha["confianca"] / maior
        cobertura = len(linha["cobre"]) / len(fraquezas) if fraquezas else 0.0
        linha["nota"] = round(100 * (PESO_PARCERIA * parceria + PESO_FRAQUEZAS * cobertura))
        porque = f"Aparece em média em {_pct(linha['confianca'])} dos times com os Pokémon que ficam"
        if linha["cobre"]:
            porque += f" e resiste a {_lista([TIPOS_PT[t] for t in linha['cobre']])}"
            porque += ", que preocupa o time." if len(linha["cobre"]) == 1 else ", que preocupam o time."
        else:
            porque += "."
        linha["porque"] = porque
        linha["cobre"] = [TIPOS_PT[t] for t in linha["cobre"]]

    linhas.sort(key=lambda l: (l["nota"], l["confianca"]), reverse=True)
    return {
        "sai": sai["especie"],
        "motivo": motivo,
        "fraquezas": [TIPOS_PT[t] for t in fraquezas],
        "substitutos": linhas[:quantos],
    }
