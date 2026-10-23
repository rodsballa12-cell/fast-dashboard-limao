# Conselho 2026-10-04 · Decisão #2 · Pipeline de dado — em jogo: metade do peso da semana (sáb+dom, ~R$ 6-7 mil só nesse fim de semana) invisível, e o problema se repete todo fim de semana até ser corrigido. Se nada for feito: o Conselho de hoje e o de segunda continuam decidindo sem metade do quadro. Decidir: autorizar checar o GitHub Actions / rodar o refresh manual dos três pipelines (painel e mídia) antes de confiar em qualquer leitura de ritmo. Executa: Operação (precisa de quem tenha acesso ao repositório).

**Data:** 2026-10-04 · **Hora do Conselho:** 22:30
**Origem:** Conselho noturno · Sincronizada automaticamente pelo
workflow `conselho_sync.yml`
**Status inicial:** pendente (aguarda o Rodrigo aprovar)

## Em jogo

(não capturado do briefing)

## Texto original do briefing

> Pipeline de dado — em jogo: metade do peso da semana (sáb+dom, ~R$ 6-7 mil só nesse fim de semana) invisível, e o problema se repete todo fim de semana até ser corrigido. Se nada for feito: o Conselho de hoje e o de segunda continuam decidindo sem metade do quadro. Decidir: autorizar checar o GitHub Actions / rodar o refresh manual dos três pipelines (painel e mídia) antes de confiar em qualquer leitura de ritmo. Executa: Operação (precisa de quem tenha acesso ao repositório).

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
