"""Análise do time com Machine Learning (src/modelo_nota.py) e dicas da IA (src/dicas_ia.py)."""

import numpy as np
import pytest
from apoio import precisa_dados, time_exemplo

from src.dicas_ia import dicas_da_ia, respostas_da_ia
from src.modelo_nota import (
    CATEGORIAS, PONTOS, analise_da_ia, avaliar, carregar_modelo, especie_conhecida,
    pontos_de_analise, sigmoide, time_do_replay, treinar, treinar_logistica,
)

# ---------------------------------------------------------------------------
# Regressão logística: não precisa de dados
# ---------------------------------------------------------------------------


def test_logistica_aprende_o_sinal_dos_pesos():
    """Dados sintéticos: o 1º número ajuda a vencer, o 2º atrapalha, o 3º é ruído."""
    sorteio = np.random.default_rng(0)
    X = sorteio.normal(size=(2000, 3))
    y = (sorteio.random(2000) < sigmoide(2 * X[:, 0] - 1 * X[:, 1])).astype(float)
    pesos = treinar_logistica(X, y)
    assert pesos[0] > 1 and pesos[1] < -0.5 and abs(pesos[2]) < 0.2
    assert avaliar(y, sigmoide(X @ pesos))["acuracia"] > 0.7


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
    assert meta["fake_out"] >= 1
    assert chuva["clima_a_favor"] >= 1          # Pelipper + Swift Swim
    assert sol_tr["trick_room"] >= 1            # lentos com quem usa Trick Room
    assert meta["clima_a_favor"] == meta["clima_contra"] == 0  # sem clima
    assert meta["aparecem_juntos"] > sol_tr["aparecem_juntos"]


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


@precisa_dados
def test_dicas_e_respostas_da_ia():
    resultado = analise_da_ia(time_exemplo("Chuva"), carregar_modelo())
    dicas = dicas_da_ia(resultado)
    assert all(d["nivel"] in ("ok", "atencao") for d in dicas)
    respostas = respostas_da_ia(resultado)
    assert [r["pergunta"][:5] for r in respostas] == ["Fake ", "Scree", "O cli"]
    assert "aproveitam" in respostas[2]["resposta"]  # o time da chuva tem clima
    sem_clima = respostas_da_ia(analise_da_ia(time_exemplo("Meta"), carregar_modelo()))
    assert "não coloca clima" in sem_clima[2]["resposta"] and sem_clima[2]["impacto"] == 0


def _resultado_falso(peso: float, valor: float, impacto: float) -> dict:
    pontos = [{"chave": c, "nome": c, "peso": peso, "valor": valor, "impacto": impacto,
               "media_vencedores": 1.0} for c in ("fake_out", "screens", "clima_a_favor", "clima_contra")]
    return {"pontos": pontos}


def test_respostas_seguem_o_sinal_do_peso():
    # Sem o golpe: a resposta não diz que ele "ajuda" e o ícone fica neutro.
    sem = respostas_da_ia(_resultado_falso(peso=-0.09, valor=0, impacto=0.1))[0]
    assert sem["resposta"].startswith("O time não usa") and sem["impacto"] == 0
    # Com o golpe e peso negativo: prejudica.
    com = respostas_da_ia(_resultado_falso(peso=-0.09, valor=2, impacto=-0.1))[0]
    assert com["resposta"].startswith("Não,") and com["impacto"] < 0
    # Peso negativo e pouco disso: a dica diz "Ter pouco de".
    dica = dicas_da_ia(_resultado_falso(peso=-0.09, valor=0, impacto=0.1))[0]
    assert dica["texto"].startswith("Ter pouco de")
