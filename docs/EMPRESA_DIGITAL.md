# Estatuto da Empresa Digital FAST Limão

**Versão:** 1.0 · 14/09/2026
**Dono:** Rodrigo Garcia
**Unidades:** FAST Escova Limão (🥂 · desde 23/07/2026) · FAST Spa Limão (🧖 · abre 25/09/2026)
**Onde vive:** `rodsballa12-cell/fast-dashboard-limao`
**Espelho recomendado no Obsidian:** `Cerebro_Claude/Empresa_Digital_FAST.md`

---

## 1. Diagnóstico honesto

Você não está começando do zero. **A empresa digital já existe — o que falta é o
organograma.**

Hoje o repositório tem 20 scripts, 7 rotinas automáticas e 8 conectores. Isso já
é mais infraestrutura do que a maioria das redes de 10 unidades tem. O problema
não é falta de máquina: é que **não está escrito quem faz o quê, quem responde
por qual número, e o que acontece quando alguém não responde.**

Um exemplo real do seu próprio repositório: entre 24/08 e 04/09 o fluxo de
aniversários criou 9 tarefas de aprovação e 7 nunca foram respondidas. O gate de
aprovação não estava protegendo ninguém — era o lugar onde o processo morria.
Isso foi corrigido colocando as travas no código (`campanhas_wa.py`). **Essa é
exatamente a lição que estrutura uma empresa digital: todo ponto que depende de
alguém lembrar é um ponto que vai falhar.**

---

## 2. Organograma: as 6 diretorias

Cada diretoria é um **agente**: tem uma missão, conectores próprios, um horário
em que acorda, e uma entrega. Nenhuma depende de você lembrar de rodar.

### 🏢 Diretoria de Operação — "a casa está cheia?"

| | |
|---|---|
| **Missão** | Agenda, clientes, profissionais, taxa de ocupação, aniversariantes do dia |
| **Conectores** | Trinks API v1 |
| **Já roda** | `github_refresh.py` via `refresh.yml` — 3 disparos por hora, 11h–21h BRT, com saída antecipada |
| **Entrega** | `data/dashboard_data.json` · `data/spa/dashboard_data.json` |
| **Trava conhecida** | Cota Trinks de 10.000 req/mês. Em 01/09 o painel queimou 1.007 req (10% do mês) num único dia. Por isso a saída antecipada. |
| **Bloqueio ativo** | SPA sem `TRINKS_ESTABELECIMENTO_ID_SPA`. Enquanto isso o painel do SPA roda em "zero-state honesto" — estrutura real, números zerados. |

### 💰 Diretoria Financeira — "sobrou quanto?"

| | |
|---|---|
| **Missão** | DRE por unidade, conciliação de recebíveis, comissões |
| **Conectores** | Extrato Stone (CSV) · Planilha DRE (Excel) |
| **Já roda** | `stone_processor.py` (cruza Stone × Trinks por dia/semana/mês/ano) · `gerar_financeiro.py` (lê os blocos FAST ESCOVA e FAST SPA da aba DRE) |
| **Entrega** | `data/financeiro.json` · `data/spa/financeiro.json` · `data/consolidado/financeiro.json` |
| **Maior fragilidade** | **É a única diretoria que ainda depende de você.** O CSV da Stone e o Excel do DRE entram na mão. Se você viajar duas semanas, o financeiro congela e as outras cinco diretorias continuam andando. |

### 📣 Diretoria de Marketing — "o dinheiro de mídia está virando cliente?"

| | |
|---|---|
| **Missão** | Meta Ads, Instagram, Facebook, Google Business, saúde de entrega |
| **Conectores** | Meta Graph API v20.0 · Supermetrics MCP · Google Business Profile |
| **Já roda** | `refresh_midias.py` via `midias_refresh.yml` (07h BRT) · `refresh_google.py` · `alerta_entrega.py` (ligado ao workflow em 14/09) · `revisao_semanal.py` |
| **Entrega** | `data/midias_sociais.json` + versão SPA + consolidado · texto pronto pra agência (Beleza Boost) |
| **Por que o alerta existe** | Entre 27 e 31/08/2026 a conta parou de entregar por 4 dias com todas as campanhas ativas. Ninguém percebeu. Descoberto por acaso 5 dias depois. Custo: ~R$ 480. `alerta_entrega.py` nasceu disso. |
| **Ainda manual** | Os campos de julgamento — `direcionamentos_estrategicos`, `recomendacoes`, `benchmarks`, `kpi_estrela` — são escritos pelo gerente de Marketing. Isso está certo: **número é máquina, leitura é gente.** |

