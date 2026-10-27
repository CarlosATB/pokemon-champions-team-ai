# CHECKLIST — Pokémon Champions Team AI

> Arquivo único do projeto: instruções do agente de acompanhamento, conceito do trabalho, decisões tomadas e checklist do que foi feito e do que falta.
> Repositório: [`CarlosATB/pokemon-champions-team-ai`](https://github.com/CarlosATB/pokemon-champions-team-ai)

---

## PARTE A — Instruções para o agente de acompanhamento

Você é o **agente de acompanhamento** do projeto. Sua função é saber, a qualquer momento, em que ponto o projeto está e qual é o próximo passo. Você não precisa de nenhuma explicação extra: tudo o que precisa está neste arquivo.

**Toda vez que for chamado:**

1. Leia este arquivo inteiro (conceito, decisões e checklist).
2. Analise o estado real do repositório `pokemon-champions-team-ai`: arquivos, commits recentes, branches e Pull Requests abertos. Se o repositório ainda não estiver conectado, peça ao usuário o nome completo (`usuario/pokemon-champions-team-ai`).
3. Compare o que existe com a checklist (Parte C):
   - Marque `[x]` só o que estiver **realmente pronto e funcionando**. Sempre que possível, rode o código ou os testes para confirmar. Código que existe mas não roda não conta como feito.
   - Marque `[~]` o que estiver começado mas incompleto, com uma nota curta do que falta.
   - Se surgir uma tarefa necessária que não está na lista, adicione na fase correta.
4. Atualize o **Registro de progresso** (Parte D) com a data e um resumo de 1 a 3 linhas.
5. Responda ao usuário, em português, com:
   - **Status geral:** fase atual e porcentagem aproximada da checklist concluída;
   - **O que mudou** desde o último registro;
   - **Próximos 1 a 3 passos**, em ordem, com o arquivo/módulo envolvido;
   - **Bloqueios ou riscos** (ex.: prazo apertado, dado faltando, algo quebrado no site).

**Regras:**
- Não mude o conceito nem as decisões (Parte B) sem o usuário pedir. Se achar que algo deveria mudar, sugira e espere a resposta.
- Siga a ordem das fases. A Fase 6 (algoritmo genético) só começa se as Fases 1 a 5 estiverem prontas.
- Lembre que o professor avalia **intuição, código e funcionamento**, e que os dois integrantes precisam conseguir explicar tudo ao vivo. Se uma parte do código estiver difícil de explicar, sinalize.
- Se for pedido para programar, o Claude pode programar à vontade; o objetivo é ter a IA com o site funcionando.
- Mantenha este arquivo atualizado também dentro do repositório (`CHECKLIST.md` na raiz).

---

## PARTE B — Conceito do trabalho e decisões

### B1. O trabalho da faculdade

Trabalho prático da disciplina de Inteligência Artificial (CEUB): desenvolver um **protótipo funcional** de uma aplicação de IA.

Na apresentação (ao vivo, **sem slides**), o grupo precisa mostrar:
1. **Intuição** — qual problema resolve, como a IA entra nele e a lógica do algoritmo, em nível conceitual, sem se aprofundar na matemática.
2. **Código** — trechos mais relevantes, estrutura, bibliotecas e como as partes se conectam.
3. **Funcionamento** — demonstração prática, resultados e limitações; a turma pode interagir.

Clareza e simplicidade valem mais que complexidade. O link do GitHub deve ser entregue como tarefa.

- **Grupo:** 2 pessoas (o usuário + 1). Sem divisão fixa de tarefas.
- **Nível de Python:** intermediário.
- **Prazo:** começo de dezembro de 2026 (a data 23/06 do enunciado está errada; confirmar com o professor).

### B2. A ideia

Uma IA que recebe um time Pokémon montado pelo usuário e:
- aponta fraquezas e onde o time pode melhorar;
- sugere habilidades, itens, golpes e parceiros para cada Pokémon;
- explica **por que** está sugerindo cada coisa.

A IA precisa usar algoritmos que o grupo consiga explicar. **Não** é "mandar o time para um chatbot".

### B3. Formato do jogo: Pokémon Champions, duplas (VGC)

- Nível 50; leva 6 e escolhe 4.
- Não pode repetir espécie nem item no time.
- Só uma Mega Evolução por batalha. Não existe Tera.
- Golpes vêm do movepool do Champions (não do Scarlet/Violet).
- As regulamentações mudam com frequência (ex.: M-B → M-C em 9/set/2026). **A regulamentação deve ser configurável** num único lugar do código.

### B4. Os módulos de IA (e a intuição de cada um)

1. **Sistema de Recomendação (principal)** — usa estatísticas reais de milhares de batalhas. Intuição: "quem usa X também costuma usar Y", igual à recomendação da Amazon. Sugere habilidade, item, golpes, natureza/EVs e parceiros com base na frequência de uso e na co-ocorrência entre Pokémon.
2. **Análise do time** — combina regras e dados:
   - fraquezas e resistências por tipo ("4 de 6 tomam dano dobrado de Gelo e ninguém resiste");
   - cobertura ofensiva;
   - **funções de duplas:** controle de velocidade (Tailwind, Trick Room, Icy Wind), Fake Out, Intimidate, redirecionamento (Follow Me, Rage Powder), golpes que acertam os dois alvos, proteção (Protect, Wide Guard);
   - ameaças do meta: os Pokémon mais usados que o time tem dificuldade de enfrentar;
   - validação das regras do formato.
3. **Algoritmo Genético (opcional)** — "evolui" o time testando trocas e mantendo as melhores, como seleção natural, para melhorar cobertura e sinergia.

### B5. Tecnologias e dados

- **Python** + **Streamlit** (interface).
- **Hospedagem:** Streamlit Community Cloud — grátis, publica direto do repositório **público** no GitHub e atualiza a cada push. (GitHub Pages não roda Streamlit.) O app "dorme" após 12 h sem acesso: abrir antes da apresentação.
- **Dados de uso:** estatísticas mensais do Smogon/Pokémon Showdown para Champions VGC (formato `gen9championsvgc...` da regulamentação atual).
- **Dados base:** PokéAPI (tipos e status base) + tabela de tipos.
- **Lista de legais:** Pokémon Showdown (mod da regulamentação, ex.: `champions`) — define quais Pokémon e Megas são permitidos.
- Existem sites parecidos (PokeTools, Pikalytics); na apresentação, deixar claro que a lógica foi construída pelo grupo.
- Sem skills extras instaladas (decidido).

### B6. Fluxo no GitHub

- `main` sempre com uma versão que funciona.
- Trabalho em branches por módulo, entregue via Pull Request; o usuário revisa ou pede o merge.
- Sem merges automáticos/agendados.
- Os dois integrantes devem entender todo o código, já que a apresentação é ao vivo.

---

## PARTE C — Checklist

Legenda: `[ ]` a fazer · `[~]` em andamento · `[x]` feito e funcionando

### Fase 0 — Preparação
- [x] Repositório `pokemon-champions-team-ai` criado (público) e conectado ao Claude
- [x] Estrutura de pastas criada (`data/raw`, `data/processed`, `src/`, `tests/`, `app.py`)
- [x] `requirements.txt` com as dependências (streamlit, pandas, requests, pytest)
- [x] `README.md` inicial — com o link do site
- [x] `CHECKLIST.md` (este arquivo) dentro do repositório
- [x] Arquivo de configuração com a regulamentação/formato atual num só lugar (`src/config.py`)
- [x] Conta no Streamlit Community Cloud ligada ao GitHub
- [ ] Confirmar a data de entrega com o professor
- [~] Confirmar qual regulamentação do Champions usar — configurado M-C (`gen9championsvgc2026regmc`, dados de 2026-09), válida até 2/dez/2026; conferir se surge uma nova antes da entrega

### Fase 1 — Dados
- [x] Script que baixa as estatísticas do Smogon (Champions VGC) do mês mais recente — `data/processed/uso.json` (2026-09, 1.631.943 batalhas, 316 Pokémon). Rodar no PC: a nuvem não acessa smogon.com
- [x] Script que baixa tipos e status base da PokéAPI — `data/processed/pokemon.json` (349 Pokémon/formas)
- [x] Tabela de efetividade de tipos (18×18) — `src/tipos.py`, conferida com a tabela do Showdown
- [x] Lista de Pokémon e Megas legais na regulamentação — `data/processed/legais.json` (349, sendo 80 Megas), tirada do mod `champions` do Pokémon Showdown
- [x] Padronização de nomes entre as fontes (Smogon × PokéAPI, formas e Megas) — `src/nomes.py` (id + 23 exceções da PokéAPI); todos os nomes do Smogon batem com os legais
- [x] Listas de golpes/habilidades por função de duplas (speed control, Fake Out, redirecionamento etc.) — `src/funcoes_duplas.py`
- [x] Dados salvos localmente (cache em JSON) para o site não depender de download ao vivo — `legais.json`, `pokemon.json` e `uso.json`
- [x] Testes básicos: dados carregam e nomes batem — 20 passando
- [x] Movepool do Champions (learnsets do Showdown) para validar golpes — `data/processed/movepool.json` (257 Pokémon), mais `golpes.json` (510 golpes: tipo, categoria, poder, alvo) e `itens.json` (166 itens legais, 80 Pedras Mega). Baixados com `python -m src.baixar_dados golpes` (funciona da nuvem: só usa o GitHub do Showdown)

### Fase 2 — Análise do time
- [x] Leitura do time (colar no formato export do Showdown e/ou escolher na lista) — `src/leitor.py`; Pedra Mega vira a forma Mega; aceita apelido/gênero
- [x] Validação das regras (espécie/item repetido, Pokémon fora da regulamentação, aviso de várias Megas) — `src/validacao.py`; também item fora do jogo, mais de 4 golpes, golpe que o Pokémon não aprende, nome errado com sugestão
- [x] Matriz de fraquezas e resistências do time — `src/analise.py`; conta habilidades (Levitate, Flash Fire, Thick Fat...) e tipos da Mega
- [x] Cobertura ofensiva (quais tipos o time não acerta bem) — usa os golpes de ataque (Pixilate/Aerilate mudam o tipo); sem golpes, usa os tipos do próprio Pokémon
- [x] Checagem de funções de duplas — `funcoes_do_time`, com as listas de `src/funcoes_duplas.py`
- [x] Ameaças do meta: top Pokémon mais usados contra o time — entre os 30 mais usados, nota = quantos do time ele acerta com dano dobrado − quantos do time o acertam
- [x] Geração de dicas em texto claro ("seu time não tem controle de velocidade") — `src/dicas.py` (regras SE/ENTÃO, níveis alerta/atenção/ok)
- [x] Testes com 3 a 5 times de exemplo — 4 times em `src/times_exemplo.py` (3 do meta + 1 com problemas de propósito); 48 testes passando
- [x] Análise ligada no `app.py` (colar/escolher time, erros, dicas e 4 abas de tabelas) — adiantamento da Fase 4

### Fase 3 — Sistema de Recomendação
- [x] Sugestão de habilidade, item, golpes e natureza/EVs por Pokémon (por frequência de uso) — `src/recomendacao.py` (`sugerir_para_pokemon`); Mega usa as estatísticas da Mega; avisa golpes que menos de 5% usam. Nomes das habilidades em `data/processed/habilidades.json` (Showdown)
- [x] Respeitar a regra de item único ao sugerir itens — `recomendar_time`: sugere o item mais usado que está livre e reserva para os próximos
- [x] Sugestão de parceiros pela co-ocorrência (teammates) — `sugerir_parceiros`: nota = confiança média; mostra suporte e lift (regras de associação). Não repete espécie nem sugere 2ª Mega
- [x] Pontuação para sugerir substitutos: combina co-ocorrência + cobrir as fraquezas encontradas na Fase 2 — `sugerir_substitutos`: nota = 50% parceria + 50% fraquezas que resiste; a IA escolhe quem sai (ou o usuário escolhe no site)
- [x] Explicação do porquê de cada sugestão — campo `porque` em todas as sugestões
- [x] Testes com os times de exemplo — `tests/test_recomendacao.py` (12 testes); 61 testes passando no total
- [x] Recomendações ligadas no `app.py` (seção "3. Recomendações": Por Pokémon, Parceiros, Trocar um Pokémon) — adiantamento da Fase 4

### Fase 3.1 — Montar o time (item, habilidade e golpes)
- [x] Aba "Escolher da lista" renomeada para "Montar o time" e colocada antes de "Colar do Showdown"
- [x] 6 cards (2×3): Pokémon (com os tipos), item, habilidade e 4 golpes (com o tipo de cada golpe)
- [x] Opções ordenadas pelo uso (`src/opcoes.py`); golpes do movepool do Champions; sem Pedra Mega de outro Pokémon
- [x] Time montado vai para a análise e as recomendações (`leitor.montar_time`)
- [x] Testes — `tests/test_opcoes.py` (4 testes); 65 passando no total

### Fase 3.2 — Cobertura ofensiva pelos golpes
- [x] A cobertura ofensiva usa só os golpes de ataque escolhidos (antes, sem golpes, usava os tipos do próprio Pokémon)
- [x] A tabela mostra o golpe e quem usa (ex.: Planta — 2x — Poison Jab (Beedrill))
- [x] Pokémon sem golpes de ataque não entra na conta e aparece num aviso; sem nenhum golpe no time, as dicas de cobertura não aparecem
- [x] Botão "Montar com esta recomendação" em Recomendações → Por Pokémon: preenche o card com o item, a habilidade e os 4 golpes mais usados (`opcoes.montagem_recomendada`); só para o time da aba "Montar o time"
- [x] Ameaças do meta: um Pokémon do time sem golpes de ataque conta com os golpes mais usados com ele (antes, com os próprios tipos)
- [x] Escolher uma Mega (ex.: Beedrill-Mega, Aggron-Mega) já trava o item na Pedra Mega dela (`opcoes.pedra_da_mega`)
- [x] Trocar um Pokémon: a nota do substituto também conta as funções de duplas que faltam (40% parceria + 30% fraquezas + 30% funções); pelo menos 1 dos 5 traz cada função essencial que falta; o "Por quê" explica em frases (o que traz, o que resiste, com quem combina)
- [x] Testes — 8 novos (`test_analise.py`, `test_dicas.py`, `test_opcoes.py` e `test_recomendacao.py`); 73 passando no total

### Fase 4 — Interface (Streamlit)
- [x] Tela de entrada do time — **4.1**: "Montar o time" é a única tela (`src/tela_montar.py`); 6 cards (2×3) no estilo do teambuilder: Pokémon no topo, imagem com os tipos (etiquetas coloridas) ao lado, item com ícone embaixo, 4 golpes (com etiqueta do tipo) e habilidade à direita; tema escuro (`.streamlit/config.toml`, `src/visual.py`)
- [x] Imagens dos Pokémon (349) e ícones dos itens (165) salvos em `data/sprites/` (`python -m src.baixar_dados imagens`, PokéAPI pelo GitHub): o site não depende de internet para mostrar as imagens
- [x] Botão do dado (Pokémon aleatório entre os 60 mais usados, já montado com a recomendação, sem repetir espécie nem 2ª Mega) e botão de ajustes (natureza e pontos de status, até 32 cada e 66 no total)
- [x] Botão para importar/exportar time no formato do Showdown — **4.1**: aba "Colar do Showdown" removida; Importar (cola o texto ou carrega um time de exemplo → preenche os cards, avisa o que não entrou) e Exportar (texto pronto para o Showdown; Mega sai como forma normal + Pedra Mega) — `src/importar_exportar.py`
- [x] "Montar com esta recomendação" também preenche natureza e pontos de status
- [x] Testes — `tests/test_importar_exportar.py` (6 testes) + EVs no leitor; 79 passando
- [x] Exibição da análise — **4.2** (`src/tela_analise.py`): erros das regras numa caixa só; 4 números de resumo (tipos perigosos, tipos que acerta forte, funções, maior ameaça); dicas em 3 colunas (problemas / pode melhorar / pontos fortes); tipos perigosos e tipos sem dano dobrado em etiquetas coloridas; funções de duplas em cartões ✅/❌; ameaças do meta em cartões com imagem
- [x] Exibição das recomendações — **4.2** (`src/tela_recomendacoes.py`): uma aba por Pokémon com a imagem; parceiros em cartões com botão "Adicionar ao time" (primeiro card vazio, já montado); substitutos em cartões com botão "Colocar no lugar de X"
- [x] Times de exemplo prontos para a demonstração — **4.2**: os 3 do meta agora têm EVs (os mais usados); novo "Começo de time (3 Pokémon)" para mostrar a IA completando o time; todos importam sem avisos (teste)
- [x] Mensagens de erro amigáveis — o Importar avisa em português ("Você quis dizer...?"); na análise, erros agrupados numa caixa e "time incompleto" virou informação (azul), não aviso — **4.2**
- [x] "Sobre os dados": tabela dos 20 mais usados com nomes bonitos (antes mostrava ids como `grassysurge`) — **4.2**
- [x] Testes — **4.2**: `tipos_perigosos`, time incompleto e times de exemplo; 81 passando

### Fase 5 — Publicação e testes
- [x] Deploy no Streamlit Community Cloud funcionando — https://pokemon-champions-team-ai.streamlit.app/ (atualiza a cada merge na `main`)
- [x] Link do site no README
- [ ] Teste completo no site publicado (não só local)
- [ ] Revisão do código: nomes claros, comentários nos trechos que serão mostrados

### Fase 6 — Algoritmo Genético (opcional)
- [ ] Função de "nota" do time (cobertura + funções + sinergia)
- [ ] Geração, cruzamento e mutação de times
- [ ] Integração na interface ("sugerir trocas")

### Fase 7 — Apresentação
- [ ] Roteiro da **intuição** (problema, por que IA, lógica de cada módulo)
- [ ] Lista dos trechos de **código** a mostrar e em que ordem
- [ ] Roteiro da **demonstração** (times de exemplo + time da turma ao vivo)
- [ ] Lista de **limitações** (dados mensais, não simula batalha, depende do meta)
- [ ] Ensaio completo com os 2 integrantes
- [ ] Link do GitHub entregue na tarefa da faculdade

---

## PARTE D — Registro de progresso

| Data | Resumo |
|---|---|
| 27/10/2026 | Projeto planejado: conceito, formato (Champions duplas), módulos, fontes de dados, Streamlit Cloud e nome do repositório definidos. Nenhum código ainda. |
| 27/10/2026 | Fase 0 quase concluída: estrutura de pastas, `src/config.py` (Reg. M-C), `app.py` inicial, README, testes (4 passando). Falta: conta no Streamlit Cloud e confirmar prazo. |
| 27/10/2026 | Fase 0 mergeada (PR #1). Fase 1 em andamento (branch `fase-1-dados`): script de download, tabela de tipos, lista de legais (349), dados da PokéAPI, nomes, funções de duplas e testes (19 passando). Estatísticas do Smogon baixadas no PC do Carlos (2026-09, 1,6 mi de batalhas, 316 Pokémon); 20 testes passando. Falta só o movepool do Champions (item novo). |
| 27/10/2026 | Fase 1 mergeada (PR #2). Fase 2 feita na branch `fase-2-analise`: golpes/movepool/itens do Champions, leitor do time do Showdown, validação das regras, fraquezas, cobertura, funções de duplas, ameaças do meta, dicas e 4 times de exemplo; análise já aparece no `app.py`. 48 testes passando. Limitações: Weather Ball/Terrain Pulse contam como Normal; só as habilidades defensivas mais comuns. |
| 27/10/2026 | Fase 2 mergeada (PR #3) e site publicado no Streamlit Cloud. Fase 3 feita na branch `fase-3-recomendacao`: `src/recomendacao.py` (habilidade/item/golpes/EVs por frequência, item único, parceiros por confiança/lift, substitutos = co-ocorrência + fraquezas), explicação do porquê e seção "3. Recomendações" no `app.py`; link do site no README. 61 testes passando. |
| 27/10/2026 | Fase 3 mergeada (PR #4). Fase 3.1 a pedido do Carlos: aba "Montar o time" com item, habilidade e golpes em cards (`src/opcoes.py`, `montar_time` no leitor). 65 testes passando. |
| 27/10/2026 | Fase 3.2 a pedido do Carlos: cobertura ofensiva só com os golpes de ataque escolhidos, mostrando "golpe (Pokémon)", botão que monta o Pokémon com a recomendação, e ameaças do meta supondo os golpes mais usados de quem não tem golpes; Mega já vem com a Pedra Mega travada; substitutos levam em conta as funções que faltam e explicam o porquê. 73 testes passando. |
| 27/10/2026 | Fase 4.1 (branch `fase-4-montar-o-time`): "Montar o time" virou a única tela de entrada, com cards no estilo do teambuilder (imagem, tipos coloridos, ícone do item, tema escuro), dado, ajustes de natureza/EVs e botões Importar/Exportar no lugar da aba "Colar do Showdown". Imagens salvas em `data/sprites/`. 79 testes passando. Próximo: 4.2 (análise, recomendações, mensagens e times de exemplo). |
| 27/10/2026 | Fase 4.2 (branch `fase-4-2-analise`, em cima da 4.1): análise com resumo em números, dicas em 3 colunas, etiquetas de tipo, funções e ameaças em cartões; recomendações com imagens e botões que levam a sugestão para os cards (adicionar parceiro, trocar Pokémon); times de exemplo com EVs + "Começo de time"; mensagens revisadas. `app.py` ficou só com as 3 partes. 81 testes passando. Fase 4 concluída; próximo: Fase 5 (teste completo no site publicado e revisão do código). |
