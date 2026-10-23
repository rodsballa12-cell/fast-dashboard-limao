# Conselho 2026-09-25 · Decisão #1 · **Rodar o refresh do pipeline e apurar por que ficou 7 dias parado.** Em jogo: toda decisão de hoje — inclusive as duas abaixo — está sendo tomada com dado de uma semana atrás; se nada for feito, a abertura do Spa fica sem nenhum registro histórico, e esse dia não se repete. Executa: sessão do PC (só ela alcança os scripts locais), com Operação conferindo o resultado.

**Data:** 2026-09-25 · **Hora do Conselho:** 22:30
**Origem:** Conselho noturno · Sincronizada automaticamente pelo
workflow `conselho_sync.yml`
**Status:** aprovada pelo Rodrigo em 2026-10-09

## Em jogo

(não capturado do briefing)

## Texto original do briefing

> **Rodar o refresh do pipeline e apurar por que ficou 7 dias parado.** Em jogo: toda decisão de hoje — inclusive as duas abaixo — está sendo tomada com dado de uma semana atrás; se nada for feito, a abertura do Spa fica sem nenhum registro histórico, e esse dia não se repete. Executa: sessão do PC (só ela alcança os scripts locais), com Operação conferindo o resultado.

## Executor

A definir

## Como sobrescrever

Se você mudou de ideia sobre esta decisão, rode `/sincronizar` manualmente
e responda com o status real (recusada/reprogramada/executada). Isso
sobrescreve o registro automático.

## Revisão

Sem prazo automático. Volte a esta decisão no próximo Conselho.

## Resultado


**EXECUTADA em 23/10/2026.**

Os dois pipelines rodam. O do painel entregou `refresh: dashboard 23/10 06:43 BRT` (`6c333ac`) e o de midias `refresh midias: 23/10 06:41 BRT` (`80db435`), ambos pela nuvem, sem ninguem ligar o PC. Em 23/10 as 15 rotinas ganharam teto de tempo e substituicao de rodada travada (`5fc5446`) e um lugar que responde 'isso ainda funciona?' no topo do painel (`24b285f`) — o motivo pelo qual este pedido voltou oito vezes era justamente a falha que nao avisava.

_Fechada na varredura de 23/10/2026, com evidencia no proprio repositorio. Se o desfecho nao confere, corrija aqui — este campo e a memoria, e memoria errada custa mais que memoria vazia._
