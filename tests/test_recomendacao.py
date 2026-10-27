"""Sistema de recomendação: testado com os times de exemplo."""

from apoio import precisa_dados, time_exemplo

from src import dados
from src.leitor import time_de_nomes
from src.recomendacao import (
    escolher_quem_sai,
    ler_spread,
    recomendar_time,
    sugerir_parceiros,
    sugerir_substitutos,
)

pytestmark = precisa_dados


def sugestao_de(sugestoes, especie):
    return next(s for s in sugestoes if s["especie"] == especie)


def test_ler_spread():
    assert ler_spread("Adamant:32/32/0/0/2/0") == ("Adamant", "32 HP / 32 Atk / 2 SpD")


def test_sugere_o_que_os_jogadores_mais_usam():
    rillaboom = sugestao_de(recomendar_time(time_exemplo("Meta")), "Rillaboom")
    assert rillaboom["habilidade"]["nome"] == "Grassy Surge"
    assert rillaboom["habilidade"]["voce_usa"]
    assert rillaboom["item"]["melhor"]["nome"] == "Miracle Seed"
    golpes = [g["nome"] for g in rillaboom["golpes"]["lista"][:4]]
    assert "Fake Out" in golpes and "Grassy Glide" in golpes
    assert rillaboom["natureza_evs"]["natureza"]
    assert "dos Rillaboom usam Miracle Seed" in rillaboom["item"]["porque"]


def test_mega_usa_as_estatisticas_da_mega():
    salamence = sugestao_de(recomendar_time(time_exemplo("Meta")), "Salamence")
    assert salamence["nome_nas_estatisticas"] == "Salamence-Mega"
    assert salamence["item"]["melhor"]["nome"] == "Salamencite"
    assert "Mega Evoluir" in salamence["habilidade"]["porque"]


def test_nao_sugere_item_que_outro_ja_usa():
    # Garchomp e Dragonite gostam de Life Orb; no time com problemas o
    # Dragonite já está com ela, então o Garchomp recebe outro item livre.
    sugestoes = recomendar_time(time_exemplo("Time com problemas"))
    garchomp = sugestao_de(sugestoes, "Garchomp")
    assert garchomp["item"]["melhor"]["nome"] != "Life Orb"
    assert "não pode repetir item" in garchomp["item"]["porque"]


def test_time_sem_itens_recebe_itens_diferentes():
    time = time_de_nomes(["Garchomp", "Dragonite", "Rillaboom", "Incineroar", "Kingambit"])
    itens = [s["item"]["melhor"]["id"] for s in recomendar_time(time)]
    assert len(itens) == len(set(itens))


def test_avisa_golpes_pouco_usados():
    salamence = sugestao_de(recomendar_time(time_exemplo("Time com problemas")), "Salamence")
    assert "Roost" in salamence["golpes"]["raros"]


def test_parceiros_por_coocorrencia():
    time = time_de_nomes(["Rillaboom"])
    parceiros = sugerir_parceiros(time)
    nomes = [p["nome"] for p in parceiros]
    assert nomes[0] == "Incineroar"  # o parceiro mais comum do Rillaboom nos dados
    assert parceiros[0]["confianca"] == dados.carregar_uso()["pokemon"]["rillaboom"]["parceiros"]["incineroar"]
    assert all(p["porque"] and p["lift"] > 0 for p in parceiros)


def test_parceiros_nao_repetem_especie_nem_segunda_mega():
    time = time_exemplo("Meta")  # já tem Salamence-Mega
    pokemon = dados.carregar_pokemon()
    especies = {pokemon[m["id"]]["especie_base"] for m in time}
    for parceiro in sugerir_parceiros(time, quantos=20):
        assert pokemon[parceiro["id"]]["especie_base"] not in especies
        assert not pokemon[parceiro["id"]]["mega"]


def test_substituto_cobre_as_fraquezas():
    resultado = sugerir_substitutos(time_exemplo("Time com problemas"))
    assert resultado["fraquezas"]  # time cheio de dragões: Gelo, Fada...
    melhor = resultado["substitutos"][0]
    assert melhor["cobre"]
    assert 0 <= melhor["nota"] <= 100
    assert "resiste a" in melhor["porque"]


def test_quem_sai_e_fraco_aos_problemas_do_time():
    time = time_exemplo("Time com problemas")
    sai, motivo = escolher_quem_sai(time)
    assert sai["especie"] in {"Garchomp", "Salamence", "Dragonite", "Garchomp (2)"}
    assert "Gelo" in motivo


def test_substituto_escolhido_pelo_usuario():
    time = time_exemplo("Chuva")
    sai = next(m for m in time if m["especie"] == "Kingambit")
    resultado = sugerir_substitutos(time, sai)
    assert resultado["sai"] == "Kingambit"
    assert all(s["nome"] != "Kingambit" for s in resultado["substitutos"])


def test_todos_os_exemplos_geram_recomendacoes():
    for nome in ["Meta", "Chuva", "Sol", "Time com problemas"]:
        time = time_exemplo(nome)
        assert all(s["tem_dados"] for s in recomendar_time(time)), nome
        assert sugerir_parceiros(time), nome
        assert sugerir_substitutos(time)["substitutos"], nome
