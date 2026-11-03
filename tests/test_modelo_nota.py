"""Nota do time com Machine Learning (src/modelo_nota.py)."""

import random

import numpy as np
from apoio import precisa_dados, time_exemplo

from src import config
from src.leitor import montar_time
from src.modelo_nota import (
    CARACTERISTICAS, caracteristicas, carregar_modelo, coesao_no_meta, gerar_dataset,
    membro_do_meta, nota_do_time, pool_do_meta, prever, time_aleatorio, time_do_meta,
    treinar, treinar_ridge,
)

pytestmark = precisa_dados


def test_ridge_aprende_uma_reta_conhecida():
    sorteio = np.random.default_rng(0)
    X = sorteio.normal(size=(200, 3))
    y = 2 * X[:, 0] - 3 * X[:, 1] + 5  # a 3ª coluna não importa
    modelo = treinar_ridge(X, y, alpha=0.001)
    assert np.allclose(prever(modelo, X), y, atol=0.01)
    assert abs(modelo["pesos"][2]) < 0.01


def test_caracteristicas_sao_numeros_de_todas_as_chaves():
    numeros = caracteristicas(time_exemplo("Meta"))
    assert list(numeros) == list(CARACTERISTICAS)
    assert all(isinstance(v, float) for v in numeros.values())
    assert numeros["funcao_fake_out"] == 2  # Rillaboom e Incineroar
    assert numeros["sem_ataques"] == 0


def test_time_com_problemas_tem_mais_tipos_perigosos():
    meta = caracteristicas(time_exemplo("Meta"))
    problemas = caracteristicas(time_exemplo("Time com problemas"))
    assert problemas["tipos_perigosos"] > meta["tipos_perigosos"]


def test_coesao_do_meta_maior_que_de_time_aleatorio():
    sorteio = random.Random(1)
    pool = pool_do_meta()
    meta = [coesao_no_meta(montar_time([membro_do_meta(p) for p in time_do_meta(sorteio, pool)]))
            for _ in range(10)]
    aleatorio = [coesao_no_meta(montar_time([membro_do_meta(p) for p in time_aleatorio(sorteio, pool)]))
                 for _ in range(10)]
    assert sum(meta) > sum(aleatorio)


def test_times_gerados_respeitam_as_regras():
    sorteio = random.Random(2)
    pool = pool_do_meta()
    for _ in range(20):
        time = montar_time([membro_do_meta(p) for p in time_do_meta(sorteio, pool)])
        assert len(time) == config.TEAM_SIZE
        assert sum(m["forma"] != m["id"] for m in time) <= 1  # no máximo uma Mega


def test_dataset_tem_os_tres_grupos():
    base = gerar_dataset(times_por_grupo=3, semente=0)
    assert base["X"].shape == (9, len(CARACTERISTICAS))
    assert sorted(set(base["grupos"])) == ["aleatorio", "meta", "perturbado"]


def test_treino_pequeno_ja_supera_chutar_a_media():
    modelo = treinar(times_por_grupo=40, semente=3)
    assert modelo["teste"]["r2"] > modelo["baseline_media"]["r2"]
    assert modelo["coesao_media_por_grupo"]["meta"] > modelo["coesao_media_por_grupo"]["aleatorio"]
    nota = nota_do_time(time_exemplo("Meta"), modelo=modelo)
    assert 0 <= nota["nota"] <= 10
    assert len(nota["contribuicoes"]) == len(CARACTERISTICAS)


def test_modelo_salvo_da_nota_maior_ao_time_do_meta():
    assert carregar_modelo() is not None, "rode python -m src.modelo_nota"
    meta = nota_do_time(time_exemplo("Meta"))
    problemas = nota_do_time(time_exemplo("Time com problemas"))
    assert meta["nota"] > problemas["nota"]
    # A explicação vem do maior impacto para o menor.
    pontos = [abs(c["pontos"]) for c in meta["contribuicoes"]]
    assert pontos == sorted(pontos, reverse=True)
