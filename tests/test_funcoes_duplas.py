"""Testes das funções de duplas."""

from src.funcoes_duplas import FUNCOES, funcoes_do_pokemon
from src.nomes import to_id


def test_incineroar():
    golpes = ["Fake Out", "Flare Blitz", "Knock Off", "Parting Shot"]
    assert funcoes_do_pokemon(golpes, "Intimidate") == ["fake_out", "intimidate"]


def test_amoonguss():
    golpes = ["Rage Powder", "Spore", "Pollen Puff", "Protect"]
    assert set(funcoes_do_pokemon(golpes, "Regenerator")) == {"redirecionamento", "protecao"}


def test_listas_estao_em_formato_id():
    for funcao in FUNCOES.values():
        for nome in funcao["golpes"] | funcao["habilidades"]:
            assert nome == to_id(nome)