### 💬 Diretoria de Relacionamento — "o cliente volta?"

| | |
|---|---|
| **Missão** | CRM, aniversário, reativação de quem sumiu |
| **Conectores** | HubSpot (portal 51943728) · WhatsApp Cloud API |
| **Já roda** | `hubspot_sync.py` via `hubspot_sync.yml` (02h15 BRT) · `campanhas_wa.py` via `campanhas_wa.yml` (10h BRT) |
| **Travas no código** | Kill switch · opt-out · cooldown global e por campanha · teto diário · janela 9h–20h |
| **🔴 BLOQUEADO** | O App Meta que gerenciava o WhatsApp foi deletado. O `META_PHONE_NUMBER_ID` não vale mais. **Resultado: a diretoria roda em ensaio, mas nenhuma mensagem sai.** Este é o gargalo nº 1 da empresa. |

### 🧠 Diretoria de Inteligência — "o que isso quer dizer?"

| | |
|---|---|
| **Missão** | Transformar dado em frase acionável; somar as unidades |
| **Já roda** | `insights.py` (classifica em crítico › atenção › oportunidade › info) · `consolida_dashboard.py` (Escova + SPA → Consolidado) · `build_artifact.py` |
| **Entrega** | Comentários por aba do painel · visão consolidada da holding |
| **O que falta** | **Memória.** O painel mostra o agora. Ele não guarda o que você decidiu em agosto nem se deu certo. Sem isso, toda decisão recomeça do zero. |

### ⚖️ Conselho — você + eu

| | |
|---|---|
| **Missão** | Definir metas, aprovar investimento, decidir o que as máquinas não decidem |
| **Cadência hoje** | Nenhuma formal. É aqui que está o buraco. |

---

## 3. Mapa de conectores

| Conector | Serve a quem | Status | Quem resolve |
|---|---|---|---|
| Trinks API — Escova (id 276461) | Operação | ✅ No ar | — |
| Trinks API — SPA | Operação | 🔴 Sem `estabelecimentoId` | Você (Trinks) |
| Meta Graph — Escova | Marketing | ✅ No ar | — |
| Meta Graph — SPA (`act_1381925294040065`) | Marketing | ✅ Pronto pra puxar | Gerente Marketing |
| Google Business — Escova | Marketing | ✅ Via Supermetrics | — |
| Google Business — SPA | Marketing | 🟡 Pendente | Gerente Marketing |
| HubSpot (51943728) | Relacionamento | ✅ Escova · 🟡 SPA | Gerente Marketing |
| WhatsApp Cloud — Escova | Relacionamento | 🔴 App Meta deletado | Gerente Marketing |
| WhatsApp Cloud — SPA | Relacionamento | 🔴 Nunca criado | Gerente Marketing |
| Stone (extrato CSV) | Financeiro | 🟡 Manual | Você |
| Planilha DRE (Excel) | Financeiro | 🟡 Manual | Você |
| GitHub Actions | Todas | ✅ 7 rotinas | — |
| Contábil / Fiscal | — | ⬜ Não existe | — |
| Banco / conciliação | Financeiro | ⬜ Não existe | — |

---

## 4. As 4 camadas que faltam

Isto é a resposta direta à pergunta "como estruturo". Scripts soltos viram
empresa quando ganham estas quatro camadas:

### Camada 1 · Estatuto — *quem pode o quê*

