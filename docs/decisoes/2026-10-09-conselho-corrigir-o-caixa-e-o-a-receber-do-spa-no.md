# Conselho 2026-10-09 · Decisão #3 · Corrigir o caixa e o a-receber do Spa no `financeiro.json` (hoje mostra zero nos dois campos) usando o valor real do extrato Stone (R$ 8.435,50 a receber)

**APROVADA em 16/10/2026** — Rodrigo escolheu corrigir **na planilha do DRE**, não
no arquivo do painel. Executor: Rodrigo, orientado pelo Financeiro. Valor de
referência: R$ 8.435,50 a receber do Spa, do extrato Stone de 30/09. Ainda não
executada. Revisar em 2026-10-23.

**Data:** 2026-10-09 · **Hora do Conselho:** 22:30
**Origem:** Conselho noturno · Sincronizada automaticamente pelo
workflow `conselho_sync.yml`
**Status inicial:** pendente (aguarda o Rodrigo aprovar)

## Em jogo

R$ 8.435,50 que não aparecem na leitura de caixa do Spa hoje

## Texto original do briefing

> Corrigir o caixa e o a-receber do Spa no `financeiro.json` (hoje mostra zero nos dois campos) usando o valor real do extrato Stone (R$ 8.435,50 a receber) · em jogo: R$ 8.435,50 que não aparecem na leitura de caixa do Spa hoje · se nada for feito: qualquer decisão de caixa do Spa (inclusive sobre antecipação) é tomada com informação errada · executa: Financeiro, confirmando com quem alimenta a planilha.

## Executor

Financeiro, confirmando com quem alimenta a planilha

## Como sobrescrever

Se você mudou de ideia sobre esta decisão, rode `/sincronizar` manualmente
e responda com o status real (recusada/reprogramada/executada). Isso
sobrescreve o registro automático.

## Revisão

Sem prazo automático. Volte a esta decisão no próximo Conselho.

## Resultado

**EXECUTADA em 23/10/2026.** O Spa deixou de aparecer com caixa e a-receber zerados: o script passou a ler o extrato de cada loja, e depois descobriu-se que o Spa tem conta Stone propria. Aberta 11 dias.

Prova no histórico:

- `74a2aa3` — conselho 2026-10-20 11:30 · caixa e a-receber do Spa, por loja
- `9de9239` — painel: Spa com caixa proprio (conta Stone do Spa), consolidado = XP + Stone Spa

_Fechada na varredura de 23/10/2026, com evidência no próprio repositório. Se o desfecho não confere, corrija aqui — este campo é a memória, e memória errada custa mais que memória vazia._
