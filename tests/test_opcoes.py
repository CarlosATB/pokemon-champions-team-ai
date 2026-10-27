"""Opções da tela "Montar o time" e o time montado a partir delas."""

from apoio import precisa_dados

from src.analise import analisar
from src.leitor import montar_time
from src.opcoes import (
    montagem_recomendada, opcoes_de_golpes, opcoes_de_habilidades, opcoes_de_itens, pedra_da_mega,
)
from src.recomendacao import sugerir_para_pokemon
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


def test_montagem_recomendada_cabe_nos_seletores():
    membro = montar_time([{"especie": "Incineroar", "item": "", "habilidade": "",
                           "natureza": "", "golpes": []}])[0]
    montagem = montagem_recomendada("incineroar", sugerir_para_pokemon(membro))
    assert montagem["item"] in opcoes_de_itens("incineroar")
    assert montagem["habilidade"] == "intimidate"
    assert len(montagem["golpes"]) == 4 and "fakeout" in montagem["golpes"]
    assert all(g in opcoes_de_golpes("incineroar") for g in montagem["golpes"])


def test_montagem_da_mega_nao_troca_a_habilidade():
    # A habilidade da Mega (Adaptability) não é uma opção do Beedrill normal.
    membro = montar_time([{"especie": "Beedrill", "item": "Beedrillite",
                           "habilidade": "", "natureza": "", "golpes": []}])[0]
    montagem = montagem_recomendada("beedrill", sugerir_para_pokemon(membro))
    assert montagem["item"] == "beedrillite" and montagem["habilidade"] is None
    assert "poisonjab" in montagem["golpes"]


def test_mega_so_pode_segurar_a_propria_pedra():
    assert opcoes_de_itens("beedrillmega") == ["beedrillite"]
    assert opcoes_de_itens("aggronmega") == ["aggronite"]
    assert pedra_da_mega("beedrill") is None  # a forma normal escolhe qualquer item
    assert "beedrillite" in opcoes_de_itens("beedrill")
