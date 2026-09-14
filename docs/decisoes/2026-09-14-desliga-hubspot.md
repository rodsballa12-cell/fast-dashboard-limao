# HubSpot desligado — o Trinks já é o cadastro de cliente

**Data:** 2026-09-14 · **Quem decidiu:** Rodrigo
**Departamentos ouvidos:** Relacionamento, Marketing

## Contexto

O `hubspot_sync.yml` rodava todos os dias às 02h15 desde a configuração,
enviando clientes do Trinks para o HubSpot (portal 51943728). O painel media o
resultado em `hubspot.contatos`, que marcava **zero** — a base nunca foi
importada. A rotina rodava, ficava verde, e não trazia nada.

Na mesma auditoria do dia apareceram outros quatro casos do mesmo padrão:
`alerta_entrega.py` escrito e nunca chamado, o `/marketing-fast` que só existia
numa máquina, a rotina de WhatsApp que descartava a fila em silêncio, e o botão
📱 do painel que funcionava sem ninguém usar.

## A pergunta que decidiu

O que o HubSpot faria que o Trinks já não faz?

| | Trinks + painel | HubSpot |
|---|---|---|
| Base de clientes | 411, com histórico | duplicaria |
| Churn e LTV | já calculado | duplicaria |
| Aniversários | com mensagem pronta | duplicaria |
| Abrir conversa | botão 📱 no painel | — |

O que o HubSpot traz de próprio — funil de vendas, sequência de e-mail,
automação de negócio — **não tem onde encostar num salão sem hora marcada**,
em que a venda acontece na porta e não há ciclo de negociação.

## Alternativas descartadas

**Importar a base e usar de verdade** — criaria um segundo cadastro de cliente
a manter sincronizado. Duas fontes da verdade sempre divergem; é exatamente o
defeito que a auditoria de coerência existe para pegar.

**Deixar rodando "por garantia"** — rotina que roda e não entrega nada é
justamente o que faz um inventário parecer mais saudável do que é.

## O que foi decidido

Desligar o cron do `hubspot_sync.yml`. O workflow fica com `workflow_dispatch`,
o script e o secret permanecem: reativar é recolocar uma linha.

## O que esperamos

Nada muda no painel, porque o HubSpot não alimentava nada. Some uma rotina
diária que dava a impressão de existir um CRM ativo.

## Revisar em

2027-03-14 — ou antes, se aparecer necessidade real de funil de vendas
(pacotes corporativos, contrato recorrente, algo com ciclo de negociação).

## Resultado

_(em branco até a revisão)_
