"""
Dicas em texto claro, geradas a partir da análise (src/analise.py).

Cada dica é uma regra simples do tipo "SE acontece X, ENTÃO avise Y".
Níveis:
    "alerta"  -> problema sério ("4 de 6 tomam dano dobrado de Gelo e ninguém resiste")
    "atencao" -> vale melhorar
    "ok"      -> ponto forte do time
"""

from src import dados
from src.funcoes_duplas import FUNCOES
from src.tipos import TIPOS, TIPOS_PT, multiplicador

# Funções que quase todo time de duplas precisa; as outras são "bom ter".
FUNCOES_ESSENCIAIS = ["controle_velocidade", "protecao", "golpe_em_area"]


def _lista(nomes: list[str], conectivo: str = "e") -> str:
    """["A", "B", "C"] -> "A, B e C" """
    return nomes[0] if len(nomes) == 1 else ", ".join(nomes[:-1]) + f" {conectivo} " + nomes[-1]


def _verbo(nomes: list[str], singular: str, plural: str) -> str:
    """Concordância: "só Torkoal segura" / "só Torkoal e Garchomp seguram"."""
    return singular if len(nomes) == 1 else plural


def _exemplos(funcao: dict) -> str:
    """Até 4 golpes/habilidades da função, com o nome bonito ("Icy Wind")."""
    golpes = dados.carregar_golpes()
    nomes = sorted(golpes[g]["nome"] for g in funcao["golpes"] if g in golpes)
    nomes += sorted(h.title() for h in funcao["habilidades"])
    return ", ".join(nomes[:4])


def tipos_que_resistem(tipo_golpe: str) -> list[str]:
    """Tipos (puros) que tomam metade ou nenhum dano de um tipo de golpe."""
    return [TIPOS_PT[t] for t in TIPOS if multiplicador(tipo_golpe, t) < 1]


def gerar_dicas(time: list[dict], analise: dict) -> list[dict]:
    dicas = []

    def dica(nivel, texto):
        dicas.append({"nivel": nivel, "texto": texto})

    total = len(time)
    if total == 0:
        return dicas

    # 1. Fraquezas: muitos fracos ao mesmo tipo e pouca gente para segurar.
    for linha in analise["defesa"]:
        fracos = len(linha["fracos"])
        seguram = len(linha["resistem"]) + len(linha["imunes"])
        tipo = TIPOS_PT[linha["tipo"]]
        if fracos >= 3 and seguram == 0:
            dica("alerta",
                 f"{fracos} de {total} Pokémon tomam dano dobrado de **{tipo}** e ninguém resiste. "
                 f"Um Pokémon de tipo {_lista(tipos_que_resistem(linha['tipo']), 'ou')} ajudaria.")
        elif fracos >= 3 and fracos > seguram:
            quem = linha["resistem"] + linha["imunes"]
            dica("atencao",
                 f"{fracos} de {total} Pokémon são fracos a **{tipo}** "
                 f"e só {_lista(quem)} {_verbo(quem, 'segura', 'seguram')}.")

    # 2. Cobertura ofensiva: tipos que os golpes do time não acertam bem.
    #    Sem nenhum golpe de ataque escolhido, não dá para saber.
    sem_dano_dobrado = [TIPOS_PT[c["tipo"]] for c in analise["cobertura"] if c["melhor"] < 2]
    mal_cobertos = [TIPOS_PT[c["tipo"]] for c in analise["cobertura"] if c["melhor"] < 1]
    alguem_ataca = len(analise["sem_ataques"]) < len(time)
    if alguem_ataca and mal_cobertos:
        dica("alerta", f"O time não tem golpe que cause dano normal em **{_lista(mal_cobertos)}**: "
                       "todos os seus ataques são resistidos por esses tipos.")
    if alguem_ataca and len(sem_dano_dobrado) > 6:
        dica("atencao", f"Cobertura ofensiva estreita: nenhum golpe acerta com dano dobrado "
                        f"{_lista(sem_dano_dobrado)}.")
    elif alguem_ataca and not sem_dano_dobrado:
        dica("ok", "Cobertura ofensiva completa: o time acerta todos os tipos com dano dobrado.")

    # 3. Funções de duplas.
    sem_golpes = all(not m["golpes"] for m in time)
    for chave, funcao in FUNCOES.items():
        quem = analise["funcoes"][chave]
        if quem:
            dica("ok", f"{funcao['nome']}: {_lista(quem)}.")
        elif sem_golpes and funcao["golpes"]:
            continue  # sem os golpes não dá para saber
        elif chave in FUNCOES_ESSENCIAIS:
            dica("alerta", f"O time não tem **{funcao['nome'].lower()}**. "
                           f"{funcao['descricao']} Exemplos: {_exemplos(funcao)}.")
        else:
            dica("atencao", f"O time não tem {funcao['nome']}. {funcao['descricao']}")

    # Protect: em duplas quase todo Pokémon usa.
    if not sem_golpes and analise["funcoes"]["protecao"]:
        sem_protecao = [m["especie"] for m in time if m["especie"] not in analise["funcoes"]["protecao"]]
        if len(sem_protecao) >= 3:
            dica("atencao", f"{_lista(sem_protecao)} não têm Protect/Detect. "
                            "Em duplas, quase todo Pokémon carrega um golpe de proteção.")

    # 4. Ameaças do meta.
    for ameaca in analise["ameacas"][:3]:
        quem = ameaca["respostas"]
        respostas = (f"só {_lista(quem)} o {_verbo(quem, 'acerta', 'acertam')} com dano dobrado"
                     if ameaca["respostas"] else "ninguém do time o acerta com dano dobrado")
        dica("alerta" if not ameaca["respostas"] else "atencao",
             f"**{ameaca['nome']}** ({ameaca['uso']:.0f}% dos times) acerta "
             f"{len(ameaca['acerta'])} dos seus Pokémon com dano dobrado e {respostas}.")
    return dicas
