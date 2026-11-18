# Os sete cargos rodam em fila de madrugada, fora da hora das outras rotinas

**Data:** 2026-11-18 · **Pedido do Rodrigo:** "ajuste o horário de todos os agentes para um horário que não corra o risco de ter estouro de cota" · **Revisar em:** 2026-12-02

## Situação

Os cargos e o conselho dividem a cota do Claude (5 horas e semanal) com mais oito rotinas do
Rodrigo (investimentos, cotações, mídias, cérebro, backup, LinkedIn). Falhas por cota:

| Dia | Quem | Mensagem |
|---|---|---|
| 11/11 | conselho 22h30 | 5-hour limit (janela aberta às 19h: cérebro + painel 19h14) |
| 13/11 | conselho 22h30 | weekly limit |
| 14/11 | memória, marketing, financeiro | 5-hour limit (janela aberta às 03h40) |

## Decisão

- Uma tarefa só no PC, `FAST\Rodada da madrugada`, às **00h40**, com os sete cargos em fila e o
  conselho por último. De 00h40 às 06h nenhuma outra rotina roda.
- Antes do meio-dia o dia de referência é **ontem** (`rodar_agente.ps1 -Ontem`): a
  ata leva a data do dia fechado, e a auditoria das 09h20 acha as sete.
- O conselho repetido do claude.ai (22h17) foi pausado.

## O que isto NÃO resolve

O **limite semanal**. Horário nenhum protege dele: se a semana inteira gastar demais, a fila da
madrugada também fica sem cota. Se voltar a aparecer "weekly limit", a saída é rodar menos
(por exemplo, cotações do pregão de hora em hora em vez de duas vezes por hora).

## Como saber se deu certo

Até 02/12: sete atas por dia em `docs/atas/`, nenhuma com "limit". `python3 scripts/auditoria_agenda.py`.
