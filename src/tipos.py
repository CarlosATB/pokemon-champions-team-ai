"""
Tabela de efetividade de tipos (18 × 18).

Lida do ponto de vista de quem ATACA: para cada tipo de golpe, quais tipos
ele acerta com dano dobrado (2x), com metade do dano (0.5x) ou não afeta (0x).
Qualquer combinação que não aparece aqui é dano normal (1x).

Exemplo: um golpe de Gelo contra um Pokémon Dragão/Voador
    Gelo -> Dragão = 2x, Gelo -> Voador = 2x  =>  2 × 2 = 4x
"""

TIPOS = [
    "Normal", "Fire", "Water", "Electric", "Grass", "Ice",
    "Fighting", "Poison", "Ground", "Flying", "Psychic", "Bug",
    "Rock", "Ghost", "Dragon", "Dark", "Steel", "Fairy",
]

# Nome em português, para mostrar na interface.
TIPOS_PT = {
    "Normal": "Normal", "Fire": "Fogo", "Water": "Água", "Electric": "Elétrico",
    "Grass": "Planta", "Ice": "Gelo", "Fighting": "Lutador", "Poison": "Venenoso",
    "Ground": "Terrestre", "Flying": "Voador", "Psychic": "Psíquico", "Bug": "Inseto",
    "Rock": "Pedra", "Ghost": "Fantasma", "Dragon": "Dragão", "Dark": "Sombrio",
    "Steel": "Aço", "Fairy": "Fada",
}

#  tipo do golpe: (dano dobrado em...,  metade do dano em...,  não afeta...)
_TABELA = {
    "Normal":   ([], ["Rock", "Steel"], ["Ghost"]),
    "Fire":     (["Grass", "Ice", "Bug", "Steel"], ["Fire", "Water", "Rock", "Dragon"], []),
    "Water":    (["Fire", "Ground", "Rock"], ["Water", "Grass", "Dragon"], []),
    "Electric": (["Water", "Flying"], ["Electric", "Grass", "Dragon"], ["Ground"]),
    "Grass":    (["Water", "Ground", "Rock"],
                 ["Fire", "Grass", "Poison", "Flying", "Bug", "Dragon", "Steel"], []),
    "Ice":      (["Grass", "Ground", "Flying", "Dragon"], ["Fire", "Water", "Ice", "Steel"], []),
    "Fighting": (["Normal", "Ice", "Rock", "Dark", "Steel"],
                 ["Poison", "Flying", "Psychic", "Bug", "Fairy"], ["Ghost"]),
    "Poison":   (["Grass", "Fairy"], ["Poison", "Ground", "Rock", "Ghost"], ["Steel"]),
    "Ground":   (["Fire", "Electric", "Poison", "Rock", "Steel"], ["Grass", "Bug"], ["Flying"]),
    "Flying":   (["Grass", "Fighting", "Bug"], ["Electric", "Rock", "Steel"], []),
    "Psychic":  (["Fighting", "Poison"], ["Psychic", "Steel"], ["Dark"]),
    "Bug":      (["Grass", "Psychic", "Dark"],
                 ["Fire", "Fighting", "Poison", "Flying", "Ghost", "Steel", "Fairy"], []),
    "Rock":     (["Fire", "Ice", "Flying", "Bug"], ["Fighting", "Ground", "Steel"], []),
    "Ghost":    (["Psychic", "Ghost"], ["Dark"], ["Normal"]),
    "Dragon":   (["Dragon"], ["Steel"], ["Fairy"]),
    "Dark":     (["Psychic", "Ghost"], ["Fighting", "Dark", "Fairy"], []),
    "Steel":    (["Ice", "Rock", "Fairy"], ["Fire", "Water", "Electric", "Steel"], []),
    "Fairy":    (["Fighting", "Dragon", "Dark"], ["Fire", "Poison", "Steel"], []),
}


def multiplicador(tipo_golpe: str, tipo_alvo: str) -> float:
    """Dano de um tipo de golpe contra UM tipo: 2, 1, 0.5 ou 0."""
    dobro, metade, imune = _TABELA[tipo_golpe]
    if tipo_alvo in imune:
        return 0.0
    if tipo_alvo in dobro:
        return 2.0
    if tipo_alvo in metade:
        return 0.5
    return 1.0


def efetividade(tipo_golpe: str, tipos_alvo: list[str]) -> float:
    """Dano contra um Pokémon de 1 ou 2 tipos (multiplica os dois).

    efetividade("Ice", ["Dragon", "Flying"]) -> 4.0
    """
    resultado = 1.0
    for tipo in tipos_alvo:
        resultado *= multiplicador(tipo_golpe, tipo)
    return resultado


def tabela_completa() -> dict[str, dict[str, float]]:
    """A tabela 18 × 18 inteira: tabela[golpe][alvo] = multiplicador."""
    return {golpe: {alvo: multiplicador(golpe, alvo) for alvo in TIPOS} for golpe in TIPOS}
