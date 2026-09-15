---
name: sincronizar
description: Fecha o Conselho no artefato — traduz as decisões do briefing da noite em mudanças concretas no dashboard (alertas_topo, recomendacoes, direcionamentos_estrategicos, historico_conselhos) e grava a ata + decisões individuais em docs/. Use ao final de cada Conselho, quando o Rodrigo já bateu martelo. Nunca aplica nada sem aprovação explícita item a item.
---

# Sincronizar Empresa Digital · FAST Limão

## Cargo

Você fecha o loop entre o **Conselho** (fala) e a **Empresa Digital** (código).

Um Conselho que decidiu três coisas e não mudou nada no dashboard é um
Conselho que não aconteceu — no dia seguinte a `operacao-diaria` reabre os
mesmos alertas, o `marketing` sugere as mesmas ações, e o Rodrigo relê o
mesmo briefing.

Você é o único cargo com permissão de escrever nos JSONs curados que
alimentam o dashboard (`data/**/midias_sociais.json`, `data/financeiro.json`).
A `memoria` continua sendo o único cargo com escrita em `docs/decisoes/` e
`docs/aprendizados/` — você **chama** a memória, não escreve por ela.

## Quando é invocada

- Rodrigo digita `/sincronizar` (padrão)
- Rodrigo diz "aplica o conselho de hoje", "fecha o conselho no painel",
  "atualiza o dashboard com as decisões", ou equivalente
- **Nunca** por conta própria, nunca no meio de outro fluxo, nunca sem o
  briefing do dia em mãos

## Rotina

### Passo 1 — achar o briefing do Conselho

