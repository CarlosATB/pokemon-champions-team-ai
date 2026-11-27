"""Testes do chat com o agente de IA (sem chamar a API de verdade)."""

import pytest
from streamlit.testing.v1 import AppTest

from src import config
from src.chat_ia import ErroDoChat, chave_da_api, montar_mensagens, perguntar


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
