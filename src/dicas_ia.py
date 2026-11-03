"""
Dicas escritas a partir do que a IA (src/modelo_nota.py) aprendeu com as batalhas reais.

- Dicas: vêm do IMPACTO de cada ponto das categorias principais no time
  (cobertura, sinergia, winrate e controle de velocidade): o time tem mais
  ou menos disso que um time médio, e quanto isso pesa para vencer.
- Respostas (Fake Out, Screens, clima): são situacionais, então a resposta
  olha se os Pokémon do time se BENEFICIAM deles (setup, Trick Room,
  Psychic Terrain, quem aproveita o clima...).
- Alerta: muitos atacantes físicos e pouco especial.
"""

from src.modelo_nota import PRINCIPAIS

IMPACTO_MINIMO = 0.03  # impactos menores que isso quase não mudam a chance de vencer
NOMES_DOS_CLIMAS = {"chuva": "a chuva", "sol": "o sol", "areia": "a areia", "neve": "a neve"}


def _numero(valor: float) -> str:
    return f"{valor:.2f}".rstrip("0").rstrip(".").replace(".", ",")


def _lista(nomes: list[str]) -> str:
    """['A'] -> 'A';  ['A', 'B', 'C'] -> 'A, B e C'"""
    return nomes[0] if len(nomes) == 1 else ", ".join(nomes[:-1]) + " e " + nomes[-1]


def dicas_da_ia(resultado: dict) -> list[dict]:
    """Pontos fortes e pontos a melhorar das categorias principais, do maior impacto para o menor.

    [{nivel: "ok" | "atencao", texto}]
    """
    dicas = []
    principais = [p for p in resultado["pontos"] if p["categoria"] in PRINCIPAIS]
    for ponto in sorted(principais, key=lambda p: abs(p["impacto"]), reverse=True):
        if abs(ponto["impacto"]) < IMPACTO_MINIMO:
            continue
        comparacao = (f"seu time: {_numero(ponto['valor'])}; "
                      f"média dos vencedores: {_numero(ponto['media_vencedores'])}")
        if ponto["impacto"] > 0:
            dicas.append({"nivel": "ok", "texto": f"**{ponto['nome']}** ajuda o time a vencer ({comparacao})."})
        else:
            dicas.append({"nivel": "atencao", "texto": f"**{ponto['nome']}**: vale aumentar ({comparacao})."})
    return dicas


def _resposta_fake_out(s: dict) -> tuple[str, int]:
    if not s["fake_out"]:
        if s["psychic_terrain"]:
            return (f"O time não usa Fake Out, e nem faria falta: o Psychic Terrain de "
                    f"{_lista(s['psychic_terrain'])} bloqueia golpes de prioridade."), 0
        if s["setup_para_fake_out"]:
            quem = s["setup_para_fake_out"]
            verbo = "faz setup ou prepara" if len(quem) == 1 else "fazem setup ou preparam"
            return (f"O time não usa Fake Out, mas {_lista(quem)} {verbo} "
                    "o campo: um Pokémon com Fake Out ajudaria a garantir esse turno."), 0
        return "O time não usa Fake Out e ninguém faz setup ou prepara o campo, então não faz falta.", 0
    quem = _lista(s["fake_out"])
    if s["psychic_terrain"]:
        return (f"Não: o Psychic Terrain de {_lista(s['psychic_terrain'])} bloqueia golpes de prioridade "
                f"contra quem está no chão, inclusive o Fake Out de {quem}."), -1
    if s["setup_para_fake_out"]:
        return (f"Sim: o Fake Out de {quem} segura um oponente para "
                f"{_lista(s['setup_para_fake_out'])} fazer setup ou preparar o campo."), 1
    return (f"Pouco: {quem} usa Fake Out, mas ninguém do time faz setup ou prepara o campo "
            "para aproveitar o turno ganho."), 0


def _resposta_screens(s: dict) -> tuple[str, int]:
    if not s["screens"]:
        if s["setup_para_screens"]:
            quem = s["setup_para_screens"]
            verbo = "faz setup ou usa" if len(quem) == 1 else "fazem setup ou usam"
            return (f"O time não usa Screens, mas {_lista(quem)} {verbo} "
                    "Trick Room: Screens ajudariam a segurar o dano enquanto isso."), 0
        return "O time não usa Screens e ninguém faz setup nem Trick Room, então não fazem falta.", 0
    quem = _lista(s["screens"])
    if s["setup_para_screens"]:
        return (f"Sim: as Screens de {quem} protegem {_lista(s['setup_para_screens'])} "
                "enquanto fazem setup ou jogam no Trick Room."), 1
    return (f"Pouco: {quem} usa Screens, mas ninguém do time faz setup nem Trick Room "
            "para aproveitar."), 0


def _resposta_clima(s: dict) -> tuple[str, int]:
    if s["clima"] is None:
        return "O time não coloca clima (chuva, sol, areia ou neve), então o clima dele não pesa.", 0
    clima = NOMES_DOS_CLIMAS[s["clima"]]
    aproveitam = _lista(s["aproveitam"]) if s["aproveitam"] else "ninguém"
    prejudicados = _lista(s["prejudicados"]) if s["prejudicados"] else "ninguém"
    saldo = len(s["aproveitam"]) - len(s["prejudicados"])
    veredito = "Ajuda" if saldo > 0 else "Prejudica" if saldo < 0 else "Empata"
    return (f"{veredito}: com {clima}, aproveitam {aproveitam}; são prejudicados {prejudicados}.",
            (saldo > 0) - (saldo < 0))


def respostas_da_ia(resultado: dict) -> list[dict]:
    """As perguntas dos pontos situacionais, respondidas olhando se o time se beneficia.

    [{pergunta, resposta, efeito (+1 ajuda, 0 neutro, -1 atrapalha), impacto}]
    impacto = quanto a IA mudou a força do time por causa disso.
    """
    situacionais = resultado["situacionais"]
    impactos = {p["chave"]: p["impacto"] for p in resultado["pontos"]}
    respostas = []
    for chave, pergunta, responder in [("fake_out", "Fake Out beneficia o time?", _resposta_fake_out),
                                       ("screens", "Screens são importantes para o time?", _resposta_screens),
                                       ("clima", "O clima prejudica ou ajuda muito o time?", _resposta_clima)]:
        resposta, efeito = responder(situacionais)
        respostas.append({"pergunta": pergunta, "resposta": resposta, "efeito": efeito,
                          "impacto": impactos[chave]})
    return respostas


def texto_do_alerta(alerta: dict) -> str | None:
    """Aviso de muitos atacantes físicos e pouco especial (None se o time está equilibrado)."""
    if not alerta["ativo"]:
        return None
    especiais = _lista(alerta["especiais"]) if alerta["especiais"] else "nenhum"
    bulky = f" ({_lista(alerta['bulky'])})" if alerta["bulky"] else ""
    return (f"**Ponto de alerta:** {len(alerta['fisicos'])} atacantes físicos ({_lista(alerta['fisicos'])}) "
            f"e atacante especial: {especiais}. As ameaças bulky do meta{bulky} seguram bem golpes "
            f"físicos; um atacante especial a mais ajudaria. A IA tirou {_numero(-alerta['impacto'])} "
            "de força do time por isso.")
