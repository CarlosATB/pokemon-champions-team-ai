"""Trocar um Pokémon com a IA (src/trocas_ia.py)."""

from apoio import precisa_dados, time_exemplo

from src.modelo_nota import analise_da_ia, carregar_modelo
from src.trocas_ia import membro_candidato, trocas_da_ia


@precisa_dados
def test_ia_escolhe_quem_sai_e_ordena_pelo_ganho():
    time = time_exemplo("Meta")
    resultado = trocas_da_ia(time)
    assert resultado["sai"] in {m["especie"] for m in time}
    assert "A IA testou" in resultado["motivo"]
    ganhos = [s["ganho"] for s in resultado["substitutos"]]
    assert ganhos == sorted(ganhos, reverse=True) and len(ganhos) == 5
    assert "Nota do time:" in resultado["substitutos"][0]["porque"]


@precisa_dados
def test_ganho_e_a_diferenca_de_forca_do_time_com_a_troca():
    time = time_exemplo("Chuva")
    sai = next(m for m in time if m["especie"] == "Kingambit")
    resultado = trocas_da_ia(time, sai)
    assert resultado["sai"] == "Kingambit" and resultado["motivo"] == "Escolhido por você."
    melhor = resultado["substitutos"][0]
    assert all(s["nome"] != "Kingambit" for s in resultado["substitutos"])
    # Refaz a conta: força do time com o substituto − força do time atual.
    resto = [m for m in time if m is not sai]
    novo = analise_da_ia(resto + [membro_candidato(melhor["id"])], carregar_modelo())
    assert abs(novo["forca"] - analise_da_ia(time, carregar_modelo())["forca"] - melhor["ganho"]) < 0.002


@precisa_dados
def test_time_incompleto_fica_com_a_regra():
    assert trocas_da_ia(time_exemplo("Começo de time")) is None
