"""Análise do time com Machine Learning (src/modelo_nota.py) e dicas da IA (src/dicas_ia.py)."""

import numpy as np
import pytest
from apoio import precisa_dados, time_exemplo

from src.dicas_ia import dicas_da_ia, respostas_da_ia, texto_do_alerta
from src.modelo_nota import (
    CATEGORIAS, PONTOS, analise_da_ia, avaliar, carregar_modelo, especie_conhecida,
    pesos_em_ordem, pontos_de_analise, sigmoide, situacionais_do_time, time_do_replay,
    treinar, treinar_em_ordem,
)

# ---------------------------------------------------------------------------
# Regressão logística com ordem: não precisa de dados
# ---------------------------------------------------------------------------


def test_pesos_em_ordem():
    pesos = pesos_em_ordem(np.array([0.1, 0.0, 0.2, 0.05, 0.01]), -0.3)
    assert pesos == pytest.approx([0.36, 0.26, 0.26, 0.06, 0.01, -0.3])


def test_logistica_aprende_respeitando_a_ordem():
    """Dados sintéticos: a 3ª coluna é a que mais ajuda, mas a ordem obriga 1ª > 2ª > 3ª > ..."""
    sorteio = np.random.default_rng(0)
    X = sorteio.normal(size=(3000, 6))
    verdade = np.array([0.2, 0.1, 1.5, 0.05, 0.0, -0.8])
    y = (sorteio.random(3000) < sigmoide(X @ verdade)).astype(float)
    pesos = treinar_em_ordem(X, y)
    assert all(pesos[k] >= pesos[k + 1] + 0.01 - 1e-9 for k in range(3))  # cada uma acima da de baixo
    assert pesos[4] >= 0 and pesos[5] < -0.3                                # alerta só tira força
    assert avaliar(y, sigmoide(X @ pesos))["acuracia"] > 0.6


def test_logistica_acha_os_pesos_quando_a_ordem_bate():
    sorteio = np.random.default_rng(1)
    X = sorteio.normal(size=(3000, 6))
    verdade = np.array([1.2, 0.9, 0.6, 0.4, 0.2, -0.5])
    y = (sorteio.random(3000) < sigmoide(X @ verdade)).astype(float)
    pesos = treinar_em_ordem(X, y)
    assert pesos == pytest.approx(verdade, abs=0.2)


def test_avaliar():
    y = np.array([1.0, 0.0, 1.0, 0.0])
    assert avaliar(y, np.array([0.9, 0.1, 0.8, 0.2]))["acuracia"] == 1.0
    assert avaliar(y, np.array([0.5, 0.5, 0.5, 0.5]))["log_loss"] == pytest.approx(np.log(2), abs=1e-3)


# ---------------------------------------------------------------------------
# Pontos de análise e modelo: precisam dos dados
# ---------------------------------------------------------------------------


@precisa_dados
def test_pontos_de_analise_dos_exemplos():
    meta = pontos_de_analise(time_exemplo("Meta"))
    chuva = pontos_de_analise(time_exemplo("Chuva"))
    sol_tr = pontos_de_analise(time_exemplo("Sol + Trick Room"))
    assert list(meta) == list(PONTOS)
    assert 0 <= meta["cobertura_ataque"] <= 1 and 0 <= meta["cobrem_fraquezas"] <= 1
    assert meta["winrate"] == 50.0                # sem tabela de winrate: todo mundo 50%
    assert meta["fake_out"] == -1                 # Psychic Terrain da Indeedee bloqueia o Fake Out
    assert chuva["clima"] >= 1                    # Pelipper + Swift Swim
    assert chuva["fake_out"] == 1                 # Fake Out com quem prepara o campo
    assert sol_tr["trick_room"] >= 1              # lentos com quem usa Trick Room
    assert meta["clima"] == 0                     # sem clima
    assert meta["aparecem_juntos"] > sol_tr["aparecem_juntos"]
    assert pontos_de_analise(time_exemplo("Time com problemas"))["fisicos_demais"] >= 1


