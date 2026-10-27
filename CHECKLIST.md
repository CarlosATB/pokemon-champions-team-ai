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
- [~] `README.md` inicial — falta o link do site (Fase 5)
- [x] `CHECKLIST.md` (este arquivo) dentro do repositório
- [x] Arquivo de configuração com a regulamentação/formato atual num só lugar (`src/config.py`)
- [ ] Conta no Streamlit Community Cloud ligada ao GitHub
- [ ] Confirmar a data de entrega com o professor
- [~] Confirmar qual regulamentação do Champions usar — configurado M-C (`gen9championsvgc2026regmc`, dados de 2026-09), válida até 2/dez/2026; conferir se surge uma nova antes da entrega

### Fase 1 — Dados
- [~] Script que baixa as estatísticas do Smogon (Champions VGC) do mês mais recente — `src/baixar_dados.py` pronto e testado com um exemplo; falta rodar no PC (a nuvem não acessa smogon.com) para gerar `data/processed/uso.json`
- [x] Script que baixa tipos e status base da PokéAPI — `data/processed/pokemon.json` (349 Pokémon/formas)
- [x] Tabela de efetividade de tipos (18×18) — `src/tipos.py`, conferida com a tabela do Showdown
- [x] Lista de Pokémon e Megas legais na regulamentação — `data/processed/legais.json` (349, sendo 80 Megas), tirada do mod `champions` do Pokémon Showdown
- [~] Padronização de nomes entre as fontes (Smogon × PokéAPI, formas e Megas) — `src/nomes.py` (id + 23 exceções da PokéAPI); falta confirmar com os nomes reais do Smogon (teste `test_nomes_do_smogon_batem_com_os_legais`)
- [x] Listas de golpes/habilidades por função de duplas (speed control, Fake Out, redirecionamento etc.) — `src/funcoes_duplas.py`
- [~] Dados salvos localmente (cache em JSON) para o site não depender de download ao vivo — `legais.json` e `pokemon.json` prontos; falta `uso.json`
- [~] Testes básicos: dados carregam e nomes batem — 19 passando; 1 é pulado até existir `uso.json`
- [ ] Movepool do Champions (learnsets do Showdown) para validar golpes — necessário na Fase 2/3

### Fase 2 — Análise do time
- [ ] Leitura do time (colar no formato export do Showdown e/ou escolher na lista)
- [ ] Validação das regras (espécie/item repetido, Pokémon fora da regulamentação, aviso de várias Megas)
- [ ] Matriz de fraquezas e resistências do time
- [ ] Cobertura ofensiva (quais tipos o time não acerta bem)
- [ ] Checagem de funções de duplas
- [ ] Ameaças do meta: top Pokémon mais usados contra o time
- [ ] Geração de dicas em texto claro ("seu time não tem controle de velocidade")
- [ ] Testes com 3 a 5 times de exemplo

### Fase 3 — Sistema de Recomendação
- [ ] Sugestão de habilidade, item, golpes e natureza/EVs por Pokémon (por frequência de uso)
- [ ] Respeitar a regra de item único ao sugerir itens
- [ ] Sugestão de parceiros pela co-ocorrência (teammates)
- [ ] Pontuação para sugerir substitutos: combina co-ocorrência + cobrir as fraquezas encontradas na Fase 2
- [ ] Explicação do porquê de cada sugestão
- [ ] Testes com os times de exemplo

### Fase 4 — Interface (Streamlit)
- [ ] Tela de entrada do time
- [ ] Exibição da análise (tabela/gráfico de fraquezas, funções, ameaças)
- [ ] Exibição das recomendações por Pokémon
- [ ] Botão para importar/exportar time no formato do Showdown
- [ ] Times de exemplo prontos para a demonstração
- [ ] Mensagens de erro amigáveis (nome errado, Pokémon ilegal)

### Fase 5 — Publicação e testes
- [ ] Deploy no Streamlit Community Cloud funcionando
- [ ] Link do site no README
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
| 27/10/2026 | Fase 0 mergeada (PR #1). Fase 1 em andamento (branch `fase-1-dados`): script de download, tabela de tipos, lista de legais (349), dados da PokéAPI, nomes, funções de duplas e testes (19 passando). Falta baixar as estatísticas do Smogon no PC do Carlos. |