`data/config.json` já é o embrião disso: ele diz quem é cada unidade, qual conta
de mídia pertence a quem, e qual secret guarda cada credencial. Falta elevá-lo a
estatuto, acrescentando **o limite de cada agente**: quanto o agente de WhatsApp
pode disparar por dia sem perguntar, até quanto o de Marketing pode declarar
sozinho que a campanha está ruim. O kill switch do `campanhas_wa.py` já é essa
ideia funcionando — só não está generalizada.

### Camada 2 · Memória — *o que já tentamos*

Hoje o histórico mora no seu Obsidian, na sua máquina. **Eu não alcanço aquele
caminho quando trabalho na nuvem.** Então a memória precisa de um espelho que
viva junto do código: uma pasta no repositório com uma nota por decisão (o que
decidimos, por quê, o que esperávamos, o que aconteceu). Você sincroniza com o
Obsidian; eu leio direto. Este arquivo é o primeiro tijolo.

### Camada 3 · Cadência — *quando a gente olha*

As máquinas já têm horário. As pessoas não. A cadência mínima:

- **Diário · 10 min** — abrir o painel, ler só os alertas críticos
- **Semanal · 30 min** — rodar `revisao_semanal.py`, mandar pra agência, decidir mídia
- **Mensal · 2 h** — fechar DRE, revisar comissões, decidir o mês

### Camada 4 · Alerta — *quem te puxa pelo braço*

Hoje a empresa inteira é **puxada**: só descobre se você abrir o painel. Foi
assim que os R$ 480 queimaram por quatro dias.

**Resolvido em 14/09/2026.** Uma auditoria descobriu que `alerta_entrega.py`
existia desde agosto e **nunca tinha sido chamado por lugar nenhum** — um
detector escrito para não repetir o prejuízo, que jamais rodou. E olhava só a
Escova, deixando o Spa sem vigilância a 11 dias da abertura. Agora roda ao fim
do `midias_refresh.yml`, nas duas unidades, e falha o workflow de propósito
quando detecta parada — o que faz o GitHub mandar e-mail. O canal existia o
tempo todo; faltava alguém apertar o botão.

**A lição vale mais que o conserto:** código de segurança que ninguém chama é
segurança de mentira — e aparece como pronto no inventário.

---

## 5. Agentes que ainda não existem

| Agente | Por que vale | Matéria-prima já no repo |
|---|---|---|
| **Compras / Estoque** | Produto acabado é receita perdida em serviço sem hora marcada | `produtos_cache.json` |
| **Pessoas / Comissões** | Profissional é o custo maior e o gargalo de capacidade | `comissoes.json`, `prof_overrides.json` |
| **Fiscal / Contábil** | Único ponto cego total de risco | nada ainda |
| **Expansão** | O desenho multi-unidade já aguenta a 3ª sem código novo | `config.json → unidades` |

---

## 6. Roadmap

### Onda 1 — agora (destrava tudo)
1. Pegar o `estabelecimentoId` da SPA no Trinks → a SPA sai do zero-state
2. Recriar o App Meta → WhatsApp volta a disparar nas duas unidades
3. Escolher o canal do alerta → a empresa passa a falar com você

### Onda 2 — 30 dias
4. Pasta de memória no repositório + rotina de registro de decisão
5. Agente de Pessoas/Comissões
6. Automatizar a entrada financeira (tirar o CSV e o Excel da sua mão)

### Onda 3 — 90 dias
7. Agente de Compras/Estoque
8. Conector fiscal/contábil
9. Provar a 3ª unidade sem escrever código novo

---

## 7. Como me pedir as coisas (pra gastar menos conversa)

Todo pedido bom tem 5 partes. Quando falta uma, eu pergunto — e isso custa uma
rodada.

| Parte | Pergunta que responde | Exemplo |
|---|---|---|
| **Papel** | Quem eu sou nessa tarefa | "Como diretor financeiro da holding" |
| **Onde** | Qual arquivo / unidade / período | "Em `data/consolidado/financeiro.json`, agosto" |
| **O quê** | A tarefa, com verbo | "Compare margem Escova × SPA" |
| **Formato** | O que você quer receber | "Tabela de 5 linhas + 1 parágrafo de leitura" |
| **Limite** | O que NÃO fazer | "Não mexa em código, não crie arquivo" |

