"""Testes das telas: cada visão desenha sem erro com os times de exemplo."""

import pytest
from apoio import precisa_dados
from streamlit.testing.v1 import AppTest


def _tela(nome: str, visao: str) -> None:
    from apoio import time_exemplo
    from src.tela_analise import mostrar_analise, mostrar_detalhes
    from src.tela_recomendacoes import mostrar_recomendacoes

    time = [{**membro, "vaga": vaga} for vaga, membro in enumerate(time_exemplo(nome))]
    {"analise": mostrar_analise, "melhorar": mostrar_recomendacoes,
     "detalhes": mostrar_detalhes}[visao](time)


@precisa_dados
@pytest.mark.parametrize("visao", ["analise", "melhorar", "detalhes"])
@pytest.mark.parametrize("nome", ["Meta", "Time com problemas"])
def test_visoes_desenham_sem_erro(nome, visao):
    tela = AppTest.from_function(_tela, args=(nome, visao), default_timeout=60).run()
    assert not tela.exception, [e.value for e in tela.exception]


@precisa_dados
def test_analise_mostra_veredito_alerta_e_proximo_passo():
    tela = AppTest.from_function(_tela, args=("Time com problemas", "analise"), default_timeout=60).run()
    html = " ".join(m.value for m in tela.markdown)
    assert 'class="veredito"' in html and html.count('class="categoria"') == 5
    assert any("Ponto de alerta" in w.value for w in tela.warning)
    assert tela.button(key="ir_para_trocas")


@precisa_dados
def test_time_incompleto_leva_aos_parceiros():
    def tela_incompleta():
        from apoio import time_exemplo
        from src.tela_analise import mostrar_analise
        mostrar_analise(time_exemplo("Meta")[:4])

    tela = AppTest.from_function(tela_incompleta, default_timeout=60).run()
    assert not tela.exception and tela.button(key="ir_para_parceiros")


@precisa_dados
def test_auto_build_monta_todos_sem_repetir_item():
    def tela_montar():
        from src.tela_montar import tela_montar_o_time
        tela_montar_o_time()

    tela = AppTest.from_function(tela_montar, default_timeout=60)
    tela.session_state["especie_0"] = "incineroar"
    tela.session_state["especie_1"] = "rillaboom"
    tela.run()
    next(b for b in tela.button if b.label == "Auto build").click().run()
    assert not tela.exception, [e.value for e in tela.exception]
    itens = [tela.session_state[f"item_{v}_{p}"] for v, p in [(0, "incineroar"), (1, "rillaboom")]]
    assert all(itens) and len(set(itens)) == 2
    assert tela.session_state["golpe_0_0_incineroar"]
