# Conselho 2026-10-03 · Decisão #1 · Destravar o refresh do painel antes de mais nada

**Data:** 2026-10-03 · **Hora do Conselho:** 22:30
**Origem:** Conselho noturno · Sincronizada automaticamente pelo
workflow `conselho_sync.yml`
**Status inicial:** pendente (aguarda o Rodrigo aprovar)

## Em jogo

visibilidade total do sábado, o dia que sozinho vale R$ 4.638,55 e 37,6% da semana — sem isso, nem a decisão nº 2 abaixo pode ser conferida pela ferramenta normal

## Texto original do briefing

> Destravar o refresh do painel antes de mais nada · em jogo: visibilidade total do sábado, o dia que sozinho vale R$ 4.638,55 e 37,6% da semana — sem isso, nem a decisão nº 2 abaixo pode ser conferida pela ferramenta normal · se nada for feito: a loja roda o dia mais forte da semana sem ninguém enxergar ocupação, cancelamento ou caixa em tempo real · executa: quem rodar o refresh precisa, nesta ordem, gerar `densidade_dow.py --gravar` antes de commitar e só depois `consolida_dashboard.py` — senão o mapa de escala some de novo, como em 14/09.

## Executor

quem rodar o refresh precisa, nesta ordem, gerar `densidade_dow.py --gravar` antes de commitar e só depois `consolida_dashboard.py` — senão o mapa de escala some de novo, como em 14/09

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
