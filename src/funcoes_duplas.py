"""
Funções de duplas (VGC): quais golpes e habilidades cumprem cada papel.

Na Fase 2, a análise do time olha os golpes e a habilidade de cada Pokémon
e verifica se o time tem cada uma destas funções.

Golpes e habilidades estão escritos como id (ver src/nomes.py), que é o
mesmo formato usado pelas estatísticas do Smogon: "Fake Out" -> "fakeout".
"""

from src.nomes import to_id

FUNCOES = {
    "controle_velocidade": {
        "nome": "Controle de velocidade",
        "descricao": "Faz o seu time agir primeiro (ou o adversário agir depois).",
        "golpes": {
            "tailwind", "trickroom", "icywind", "electroweb", "thunderwave",
            "rocktomb", "bulldoze", "scaryface", "nuzzle",
        },
        "habilidades": set(),
    },
    "fake_out": {
        "nome": "Fake Out",
        "descricao": "Faz um adversário perder o primeiro turno.",
        "golpes": {"fakeout"},
        "habilidades": set(),
    },
    "intimidate": {
        "nome": "Intimidate",
        "descricao": "Reduz o Ataque dos dois adversários ao entrar.",
        "golpes": set(),
        "habilidades": {"intimidate"},
    },
    "redirecionamento": {
        "nome": "Redirecionamento",
        "descricao": "Puxa os golpes do adversário para si e protege o parceiro.",
        "golpes": {"followme", "ragepowder"},
        "habilidades": {"lightningrod", "stormdrain"},
    },
    "golpe_em_area": {
        "nome": "Golpes que acertam os dois alvos",
        "descricao": "Causam dano nos dois adversários de uma vez.",
        "golpes": {
            "earthquake", "rockslide", "heatwave", "dazzlinggleam", "hypervoice",
            "surf", "muddywater", "blizzard", "eruption", "waterspout",
            "discharge", "makeitrain", "bleakwindstorm", "sludgewave", "snarl",
            "icywind", "electroweb", "breakingswipe", "boomburst", "lavaplume",
            "expandingforce", "petalblizzard", "originpulse", "precipiceblades",
        },
        "habilidades": set(),
    },
    "protecao": {
        "nome": "Proteção",
        "descricao": "Bloqueia ataques por um turno (Protect) ou protege o time todo (Wide Guard).",
        "golpes": {
            "protect", "detect", "spikyshield", "kingsshield", "banefulbunker",
            "silktrap", "burningbulwark", "wideguard", "quickguard",
        },
        "habilidades": set(),
    },
}


def funcoes_do_pokemon(golpes: list[str], habilidade: str = "") -> list[str]:
    """Lista as funções de duplas que um Pokémon cumpre.

    Aceita nomes "bonitos" ou ids: "Fake Out" e "fakeout" funcionam igual.
    """
    golpes_ids = {to_id(g) for g in golpes}
    habilidade_id = to_id(habilidade)
    encontradas = []
    for chave, funcao in FUNCOES.items():
        if golpes_ids & funcao["golpes"] or habilidade_id in funcao["habilidades"]:
            encontradas.append(chave)
    return encontradas
