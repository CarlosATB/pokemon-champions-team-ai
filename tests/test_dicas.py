"""Dicas em texto: testadas com os times de exemplo."""

from apoio import precisa_dados, time_exemplo

from src.analise import analisar
from src.dicas import gerar_dicas
from src.leitor import time_de_nomes

pytestmark = precisa_dados


def dicas_de(time, nivel=None):
    return [d["texto"] for d in gerar_dicas(time, analisar(time)) if nivel in (None, d["nivel"])]


def test_time_com_problemas_recebe_os_alertas_certos():
    alertas = " | ".join(dicas_de(time_exemplo("Time com problemas"), "alerta"))
    assert "dano dobrado de **Gelo** e ninguém resiste" in alertas
    assert "controle de velocidade" in alertas
    assert "proteção" in alertas


def test_time_do_meta_tem_as_funcoes_principais():
    time = time_exemplo("Meta")
    alertas = " | ".join(dicas_de(time, "alerta"))
    assert "controle de velocidade" not in alertas
    assert any(d.startswith("Fake Out:") for d in dicas_de(time, "ok"))


def test_todos_os_exemplos_geram_dicas():
    for nome in ["Meta", "Chuva", "Sol", "Time com problemas"]:
        assert dicas_de(time_exemplo(nome)), nome


def test_time_sem_golpes_nao_reclama_de_funcoes_de_golpe():
    textos = " | ".join(dicas_de(time_de_nomes(["Garchomp", "Dragonite", "Salamence"])))
    assert "controle de velocidade" not in textos
    assert "dano dobrado de **Gelo**" in textos


def test_time_sem_golpes_nao_fala_de_cobertura_ofensiva():
    textos = " | ".join(dicas_de(time_de_nomes(["Beedrill", "Rillaboom"])))
    assert "Cobertura ofensiva" not in textos and "não tem golpe" not in textos
