"""
O chatzinho flutuante no canto inferior direito (em todas as abas do site).

- O botão redondo é um st.popover dentro de um container com key="chat_flutuante";
  o CSS em src/visual.py prende esse container no canto da tela.
- É um @st.fragment: mandar uma mensagem só redesenha o chat, não o site inteiro
  (a análise do time não roda de novo a cada pergunta).
- A conversa fica em st.session_state["chat_historico"].
A lógica (papel do agente e chamada da API) está em src/chat_ia.py.
"""

import streamlit as st

from src import config
from src.chat_ia import ErroDoChat, chave_da_api, montar_mensagens, perguntar

HISTORICO = "chat_historico"
BOAS_VINDAS = ("Oi! Sou o assistente do site. Pergunte sobre Pokémon e duplas (VGC), por exemplo: "
               "*\"O que faz o Trick Room?\"* ou *\"Quem é bom contra Incineroar?\"*")


def _ler_secrets():
    try:
        return st.secrets
    except Exception:
        return None


def _sem_chave() -> None:
    st.info(
        f"O chat precisa de uma chave da API da Groq (grátis). Crie em console.groq.com → "
        f"API Keys e cadastre como `{config.CHAT_NOME_DA_CHAVE}` nos Secrets do Streamlit "
        f"(ou em `.streamlit/secrets.toml` no PC).", icon=":material/key:")


@st.fragment
def mostrar_chat() -> None:
    historico = st.session_state.setdefault(HISTORICO, [])
    with st.container(key="chat_flutuante"):
        with st.popover(":material/chat:"):
            st.markdown("**Agente de IA** · pergunte sobre Pokémon e VGC")
            chave = chave_da_api(_ler_secrets())
            if not chave:
                _sem_chave()
                return
            conversa = st.container(height=360, key="chat_conversa")
            with conversa:
                st.chat_message("assistant").markdown(BOAS_VINDAS)
                for mensagem in historico:
                    st.chat_message(mensagem["role"]).markdown(mensagem["content"])

            pergunta = st.chat_input("Escreva sua pergunta...", key="chat_pergunta")
            if pergunta:
                historico.append({"role": "user", "content": pergunta})
                conversa.chat_message("user").markdown(pergunta)
                with conversa.chat_message("assistant"):
                    with st.spinner("Pensando..."):
                        try:
                            resposta = perguntar(montar_mensagens(historico), chave)
                        except ErroDoChat as erro:
                            historico.pop()  # a pergunta não foi respondida: não entra no histórico
                            st.warning(str(erro), icon=":material/error:")
                            return
                    st.markdown(resposta)
                historico.append({"role": "assistant", "content": resposta})

            if historico:
                st.button("Limpar conversa", key="chat_limpar", icon=":material/delete:",
                          on_click=lambda: st.session_state[HISTORICO].clear(), type="tertiary")
