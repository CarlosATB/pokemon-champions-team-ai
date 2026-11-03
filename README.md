# Pokémon Champions Team AI

IA que analisa times de **Pokémon Champions** no formato de **duplas (VGC)**: aponta fraquezas, checa as funções do time e recomenda habilidades, itens, golpes e parceiros com base em dados reais de uso. Feito em **Python + Streamlit**.

> Trabalho prático da disciplina de Inteligência Artificial (CEUB).
>
> 🌐 **Site:** <https://pokemon-champions-team-ai.streamlit.app/> (Streamlit Community Cloud; atualiza a cada merge na `main`)

---

## O que a IA faz

1. **Sistema de Recomendação** — usa as estatísticas de milhares de batalhas reais (Smogon / Pokémon Showdown). A ideia é a mesma da recomendação de uma loja online: *"quem usa este Pokémon também costuma usar esta habilidade, este item e este parceiro"*. Em **Trocar um Pokémon**, quem decide é a IA da análise: ela testa cada Pokémon do meta no lugar de quem sai e sugere as trocas que mais aumentam a chance de vencer.
2. **Análise do time feita pela IA** — um modelo de **Machine Learning (regressão logística, feita com numpy)** aprendeu com **milhares de batalhas reais do Pokémon Showdown** (replays de jogadores com rating 1200+) quais pontos fazem um time **vencer**. Ele avalia o time em 6 categorias: **cobertura contra o top 10** (ataque e defesa), **controle de velocidade** (breakers rápidos, Trick Room, Tailwind), **sinergia** (aparecem juntos no meta, cobrem as fraquezas um do outro), **Fake Out**, **Screens** e **clima**. Dá uma nota de 0 a 10, responde "Fake Out / Screens / clima ajudam o time?" e mostra tudo em **gráficos** (inclusive os resultados do treinamento). As abas de fraquezas, cobertura, funções de duplas e ameaças do meta continuam como dados de apoio.
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
│   ├── tela_montar.py  # 1. Seu time: 6 cards, dado, ajustes, Importar/Exportar
│   ├── tela_analise.py # 2. Análise da IA: nota, dicas, pontos, gráficos + abas de apoio
│   ├── tela_recomendacoes.py # 3. Recomendações: por Pokémon, parceiros, trocas
│   ├── importar_exportar.py # texto do Showdown <-> cards
│   ├── opcoes.py       # opções dos seletores (ordenadas pelo uso), dado, Pedra Mega
│   ├── visual.py       # cores dos tipos e CSS dos cards
│   ├── validacao.py    # confere as regras do formato (espécie/item repetido, Megas...)
│   ├── analise.py      # fraquezas, cobertura ofensiva, funções e ameaças do meta
│   ├── dicas.py        # transforma a análise em dicas em texto
│   ├── recomendacao.py # habilidade/item/golpes/EVs, parceiros e substitutos (co-ocorrência)
│   ├── replays.py      # baixa e lê batalhas reais (replays) do Pokémon Showdown
│   ├── modelo_nota.py  # Machine Learning: pontos da análise + regressão logística (quem vence?)
│   ├── dicas_ia.py     # dicas e respostas escritas a partir do que o modelo aprendeu
│   ├── trocas_ia.py    # "Trocar um Pokémon": a IA testa cada troca e mede o ganho de força
│   └── times_exemplo.py # times prontos para testes e demonstração
├── data/
│   ├── raw/            # dados baixados (Smogon, PokéAPI)
│   └── processed/      # dados tratados usados pelo app
├── static/sprites/     # imagens dos Pokémon e dos itens (PokéAPI), servidas pelo Streamlit
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

# 5. (Opcional) baixar mais batalhas reais e treinar de novo a IA da análise
python -m src.replays 12000   # baixa até 12.000 batalhas (continua de onde parou)
python -m src.modelo_nota      # treina, avalia e salva o modelo

# 6. Rodar o site
streamlit run app.py

# 7. Rodar os testes
pytest
```

### Como funciona a IA da análise (`src/modelo_nota.py`)

1. **Dados** — 12.000 batalhas reais do formato de duplas do Champions, baixadas dos replays públicos do Pokémon Showdown (`src/replays.py`). Para cada batalha guardamos os 2 times (Pokémon, golpes, item, habilidade) e quem venceu. Usamos as de rating 1200+ (≈ 5.000), onde o time pesa mais que o erro de jogador iniciante.
2. **Pontos da análise (entradas)** — 11 números por time:
   - *Cobertura contra o top 10 mais usados*: ataque (quantos o time acerta com dano dobrado) e defesa (quantos ataques do top 10 alguém resiste).
   - *Controle de velocidade*: breakers rápidos (velocidade ≥ 100 e ataque ≥ 110), Trick Room (lentos com quem usa TR), Tailwind.
   - *Sinergia*: aparecem juntos no meta (parceiros do Smogon) e cobrem as fraquezas um do outro.
   - *Fake Out*, *Screens* (Reflect, Light Screen, Aurora Veil) e *clima* (quem aproveita × quem é prejudicado).
3. **Modelo** — regressão logística com descida do gradiente: recebe a diferença entre os pontos do time 1 e do time 2 e aprende a probabilidade de o time 1 vencer. Os **pesos** dizem se cada ponto ajuda (+) ou atrapalha (−).
4. **Avaliação** — 80% treino / 20% teste e validação cruzada (5 partes): acerta ≈ 53% de quem venceu (chutar dá 50%). É pouco porque **quem joga melhor costuma vencer com qualquer time** — a montagem explica só uma parte do resultado, e o site deixa isso claro.
5. **Uso** — o modelo fica salvo em `data/processed/modelo_nota.json`. Na análise do site aparecem a nota (0 a 10 = mais forte que X% dos times reais), as dicas, as respostas sobre Fake Out/Screens/clima e a aba **Gráficos** (notas por categoria, impacto de cada ponto, seu time × vencedores × perdedores, pesos aprendidos, acurácia e a força dos times reais). A nota aparece com o time completo (6 Pokémon).
6. **Trocar um Pokémon** (`src/trocas_ia.py`) — para cada candidato do meta, a IA monta o time com ele no lugar de quem sai (golpes, item e habilidade mais usados) e calcula a nova força; as sugestões são as de maior ganho, explicadas pelos pontos que mais mudam. Se o usuário não escolhe quem sai, a IA testa trocar cada um e fica com a melhor troca. Com menos de 6 Pokémon, vale a regra antiga (co-ocorrência + fraquezas + funções).

## Fontes de dados

- [Smogon Usage Stats](https://www.smogon.com/stats/) — estatísticas mensais de uso do Pokémon Showdown.
- [PokéAPI](https://pokeapi.co/) — tipos e status base dos Pokémon.
- [Pokémon Showdown](https://github.com/smogon/pokemon-showdown) — Pokémon e Megas legais, golpes, movepool, itens e habilidades do Champions.
- [Replays do Pokémon Showdown](https://replay.pokemonshowdown.com/) — batalhas reais (times e vencedor) usadas para treinar a IA da análise.
## Andamento

O progresso do projeto está em [`CHECKLIST.md`](CHECKLIST.md).

---

*Projeto acadêmico, sem fins comerciais. Pokémon é marca registrada da Nintendo, Creatures Inc. e GAME FREAK inc.*
