---
titulo: "Respeitar o schema virou jogar dado fora"
data: 2026-09-19
cargo: Memória
status: vigente
custo: "o Spa passou quase um mês sem metade das métricas de mídia, a seis dias de abrir"
---

## O que aconteceu

O Rodrigo reclamou que o card principal da aba Mídias não atualizava. Eram
quatro defeitos empilhados, e o de baixo era o grave.

`refresh_midias.py` tinha em `_update_periodo` a regra:

```python
# nunca criar chaves que a base nao tenha (respeita schema)
if k in base_periodo:
    base_periodo[k] = v
```

A intenção era não pisar em campo curado à mão. O efeito era outro: **campo que
a API traz todo dia era descartado para sempre se o arquivo de andaime não o
tivesse declarado.**

O `data/spa/midias_sociais.json` nasceu do `build_spa_midias.py` sem `inicio`,
`fim`, `cliques`, `link_clicks`, `cpc`, `cpc_link`, `link_ctr_pct` e
`post_engagement`. Oito campos, cinco janelas, todos os dias, por quase um mês.
A Meta devolvia os números; o script os lia; e a regra os apagava na hora de
gravar.

Sem `inicio`/`fim` o painel não consegue contar os dias da janela. O card do
Spa exibia **"MES CORRENTE · NAN DIAS"**, "NaN/dia" e "R$ 31/dia" lido como
"R$ 0/dia" — e metade das métricas como travessão. O Spa abre em 25/09.

## Por que ninguém viu

Nenhum erro em lugar nenhum. A rotina terminava verde, o arquivo era gravado,
o commit saía com o resumo de sempre. O dado simplesmente não chegava — e
"não chegou" e "é zero" são indistinguíveis no painel.

A auditoria de coerência também passava: ela confere se as unidades somam no
consolidado e se os períodos batem, não se um campo que deveria existir existe.

## Os três defeitos em cima

1. **`MID.kpi_estrela.explicacao` sem guarda.** O Consolidado nunca teve
   `kpi_estrela`. `TypeError` no meio da montagem do card → `renderMidias`
   morria ali → o `catch` do loader só escrevia `console.warn`. A aba ficava
   com o desenho anterior na tela.
2. **Mensagem de alerta avaliada antes da condição.** Em
   `n.tira(p.frequency >= teto, 15, 'warn', \`...${p.frequency.toFixed(2)}\`)`
   a mensagem é um argumento, então roda mesmo com a condição falsa. Campo
   ausente vira `TypeError` num caminho que parecia inalcançável.
3. **Só a Escova ia embutida no artefato.** No celular, trocar para Spa ou
   Consolidado mandava o `fetch` para a rede; a CSP do Artifact recusava; a
   promessa **rejeitava** — não um 404, então nem o fallback para a Escova
   disparava.

## As regras

**Uma regra que protege um campo não pode decidir quais campos existem.** Se o
objetivo é preservar o que foi escrito à mão, nomeie o que é curado — não
transforme o arquivo de ontem na lista do que pode existir amanhã.

**Mensagem de erro não é lugar de calcular.** Se o texto do alerta desreferencia
um campo, ele roda sempre, não só quando o alerta dispara.

**Andaime vira contrato.** O arquivo criado para "ter alguma coisa ali" definiu,
sem querer, o schema permanente da unidade. Toda vez que um andaime nascer,
ele precisa nascer com todos os campos da unidade que ele imita — ou a regra
que o lê precisa aceitar campos novos.

E, de novo, a de sempre: **o sistema não ter visto não é a mesma coisa que não
ter acontecido.** Sexto caso da semana.
