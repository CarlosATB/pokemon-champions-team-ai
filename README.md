# Pokémon Champions Team AI

IA que analisa times de **Pokémon Champions** no formato de **duplas (VGC)**: aponta fraquezas, checa as funções do time e recomenda habilidades, itens, golpes e parceiros com base em dados reais de uso. Feito em **Python + Streamlit**.

> Trabalho prático da disciplina de Inteligência Artificial (CEUB).
>
> 🌐 **Site:** <https://pokemon-champions-team-ai.streamlit.app/> (Streamlit Community Cloud; atualiza a cada merge na `main`)

---

## O que a IA faz

1. **Sistema de Recomendação** — usa as estatísticas de milhares de batalhas reais (Smogon / Pokémon Showdown). A ideia é a mesma da recomendação de uma loja online: *"quem usa este Pokémon também costuma usar esta habilidade, este item e este parceiro"*.
2. **Análise do time** — mostra as fraquezas e resistências por tipo, a cobertura ofensiva e se o time tem as funções essenciais de duplas (controle de velocidade, Fake Out, Intimidate, redirecionamento, proteção).
3. **Algoritmo Genético** *(opcional)* — testa trocas no time e vai "evoluindo" para versões com melhor cobertura e sinergia.

Cada sugestão vem com a explicação do **porquê**.

## Formato considerado

- Pokémon Champions, duplas, nível 50 — leva 6 e escolhe 4.
- Não pode repetir espécie nem item; uma Mega Evolução por batalha; sem Tera.
- A regulamentação atual fica configurada em [`src/config.py`](src/config.py). Quando ela mudar, basta atualizar esse arquivo.

## Estrutura do projeto

```
pokemon-champions-team-ai/
├── app.py              # interface (Streamlit): 1. Seu time, 2. Análise, 3. Recomendações
├── .streamlit/config.toml # tema escuro
├── src/
│   ├── config.py       # regulamentação, regras do formato e fontes de dados
│   ├── baixar_dados.py # baixa os dados (Showdown, PokéAPI, Smogon) e gera o cache
│   ├── dados.py        # lê o cache em JSON (usado pelo resto do projeto)
│   ├── nomes.py        # padroniza os nomes entre as fontes
│   ├── tipos.py        # tabela de efetividade de tipos 18 × 18
│   ├── funcoes_duplas.py # golpes/habilidades de cada função de duplas
│   ├── leitor.py       # lê o time no formato do Showdown (botão Export)
│   ├── tela_montar.py  # tela "Montar o time": 6 cards, dado, ajustes, Importar/Exportar
│   ├── importar_exportar.py # texto do Showdown <-> cards
│   ├── opcoes.py       # opções dos seletores (ordenadas pelo uso), dado, Pedra Mega
│   ├── visual.py       # cores dos tipos e CSS dos cards
│   ├── validacao.py    # confere as regras do formato (espécie/item repetido, Megas...)
│   ├── analise.py      # fraquezas, cobertura ofensiva, funções e ameaças do meta
│   ├── dicas.py        # transforma a análise em dicas em texto
│   ├── recomendacao.py # habilidade/item/golpes/EVs, parceiros e substitutos (co-ocorrência)
│   └── times_exemplo.py # times prontos para testes e demonstração
├── data/
│   ├── raw/            # dados baixados (Smogon, PokéAPI)
│   ├── processed/      # dados tratados usados pelo app
│   └── sprites/        # imagens dos Pokémon e dos itens (PokéAPI)
├── tests/              # testes automatizados
├── requirements.txt
└── CHECKLIST.md        # acompanhamento do projeto
```

## Como rodar localmente

```bash
# 1. Clonar o repositório
git clone https://github.com/CarlosATB/pokemon-champions-team-ai.git
cd pokemon-champions-team-ai

# 2. (Opcional) criar um ambiente virtual
python -m venv .venv
# Windows: .venv\Scripts\activate   |   Linux/Mac: source .venv/bin/activate

# 3. Instalar as dependências
pip install -r requirements.txt

# 4. (Só quando mudar a regulamentação/mês) baixar os dados
python -m src.baixar_dados

# 5. Rodar o site
streamlit run app.py

# 6. Rodar os testes
pytest
```

## Fontes de dados

- [Smogon Usage Stats](https://www.smogon.com/stats/) — estatísticas mensais de uso do Pokémon Showdown.
- [PokéAPI](https://pokeapi.co/) — tipos e status base dos Pokémon.
- [Pokémon Showdown](https://github.com/smogon/pokemon-showdown) — Pokémon e Megas legais, golpes, movepool, itens e habilidades do Champions.

## Andamento

O progresso do projeto está em [`CHECKLIST.md`](CHECKLIST.md).

---

*Projeto acadêmico, sem fins comerciais. Pokémon é marca registrada da Nintendo, Creatures Inc. e GAME FREAK inc.*
