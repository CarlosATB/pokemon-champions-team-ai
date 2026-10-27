"""Análise do time: fraquezas, cobertura, funções e ameaças."""

from apoio import precisa_dados, time_exemplo

from src.analise import (
    tipos_perigosos,
    analisar, ataques_do_membro, cobertura_ofensiva, dano_recebido, funcoes_do_time, golpes_de_ataque,
    matriz_defensiva, tipos_de_ataque,
)
from src.leitor import ler_time, montar_time, time_de_nomes

pytestmark = precisa_dados


def linha_do_tipo(matriz, tipo):
    return next(linha for linha in matriz if linha["tipo"] == tipo)


def test_habilidade_muda_o_dano_recebido():
    assert dano_recebido("Ground", ["Dragon"], "") == 1
    assert dano_recebido("Ground", ["Dragon"], "levitate") == 0
    assert dano_recebido("Ice", ["Dragon", "Flying"], "thickfat") == 2  # 4x vira 2x


def test_pixilate_transforma_golpe_normal_em_fada():
    assert tipos_de_ataque(["hypervoice"], "pixilate", ["Fairy"]) == {"Fairy"}
    assert tipos_de_ataque(["hypervoice"], "", ["Fairy"]) == {"Normal"}
    # Golpe de status não conta como ataque; sem ataques, usa os próprios tipos.
    assert tipos_de_ataque(["protect"], "", ["Fire", "Dark"]) == {"Fire", "Dark"}


def test_golpes_de_ataque_trazem_nome_e_tipo():
    assert golpes_de_ataque(["poisonjab", "protect", "hypervoice"], "pixilate") == [
        ("Poison Jab", "Poison"), ("Hyper Voice", "Fairy")]


def test_time_de_dragoes_e_fraco_a_gelo():
    gelo = linha_do_tipo(matriz_defensiva(time_exemplo("Time com problemas")), "Ice")
    # Garchomp, Garchomp (2), Salamence (Mega), Dragonite e Rillaboom.
    assert len(gelo["fracos"]) == 5
    assert gelo["resistem"] == [] and gelo["imunes"] == []


def test_mega_usa_os_tipos_da_mega():
    # Charizard é Fogo/Voador (imune a Terra); a Mega X é Fogo/Dragão (toma dobrado).
    normal = ler_time("Charizard @ Sitrus Berry\n- Heat Wave")
    mega_x = ler_time("Charizard @ Charizardite X\n- Heat Wave")
    assert linha_do_tipo(matriz_defensiva(normal), "Ground")["dano"]["Charizard"] == 0
    assert linha_do_tipo(matriz_defensiva(mega_x), "Ground")["dano"]["Charizard"] == 2


def test_cobertura_tem_os_18_tipos():
    cobertura = cobertura_ofensiva(time_exemplo("Meta"))
    assert len(cobertura) == 18
    agua = next(c for c in cobertura if c["tipo"] == "Water")
    assert agua["melhor"] == 2 and "Wood Hammer (Rillaboom)" in agua["quem"]


def test_cobertura_usa_so_os_golpes_escolhidos():
    beedrill = {"especie": "Beedrill", "item": "Beedrillite", "habilidade": "", "golpes": []}
    # Sem golpes: ninguém acerta nada (antes usava os tipos do Pokémon).
    sem_golpes = analisar(montar_time([beedrill]))
    assert all(c["melhor"] == 0 and c["quem"] == [] for c in sem_golpes["cobertura"])
    assert sem_golpes["sem_ataques"] == ["Beedrill"]
    # Com Poison Jab: dano dobrado em Planta, mostrando o golpe e quem usa.
    com_golpe = analisar(montar_time([{**beedrill, "golpes": ["Poison Jab", "Protect"]}]))
    planta = next(c for c in com_golpe["cobertura"] if c["tipo"] == "Grass")
    assert planta["melhor"] == 2 and planta["quem"] == ["Poison Jab (Beedrill)"]
    assert com_golpe["sem_ataques"] == []


def test_funcoes_de_duplas():
    funcoes = funcoes_do_time(time_exemplo("Meta"))
    assert funcoes["fake_out"] == ["Rillaboom", "Incineroar"]
    assert funcoes["redirecionamento"] == ["Indeedee-F"]
    # Salamence Mega troca Intimidate por Aerilate.
    assert funcoes["intimidate"] == ["Incineroar"]


def test_ameacas_ordenadas_pela_nota():
    ameacas = analisar(time_exemplo("Time com problemas"))["ameacas"]
    assert 1 <= len(ameacas) <= 5
    notas = [a["nota"] for a in ameacas]
    assert notas == sorted(notas, reverse=True) and min(notas) > 0
    assert "Milotic" in [a["nome"] for a in ameacas]  # Gelo + Água contra dragões


def test_ameacas_supoem_os_golpes_mais_usados_de_quem_nao_tem_golpes():
    beedrill = {"especie": "Beedrill", "item": "Beedrillite", "habilidade": "",
                "natureza": "", "golpes": []}
    # Sem golpes: os mais usados pelo Beedrill-Mega (Drill Run é de Terra), não só os tipos dele.
    assert "Ground" in ataques_do_membro(montar_time([beedrill])[0])
    # Com golpes escolhidos, valem os golpes escolhidos.
    com_golpe = montar_time([{**beedrill, "golpes": ["Poison Jab"]}])[0]
    assert ataques_do_membro(com_golpe) == {"Poison"}


def test_pokemon_desconhecido_fica_de_fora():
    analise = analisar(time_de_nomes(["Rillaboom", "Pokémon Inventado"]))
    assert list(linha_do_tipo(analise["defesa"], "Fire")["dano"]) == ["Rillaboom"]


def test_tipos_perigosos():
    perigosos = tipos_perigosos(analisar(time_exemplo("Time com problemas")))
    tipos = [p["tipo"] for p in perigosos]
    assert tipos[0] == "Ice"  # 4 dragões/voadores fracos a Gelo
    assert all(p["fracos"] >= 2 and p["fracos"] > p["seguram"] for p in perigosos)
