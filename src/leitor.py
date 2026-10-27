"""
Leitura do time no formato de exportação do Pokémon Showdown.

É o texto que o Showdown gera em "Export" (e que todo jogador de VGC usa
para compartilhar times). Um Pokémon por bloco, separados por linha vazia:

    Incineroar @ Sitrus Berry
    Ability: Intimidate
    Level: 50
    EVs: 32 HP / 2 Atk / 32 SpD
    Careful Nature
    - Fake Out
    - Knock Off
    - Parting Shot
    - Protect

A primeira linha pode ter apelido e gênero: "Gato (Incineroar) (M) @ Sitrus Berry".
"""

import re

from src import dados
from src.nomes import to_id


def _ler_primeira_linha(linha: str) -> tuple[str, str]:
    """"Gato (Incineroar) (M) @ Sitrus Berry" -> ("Incineroar", "Sitrus Berry")"""
    nome, _, item = linha.partition(" @ ")
    nome = re.sub(r"\s*\((M|F)\)\s*$", "", nome.strip())  # tira o gênero
    apelido = re.match(r"^.+\((.+)\)$", nome)               # "Apelido (Espécie)"
    if apelido:
        nome = apelido.group(1)
    return nome.strip(), item.strip()


def ler_bloco(bloco: str) -> dict:
    """Lê UM Pokémon do texto exportado."""
    linhas = [linha.strip() for linha in bloco.strip().splitlines() if linha.strip()]
    especie, item = _ler_primeira_linha(linhas[0])
    membro = {"especie": especie, "item": item, "habilidade": "", "natureza": "", "evs": {},
              "golpes": []}
    for linha in linhas[1:]:
        if linha.startswith("-"):
            membro["golpes"].append(linha.lstrip("- ").strip())
        elif linha.startswith("Ability:"):
            membro["habilidade"] = linha.split(":", 1)[1].strip()
        elif linha.endswith("Nature"):
            membro["natureza"] = linha.replace("Nature", "").strip()
        elif linha.startswith("EVs:"):
            membro["evs"] = ler_evs(linha.split(":", 1)[1])
        # Level, IVs, Shiny etc. não importam.
    return completar(membro)


def ler_evs(texto: str) -> dict[str, int]:
    """"32 HP / 2 Atk / 32 SpD" -> {"HP": 32, "Atk": 2, "SpD": 32}"""
    evs = {}
    for parte in texto.split("/"):
        valor, _, status = parte.strip().partition(" ")
        if valor.isdigit():
            evs[status.strip()] = int(valor)
    return evs


def completar(membro: dict) -> dict:
    """Acrescenta os ids e descobre a forma que o Pokémon usa na batalha.

    - id:    o Pokémon como foi escrito ("charizard")
    - forma: o que vale na batalha. Se ele segura a própria Pedra Mega,
             a forma é a Mega ("charizardmegay"), que tem outros tipos e
             outra habilidade.
    """
    membro["id"] = dados.id_do_pokemon(membro["especie"])
    membro["item_id"] = to_id(membro["item"])
    membro["forma"] = membro["id"]
    pedra = dados.carregar_itens()["pedras_mega"].get(membro["item_id"])
    info = dados.carregar_pokemon().get(membro["id"])
    if pedra and info and pedra["pokemon"] in (membro["id"], info["especie_base"]):
        membro["forma"] = pedra["mega"]
    return membro


def ler_time(texto: str) -> list[dict]:
    """Lê o time inteiro (blocos separados por linha em branco)."""
    blocos = re.split(r"\n\s*\n", texto.strip())
    return _nomes_unicos([ler_bloco(bloco) for bloco in blocos if bloco.strip()])


def _nomes_unicos(time: list[dict]) -> list[dict]:
    """Se a mesma espécie aparece duas vezes, a segunda vira "Garchomp (2)".

    O time é inválido assim, mas a análise continua funcionando e as tabelas
    mostram uma coluna para cada um.
    """
    vistos = {}
    for membro in time:
        vistos[membro["especie"]] = vistos.get(membro["especie"], 0) + 1
        if vistos[membro["especie"]] > 1:
            membro["especie"] = f"{membro['especie']} ({vistos[membro['especie']]})"
    return time


def time_de_nomes(nomes: list[str]) -> list[dict]:
    """Monta um time só com os nomes (sem item/golpes). Usado nos testes.

    Golpes e habilidade ficam vazios: a análise de tipos funciona, mas a de
    funções de duplas e cobertura ofensiva precisa dos golpes.
    """
    return _nomes_unicos([
        completar({"especie": nome, "item": "", "habilidade": "", "natureza": "", "golpes": []})
        for nome in nomes
    ])


def montar_time(membros: list[dict]) -> list[dict]:
    """Time vindo da tela "Montar o time": cada membro já tem espécie, item,
    habilidade e golpes escolhidos nos seletores (com os nomes do Showdown)."""
    return _nomes_unicos([completar(dict(membro)) for membro in membros])
