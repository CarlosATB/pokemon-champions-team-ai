"""Botões Importar e Exportar da tela "Montar o time"."""

import random

from apoio import precisa_dados

from src import config, dados
from src.importar_exportar import exportar, importar
from src.leitor import ler_time
from src.opcoes import pokemon_aleatorio
from src.times_exemplo import TIMES_EXEMPLO

pytestmark = precisa_dados


def test_importar_preenche_os_cards_com_ids():
    cards, avisos = importar(
        "Incineroar @ Sitrus Berry\nAbility: Intimidate\nLevel: 50\n"
        "EVs: 32 HP / 2 Atk / 32 SpD\nCareful Nature\n- Fake Out\n- Parting Shot\n")
    assert avisos == []
    assert cards == [{"pokemon": "incineroar", "item": "sitrusberry", "habilidade": "intimidate",
                      "golpes": ["fakeout", "partingshot"], "natureza": "Careful",
                      "evs": {"HP": 32, "Atk": 2, "SpD": 32}}]


def test_importar_avisa_o_que_ficou_de_fora():
    cards, avisos = importar("Incinerar @ Sitrus Berry\n- Fake Out\n\n"
                             "Rillaboom @ Bolinha\nAbility: Levitate\n- Fake Out\n- Surf\n")
    assert [c["pokemon"] for c in cards] == ["rillaboom"]
    assert cards[0]["item"] is None and cards[0]["golpes"] == ["fakeout"]
    texto = " ".join(avisos)
    assert 'Você quis dizer "Incineroar"?' in texto
    assert "Bolinha" in texto and "Levitate" in texto and "Surf" in texto


def test_todos_os_times_de_exemplo_importam():
    for nome, texto in TIMES_EXEMPLO.items():
        cards, _ = importar(texto)
        assert len(cards) == config.TEAM_SIZE, nome


def test_exportar_e_importar_de_novo_da_o_mesmo_time():
    cards, _ = importar(TIMES_EXEMPLO["Meta (Rillaboom + Incineroar)"])
    assert importar(exportar(cards))[0] == cards


def test_exportar_mega_sai_como_forma_normal_com_a_pedra():
    texto = exportar([{"pokemon": "beedrillmega", "item": "beedrillite",
                       "habilidade": "adaptability", "golpes": ["protect"],
                       "natureza": "Jolly", "evs": {"Atk": 32, "Spe": 32}}])
    primeira_linha, habilidade = texto.splitlines()[:2]
    assert primeira_linha == "Beedrill @ Beedrillite"
    assert habilidade != "Ability: Adaptability"
    assert "EVs: 32 Atk / 32 Spe" in texto and "Jolly Nature" in texto
    assert ler_time(texto)[0]["forma"] == "beedrillmega"  # a análise ainda vê a Mega


def test_dado_nao_repete_especie_nem_segunda_mega():
    time = ["rillaboom", "salamencemega"]
    for semente in range(30):
        sorteado = pokemon_aleatorio(time, random.Random(semente))
        assert sorteado not in ("rillaboom", "salamence", "salamencemega")
        assert not dados.carregar_pokemon()[sorteado]["mega"]