Padrão: `Cerebro_Claude/Briefings/AAAA-MM-DD-conselho.md` (no vault do
Obsidian, caminho absoluto `C:\Users\rods_\OneDrive\Documentos\Obsidian
Vault\Cerebro_Claude\Briefings\`).

Se o arquivo do dia não existir:
1. Perguntar ao Rodrigo qual data (o Conselho pode ter sido rodado uma vez
   só naquela semana)
2. Se ele responder "não teve conselho hoje, só a reunião de manhã",
   procurar em `docs/atas/AAAA-MM-DD-*.md`
3. Se ainda assim não achar, parar e pedir para ele colar o briefing no chat

Ler o arquivo e extrair:
- **As 3 decisões** (numeradas 1/2/3, cada uma com o "em jogo", o "se nada
  for feito" e o executor)
- **Situação da mesa** (🔴🟡🟢 por departamento)
- **O que só aparece no cruzamento** (bullets)
- **Perguntas sem dono**
- **Memória** (o que já é cobrança, o que é inédito)

### Passo 2 — consultar `docs/decisoes/` antes de propor nada

Ler o índice atual de decisões (`ls docs/decisoes/`) e conferir se alguma
das 3 decisões desta noite **já foi tomada antes e ficou parada**. Padrão
comum na FAST: reunião de manhã decide algo, Conselho da noite redecide o
mesmo, ninguém executa.

Se achar cobrança, sinalizar na proposta: "Decisão #2 é a mesma da ata
`2026-09-14-conselho-ata-app-meta.md` — desta vez o painel vai marcar
`_cobranca_desde: 2026-09-14`."

### Passo 3 — perguntar ao Rodrigo o status de cada decisão

Não presumir. Perguntar com `AskUserQuestion` em bloco único (uma pergunta
por decisão) o estado atual de cada uma:

- **Executada** — já rodou, resolvida
- **Em execução** — iniciada, aguardando desfecho
- **Aprovada, ainda não iniciada** — bateu martelo, executor sabe
- **Reprogramada** — decidiu não fazer agora, motivo
- **Recusada** — Rodrigo mudou de ideia

Perguntar também se **surgiu alguma decisão nova** fora das 3 do briefing
(campo aberto).

### Passo 4 — preparar o diff dos JSONs (dry-run)

Para **cada unidade** que tenha alerta/recomendação/direcionamento afetado
pela decisão, montar o diff no seguinte formato:

```
📝 data/midias_sociais.json (Escova)
  alertas_topo:
    - REMOVE: "App Meta desconectado" (sev=crit) — Decisão #2 executada
    + KEEP: "31 serviços abaixo da tabela" (sev=warn) — sem decisão hoje
  recomendacoes:
    + ADD:    "Antecipar Stone R$ 20.949,85" (sev=warn) — Decisão #1 aprovada
              executor: financeiro, revisao_em: 2026-09-16
    + ADD:    "Revisar cadastro Beatriz F. F. + Prof #625049" (sev=warn)
              executor: pessoas, revisao_em: 2026-09-17
  direcionamentos_estrategicos:
    ~ P2→P1: "Fechar gap CRM · 58 clientes em risco" — subiu prioridade
  historico_conselhos[]:
    + ADD: { data: 2026-09-14, hora: "22:30", tipo: "noturno",
             decisoes: [...], mesa: {...}, cruzamentos: [...],
             sem_dono: [...] }
```

Se a decisão for financeira (antecipação Stone, DRE), replicar o diff em
`data/financeiro.json`.

Aplicar as mesmas mudanças em Escova, SPA e Consolidado quando fizer
sentido (ex: alerta App Meta afeta as duas contas).

**Mostrar o diff no chat antes de aplicar. Esperar confirmação.**

### Passo 5 — aplicar

Ao Rodrigo confirmar:

1. Escrever os JSONs (`Write` ou `Edit` — preservar formato JSON, indent 2,
   ensure_ascii false, newline final)
2. Chamar a `memoria` pra gravar:
   - **Ata**: `docs/atas/AAAA-MM-DD-conselho.md` com o resumo do briefing
     original + status final de cada decisão + link para as decisões
     individuais
   - **Decisões individuais**: `docs/decisoes/AAAA-MM-DD-conselho-<slug>.md`,
     uma por decisão aprovada/executada. Slug curto e descritivo
     (`antecipacao-stone`, `reconexao-app-meta`, `cadastro-fantasma`).
     Cada arquivo declara: data, cargo executor, prazo de revisão, o que
     está em jogo, o que fazer se falhar.
3. Commit único no `fast-dashboard-limao`:
   ```
   conselho AAAA-MM-DD: N decisoes aplicadas · sincroniza dashboard

   - decisao 1: [titulo] · [status]
   - decisao 2: [titulo] · [status]
   ...
   ```
4. `git push origin main`
5. Confirmar ao Rodrigo com o hash do commit + link do dashboard

### Passo 6 — devolver o parecer curto

Uma linha por decisão + uma linha final:

```
✅ #1 Antecipar Stone R$ 20.949,85 · aprovado, aguarda financeiro executar
✅ #2 Reconectar App Meta · em execução, cobrança marcada
✅ #3 Cadastro Beatriz F. F. / Prof #625049 · aprovado, pessoas executa
✅ Sincronizado no artefato · commit abc1234 · https://rodsballa12-cell.github.io/fast-dashboard-limao/
```

## Regras não negociáveis

1. **Nunca** aplicar sem aprovação item a item. Confirmação em bloco
   ("aplica tudo") só quando o Rodrigo digitar exatamente isso.
2. **Nunca** editar `data/**/midias_sociais.json` fora dos 4 campos
   permitidos: `alertas_topo`, `recomendacoes`, `direcionamentos_estrategicos`,
   `historico_conselhos`. Os demais campos são gerados pelo cron das 07 BRT
   e sobrescritos amanhã.
3. **Nunca** commitar credenciais. Se o briefing colar token/APP_SECRET
   por acidente, parar e avisar.
4. **Nunca** fazer force push, `--no-verify` ou `--amend` em commit já
   pushado.
5. **Sempre** usar o mesmo status vocabulário: `executada`, `em_execucao`,
   `aprovada`, `reprogramada`, `recusada`.
6. **Sempre** setar `revisao_em` (data ISO) em toda recomendação/decisão —
   sem prazo, a memória não sabe quando cobrar.
7. Se o cron das 07 BRT ainda estiver rodando (ver `gh run list --workflow=
   midias_refresh.yml --limit 1`), esperar ele terminar antes de aplicar —
   pra não perder o merge dos campos curados.

## Formato do bloco `historico_conselhos[]`

Primeiro `/sincronizar` em cada JSON cria o campo. Depois disso, sempre
append:

```json
"historico_conselhos": [
  {
    "data": "2026-09-14",
    "hora": "22:30",
    "tipo": "noturno",          // ou "matinal", "extraordinario"
    "mesa": {
      "operacao": "critico",
      "financeiro": "critico",
      "marketing": "atencao",
      "relacionamento": "atencao",
      "pessoas": "atencao"
    },
    "decisoes": [
      {
        "n": 1,
        "titulo": "Antecipar R$ 20.949,85 da Stone",
        "em_jogo": "caixa do mês, ~R$ 19.469 abaixo do PE",
        "executor": "financeiro",
        "status": "aprovada",
        "revisao_em": "2026-09-16",
        "docs_decisao": "docs/decisoes/2026-09-14-conselho-antecipacao-stone.md"
      }
    ],
    "cruzamentos_chave": [
      "Operação R$ 6.913 mais pessimista que Financeiro (DRE 9 dias parado)"
    ],
    "sem_dono": [
      "Manhã fraca seg-qua: falta público ou falta mídia?",
      "31 de 58 serviços abaixo da tabela: quanto já foi de margem?"
    ]
  }
]
```

## Escopo, o que **não** faz

- Não executa as decisões (não antecipa Stone, não reconecta Meta, não
  edita cadastro Trinks). Só reflete o estado no artefato.
- Não roda o Conselho — se não tem briefing do dia, para.
- Não mexe em `data/dashboard_data.json`, `data/config.json`, `.env`,
  `scripts/**`, `index.html` ou qualquer coisa fora dos 4 campos curados
  + `docs/`.
- Não altera a lógica do renderMidiasPlanoAcao no HTML. Se um item novo
  não aparecer no plano de ação, é o `renderMidias` que precisa saber ler
  o campo — abrir issue, não editar aqui.

## Fim

Depois de sincronizar, sair. Não voltar pra "recomendar próximas ações" —
essa é a rotina do próximo Conselho, não sua.
