# Memória antes de decisão financeira

**Data do aprendizado:** 2026-09-19
**Custo:** 2 Conselhos gastando cota de decisão em item já decidido
**Origem:** Rodrigo teve que recusar pela 2ª vez a mesma proposta
(antecipar R$ 8-10k da Stone), 5 dias depois de já ter recusado com
motivo registrado.

## O que aconteceu

- **14/09:** Conselho propõe antecipar R$ 20.949 da Stone. Rodrigo
  recusa. Motivo registrado: reserva XP R$ 500k cobre custo fixo,
  antecipação destrói valor (custo 2-3% > CDI da reserva). Decisão
  gravada em `docs/decisoes/2026-09-14-conselho-nao-antecipar-stone.md`.
- **18/09 (4 dias depois):** Conselho volta a propor antecipar R$ 8-10k
  da Stone. Não consultou a decisão de 14/09. Rodrigo recusa de novo,
  reafirmando o mesmo motivo.

## Por que aconteceu

O Conselho lê Financeiro (bloco Stone, caixa, custo fixo), vê o alarme
puro (caixa < 2 dias de custo fixo) e monta a decisão sem cruzar com a
Memória — que já tem o motivo pra ignorar esse alarme registrado.

## Regra emergente

**Toda decisão financeira que envolva ≥R$ 5k passa pela Memória antes
de ir pro Rodrigo.** O passo é 1 grep em `docs/decisoes/`:

```bash
grep -ril "<assunto ou valor>" docs/decisoes/
```

Se aparecer decisão anterior sobre o mesmo assunto, o Conselho tem duas
opções: (a) manter a decisão antiga e não propor de novo, (b) propor
com evidência explícita do que mudou desde a decisão antiga.

Nunca propor a mesma coisa sem citar a decisão anterior.

## Onde essa regra vive

- Skill `/conselho`: no Passo 6 (decidir o que vai pro Rodrigo), rodar
  o grep antes de escrever cada decisão.
- Skill `/financeiro`: no bloco "Recomenda", checar se a recomendação
  já é decisão antiga antes de escrever.

## Custo real do erro

- 1ª vez (14/09): 1 rodada de Conselho perdida
- 2ª vez (18/09): 1 rodada de Conselho perdida + confiança do Rodrigo
  no filtro do Conselho corroída · a próxima vez que o Conselho fizer
  uma proposta ousada, ele vai desconfiar antes de ler
- Se acontecer 3ª vez: Rodrigo para de ler decisões do Conselho

## Como saber se funcionou

Se nas próximas 4 semanas o Rodrigo não precisar recusar uma proposta
já registrada como decisão, a regra pegou. Se acontecer de novo, é
sinal de que a regra precisa virar hook automatizado (script que roda
antes do briefing e alerta o Conselho).