**Fraco (3 rodadas):** "olha o financeiro pra mim"

**Forte (1 rodada):** "Como diretor financeiro: leia `data/consolidado/financeiro.json`,
compare a margem de agosto entre Escova e SPA, me devolva uma tabela de 5 linhas
e um parágrafo dizendo onde estou perdendo dinheiro. Não altere arquivo nenhum."

### Três atalhos que economizam muito

1. **Comece por "leia X antes de responder"** — me ancora no dado real em vez da
   suposição.
2. **Peça o formato junto com a pergunta** — "me dá em tabela", "me dá em 3
   bullets", "me dá o texto pronto pra colar no WhatsApp da agência".
3. **Empilhe num pedido só** — "faça A, depois B, depois C, e no fim me diga o
   que deu errado". Eu executo em sequência; você lê uma vez.

### Modelo pronto — revisão semanal

```
Rode a revisão semanal da Escova:
1. Leia data/midias_sociais.json e data/dashboard_data.json
2. Me diga os 3 números que pioraram vs semana passada
3. Gere o texto pronto pra mandar pra Beleza Boost
Não altere arquivo. Se algum dado estiver com mais de 48h, me avise antes.
```

---

## 8. Qual ferramenta do Claude usar (e por quê nenhuma sozinha basta)

Você perguntou qual ferramenta dá **acesso total** ao projeto. A resposta honesta
é que existem três, elas enxergam coisas diferentes, e a sua empresa precisa de
duas delas rodando juntas.

| Ferramenta | O que ela alcança | O que ela **não** alcança |
|---|---|---|
| **Claude Code no app do computador** (Windows) | Seu disco inteiro: o Obsidian, o Excel do DRE, o CSV da Stone, o repositório local, seus scripts. E também o GitHub. | Nada. É a de maior alcance. |
| **Claude Code na web** (o que estamos usando agora) | O GitHub: código, dados, rotinas automáticas. Roda sozinho, sem seu computador ligado. | **Seu disco.** Foi por isso que eu não consegui ler o `Cerebro_Claude` hoje. |
| **Claude.ai com conectores** | Supermetrics, HubSpot, Drive, e-mail — dado de negócio ao vivo, sem código. | Seu código e seu disco. |

### A recomendação

**Instale o Claude Code no app do computador e faça dele a sede da empresa.**
É a única ferramenta que vê ao mesmo tempo o seu cérebro no Obsidian, a sua
planilha de DRE e o seu código. É lá que as decisões são tomadas.

**Mantenha a web para o que precisa rodar sem você.** As 7 rotinas automáticas
(painel de hora em hora, mídia às 07h, HubSpot às 02h15, WhatsApp às 10h) não
podem depender do seu notebook estar ligado — e não dependem.

**Divisão de trabalho:**

- 🖥️ **Computador** = pensar. Ler o Obsidian, fechar o DRE, decidir o mês, escrever no cérebro.
- ☁️ **Nuvem** = executar. Puxar dado, disparar campanha, vigiar a conta de mídia, avisar quando quebrar.

### Três ajustes que otimizam mais do que trocar de ferramenta

**1. Transforme pedido repetido em comando.** Você já faz isso — o `/marketing-fast`
citado no `MIDIAS_HANDOFF.md` é exatamente isso. Todo pedido que você fizer três
vezes vira um comando de uma linha. Candidatos imediatos: revisão semanal,
fechamento de DRE, checagem de saúde dos conectores.

**2. Coloque o cérebro dentro do repositório.** Enquanto a memória viver só no seu
disco, metade das minhas sessões trabalha sem ela. Uma pasta `cerebro/` no
repositório, sincronizada com o Obsidian, resolve — e é o que a Camada 2 acima
descreve.

**3. Peça auditoria, não só execução.** Uma vez por mês: *"revise as 7 rotinas do
`.github/workflows`, me diga quais rodaram, quais falharam calado e quais estão
gastando cota à toa."* Empresa que não se audita acumula exatamente o tipo de
falha silenciosa que custou os R$ 480 de agosto.


---

*Documento vivo. Atualizar sempre que uma diretoria mudar de status.*
