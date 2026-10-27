"""Opções da tela "Montar o time" e o time montado a partir delas."""

from apoio import precisa_dados

from src.analise import analisar
from src.leitor import montar_time
from src.opcoes import opcoes_de_golpes, opcoes_de_habilidades, opcoes_de_itens
from src.validacao import tem_erro, validar_time

pytestmark = precisa_dados


def test_opcoes_comecam_pelo_mais_usado():
    assert opcoes_de_itens("rillaboom")[0] == "miracleseed"
    assert opcoes_de_habilidades("rillaboom")[0] == "grassysurge"
    assert opcoes_de_golpes("rillaboom")[:2] == ["grassyglide", "fakeout"]


def test_itens_nao_mostram_pedra_mega_de_outro_pokemon():
    itens = opcoes_de_itens("charizard")
    assert "charizarditey" in itens
    assert "salamencite" not in itens
    assert "sitrusberry" in itens


def test_mega_usa_os_golpes_da_forma_normal():
    assert "tailwind" in opcoes_de_golpes("salamencemega")


def test_time_montado_vai_para_a_analise():
    time = montar_time([
        {"especie": "Rillaboom", "item": "Miracle Seed", "habilidade": "Grassy Surge",
         "natureza": "", "golpes": ["Fake Out", "Grassy Glide"]},
        {"especie": "Salamence", "item": "Salamencite", "habilidade": "Intimidate",
         "natureza": "", "golpes": ["Tailwind", "Hyper Voice"]},
    ])
    assert time[1]["forma"] == "salamencemega"
    assert not tem_erro(validar_time(time))
    assert "Rillaboom" in analisar(time)["funcoes"]["fake_out"]
