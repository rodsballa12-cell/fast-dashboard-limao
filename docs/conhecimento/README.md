# Conhecimento · os nove meses que construíram o negócio

Aqui mora o que o Rodrigo aprendeu montando a FAST Limão, de janeiro de 2026
até a abertura — e o que veio depois. Veio do cérebro dele no Obsidian, que só
a máquina dele alcança.

## A regra que faz isto funcionar

**Nada aqui é lido automaticamente.** Nenhum cargo carrega esta pasta ao
começar, e é de propósito: cinco arquivos do vault somam 667 KB, que é quase
uma sessão inteira só para abrir o índice, sem sobrar espaço para o painel.

O acesso é **por busca, sob demanda** — do mesmo jeito que ninguém lê os 30
scripts do repositório para mexer em um:

```bash
grep -ril "rateio" docs/conhecimento/     # quais arquivos falam disso
grep -rn "45,5%" docs/conhecimento/       # onde exatamente
```

Achou o arquivo, lê só ele. **Mais contexto não é melhor contexto:** um agente
com 250 notas de qualidade misturada decide pior que um com 20 regras
verificadas, porque não sabe qual está desatualizada.

## O que entra aqui, e o que não

| | vai para |
|---|---|
| Como se chegou numa decisão · negociação com a franqueadora · o que se tentou e falhou · pesquisa de bairro, de preço, de concorrente | **aqui** |
| Regra que vale hoje — contrato, rateio, tabela, meta | `.claude/skills/` ou `data/config.json` |
| Decisão batida, com data de revisão | `docs/decisoes/` |
| Resumo de reunião · rascunho · nota de leitura · conversa | **fica no Obsidian** |

**Uma coisa tem um lugar só.** Regra que ficar aqui *e* no vault vira duas
versões divergindo, e daqui a dois meses ninguém sabe qual vale. Histórico não
muda — pode ficar nos dois.

## Cuidado com o que foi revertido

Nove meses contêm decisões abandonadas no caminho. Se elas entrarem sem marca,
algum cargo vai recomendar amanhã o que você já descartou em maio.

**Todo arquivo aqui abre dizendo de quando é e se ainda vale:**

```markdown
---
periodo: 2026-03 a 2026-05
status: histórico · decisão revertida em 2026-06
---
```

`status: vigente` só para o que ainda é verdade hoje. Na dúvida, `histórico`.

## Como nomear

`assunto-especifico.md`, em minúsculas, sem data no nome — a data vai no
frontmatter. `negociacao-ponto-limao.md`, não `notas-marco.md`: quem procura
busca pelo assunto, não pelo mês.
