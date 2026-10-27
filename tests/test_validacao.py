"""Validação das regras do formato."""

from apoio import precisa_dados, time_exemplo

from src.leitor import ler_time
from src.validacao import tem_erro, validar_time

pytestmark = precisa_dados


def mensagens(time):
    return [p["mensagem"] for p in validar_time(time)]


def test_times_do_meta_sao_validos():
    for nome in ["Meta", "Chuva", "Sol"]:
        assert validar_time(time_exemplo(nome)) == [], nome


def test_time_com_problemas():
    problemas = validar_time(time_exemplo("Time com problemas"))
    texto = " | ".join(p["mensagem"] for p in problemas)
    assert tem_erro(problemas)
    assert "Espécie repetida" in texto
    assert "Item repetido" in texto and "Life Orb" in texto
    assert "2 Megas" in texto


def test_nome_errado_sugere_o_certo():
    (mensagem,) = [m for m in mensagens(ler_time("Incinerar @ Sitrus Berry\n- Fake Out"))
                   if "reconhecido" in m]
    assert "Incineroar" in mensagem


def test_mega_e_forma_normal_contam_como_mesma_especie():
    time = ler_time("Charizard @ Charizardite Y\n- Heat Wave\n\nCharizard-Mega-X\n- Flare Blitz")
    assert any("Espécie repetida" in m for m in mensagens(time))


def test_item_fora_do_jogo_e_golpes_demais():
    time = ler_time("Incineroar @ Eviolite\n- Fake Out\n- Protect\n- Flare Blitz\n"
                    "- Parting Shot\n- Snarl")
    texto = " | ".join(mensagens(time))
    assert "Eviolite" in texto
    assert "5 golpes" in texto


def test_golpe_que_o_pokemon_nao_aprende():
    time = ler_time("Incineroar @ Sitrus Berry\n- Surf")
    assert any("não aprende Surf" in m for m in mensagens(time))
