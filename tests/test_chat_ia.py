"""Testes do chat com o agente de IA (sem chamar a API de verdade)."""

import pytest
from streamlit.testing.v1 import AppTest

from src import config
from apoio import precisa_dados

from src.chat_ia import (
    ErroDoChat, chave_da_api, fatos_do_pokemon, montar_mensagens, perguntar, pokemon_citados,
    tabela_de_tipos_em_texto,
)


class RespostaFalsa:
    def __init__(self, status: int, corpo: dict | None = None, texto: str = ""):
        self.status_code, self._corpo, self.text = status, corpo, texto

    def json(self):
        if self._corpo is None:
            raise ValueError("sem json")
        return self._corpo


def _resposta(texto: str) -> RespostaFalsa:
    return RespostaFalsa(200, {"choices": [{"message": {"content": texto}}]})


def test_chave_vem_dos_secrets_ou_do_ambiente(monkeypatch):
    monkeypatch.delenv(config.CHAT_NOME_DA_CHAVE, raising=False)
    assert chave_da_api({}) is None
    assert chave_da_api({config.CHAT_NOME_DA_CHAVE: " abc "}) == "abc"
    monkeypatch.setenv(config.CHAT_NOME_DA_CHAVE, "do-ambiente")
    assert chave_da_api(None) == "do-ambiente"


def test_mensagens_tem_o_papel_do_agente_e_limitam_o_historico():
    historico = [{"role": "user", "content": str(n)} for n in range(30)]
    mensagens = montar_mensagens(historico)
    assert mensagens[0]["role"] == "system" and "português" in mensagens[0]["content"]
    assert "Terastalização" in mensagens[0]["content"]  # conhece as regras do formato
    assert len(mensagens) == 1 + config.CHAT_MAX_MENSAGENS
    assert mensagens[-1]["content"] == "29"


def test_perguntar_manda_a_chave_e_le_a_resposta():
    chamadas = []

    def post(url, json, timeout, headers):
        chamadas.append((url, json, headers))
        return _resposta("  Use Intimidate.  ")

    assert perguntar([{"role": "user", "content": "oi"}], "minha-chave", post=post) == "Use Intimidate."
    url, corpo, headers = chamadas[0]
    assert url == config.CHAT_API_URL and corpo["model"] == config.CHAT_MODELO
    assert headers["Authorization"] == "Bearer minha-chave"


def test_modelo_fora_do_ar_usa_o_reserva():
    modelos = []

    def post(url, json, timeout, headers):
        modelos.append(json["model"])
        if len(modelos) == 1:
            return RespostaFalsa(404, texto='{"error": "The model does not exist"}')
        return _resposta("ok")

    assert perguntar([], "k", post=post) == "ok"
    assert modelos == [config.CHAT_MODELO, config.CHAT_MODELO_RESERVA]


@pytest.mark.parametrize("status, trecho", [(401, "chave"), (429, "limite"), (500, "500")])
def test_erros_viram_mensagens_amigaveis(status, trecho):
    with pytest.raises(ErroDoChat, match=trecho):
        perguntar([], "k", post=lambda *a, **k: RespostaFalsa(status, texto="erro"))


def test_tabela_de_tipos_no_prompt_tem_as_imunidades():
    tabela = tabela_de_tipos_em_texto()
    assert "- Dragão: 2x em Dragão; 0,5x em Aço; 0x/imune em Fada" in tabela
    assert "- Terrestre:" in tabela and "0x/imune em Voador" in tabela
    assert tabela in montar_mensagens([])[0]["content"]


def test_temperatura_baixa_e_modelo_maior():
    corpos = []

    def post(url, json, timeout, headers):
        corpos.append(json)
        return _resposta("ok")

    perguntar([], "k", post=post)
    assert corpos[0]["temperature"] == config.CHAT_TEMPERATURA <= 0.3
    assert corpos[0]["model"] == "openai/gpt-oss-120b"


@precisa_dados
def test_pokemon_citados_e_as_megas_deles():
    citados = pokemon_citados("o garchomp e o Rotom-Wash aguentam? e o xerneas?")
    assert "garchomp" in citados and "rotomwash" in citados
    assert any(pid.startswith("garchompmega") for pid in citados)  # a Mega vem junto
    assert all("xerneas" not in pid for pid in citados)  # não está nos dados da regulamentação
    assert pokemon_citados("oi, tudo bem?") == []


@precisa_dados
def test_fatos_calculados_pela_tabela():
    garchomp = fatos_do_pokemon("garchomp")
    assert "toma 4x de Gelo" in garchomp and "IMUNE (0x) a Elétrico" in garchomp
    assert "Levitate: Terrestre vira 0x" in fatos_do_pokemon("rotomwash")


@precisa_dados
def test_fatos_vao_no_prompt():
    sistema = montar_mensagens([{"role": "user", "content": "Garchomp é fraco a quê?"}])[0]["content"]
    assert "Fatos dos Pokémon citados" in sistema and "toma 4x de Gelo" in sistema


def _so_o_chat():
    from src.tela_chat import mostrar_chat
    mostrar_chat()


def test_chat_sem_chave_explica_como_configurar(monkeypatch):
    monkeypatch.delenv(config.CHAT_NOME_DA_CHAVE, raising=False)
    tela = AppTest.from_function(_so_o_chat).run()
    assert not tela.exception
    assert any("console.groq.com" in i.value for i in tela.info)


def test_chat_responde_com_a_api_falsa(monkeypatch):
    monkeypatch.setenv(config.CHAT_NOME_DA_CHAVE, "chave-de-teste")
    monkeypatch.setattr("requests.post", lambda *a, **k: _resposta("Resposta do agente"))
    tela = AppTest.from_function(_so_o_chat).run()
    tela.chat_input(key="chat_pergunta").set_value("Qual o problema do meu time?").run()
    assert not tela.exception
    historico = tela.session_state["chat_historico"]
    assert [m["role"] for m in historico] == ["user", "assistant"]
    assert historico[1]["content"] == "Resposta do agente"
