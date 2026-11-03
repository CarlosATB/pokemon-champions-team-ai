"""
Dicas escritas a partir do que a IA (src/modelo_nota.py) aprendeu com as batalhas reais.

Nada aqui é regra escrita à mão: cada texto vem do PESO que o modelo aprendeu
para um ponto (ajuda ou atrapalha a vencer?) e do IMPACTO desse ponto no time
(o time tem mais ou menos disso que um time médio?).
"""

IMPACTO_MINIMO = 0.03  # impactos menores que isso quase não mudam a chance de vencer


def _numero(valor: float) -> str:
    return f"{valor:.2f}".rstrip("0").rstrip(".").replace(".", ",")


def dicas_da_ia(resultado: dict) -> list[dict]:
    """Pontos fortes e pontos a melhorar, do maior impacto para o menor.

    [{nivel: "ok" | "atencao", texto}]
    """
    dicas = []
    for ponto in sorted(resultado["pontos"], key=lambda p: abs(p["impacto"]), reverse=True):
        if abs(ponto["impacto"]) < IMPACTO_MINIMO:
            continue
        comparacao = (f"seu time: {_numero(ponto['valor'])}; "
                      f"média dos vencedores: {_numero(ponto['media_vencedores'])}")
        if ponto["impacto"] > 0:
            # Peso negativo: o time ganha força por ter MENOS disso que a média.
            quanto = "Ter pouco de " if ponto["peso"] < 0 else ""
            nome = ponto["nome"] if not quanto else ponto["nome"][0].lower() + ponto["nome"][1:]
            texto = f"{quanto}**{nome}** ajuda o time a vencer ({comparacao})."
            dicas.append({"nivel": "ok", "texto": texto})
        else:
            # Peso positivo: ter MAIS ajudaria. Peso negativo: ter MENOS ajudaria.
            direcao = "aumentar" if ponto["peso"] > 0 else "diminuir"
            texto = f"**{ponto['nome']}**: vale {direcao} ({comparacao})."
            dicas.append({"nivel": "atencao", "texto": texto})
    return dicas


def _veredito(impacto: float, assunto: str) -> str:
    if impacto >= IMPACTO_MINIMO:
        return f"Sim, {assunto} ajuda o time"
    if impacto <= -IMPACTO_MINIMO:
        return f"Não, {assunto} prejudica o time"
    return f"{assunto[0].upper() + assunto[1:]} quase não faz diferença no time"


def respostas_da_ia(resultado: dict) -> list[dict]:
    """As perguntas da análise, respondidas pelo modelo.

    [{pergunta, resposta, impacto}]
    """
    pontos = {p["chave"]: p for p in resultado["pontos"]}
    respostas = []
    for chave, pergunta, nome in [("fake_out", "Fake Out beneficia o time?", "Fake Out"),
                                  ("screens", "Screens são importantes para o time?", "Screens")]:
        ponto = pontos[chave]
        aprendeu = ("times com mais" if ponto["peso"] > 0 else "times com menos")
        licao = (f"Nas batalhas reais, {aprendeu} {nome} venceram mais (peso {ponto['peso']:+.3f})")
        if ponto["valor"] == 0:
            impacto = 0.0
            conselho = "vale testar colocar" if ponto["peso"] > 0 else "não faz falta colocar"
            resposta = f"O time não usa {nome}. {licao}, então {conselho}."
        else:
            # Quem tem o golpe: ajuda se o peso é positivo, prejudica se é negativo.
            impacto = ponto["peso"] * ponto["valor"] if abs(ponto["impacto"]) >= IMPACTO_MINIMO else 0.0
            resposta = (f"{_veredito(impacto, nome)}: ele tem {_numero(ponto['valor'])} "
                        f"Pokémon com {nome}. {licao}.")
        respostas.append({"pergunta": pergunta, "resposta": resposta, "impacto": round(impacto, 3)})

    a_favor, contra = pontos["clima_a_favor"], pontos["clima_contra"]
    impacto = a_favor["impacto"] + contra["impacto"]
    if a_favor["valor"] == 0 and contra["valor"] == 0:
        impacto = 0.0
        resposta = "O time não coloca clima (chuva, sol, areia ou neve), então o clima dele não pesa."
    else:
        resposta = (f"{_veredito(impacto, 'o clima')}: {_numero(a_favor['valor'])} Pokémon "
                    f"aproveitam e {_numero(contra['valor'])} são prejudicados por ele.")
    respostas.append({"pergunta": "O clima prejudica ou ajuda muito o time?",
                      "resposta": resposta, "impacto": round(impacto, 3)})
    return respostas