@precisa_dados
def test_situacionais_olham_se_o_time_se_beneficia():
    meta = situacionais_do_time(time_exemplo("Meta"))
    assert meta["psychic_terrain"] == ["Indeedee-F"] and meta["valores"]["fake_out"] == -1
    chuva = situacionais_do_time(time_exemplo("Chuva"))
    assert chuva["clima"] == "chuva" and chuva["aproveitam"]


@precisa_dados
def test_time_do_replay_e_formas_de_aparencia():
    assert especie_conhecida("vivillonpokeball") == "vivillon"
    assert especie_conhecida("naoexiste") is None
    time = time_do_replay([
        {"especie": "garchomp", "golpes": ["earthquake"], "item": "garchompite", "habilidade": ""},
        {"especie": "incineroar", "golpes": [], "item": "", "habilidade": ""},
    ])
    assert time[0]["forma"] == "garchompmega"
    assert len(time[0]["golpes"]) == 4 and time[0]["golpes"][0] == "earthquake"


@precisa_dados
def test_treinar_com_batalhas_pequenas():
    meta, problemas = time_exemplo("Meta"), time_exemplo("Time com problemas")

    def revelados(time):
        return [{"especie": m["id"], "golpes": [], "item": "", "habilidade": ""} for m in time]

    batalhas = [{"vencedor": 1 + i % 2, "p1": revelados(meta if i % 2 == 0 else problemas),
                 "p2": revelados(problemas if i % 2 == 0 else meta)} for i in range(40)]
    modelo = treinar(batalhas, rating_minimo=0)  # o Meta sempre vence
    assert modelo["teste"]["acuracia"] == 1.0
    resultado = analise_da_ia(meta, modelo)
    assert resultado["nota"] > analise_da_ia(problemas, modelo)["nota"]
    assert [c["nome"] for c in resultado["categorias"]] == CATEGORIAS


@precisa_dados
def test_modelo_salvo_analisa_os_exemplos():
    modelo = carregar_modelo()
    assert modelo is not None, "rode python -m src.replays e python -m src.modelo_nota"
    assert modelo["batalhas_treino"] > 1000
    resultado = analise_da_ia(time_exemplo("Meta"), modelo)
    assert 0 <= resultado["nota"] <= 10 and 0 < resultado["chance"] < 100
    assert sum(p["impacto"] for p in resultado["pontos"]) == pytest.approx(resultado["forca"], abs=0.01)
    assert all(0 <= c["nota"] <= 10 for c in resultado["categorias"])
    pesos = modelo["pesos"]
    assert all(pesos[k] > pesos[k + 1] for k in range(len(CATEGORIAS) - 1)) and pesos[-1] <= 0


@precisa_dados
def test_dicas_e_respostas_da_ia():
    chuva = analise_da_ia(time_exemplo("Chuva"), carregar_modelo())
    assert all(d["nivel"] in ("ok", "atencao") for d in dicas_da_ia(chuva))
    respostas = respostas_da_ia(chuva)
    assert [r["pergunta"][:5] for r in respostas] == ["Fake ", "Scree", "O cli"]
    assert respostas[0]["efeito"] == 1 and respostas[0]["resposta"].startswith("Sim:")
    assert "aproveitam" in respostas[2]["resposta"] and respostas[2]["efeito"] == 1
    meta = respostas_da_ia(analise_da_ia(time_exemplo("Meta"), carregar_modelo()))
    assert meta[0]["efeito"] == -1 and "Psychic Terrain" in meta[0]["resposta"]
    assert "não coloca clima" in meta[2]["resposta"] and meta[2]["efeito"] == 0


@precisa_dados
def test_alerta_de_fisicos_demais():
    problemas = analise_da_ia(time_exemplo("Time com problemas"), carregar_modelo())
    assert problemas["alerta"]["ativo"] and problemas["alerta"]["impacto"] < 0
    assert texto_do_alerta(problemas["alerta"]).startswith("**Ponto de alerta:**")
    meta = analise_da_ia(time_exemplo("Meta"), carregar_modelo())
    assert not meta["alerta"]["ativo"] and texto_do_alerta(meta["alerta"]) is None
    assert meta["nota"] > problemas["nota"]


